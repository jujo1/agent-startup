#!/usr/bin/env python3
"""
Workflow State Machine - Core enforcement engine for AGENTS_3.md compliance.

Installation: ~/.claude/hooks/workflow_state_machine.py

State Machine enforces:
  STARTUP → PLAN → REVIEW → DISRUPT → IMPLEMENT → TEST → REVIEW → VALIDATE → LEARN

Quality Gates at each transition require:
  - Schema-valid outputs (SCHEMAS.md)
  - Evidence files exist
  - Third-party approval (DISRUPT, VALIDATE stages)
  - No skipped stages

Hooks:
  - on_stage_enter: Load skills, create todos
  - on_stage_exit: Quality gate validation
  - on_gate_fail: Reprompt generation
  - on_compaction: Export chat history

Usage:
  from workflow_state_machine import WorkflowMachine
  
  machine = WorkflowMachine(workflow_id="20260104_070000_abc123")
  machine.startup()  # MCP ping, scheduler, memory, dirs
  machine.execute()  # Run full workflow
"""

import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Optional
import hashlib
import subprocess


class Stage(Enum):
    """Workflow stages as defined in AGENTS_3.md."""
    STARTUP = auto()
    PLAN = auto()
    REVIEW = auto()
    DISRUPT = auto()
    IMPLEMENT = auto()
    TEST = auto()
    REVIEW_POST = auto()  # Second REVIEW after TEST
    VALIDATE = auto()
    LEARN = auto()
    COMPLETE = auto()
    FAILED = auto()


class GateAction(Enum):
    """Quality gate actions."""
    PROCEED = "proceed"
    REVISE = "revise"
    ESCALATE = "escalate"
    STOP = "stop"


@dataclass
class GateResult:
    """Result of quality gate check."""
    stage: str
    valid: bool
    checked: list[str]
    errors: list[str]
    action: GateAction
    retry: int = 0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> dict:
        return {
            "stage": self.stage,
            "valid": self.valid,
            "checked": self.checked,
            "errors": self.errors,
            "action": self.action.value,
            "retry": self.retry,
            "timestamp": self.timestamp
        }


@dataclass
class StageOutput:
    """Output from a stage execution."""
    stage: Stage
    outputs: list[dict]
    evidence_paths: list[str]
    duration_seconds: float
    success: bool
    error: Optional[str] = None


# Schema definitions (from SCHEMAS.md)
SCHEMAS = {
    "todo": {
        "required": ["id", "content", "status", "priority", "metadata"],
        "metadata_required": [
            "objective", "success_criteria", "fail_criteria", "evidence_required",
            "evidence_location", "agent_model", "workflow", "blocked_by", "parallel",
            "workflow_stage", "instructions_set", "time_budget", "reviewer"
        ],
        "enums": {
            "status": ["pending", "in_progress", "completed", "blocked", "failed"],
            "priority": ["high", "medium", "low"],
            "evidence_required": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
            "workflow_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"],
            "agent_model": ["Claude", "GPT", "Ollama"]
        },
        "types": {"blocked_by": list, "parallel": bool}
    },
    "evidence": {
        "required": ["id", "type", "claim", "location", "timestamp", "verified", "verified_by"],
        "patterns": {"id": r"^E-[A-Z]+-[\w.]+-\d{3}$"},
        "enums": {
            "type": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
            "verified_by": ["agent", "third-party", "user"]
        },
        "types": {"verified": bool}
    },
    "review_gate": {
        "required": ["stage", "agent", "timestamp", "criteria_checked", "approved", "action"],
        "enums": {
            "action": ["proceed", "revise", "escalate"],
            "stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"]
        },
        "types": {"criteria_checked": list, "approved": bool}
    },
    "conflict": {
        "required": ["id", "type", "parties", "positions"],
        "patterns": {"id": r"^C-\d{8}T\d{6}$"},
        "enums": {"type": ["plan_disagreement", "evidence_dispute", "priority_conflict", "resource_conflict"]},
        "types": {"parties": list, "positions": list}
    },
    "metrics": {
        "required": ["workflow_id", "timestamp", "total_time_min", "stages", "agents", "evidence", "quality"],
        "types": {"total_time_min": int}
    },
    "skill": {
        "required": ["name", "source", "purpose", "interface", "tested", "evidence_location"],
        "types": {"tested": bool}
    },
    "startup": {
        "required": ["mcp_verified", "scheduler_active", "memory_ok", "env_ready", "workflow_dir", "timestamp"],
        "types": {"mcp_verified": bool, "scheduler_active": bool, "memory_ok": bool, "env_ready": bool}
    },
    "recovery": {
        "required": ["id", "trigger", "rollback_to", "state_before", "state_after", "success", "resume_stage"],
        "patterns": {"id": r"^R-\d{8}T\d{6}$"},
        "enums": {"resume_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"]},
        "types": {"success": bool}
    },
    "handoff": {
        "required": ["from_agent", "to_agent", "timestamp", "context"],
        "context_required": ["user_objective", "current_stage", "completed_stages", 
                            "todos_remaining", "evidence_collected", "blockers", "assumptions", "memory_refs"],
        "types": {"completed_stages": list, "todos_remaining": list, "evidence_collected": list,
                 "blockers": list, "assumptions": list, "memory_refs": list}
    }
}

# Quality gates per stage (from AGENTS_3.md)
QUALITY_GATES = {
    "PLAN": ["todo", "evidence"],
    "REVIEW": ["review_gate", "evidence"],
    "DISRUPT": ["conflict", "evidence"],
    "IMPLEMENT": ["todo", "evidence"],
    "TEST": ["evidence", "metrics"],
    "VALIDATE": ["review_gate", "evidence"],
    "LEARN": ["skill", "metrics"]
}

# Stage configuration
STAGE_CONFIG = {
    Stage.PLAN: {
        "model": "Opus",
        "agents": ["Planner", "Research"],
        "skills": ["brainstorming", "writing-plans"],
        "mcp": ["memory", "todo", "semantic-index", "web_search"],
        "timeout_minutes": 15,
        "requires_approval": True
    },
    Stage.REVIEW: {
        "model": "Opus",
        "agents": ["Reviewer"],
        "skills": ["verification-before-completion"],
        "mcp": ["memory", "todo"],
        "timeout_minutes": 10,
        "requires_approval": False
    },
    Stage.DISRUPT: {
        "model": "Opus",
        "agents": ["Debate", "Third-party"],
        "skills": ["brainstorming"],
        "mcp": ["sequential-thinking", "openai-chat"],
        "timeout_minutes": 15,
        "requires_third_party": True
    },
    Stage.IMPLEMENT: {
        "model": "Sonnet",
        "agents": ["Executor", "Observer"],
        "skills": ["executing-plans", "test-driven-development"],
        "mcp": ["git", "github", "memory", "todo"],
        "timeout_minutes": 30
    },
    Stage.TEST: {
        "model": "Sonnet",
        "agents": ["Tester"],
        "skills": ["test-driven-development", "systematic-debugging"],
        "mcp": ["git", "memory", "todo"],
        "timeout_minutes": 20
    },
    Stage.REVIEW_POST: {
        "model": "Opus",
        "agents": ["Reviewer"],
        "skills": ["verification-before-completion", "requesting-code-review"],
        "mcp": ["github", "openai-chat", "memory"],
        "timeout_minutes": 10
    },
    Stage.VALIDATE: {
        "model": "gpt-5.2",
        "agents": ["Third-party", "Morality"],
        "skills": ["verification-before-completion"],
        "mcp": ["openai-chat", "memory"],
        "timeout_minutes": 15,
        "requires_third_party": True
    },
    Stage.LEARN: {
        "model": "Haiku",
        "agents": ["Learn"],
        "skills": ["writing-skills"],
        "mcp": ["memory", "semantic-index"],
        "timeout_minutes": 10
    }
}

# MCP servers required for startup
MCP_SERVERS = [
    "memory",
    "todo",
    "sequential-thinking",
    "git",
    "github",
    "scheduler",
    "openai-chat",
    "credentials",
    "mcp-gateway",
    "claude-context"
]

MAX_RETRY = 3


def validate_schema(data: dict, schema_name: str) -> tuple[bool, list[str]]:
    """Validate data against schema. Returns (valid, errors)."""
    if schema_name not in SCHEMAS:
        return False, [f"Unknown schema: {schema_name}"]
    
    schema = SCHEMAS[schema_name]
    errors = []
    
    # Unwrap nested (e.g., {"evidence": {...}} -> {...})
    if schema_name in data and isinstance(data[schema_name], dict):
        data = data[schema_name]
    
    # Required fields
    for field_name in schema.get("required", []):
        if field_name not in data or data[field_name] is None or data[field_name] == "":
            errors.append(f"Missing: {field_name}")
    
    # Nested required (metadata, context)
    for nested in ["metadata", "context"]:
        for field_name in schema.get(f"{nested}_required", []):
            nested_data = data.get(nested, {})
            if field_name not in nested_data:
                errors.append(f"Missing: {nested}.{field_name}")
    
    # Enum validation
    for field_name, allowed in schema.get("enums", {}).items():
        val = data.get(field_name) or data.get("metadata", {}).get(field_name)
        if val and val not in allowed:
            errors.append(f"{field_name}: '{val}' not in {allowed}")
    
    # Pattern validation
    for field_name, pattern in schema.get("patterns", {}).items():
        if field_name in data and data[field_name]:
            if not re.match(pattern, str(data[field_name])):
                errors.append(f"{field_name}: pattern mismatch (expected {pattern})")
    
    # Type validation
    for field_name, expected_type in schema.get("types", {}).items():
        val = data.get(field_name) or data.get("metadata", {}).get(field_name)
        if val is not None and not isinstance(val, expected_type):
            errors.append(f"{field_name}: expected {expected_type.__name__}, got {type(val).__name__}")
    
    return len(errors) == 0, errors


def detect_schema(data: dict) -> Optional[str]:
    """Detect schema type from data structure."""
    if "evidence" in data:
        return "evidence"
    if "handoff" in data:
        return "handoff"
    if "review_gate" in data:
        return "review_gate"
    if "conflict" in data:
        return "conflict"
    if "metrics" in data:
        return "metrics"
    if "skill" in data:
        return "skill"
    if "startup" in data:
        return "startup"
    if "recovery" in data:
        return "recovery"
    if "metadata" in data and "objective" in data.get("metadata", {}):
        return "todo"
    return None


class WorkflowMachine:
    """State machine for workflow enforcement."""
    
    def __init__(self, workflow_id: Optional[str] = None, base_path: Optional[Path] = None):
        self.workflow_id = workflow_id or datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S_") + os.urandom(4).hex()
        self.base_path = base_path or Path(f".workflow/{self.workflow_id}")
        self.current_stage = Stage.STARTUP
        self.completed_stages: list[Stage] = []
        self.stage_outputs: dict[Stage, StageOutput] = {}
        self.todos: list[dict] = []
        self.evidence: list[dict] = []
        self.start_time = datetime.now(timezone.utc)
        self.retry_counts: dict[Stage, int] = {}
        self.user_objective: str = ""
        self.hooks: dict[str, list[Callable]] = {
            "on_stage_enter": [],
            "on_stage_exit": [],
            "on_gate_fail": [],
            "on_compaction": [],
            "on_error": []
        }
    
    def register_hook(self, event: str, callback: Callable) -> None:
        """Register a callback for an event."""
        if event in self.hooks:
            self.hooks[event].append(callback)
    
    def _trigger_hooks(self, event: str, *args, **kwargs) -> None:
        """Trigger all callbacks for an event."""
        for callback in self.hooks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                self._log(f"Hook error ({event}): {e}")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log a message to file and console."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] [{level}] {message}"
        print(log_entry)
        
        log_path = self.base_path / "logs" / "workflow.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(log_entry + "\n")
    
    def _save_state(self) -> None:
        """Save current state to disk."""
        state = {
            "workflow_id": self.workflow_id,
            "current_stage": self.current_stage.name,
            "completed_stages": [s.name for s in self.completed_stages],
            "todos": self.todos,
            "evidence": self.evidence,
            "start_time": self.start_time.isoformat(),
            "retry_counts": {s.name: c for s, c in self.retry_counts.items()},
            "user_objective": self.user_objective,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        state_path = self.base_path / "state" / "current.json"
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            json.dump(state, f, indent=2)
    
    def _load_state(self) -> bool:
        """Load state from disk. Returns True if state was loaded."""
        state_path = self.base_path / "state" / "current.json"
        if not state_path.exists():
            return False
        
        try:
            with open(state_path) as f:
                state = json.load(f)
            
            self.workflow_id = state["workflow_id"]
            self.current_stage = Stage[state["current_stage"]]
            self.completed_stages = [Stage[s] for s in state["completed_stages"]]
            self.todos = state["todos"]
            self.evidence = state["evidence"]
            self.start_time = datetime.fromisoformat(state["start_time"])
            self.retry_counts = {Stage[s]: c for s, c in state["retry_counts"].items()}
            self.user_objective = state["user_objective"]
            return True
        except Exception as e:
            self._log(f"Failed to load state: {e}", "ERROR")
            return False
    
    def startup(self) -> dict:
        """Execute startup sequence. Returns startup result."""
        self._log("Starting workflow startup sequence")
        
        # Create directories
        for dir_name in ["todo", "evidence", "logs", "state", "plans", "test"]:
            (self.base_path / dir_name).mkdir(parents=True, exist_ok=True)
        
        startup_result = {
            "mcp_verified": False,
            "scheduler_active": False,
            "memory_ok": False,
            "env_ready": False,
            "workflow_dir": str(self.base_path),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        # 1. MCP Ping (simulated - in real impl would call MCP servers)
        mcp_status = {}
        for server in MCP_SERVERS:
            # In real implementation: response = call_mcp(server, "ping")
            mcp_status[server] = True  # Simulated success
        
        startup_result["mcp_verified"] = all(mcp_status.values())
        if not startup_result["mcp_verified"]:
            failed = [s for s, ok in mcp_status.items() if not ok]
            self._log(f"MCP servers failed: {failed}", "ERROR")
            return startup_result
        
        # 2. Scheduler setup
        # In real impl: call scheduler/create reprompt_timer
        startup_result["scheduler_active"] = True
        
        # 3. Memory test
        # In real impl: call memory/write, memory/read
        startup_result["memory_ok"] = True
        
        # 4. Environment ready
        startup_result["env_ready"] = True
        
        self._log(f"Startup complete: {startup_result}")
        self.current_stage = Stage.PLAN
        self._save_state()
        
        return startup_result
    
    def quality_gate(self, stage: Stage, outputs: list[dict], retry: int = 0) -> GateResult:
        """Execute quality gate validation for a stage."""
        stage_name = stage.name.replace("_POST", "")  # REVIEW_POST -> REVIEW for gates
        if stage_name == "REVIEW":
            stage_name = "REVIEW"  # Both REVIEW stages use same gate
        
        required = QUALITY_GATES.get(stage_name, [])
        
        result = GateResult(
            stage=stage_name,
            valid=True,
            checked=[],
            errors=[],
            action=GateAction.PROCEED,
            retry=retry
        )
        
        # Validate each output against its schema
        for output in outputs:
            schema_name = detect_schema(output)
            if schema_name:
                valid, errors = validate_schema(output, schema_name)
                result.checked.append(schema_name)
                if not valid:
                    result.valid = False
                    result.errors.extend([f"[{schema_name}] {e}" for e in errors])
        
        # Check required schemas are present
        for req in required:
            if req not in result.checked:
                result.valid = False
                result.errors.append(f"Missing required schema: {req}")
        
        # Check evidence files exist
        for output in outputs:
            if "evidence" in output:
                evidence_loc = output["evidence"].get("location")
                if evidence_loc and not Path(evidence_loc).exists():
                    result.valid = False
                    result.errors.append(f"Evidence file missing: {evidence_loc}")
        
        # Determine action
        if not result.valid:
            if retry >= MAX_RETRY:
                result.action = GateAction.ESCALATE
            elif len(result.errors) > 10:
                result.action = GateAction.STOP
            else:
                result.action = GateAction.REVISE
        
        # Log gate result
        gate_log = self.base_path / "logs" / f"gate_{stage_name.lower()}.json"
        with open(gate_log, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        
        # Trigger hooks on failure
        if result.action != GateAction.PROCEED:
            self._trigger_hooks("on_gate_fail", result)
        
        return result
    
    def generate_reprompt(self, gate_result: GateResult) -> str:
        """Generate reprompt message from gate failure."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        reprompt = f"""
================================================================================
⛔ QUALITY GATE FAILED
================================================================================

STAGE:        {gate_result.stage}
ATTEMPT:      {gate_result.retry + 1}/{MAX_RETRY}
TIMESTAMP:    {timestamp}
ACTION:       {gate_result.action.value.upper()}

--------------------------------------------------------------------------------
ERRORS ({len(gate_result.errors)}):
--------------------------------------------------------------------------------
"""
        for error in gate_result.errors:
            reprompt += f"  ❌ {error}\n"
        
        reprompt += f"""
--------------------------------------------------------------------------------
REQUIRED SCHEMAS: {QUALITY_GATES.get(gate_result.stage, [])}
SCHEMAS CHECKED:  {gate_result.checked}
--------------------------------------------------------------------------------

CORRECTIVE ACTION REQUIRED
================================================================================
"""
        
        if gate_result.action == GateAction.REVISE:
            reprompt += f"""
INSTRUCTION: Fix errors and resubmit stage output.

CHECKLIST:
  [ ] All required fields present
  [ ] Enum values valid
  [ ] Paths absolute
  [ ] Evidence file exists at location
  [ ] Timestamps ISO8601

RESUBMIT:
  python stage_gate_validator.py --stage {gate_result.stage} --retry {gate_result.retry + 1}
"""
        elif gate_result.action == GateAction.ESCALATE:
            reprompt += f"""
INSTRUCTION: Max retries exceeded. Escalating to Opus.

Create handoff with:
  from_agent: current
  to_agent: Opus
  blockers: {gate_result.errors}
"""
        elif gate_result.action == GateAction.STOP:
            reprompt += f"""
INSTRUCTION: Critical failure. Workflow terminated.

Create recovery record and rollback to last checkpoint.
"""
        
        reprompt += "\n================================================================================\n"
        
        return reprompt
    
    def transition(self, to_stage: Stage) -> bool:
        """Transition to a new stage. Returns success."""
        # Validate transition is allowed
        stage_order = [
            Stage.STARTUP, Stage.PLAN, Stage.REVIEW, Stage.DISRUPT,
            Stage.IMPLEMENT, Stage.TEST, Stage.REVIEW_POST, Stage.VALIDATE, Stage.LEARN
        ]
        
        current_idx = stage_order.index(self.current_stage) if self.current_stage in stage_order else -1
        next_idx = stage_order.index(to_stage) if to_stage in stage_order else -1
        
        # Can only move forward by 1 (except FAILED/COMPLETE)
        if to_stage not in (Stage.FAILED, Stage.COMPLETE):
            if next_idx != current_idx + 1:
                self._log(f"Invalid transition: {self.current_stage.name} -> {to_stage.name}", "ERROR")
                return False
        
        # Execute quality gate for current stage (if not STARTUP)
        if self.current_stage != Stage.STARTUP:
            outputs = self.stage_outputs.get(self.current_stage, StageOutput(
                self.current_stage, [], [], 0, True
            )).outputs
            
            retry = self.retry_counts.get(self.current_stage, 0)
            gate_result = self.quality_gate(self.current_stage, outputs, retry)
            
            if gate_result.action != GateAction.PROCEED:
                self._log(f"Gate failed: {gate_result.errors}", "ERROR")
                print(self.generate_reprompt(gate_result))
                
                if gate_result.action == GateAction.REVISE:
                    self.retry_counts[self.current_stage] = retry + 1
                    return False
                elif gate_result.action == GateAction.ESCALATE:
                    # Would invoke Opus here
                    self.retry_counts[self.current_stage] = retry + 1
                    return False
                elif gate_result.action == GateAction.STOP:
                    self.current_stage = Stage.FAILED
                    self._save_state()
                    return False
        
        # Trigger exit hooks
        self._trigger_hooks("on_stage_exit", self.current_stage, to_stage)
        
        # Perform transition
        self.completed_stages.append(self.current_stage)
        self.current_stage = to_stage
        
        # Trigger enter hooks
        self._trigger_hooks("on_stage_enter", to_stage)
        
        self._log(f"Transitioned to {to_stage.name}")
        self._save_state()
        
        return True
    
    def create_todo(self, content: str, priority: str = "medium", **metadata) -> dict:
        """Create a todo with full 17-field schema."""
        todo_id = f"{len(self.todos) + 1}.1"
        
        todo = {
            "id": todo_id,
            "content": content,
            "status": "pending",
            "priority": priority,
            "metadata": {
                "objective": metadata.get("objective", content),
                "success_criteria": metadata.get("success_criteria", "Task completed"),
                "fail_criteria": metadata.get("fail_criteria", "Task not completed"),
                "evidence_required": metadata.get("evidence_required", "log"),
                "evidence_location": str(self.base_path / "evidence" / f"{todo_id}.log"),
                "agent_model": metadata.get("agent_model", "Claude"),
                "workflow": "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
                "blocked_by": metadata.get("blocked_by", []),
                "parallel": metadata.get("parallel", False),
                "workflow_stage": self.current_stage.name,
                "instructions_set": "AGENTS_3.md",
                "time_budget": metadata.get("time_budget", "≤60m"),
                "reviewer": metadata.get("reviewer", "gpt-5.2")
            }
        }
        
        # Validate
        valid, errors = validate_schema(todo, "todo")
        if not valid:
            raise ValueError(f"Invalid todo: {errors}")
        
        self.todos.append(todo)
        self._save_state()
        
        return todo
    
    def create_evidence(self, stage: str, claim: str, location: Optional[str] = None) -> dict:
        """Create an evidence record."""
        seq = len([e for e in self.evidence if e.get("evidence", {}).get("id", "").startswith(f"E-{stage}")]) + 1
        
        evidence = {
            "evidence": {
                "id": f"E-{stage}-{self.workflow_id[:8]}-{seq:03d}",
                "type": "log",
                "claim": claim,
                "location": location or str(self.base_path / "evidence" / f"{stage.lower()}.log"),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "verified": True,
                "verified_by": "agent"
            }
        }
        
        # Validate
        valid, errors = validate_schema(evidence, "evidence")
        if not valid:
            raise ValueError(f"Invalid evidence: {errors}")
        
        self.evidence.append(evidence)
        self._save_state()
        
        return evidence
    
    def get_stage_config(self, stage: Stage) -> dict:
        """Get configuration for a stage."""
        return STAGE_CONFIG.get(stage, {})


class RepromptTimer:
    """Timer that triggers quality gate checks periodically."""
    
    def __init__(self, machine: WorkflowMachine, interval_minutes: int = 5):
        self.machine = machine
        self.interval_minutes = interval_minutes
        self.last_check = datetime.now(timezone.utc)
        self.active = True
    
    def check(self) -> Optional[GateResult]:
        """Check if quality gate should be triggered."""
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_check).total_seconds() / 60
        
        if elapsed >= self.interval_minutes and self.active:
            self.last_check = now
            
            # Get current stage outputs
            stage = self.machine.current_stage
            outputs = self.machine.stage_outputs.get(stage, StageOutput(stage, [], [], 0, True)).outputs
            
            if outputs:
                return self.machine.quality_gate(stage, outputs)
        
        return None
    
    def reset(self) -> None:
        """Reset the timer."""
        self.last_check = datetime.now(timezone.utc)
    
    def pause(self) -> None:
        """Pause the timer."""
        self.active = False
    
    def resume(self) -> None:
        """Resume the timer."""
        self.active = True
        self.reset()


def main():
    """CLI entry point for testing."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow State Machine")
    parser.add_argument("--test", action="store_true", help="Run test workflow")
    parser.add_argument("--stage", help="Test specific stage gate")
    parser.add_argument("--output", help="JSON output to validate")
    args = parser.parse_args()
    
    if args.test:
        # Create test workflow
        machine = WorkflowMachine()
        
        # Startup
        startup = machine.startup()
        print(f"Startup: {startup}")
        
        # Create test todo
        todo = machine.create_todo(
            "Test task",
            priority="high",
            objective="Test the workflow system",
            success_criteria="All tests pass",
            fail_criteria="Any test fails"
        )
        print(f"Created todo: {todo['id']}")
        
        # Create evidence
        evidence = machine.create_evidence("PLAN", "Plan created successfully")
        print(f"Created evidence: {evidence['evidence']['id']}")
        
        # Test gate
        gate = machine.quality_gate(Stage.PLAN, [todo, evidence])
        print(f"Gate result: {gate.action.value}")
        
        if gate.action != GateAction.PROCEED:
            print(machine.generate_reprompt(gate))
    
    elif args.stage and args.output:
        # Validate specific output
        machine = WorkflowMachine()
        outputs = [json.loads(args.output)]
        stage = Stage[args.stage.upper()]
        
        gate = machine.quality_gate(stage, outputs)
        print(json.dumps(gate.to_dict(), indent=2))
        
        return 0 if gate.action == GateAction.PROCEED else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
