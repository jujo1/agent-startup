#!/usr/bin/env python3
"""
Workflow Enforcement System - Main Entry Point

This script orchestrates the complete workflow enforcement system:
  1. Startup validation (MCP, scheduler, memory, dirs)
  2. Skills loading (superpowers)
  3. State machine execution (8 stages)
  4. Quality gate enforcement (hooks)
  5. Reprompt timer (5-minute checks)
  6. Pre-compaction export

Installation:
  Copy entire workflow_system/ to ~/.claude/
  Add to AGENTS.md: "Run workflow_main.py on session start"

Usage:
  # Start new workflow
  python workflow_main.py --start --objective "Build feature X"
  
  # Resume existing workflow
  python workflow_main.py --resume --workflow-id 20260104_070000_abc123
  
  # Run with all hooks
  python workflow_main.py --start --objective "Test" --with-timer --with-compaction-hook

Environment:
  WORKFLOW_DIR=.workflow
  AGENT_MODEL=Claude
  SESSION_ID=auto
"""

import argparse
import json
import os
import signal
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from workflow_state_machine import WorkflowMachine, Stage, GateAction
from hooks.startup_validator import StartupValidator
from hooks.skills_loader import SkillsLoader, STAGE_SKILLS
from hooks.reprompt_timer import RepromptTimer
from hooks.pre_compaction_hook import PreCompactionHook


class WorkflowOrchestrator:
    """Orchestrates the complete workflow enforcement system."""
    
    def __init__(
        self,
        workflow_id: str | None = None,
        base_path: Path | None = None,
        with_timer: bool = True,
        with_compaction_hook: bool = True,
        timer_interval: int = 5
    ):
        self.workflow_id = workflow_id
        self.base_path = base_path
        self.with_timer = with_timer
        self.with_compaction_hook = with_compaction_hook
        self.timer_interval = timer_interval
        
        self.machine: WorkflowMachine | None = None
        self.timer: RepromptTimer | None = None
        self.skills_loader: SkillsLoader | None = None
        self.running = False
        
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Set up graceful shutdown handlers."""
        def handler(signum, frame):
            print("\n[ORCHESTRATOR] Shutdown signal received...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)
    
    def _log(self, message: str, level: str = "INFO"):
        """Log message."""
        timestamp = datetime.now(timezone.utc).isoformat()
        print(f"[{timestamp}] [ORCHESTRATOR] [{level}] {message}")
    
    def startup(self) -> dict:
        """Run startup sequence."""
        self._log("=" * 60)
        self._log("WORKFLOW ORCHESTRATOR STARTUP")
        self._log("=" * 60)
        
        # 1. Run startup validator
        self._log("Phase 1: Startup validation")
        validator = StartupValidator()
        startup_result = validator.run_all_checks()
        
        if startup_result["startup"].get("status") != "PASS":
            self._log("Startup validation FAILED", "ERROR")
            return {"status": "FAIL", "phase": "startup", "result": startup_result}
        
        # Use validator's workflow ID and path
        self.workflow_id = self.workflow_id or validator.workflow_id
        self.base_path = self.base_path or validator.base_path
        
        # 2. Initialize state machine
        self._log("Phase 2: State machine initialization")
        self.machine = WorkflowMachine(
            workflow_id=self.workflow_id,
            base_path=self.base_path
        )
        
        # Register hooks
        self.machine.register_hook("on_stage_enter", self._on_stage_enter)
        self.machine.register_hook("on_stage_exit", self._on_stage_exit)
        self.machine.register_hook("on_gate_fail", self._on_gate_fail)
        self.machine.register_hook("on_compaction", self._on_compaction)
        
        machine_result = self.machine.startup()
        
        # 3. Load skills
        self._log("Phase 3: Skills loading")
        self.skills_loader = SkillsLoader()
        skills = self.skills_loader.load_all_skills()
        self._log(f"Loaded {len(skills)} skills")
        
        # 4. Start reprompt timer
        if self.with_timer:
            self._log("Phase 4: Reprompt timer")
            self.timer = RepromptTimer(
                interval_minutes=self.timer_interval,
                workflow_dir=self.base_path,
                on_gate_fail=self._on_timer_gate_fail
            )
            self.timer.start()
            self._log(f"Timer started ({self.timer_interval}m interval)")
        
        # 5. Register compaction hook
        if self.with_compaction_hook:
            self._log("Phase 5: Compaction hook registered")
        
        self._log("=" * 60)
        self._log("STARTUP COMPLETE")
        self._log(f"Workflow ID: {self.workflow_id}")
        self._log(f"Workflow Dir: {self.base_path}")
        self._log("=" * 60)
        
        self.running = True
        
        return {
            "status": "PASS",
            "workflow_id": self.workflow_id,
            "base_path": str(self.base_path),
            "startup": startup_result,
            "machine": machine_result,
            "skills_loaded": len(skills),
            "timer_active": self.with_timer,
            "compaction_hook": self.with_compaction_hook
        }
    
    def resume(self, workflow_id: str) -> dict:
        """Resume an existing workflow."""
        self._log(f"Resuming workflow: {workflow_id}")
        
        # Find workflow directory
        base_path = Path(os.environ.get("WORKFLOW_DIR", ".workflow")) / workflow_id
        if not base_path.exists():
            return {"status": "FAIL", "error": f"Workflow not found: {base_path}"}
        
        self.workflow_id = workflow_id
        self.base_path = base_path
        
        # Initialize machine and load state
        self.machine = WorkflowMachine(
            workflow_id=workflow_id,
            base_path=base_path
        )
        
        if not self.machine._load_state():
            return {"status": "FAIL", "error": "Could not load workflow state"}
        
        # Register hooks
        self.machine.register_hook("on_stage_enter", self._on_stage_enter)
        self.machine.register_hook("on_stage_exit", self._on_stage_exit)
        self.machine.register_hook("on_gate_fail", self._on_gate_fail)
        
        # Load skills
        self.skills_loader = SkillsLoader()
        self.skills_loader.load_all_skills()
        
        # Start timer if enabled
        if self.with_timer:
            self.timer = RepromptTimer(
                interval_minutes=self.timer_interval,
                workflow_dir=self.base_path,
                on_gate_fail=self._on_timer_gate_fail
            )
            self.timer.start()
        
        self.running = True
        
        self._log(f"Resumed at stage: {self.machine.current_stage.name}")
        
        return {
            "status": "PASS",
            "workflow_id": workflow_id,
            "current_stage": self.machine.current_stage.name,
            "completed_stages": [s.name for s in self.machine.completed_stages],
            "todos": len(self.machine.todos),
            "evidence": len(self.machine.evidence)
        }
    
    def stop(self):
        """Stop the orchestrator gracefully."""
        self._log("Stopping orchestrator...")
        
        self.running = False
        
        if self.timer:
            self.timer.stop()
        
        if self.machine:
            self.machine._save_state()
        
        # Run pre-compaction export if enabled
        if self.with_compaction_hook and self.base_path:
            self._log("Running pre-compaction export...")
            hook = PreCompactionHook(workflow_dir=self.base_path)
            hook.run_full_export(force=True)
        
        self._log("Orchestrator stopped")
    
    def _on_stage_enter(self, stage: Stage):
        """Hook: Called when entering a stage."""
        self._log(f"Entering stage: {stage.name}")
        
        # Load skills for this stage
        if self.skills_loader:
            stage_name = stage.name.replace("_POST", "")
            skills = STAGE_SKILLS.get(stage_name, [])
            self._log(f"Active skills: {skills}")
            
            # Print skill prompt
            prompt = self.skills_loader.generate_stage_prompt(stage_name)
            print("\n" + "=" * 60)
            print(prompt)
            print("=" * 60 + "\n")
        
        # Reset timer
        if self.timer:
            self.timer.reset()
    
    def _on_stage_exit(self, from_stage: Stage, to_stage: Stage):
        """Hook: Called when exiting a stage."""
        self._log(f"Exiting stage: {from_stage.name} -> {to_stage.name}")
    
    def _on_gate_fail(self, gate_result):
        """Hook: Called when quality gate fails."""
        self._log(f"Quality gate FAILED: {gate_result.action.value}", "WARN")
        
        # Log to file
        if self.base_path:
            fail_log = self.base_path / "logs" / "gate_failures.jsonl"
            fail_log.parent.mkdir(parents=True, exist_ok=True)
            with open(fail_log, "a") as f:
                f.write(json.dumps(gate_result.to_dict()) + "\n")
    
    def _on_timer_gate_fail(self, gate_result):
        """Hook: Called when timer-triggered gate fails."""
        self._log(f"Timer gate check FAILED: {gate_result.action.value}", "WARN")
        
        # Generate and print reprompt
        if self.machine:
            reprompt = self.machine.generate_reprompt(gate_result)
            print(reprompt)
    
    def _on_compaction(self):
        """Hook: Called before context compaction."""
        self._log("Compaction event triggered")
        
        if self.base_path:
            hook = PreCompactionHook(workflow_dir=self.base_path)
            hook.run_full_export(force=True)
    
    def get_status(self) -> dict:
        """Get current orchestrator status."""
        status = {
            "running": self.running,
            "workflow_id": self.workflow_id,
            "base_path": str(self.base_path) if self.base_path else None,
        }
        
        if self.machine:
            status["current_stage"] = self.machine.current_stage.name
            status["completed_stages"] = [s.name for s in self.machine.completed_stages]
            status["todos_count"] = len(self.machine.todos)
            status["evidence_count"] = len(self.machine.evidence)
        
        if self.timer:
            status["timer"] = self.timer.status()
        
        return status
    
    def create_plan(self, objective: str) -> dict:
        """Create initial plan for objective."""
        if not self.machine:
            return {"status": "FAIL", "error": "Machine not initialized"}
        
        self.machine.user_objective = objective
        
        # Create initial todo
        todo = self.machine.create_todo(
            f"Complete: {objective}",
            priority="high",
            objective=objective,
            success_criteria="Objective fully satisfied",
            fail_criteria="Objective not met",
            workflow_stage="PLAN"
        )
        
        # Create plan evidence
        evidence = self.machine.create_evidence(
            "PLAN",
            f"Plan created for objective: {objective}"
        )
        
        # Create evidence file
        evidence_path = Path(evidence["evidence"]["location"])
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(json.dumps({
            "objective": objective,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "todos": [todo]
        }, indent=2))
        
        return {
            "status": "PASS",
            "objective": objective,
            "todo": todo,
            "evidence": evidence
        }


def main():
    parser = argparse.ArgumentParser(description="Workflow Enforcement System")
    
    # Actions
    parser.add_argument("--start", action="store_true", help="Start new workflow")
    parser.add_argument("--resume", action="store_true", help="Resume existing workflow")
    parser.add_argument("--status", action="store_true", help="Show current status")
    parser.add_argument("--test", action="store_true", help="Run test workflow")
    
    # Options
    parser.add_argument("--objective", help="User objective for new workflow")
    parser.add_argument("--workflow-id", help="Workflow ID to resume")
    parser.add_argument("--workflow-dir", type=Path, help="Workflow directory")
    parser.add_argument("--with-timer", action="store_true", default=True, help="Enable reprompt timer")
    parser.add_argument("--no-timer", action="store_true", help="Disable reprompt timer")
    parser.add_argument("--timer-interval", type=int, default=5, help="Timer interval in minutes")
    parser.add_argument("--with-compaction-hook", action="store_true", default=True, help="Enable compaction hook")
    parser.add_argument("--no-compaction-hook", action="store_true", help="Disable compaction hook")
    parser.add_argument("--output", type=Path, help="Output file for status")
    
    args = parser.parse_args()
    
    # Determine settings
    with_timer = not args.no_timer
    with_compaction = not args.no_compaction_hook
    
    orchestrator = WorkflowOrchestrator(
        workflow_id=args.workflow_id,
        base_path=args.workflow_dir,
        with_timer=with_timer,
        with_compaction_hook=with_compaction,
        timer_interval=args.timer_interval
    )
    
    if args.start:
        if not args.objective:
            print("Error: --objective required for --start")
            return 1
        
        result = orchestrator.startup()
        if result["status"] != "PASS":
            print(f"Startup failed: {result}")
            return 1
        
        plan_result = orchestrator.create_plan(args.objective)
        print(json.dumps(plan_result, indent=2, default=str))
        
        # Keep running if timer is enabled
        if with_timer:
            print("\n[ORCHESTRATOR] Running with timer. Press Ctrl+C to stop.\n")
            try:
                while orchestrator.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                orchestrator.stop()
        
        return 0
    
    if args.resume:
        if not args.workflow_id:
            print("Error: --workflow-id required for --resume")
            return 1
        
        result = orchestrator.resume(args.workflow_id)
        print(json.dumps(result, indent=2, default=str))
        
        if result["status"] != "PASS":
            return 1
        
        # Keep running if timer is enabled
        if with_timer:
            print("\n[ORCHESTRATOR] Running with timer. Press Ctrl+C to stop.\n")
            try:
                while orchestrator.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
            finally:
                orchestrator.stop()
        
        return 0
    
    if args.status:
        status = orchestrator.get_status()
        print(json.dumps(status, indent=2, default=str))
        
        if args.output:
            with open(args.output, "w") as f:
                json.dump(status, f, indent=2, default=str)
        
        return 0
    
    if args.test:
        print("Running test workflow...")
        
        result = orchestrator.startup()
        if result["status"] != "PASS":
            print(f"Startup failed: {result}")
            return 1
        
        plan_result = orchestrator.create_plan("Test workflow execution")
        print(f"Plan created: {plan_result['status']}")
        
        # Run a few timer checks
        if orchestrator.timer:
            print("\nRunning 3 timer checks...")
            for i in range(3):
                result = orchestrator.timer.check()
                if result:
                    print(f"Check {i+1}: {result.action.value}")
                time.sleep(1)
        
        orchestrator.stop()
        print("\nTest complete!")
        return 0
    
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
