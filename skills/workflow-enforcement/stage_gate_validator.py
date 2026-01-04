#!/usr/bin/env python3
"""
Stage Gate Hook - Stops agent on schema validation failure.

Installation: ~/.claude/hooks/stage_gate_validator.py

Quality Gates (AGENTS_2.md):
  PLAN       → requires: todo, evidence
  REVIEW     → requires: review_gate, evidence  
  DISRUPT    → requires: conflict, evidence
  IMPLEMENT  → requires: todo, evidence
  TEST       → requires: evidence, metrics
  VALIDATE   → requires: review_gate, evidence
  LEARN      → requires: skill, metrics

Usage in AGENTS.md hooks section:
  hooks/stage_gate_validator.py | M4/M19 | Stage exit validation

Invocation:
  python stage_gate_validator.py --stage IMPLEMENT --file outputs.json
  python stage_gate_validator.py --stage IMPLEMENT --output '{...}'

Exit codes:
  0 = PASS (proceed to next stage)
  1 = STOP (revise current stage)
  2 = ESCALATE (too many errors, escalate to Opus)
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
        }
    },
    "evidence": {
        "required": ["id", "type", "claim", "location", "timestamp", "verified", "verified_by"],
        "patterns": {"id": r"^E-\w+-[\w.]+-\d+$"},
        "enums": {
            "type": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
            "verified_by": ["agent", "third-party", "user"]
        }
    },
    "handoff": {
        "required": ["from_agent", "to_agent", "timestamp", "context"],
        "context_required": ["user_objective", "current_stage", "todos_remaining", "evidence_collected", "blockers"]
    },
    "review_gate": {
        "required": ["stage", "agent", "timestamp", "criteria_checked", "approved", "action"],
        "enums": {"action": ["proceed", "revise", "escalate"]}
    },
    "conflict": {
        "required": ["id", "type", "parties", "positions"],
        "enums": {"type": ["plan_disagreement", "evidence_dispute", "priority_conflict", "resource_conflict"]}
    },
    "metrics": {
        "required": ["workflow_id", "timestamp", "total_time_min", "stages", "agents", "evidence", "quality"]
    },
    "skill": {
        "required": ["name", "source", "purpose", "interface", "tested", "evidence_location"]
    },
    "startup": {
        "required": ["mcp_verified", "scheduler_active", "memory_ok", "env_ready", "workflow_dir", "timestamp"]
    },
    "recovery": {
        "required": ["id", "trigger", "rollback_to", "state_before", "state_after", "success", "resume_stage"]
    }
}

QUALITY_GATES = {
    "PLAN": ["todo", "evidence"],
    "REVIEW": ["review_gate", "evidence"],
    "DISRUPT": ["conflict", "evidence"],
    "IMPLEMENT": ["todo", "evidence"],
    "TEST": ["evidence", "metrics"],
    "VALIDATE": ["review_gate", "evidence"],
    "LEARN": ["skill", "metrics"]
}

MAX_RETRY = 3


def validate_schema(data: dict, schema_name: str) -> tuple[bool, list[str]]:
    """Validate data against schema. Returns (valid, errors)."""
    if schema_name not in SCHEMAS:
        return False, [f"Unknown schema: {schema_name}"]
    
    schema = SCHEMAS[schema_name]
    errors = []
    
    # Unwrap nested
    if schema_name in data and isinstance(data[schema_name], dict):
        data = data[schema_name]
    
    # Required fields
    for field in schema.get("required", []):
        if field not in data or data[field] is None or data[field] == "":
            errors.append(f"Missing: {field}")
    
    # Nested required
    for nested in ["metadata", "context"]:
        for field in schema.get(f"{nested}_required", []):
            if nested in data and field not in data.get(nested, {}):
                errors.append(f"Missing: {nested}.{field}")
    
    # Enums
    for field, allowed in schema.get("enums", {}).items():
        val = data.get(field) or data.get("metadata", {}).get(field)
        if val and val not in allowed:
            errors.append(f"{field}: '{val}' invalid")
    
    # Patterns
    for field, pattern in schema.get("patterns", {}).items():
        if field in data and data[field] and not re.match(pattern, data[field]):
            errors.append(f"{field}: pattern mismatch")
    
    return len(errors) == 0, errors


def detect_schema(data: dict) -> str | None:
    """Detect schema type from data structure."""
    if "evidence" in data: return "evidence"
    if "handoff" in data: return "handoff"
    if "review_gate" in data: return "review_gate"
    if "conflict" in data: return "conflict"
    if "metrics" in data: return "metrics"
    if "skill" in data: return "skill"
    if "startup" in data: return "startup"
    if "recovery" in data: return "recovery"
    if "metadata" in data and "objective" in data.get("metadata", {}): return "todo"
    return None


def validate_stage(stage: str, outputs: list[dict], retry_count: int = 0) -> dict:
    """Validate stage outputs. Returns result with action."""
    required = QUALITY_GATES.get(stage, [])
    result = {
        "stage": stage,
        "valid": True,
        "checked": [],
        "errors": [],
        "retry": retry_count,
        "action": "proceed",
        "exit_code": 0
    }
    
    for output in outputs:
        schema = detect_schema(output)
        if schema:
            valid, errs = validate_schema(output, schema)
            result["checked"].append(schema)
            if not valid:
                result["valid"] = False
                result["errors"].extend([f"[{schema}] {e}" for e in errs])
    
    # Check required schemas present
    for req in required:
        if req not in result["checked"]:
            result["valid"] = False
            result["errors"].append(f"Missing required: {req}")
    
    # Determine action
    if not result["valid"]:
        if retry_count >= MAX_RETRY:
            result["action"] = "escalate"
            result["exit_code"] = 2
        else:
            result["action"] = "revise"
            result["exit_code"] = 1
    
    return result


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", required=True)
    parser.add_argument("--output", help="JSON string")
    parser.add_argument("--file", type=Path, help="JSON file")
    parser.add_argument("--retry", type=int, default=0)
    args = parser.parse_args()
    
    outputs = []
    if args.output:
        outputs = [json.loads(args.output)]
    elif args.file and args.file.exists():
        with open(args.file) as f:
            data = json.load(f)
            outputs = data if isinstance(data, list) else [data]
    
    result = validate_stage(args.stage, outputs, args.retry)
    print(json.dumps(result, indent=2))
    return result["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
