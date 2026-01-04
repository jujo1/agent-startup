#!/usr/bin/env python3
"""
Reprompt Timer Hook - Triggers quality gate checks on interval and compaction events.

Installation: ~/.claude/hooks/reprompt_timer.py

Triggers:
  1. Every 5 minutes (configurable)
  2. Before context compaction (pre_compaction event)
  3. On stage transition
  4. On explicit check request

Actions on trigger:
  1. Load current stage outputs
  2. Validate against SCHEMAS.md
  3. Generate reprompt if validation fails
  4. Log gate result to .workflow/logs/

Usage:
  # Start timer (background)
  python reprompt_timer.py --start --interval 5
  
  # Manual check
  python reprompt_timer.py --check
  
  # Check specific stage
  python reprompt_timer.py --stage IMPLEMENT --outputs outputs.json

Environment:
  REPROMPT_INTERVAL=5  # Minutes between checks
  WORKFLOW_DIR=.workflow
  CURRENT_STAGE=PLAN
"""

import json
import os
import sys
import time
import signal
import threading
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Callable
import argparse

# Import from workflow_state_machine
sys.path.insert(0, str(Path(__file__).parent.parent))
from workflow_state_machine import (
    WorkflowMachine, Stage, GateAction, GateResult,
    QUALITY_GATES, validate_schema, detect_schema, MAX_RETRY
)


class RepromptTimer:
    """Timer that triggers quality gate checks periodically."""
    
    def __init__(
        self,
        interval_minutes: int = 5,
        workflow_dir: Optional[Path] = None,
        on_gate_fail: Optional[Callable[[GateResult], None]] = None
    ):
        self.interval_minutes = interval_minutes
        self.interval_seconds = interval_minutes * 60
        self.workflow_dir = workflow_dir or Path(os.environ.get("WORKFLOW_DIR", ".workflow"))
        self.on_gate_fail = on_gate_fail
        
        self.last_check = datetime.now(timezone.utc)
        self.active = False
        self.timer_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        
        self.check_count = 0
        self.fail_count = 0
        self.last_result: Optional[GateResult] = None
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message to file and console."""
        timestamp = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{timestamp}] [REPROMPT] [{level}] {message}"
        print(log_entry)
        
        log_path = self.workflow_dir / "logs" / "reprompt_timer.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(log_entry + "\n")
    
    def _get_current_stage(self) -> Optional[Stage]:
        """Get current stage from state file."""
        state_path = self.workflow_dir / "state" / "current.json"
        if not state_path.exists():
            return None
        
        try:
            with open(state_path) as f:
                state = json.load(f)
            return Stage[state.get("current_stage", "PLAN")]
        except Exception as e:
            self._log(f"Failed to read state: {e}", "ERROR")
            return None
    
    def _get_stage_outputs(self, stage: Stage) -> list[dict]:
        """Get outputs for a stage from workflow directory."""
        outputs = []
        
        # Check stage output file
        output_path = self.workflow_dir / f"{stage.name.lower()}_output.json"
        if output_path.exists():
            try:
                with open(output_path) as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        outputs.extend(data)
                    else:
                        outputs.append(data)
            except Exception as e:
                self._log(f"Failed to read outputs: {e}", "ERROR")
        
        # Check todo directory
        todo_path = self.workflow_dir / "todo" / "todos.json"
        if todo_path.exists():
            try:
                with open(todo_path) as f:
                    todos = json.load(f)
                    if isinstance(todos, list):
                        outputs.extend(todos)
            except Exception:
                pass
        
        # Check evidence directory
        evidence_dir = self.workflow_dir / "evidence"
        if evidence_dir.exists():
            for evidence_file in evidence_dir.glob("*.json"):
                try:
                    with open(evidence_file) as f:
                        outputs.append(json.load(f))
                except Exception:
                    pass
        
        return outputs
    
    def _get_retry_count(self, stage: Stage) -> int:
        """Get retry count for a stage."""
        retry_path = self.workflow_dir / "state" / f"retry_{stage.name.lower()}.txt"
        if retry_path.exists():
            try:
                return int(retry_path.read_text().strip())
            except Exception:
                pass
        return 0
    
    def _increment_retry(self, stage: Stage) -> int:
        """Increment and return retry count for a stage."""
        count = self._get_retry_count(stage) + 1
        retry_path = self.workflow_dir / "state" / f"retry_{stage.name.lower()}.txt"
        retry_path.parent.mkdir(parents=True, exist_ok=True)
        retry_path.write_text(str(count))
        return count
    
    def check(self) -> Optional[GateResult]:
        """Run quality gate check on current stage."""
        self.check_count += 1
        self._log(f"Running quality gate check #{self.check_count}")
        
        # Get current stage
        stage = self._get_current_stage()
        if not stage:
            self._log("No current stage found", "WARN")
            return None
        
        if stage in (Stage.STARTUP, Stage.COMPLETE, Stage.FAILED):
            self._log(f"Stage {stage.name} does not require quality gate")
            return None
        
        # Get stage outputs
        outputs = self._get_stage_outputs(stage)
        if not outputs:
            self._log(f"No outputs found for stage {stage.name}", "WARN")
            # Create a minimal check result
            result = GateResult(
                stage=stage.name,
                valid=False,
                checked=[],
                errors=["No outputs found for stage"],
                action=GateAction.REVISE,
                retry=self._get_retry_count(stage)
            )
            self.last_result = result
            return result
        
        # Run quality gate
        retry = self._get_retry_count(stage)
        result = self._quality_gate(stage, outputs, retry)
        self.last_result = result
        
        # Handle result
        if result.action != GateAction.PROCEED:
            self.fail_count += 1
            self._log(f"Gate FAILED: {result.action.value}", "WARN")
            
            # Generate reprompt
            reprompt = self._generate_reprompt(result)
            print("\n" + reprompt)
            
            # Save reprompt
            reprompt_path = self.workflow_dir / "logs" / f"reprompt_{stage.name.lower()}_{self.check_count}.md"
            reprompt_path.write_text(reprompt)
            
            # Call callback
            if self.on_gate_fail:
                self.on_gate_fail(result)
            
            # Increment retry
            self._increment_retry(stage)
        else:
            self._log(f"Gate PASSED for stage {stage.name}")
        
        # Log result
        gate_log = self.workflow_dir / "logs" / f"gate_{stage.name.lower()}_{self.check_count}.json"
        gate_log.parent.mkdir(parents=True, exist_ok=True)
        with open(gate_log, "w") as f:
            json.dump(result.to_dict(), f, indent=2)
        
        return result
    
    def _quality_gate(self, stage: Stage, outputs: list[dict], retry: int = 0) -> GateResult:
        """Execute quality gate validation."""
        stage_name = stage.name.replace("_POST", "")
        required = QUALITY_GATES.get(stage_name, [])
        
        result = GateResult(
            stage=stage_name,
            valid=True,
            checked=[],
            errors=[],
            action=GateAction.PROCEED,
            retry=retry
        )
        
        # Validate each output
        for output in outputs:
            schema = detect_schema(output)
            if schema:
                valid, errors = validate_schema(output, schema)
                result.checked.append(schema)
                if not valid:
                    result.valid = False
                    result.errors.extend([f"[{schema}] {e}" for e in errors])
        
        # Check required schemas present
        for req in required:
            if req not in result.checked:
                result.valid = False
                result.errors.append(f"Missing required schema: {req}")
        
        # Determine action
        if not result.valid:
            if retry >= MAX_RETRY:
                result.action = GateAction.ESCALATE
            elif len(result.errors) > 10:
                result.action = GateAction.STOP
            else:
                result.action = GateAction.REVISE
        
        return result
    
    def _generate_reprompt(self, gate_result: GateResult) -> str:
        """Generate reprompt message."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Schema descriptions
        schema_desc = {
            "todo": "Task with 17 fields: id, content, status, priority, metadata.*",
            "evidence": "Proof with id (E-{stage}-{task}-{seq}), type, claim, location, verified",
            "review_gate": "Gate result with stage, agent, criteria_checked[], approved, action",
            "conflict": "Dispute with id, type, parties[], positions[], resolution",
            "metrics": "Stats with workflow_id, stages.*, agents.*, evidence.*, quality.*",
            "skill": "Capability with name, source, purpose, interface, tested, evidence_location",
            "handoff": "Transfer with from_agent, to_agent, context.*, instructions",
        }
        
        required = QUALITY_GATES.get(gate_result.stage, [])
        missing = [s for s in required if s not in gate_result.checked]
        
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
        
        if missing:
            reprompt += f"""
--------------------------------------------------------------------------------
REQUIRED SCHEMAS NOT SATISFIED:
--------------------------------------------------------------------------------
"""
            for schema in missing:
                reprompt += f"  ⚠️  {schema}: {schema_desc.get(schema, 'Unknown')}\n"
        
        reprompt += f"""
--------------------------------------------------------------------------------
SCHEMAS CHECKED:
--------------------------------------------------------------------------------
"""
        for schema in gate_result.checked:
            status = "✅" if schema in required else "ℹ️"
            reprompt += f"  {status} {schema}\n"
        
        reprompt += """
================================================================================
CORRECTIVE ACTION REQUIRED
================================================================================
"""
        
        if gate_result.action == GateAction.REVISE:
            reprompt += f"""
INSTRUCTION: Fix errors and resubmit stage output.

CHECKLIST:
  [ ] All required fields present
  [ ] Enum values valid (status, priority, evidence_required, etc.)
  [ ] Paths absolute
  [ ] Evidence file exists at location
  [ ] Timestamps ISO8601

RESUBMIT COMMAND:
  python reprompt_timer.py --check

REQUIRED SCHEMAS: {required}
"""
        elif gate_result.action == GateAction.ESCALATE:
            reprompt += f"""
INSTRUCTION: Max retries ({MAX_RETRY}) exceeded. Escalating to Opus.

HANDOFF TEMPLATE:
{{
  "handoff": {{
    "from_agent": "Sonnet",
    "to_agent": "Opus",
    "timestamp": "{timestamp}",
    "context": {{
      "user_objective": "[USER_OBJECTIVE]",
      "current_stage": "{gate_result.stage}",
      "completed_stages": [],
      "todos_remaining": [],
      "evidence_collected": [],
      "blockers": {json.dumps(gate_result.errors)},
      "assumptions": [],
      "memory_refs": []
    }},
    "instructions": "Quality gate failed after {MAX_RETRY} attempts. Review and fix.",
    "expected_output": "Valid {gate_result.stage} output passing all schema validations"
  }}
}}
"""
        elif gate_result.action == GateAction.STOP:
            timestamp_compact = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            reprompt += f"""
INSTRUCTION: Critical failure. Workflow terminated.

RECOVERY TEMPLATE:
{{
  "recovery": {{
    "id": "R-{timestamp_compact}",
    "trigger": "quality_gate_critical_failure",
    "rollback_to": "last_checkpoint",
    "state_before": ".workflow/state/before.json",
    "state_after": ".workflow/state/after.json",
    "success": false,
    "resume_stage": "{gate_result.stage}"
  }}
}}
"""
        
        reprompt += "\n================================================================================\n"
        
        return reprompt
    
    def _timer_loop(self) -> None:
        """Background timer loop."""
        self._log(f"Timer started with {self.interval_minutes}m interval")
        
        while not self.stop_event.is_set():
            # Wait for interval or stop event
            if self.stop_event.wait(timeout=self.interval_seconds):
                break
            
            # Run check
            try:
                self.check()
            except Exception as e:
                self._log(f"Check failed: {e}", "ERROR")
        
        self._log("Timer stopped")
    
    def start(self) -> None:
        """Start the background timer."""
        if self.active:
            self._log("Timer already running", "WARN")
            return
        
        self.active = True
        self.stop_event.clear()
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
    
    def stop(self) -> None:
        """Stop the background timer."""
        if not self.active:
            return
        
        self.active = False
        self.stop_event.set()
        if self.timer_thread:
            self.timer_thread.join(timeout=5)
    
    def reset(self) -> None:
        """Reset the timer countdown."""
        self.last_check = datetime.now(timezone.utc)
        self._log("Timer reset")
    
    def status(self) -> dict:
        """Get timer status."""
        now = datetime.now(timezone.utc)
        elapsed = (now - self.last_check).total_seconds()
        remaining = max(0, self.interval_seconds - elapsed)
        
        return {
            "active": self.active,
            "interval_minutes": self.interval_minutes,
            "last_check": self.last_check.isoformat(),
            "next_check_in_seconds": remaining,
            "check_count": self.check_count,
            "fail_count": self.fail_count,
            "last_result": self.last_result.to_dict() if self.last_result else None
        }


def on_compaction_event(timer: RepromptTimer) -> None:
    """Handler for pre-compaction events."""
    print("\n[COMPACTION] Pre-compaction event triggered")
    print("[COMPACTION] Running quality gate check before compaction...")
    
    result = timer.check()
    
    if result and result.action != GateAction.PROCEED:
        print("[COMPACTION] WARNING: Quality gate failed before compaction!")
        print("[COMPACTION] Exporting chat history before context loss...")
        
        # Trigger chat export (would call pre_compaction_hook.py)
        # In real impl: subprocess.run(["python", "pre_compaction_hook.py", "--export"])


def main():
    parser = argparse.ArgumentParser(description="Reprompt Timer")
    parser.add_argument("--start", action="store_true", help="Start background timer")
    parser.add_argument("--check", action="store_true", help="Run single check")
    parser.add_argument("--status", action="store_true", help="Show timer status")
    parser.add_argument("--interval", type=int, default=5, help="Check interval in minutes")
    parser.add_argument("--stage", help="Check specific stage")
    parser.add_argument("--outputs", type=Path, help="Outputs file to check")
    parser.add_argument("--workflow-dir", type=Path, help="Workflow directory")
    args = parser.parse_args()
    
    workflow_dir = args.workflow_dir or Path(os.environ.get("WORKFLOW_DIR", ".workflow"))
    timer = RepromptTimer(interval_minutes=args.interval, workflow_dir=workflow_dir)
    
    if args.status:
        print(json.dumps(timer.status(), indent=2))
        return 0
    
    if args.check:
        result = timer.check()
        if result:
            return 0 if result.action == GateAction.PROCEED else 1
        return 0
    
    if args.start:
        # Handle signals for graceful shutdown
        def signal_handler(signum, frame):
            print("\nStopping timer...")
            timer.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        timer.start()
        
        # Keep main thread alive
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            timer.stop()
        
        return 0
    
    # Default: single check
    result = timer.check()
    if result:
        print(json.dumps(result.to_dict(), indent=2))
        return 0 if result.action == GateAction.PROCEED else 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
