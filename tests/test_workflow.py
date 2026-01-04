#!/usr/bin/env python3
"""
Test Suite for Workflow State Machine

Tests:
  - Schema validation (all 9 schemas from SCHEMAS.md)
  - Quality gate logic (PROCEED, REVISE, ESCALATE, STOP)
  - Stage transitions (valid and invalid)
  - Reprompt generation
  - Todo creation with 17 fields
  - Evidence creation and validation
  - Startup sequence
  - State persistence

Usage:
  pytest test_workflow.py -v
  python test_workflow.py  # Run directly
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from workflow_state_machine import (
    WorkflowMachine, Stage, GateAction, GateResult,
    validate_schema, detect_schema, SCHEMAS, QUALITY_GATES,
    STAGE_CONFIG, MCP_SERVERS, MAX_RETRY
)


class TestSchemaValidation(unittest.TestCase):
    """Test schema validation functions."""
    
    def test_valid_todo(self):
        """Test valid todo passes validation."""
        todo = {
            "id": "1.1",
            "content": "Test task",
            "status": "pending",
            "priority": "high",
            "metadata": {
                "objective": "Test objective",
                "success_criteria": "Task passes",
                "fail_criteria": "Task fails",
                "evidence_required": "log",
                "evidence_location": "/tmp/evidence/1.1.log",
                "agent_model": "Claude",
                "workflow": "PLAN→IMPLEMENT→TEST",
                "blocked_by": [],
                "parallel": False,
                "workflow_stage": "PLAN",
                "instructions_set": "AGENTS_3.md",
                "time_budget": "≤60m",
                "reviewer": "gpt-5.2"
            }
        }
        
        valid, errors = validate_schema(todo, "todo")
        self.assertTrue(valid, f"Errors: {errors}")
        self.assertEqual(len(errors), 0)
    
    def test_todo_missing_field(self):
        """Test todo missing required field fails."""
        todo = {
            "id": "1.1",
            "content": "Test task",
            "status": "pending",
            # Missing: priority, metadata
        }
        
        valid, errors = validate_schema(todo, "todo")
        self.assertFalse(valid)
        self.assertIn("Missing: priority", errors)
        self.assertIn("Missing: metadata", errors)
    
    def test_todo_invalid_enum(self):
        """Test todo with invalid enum value fails."""
        todo = {
            "id": "1.1",
            "content": "Test",
            "status": "invalid_status",  # Invalid
            "priority": "high",
            "metadata": {
                "objective": "Test",
                "success_criteria": "Pass",
                "fail_criteria": "Fail",
                "evidence_required": "log",
                "evidence_location": "/tmp/test.log",
                "agent_model": "Claude",
                "workflow": "PLAN",
                "blocked_by": [],
                "parallel": False,
                "workflow_stage": "PLAN",
                "instructions_set": "AGENTS_3.md",
                "time_budget": "≤60m",
                "reviewer": "gpt-5.2"
            }
        }
        
        valid, errors = validate_schema(todo, "todo")
        self.assertFalse(valid)
        self.assertTrue(any("status" in e for e in errors))
    
    def test_valid_evidence(self):
        """Test valid evidence passes validation."""
        evidence = {
            "evidence": {
                "id": "E-PLAN-test123-001",
                "type": "log",
                "claim": "Test claim",
                "location": "/tmp/evidence.log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "verified": True,
                "verified_by": "agent"
            }
        }
        
        valid, errors = validate_schema(evidence, "evidence")
        self.assertTrue(valid, f"Errors: {errors}")
    
    def test_evidence_invalid_pattern(self):
        """Test evidence with invalid ID pattern fails."""
        evidence = {
            "evidence": {
                "id": "invalid-id",  # Invalid pattern
                "type": "log",
                "claim": "Test",
                "location": "/tmp/test.log",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "verified": True,
                "verified_by": "agent"
            }
        }
        
        valid, errors = validate_schema(evidence, "evidence")
        self.assertFalse(valid)
        self.assertTrue(any("pattern" in e for e in errors))
    
    def test_valid_review_gate(self):
        """Test valid review_gate passes validation."""
        review_gate = {
            "review_gate": {
                "stage": "REVIEW",
                "agent": "Opus",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "criteria_checked": [
                    {"criterion": "17 fields", "pass": True}
                ],
                "approved": True,
                "action": "proceed"
            }
        }
        
        valid, errors = validate_schema(review_gate, "review_gate")
        self.assertTrue(valid, f"Errors: {errors}")
    
    def test_valid_handoff(self):
        """Test valid handoff passes validation."""
        handoff = {
            "handoff": {
                "from_agent": "Sonnet",
                "to_agent": "Opus",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "context": {
                    "user_objective": "Build workflow system",
                    "current_stage": "IMPLEMENT",
                    "completed_stages": ["PLAN", "REVIEW"],
                    "todos_remaining": [],
                    "evidence_collected": [],
                    "blockers": ["Test failure"],
                    "assumptions": [],
                    "memory_refs": []
                }
            }
        }
        
        valid, errors = validate_schema(handoff, "handoff")
        self.assertTrue(valid, f"Errors: {errors}")
    
    def test_detect_schema(self):
        """Test schema detection."""
        self.assertEqual(detect_schema({"evidence": {}}), "evidence")
        self.assertEqual(detect_schema({"handoff": {}}), "handoff")
        self.assertEqual(detect_schema({"review_gate": {}}), "review_gate")
        self.assertEqual(detect_schema({"conflict": {}}), "conflict")
        self.assertEqual(detect_schema({"metrics": {}}), "metrics")
        self.assertEqual(detect_schema({"skill": {}}), "skill")
        self.assertEqual(detect_schema({"startup": {}}), "startup")
        self.assertEqual(detect_schema({"recovery": {}}), "recovery")
        
        # Todo detection by metadata.objective
        self.assertEqual(
            detect_schema({"id": "1", "metadata": {"objective": "test"}}),
            "todo"
        )


class TestQualityGate(unittest.TestCase):
    """Test quality gate logic."""
    
    def setUp(self):
        """Set up test machine."""
        self.temp_dir = tempfile.mkdtemp()
        self.machine = WorkflowMachine(
            workflow_id="test_workflow",
            base_path=Path(self.temp_dir) / ".workflow" / "test_workflow"
        )
        self.machine.startup()
    
    def tearDown(self):
        """Clean up temp directory."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_gate_proceed_with_valid_outputs(self):
        """Test gate proceeds with valid outputs."""
        todo = self.machine.create_todo(
            "Test task",
            priority="high",
            objective="Test",
            success_criteria="Pass",
            fail_criteria="Fail"
        )
        
        evidence = self.machine.create_evidence("PLAN", "Plan created")
        
        # Create evidence file
        evidence_path = Path(evidence["evidence"]["location"])
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text("Evidence content")
        
        result = self.machine.quality_gate(Stage.PLAN, [todo, evidence])
        
        self.assertEqual(result.action, GateAction.PROCEED)
        self.assertTrue(result.valid)
        self.assertIn("todo", result.checked)
        self.assertIn("evidence", result.checked)
    
    def test_gate_revise_with_missing_schema(self):
        """Test gate revises when required schema missing."""
        todo = self.machine.create_todo("Test", priority="high")
        # Missing evidence
        
        result = self.machine.quality_gate(Stage.PLAN, [todo])
        
        self.assertEqual(result.action, GateAction.REVISE)
        self.assertFalse(result.valid)
        self.assertIn("Missing required schema: evidence", result.errors)
    
    def test_gate_escalate_after_max_retries(self):
        """Test gate escalates after max retries."""
        result = self.machine.quality_gate(
            Stage.PLAN,
            [],
            retry=MAX_RETRY
        )
        
        self.assertEqual(result.action, GateAction.ESCALATE)
    
    def test_required_schemas_per_stage(self):
        """Test each stage has correct required schemas."""
        expected = {
            "PLAN": ["todo", "evidence"],
            "REVIEW": ["review_gate", "evidence"],
            "DISRUPT": ["conflict", "evidence"],
            "IMPLEMENT": ["todo", "evidence"],
            "TEST": ["evidence", "metrics"],
            "VALIDATE": ["review_gate", "evidence"],
            "LEARN": ["skill", "metrics"]
        }
        
        for stage, schemas in expected.items():
            self.assertEqual(QUALITY_GATES.get(stage), schemas)


class TestWorkflowMachine(unittest.TestCase):
    """Test workflow state machine."""
    
    def setUp(self):
        """Set up test machine."""
        self.temp_dir = tempfile.mkdtemp()
        self.machine = WorkflowMachine(
            workflow_id="test_workflow",
            base_path=Path(self.temp_dir) / ".workflow" / "test_workflow"
        )
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_startup_creates_directories(self):
        """Test startup creates workflow directories."""
        result = self.machine.startup()
        
        self.assertTrue(result["mcp_verified"])
        self.assertTrue(result["scheduler_active"])
        self.assertTrue(result["memory_ok"])
        self.assertTrue(result["env_ready"])
        
        # Check directories created
        for dir_name in ["todo", "evidence", "logs", "state", "plans", "test"]:
            self.assertTrue((self.machine.base_path / dir_name).exists())
    
    def test_state_transitions(self):
        """Test valid state transitions."""
        self.machine.startup()
        self.assertEqual(self.machine.current_stage, Stage.PLAN)
        
        # Create required outputs for PLAN
        todo = self.machine.create_todo("Test", priority="high")
        evidence = self.machine.create_evidence("PLAN", "Test")
        
        # Create evidence file
        Path(evidence["evidence"]["location"]).parent.mkdir(parents=True, exist_ok=True)
        Path(evidence["evidence"]["location"]).write_text("Evidence")
        
        self.machine.stage_outputs[Stage.PLAN] = type('obj', (object,), {
            'outputs': [todo, evidence]
        })()
    
    def test_invalid_transition_rejected(self):
        """Test invalid transitions are rejected."""
        self.machine.startup()
        self.assertEqual(self.machine.current_stage, Stage.PLAN)
        
        # Try to skip to IMPLEMENT (should fail)
        result = self.machine.transition(Stage.IMPLEMENT)
        self.assertFalse(result)
        self.assertEqual(self.machine.current_stage, Stage.PLAN)
    
    def test_todo_creation_validates_schema(self):
        """Test todo creation validates against schema."""
        self.machine.startup()
        
        todo = self.machine.create_todo(
            "Test task",
            priority="high",
            objective="Test objective",
            success_criteria="Task passes",
            fail_criteria="Task fails"
        )
        
        self.assertEqual(todo["id"], "1.1")
        self.assertEqual(todo["status"], "pending")
        self.assertEqual(todo["priority"], "high")
        self.assertIn("metadata", todo)
        self.assertEqual(todo["metadata"]["objective"], "Test objective")
    
    def test_evidence_creation_validates_schema(self):
        """Test evidence creation validates against schema."""
        self.machine.startup()
        
        evidence = self.machine.create_evidence(
            "PLAN",
            "Plan created successfully"
        )
        
        self.assertIn("evidence", evidence)
        self.assertTrue(evidence["evidence"]["id"].startswith("E-PLAN-"))
        self.assertEqual(evidence["evidence"]["type"], "log")
        self.assertTrue(evidence["evidence"]["verified"])
    
    def test_state_persistence(self):
        """Test state is saved and loaded correctly."""
        self.machine.startup()
        self.machine.user_objective = "Test objective"
        
        todo = self.machine.create_todo("Test", priority="high")
        evidence = self.machine.create_evidence("PLAN", "Test")
        
        self.machine._save_state()
        
        # Create new machine and load state
        machine2 = WorkflowMachine(base_path=self.machine.base_path)
        loaded = machine2._load_state()
        
        self.assertTrue(loaded)
        self.assertEqual(machine2.workflow_id, self.machine.workflow_id)
        self.assertEqual(machine2.user_objective, "Test objective")
        self.assertEqual(len(machine2.todos), 1)
        self.assertEqual(len(machine2.evidence), 1)


class TestRepromptGeneration(unittest.TestCase):
    """Test reprompt generation."""
    
    def setUp(self):
        """Set up test machine."""
        self.temp_dir = tempfile.mkdtemp()
        self.machine = WorkflowMachine(
            workflow_id="test_workflow",
            base_path=Path(self.temp_dir) / ".workflow" / "test_workflow"
        )
        self.machine.startup()
    
    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_reprompt_contains_errors(self):
        """Test reprompt contains error details."""
        gate_result = GateResult(
            stage="PLAN",
            valid=False,
            checked=["todo"],
            errors=["Missing required schema: evidence", "[todo] Missing: metadata.objective"],
            action=GateAction.REVISE,
            retry=0
        )
        
        reprompt = self.machine.generate_reprompt(gate_result)
        
        self.assertIn("QUALITY GATE FAILED", reprompt)
        self.assertIn("PLAN", reprompt)
        self.assertIn("REVISE", reprompt)
        self.assertIn("Missing required schema: evidence", reprompt)
        self.assertIn("[todo] Missing: metadata.objective", reprompt)
    
    def test_reprompt_escalate_includes_handoff(self):
        """Test escalate reprompt includes handoff template."""
        gate_result = GateResult(
            stage="IMPLEMENT",
            valid=False,
            checked=[],
            errors=["Critical error"],
            action=GateAction.ESCALATE,
            retry=MAX_RETRY
        )
        
        reprompt = self.machine.generate_reprompt(gate_result)
        
        self.assertIn("ESCALATE", reprompt)
        self.assertIn("Opus", reprompt)
        self.assertIn("handoff", reprompt.lower())


class TestStageConfig(unittest.TestCase):
    """Test stage configuration."""
    
    def test_all_stages_have_config(self):
        """Test all workflow stages have configuration."""
        stages = [
            Stage.PLAN, Stage.REVIEW, Stage.DISRUPT,
            Stage.IMPLEMENT, Stage.TEST, Stage.REVIEW_POST,
            Stage.VALIDATE, Stage.LEARN
        ]
        
        for stage in stages:
            self.assertIn(stage, STAGE_CONFIG)
            config = STAGE_CONFIG[stage]
            self.assertIn("model", config)
            self.assertIn("agents", config)
            self.assertIn("skills", config)
            self.assertIn("mcp", config)
    
    def test_third_party_stages_flagged(self):
        """Test stages requiring third-party are flagged."""
        self.assertTrue(STAGE_CONFIG[Stage.DISRUPT].get("requires_third_party"))
        self.assertTrue(STAGE_CONFIG[Stage.VALIDATE].get("requires_third_party"))


def run_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestSchemaValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestQualityGate))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowMachine))
    suite.addTests(loader.loadTestsFromTestCase(TestRepromptGeneration))
    suite.addTests(loader.loadTestsFromTestCase(TestStageConfig))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    sys.exit(run_tests())
