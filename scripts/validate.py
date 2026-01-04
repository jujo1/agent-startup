#!/usr/bin/env python3
"""
Validation Utilities
====================

Schema validation, evidence verification, and quality gate checks.

Usage:
    python validate.py --todo todo.json
    python validate.py --evidence log.log --claim "Tests pass"
    python validate.py --gate IMPLEMENT --file outputs.json
"""

import json
import re
import sys
import argparse
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass


# Schema definitions
SCHEMAS = {
    "todo": {
        "required": ["id", "content", "status", "priority", "metadata"],
        "metadata_required": [
            "objective", "success_criteria", "fail_criteria",
            "evidence_required", "evidence_location", "agent_model",
            "workflow", "blocked_by", "parallel", "workflow_stage",
            "instructions_set", "time_budget", "reviewer"
        ],
        "enums": {
            "status": ["pending", "in_progress", "completed", "blocked", "failed"],
            "priority": ["high", "medium", "low"],
            "workflow_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"]
        }
    },
    "evidence": {
        "required": ["id", "type", "claim", "location", "timestamp", "verified", "verified_by"],
        "patterns": {
            "id": r"^E-[A-Z]+-[\w.]+-\d{3}$"
        },
        "enums": {
            "type": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
            "verified_by": ["agent", "third-party", "user"]
        }
    },
    "review_gate": {
        "required": ["stage", "agent", "timestamp", "criteria_checked", "approved", "action"],
        "enums": {
            "action": ["proceed", "revise", "escalate", "stop"]
        }
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


def validate_schema(data: Dict, schema_name: str) -> Tuple[bool, List[str]]:
    """Validate data against schema."""
    errors = []
    
    if schema_name not in SCHEMAS:
        return True, []  # Unknown schema, pass
    
    schema = SCHEMAS[schema_name]
    
    # Unwrap nested
    if schema_name in data:
        data = data[schema_name]
    
    # Required fields
    for field in schema.get("required", []):
        if field not in data or data[field] in [None, ""]:
            errors.append(f"Missing required field: {field}")
    
    # Metadata required
    if "metadata_required" in schema and "metadata" in data:
        for field in schema["metadata_required"]:
            if field not in data.get("metadata", {}):
                errors.append(f"Missing metadata field: {field}")
    
    # Enums
    for field, allowed in schema.get("enums", {}).items():
        val = data.get(field) or data.get("metadata", {}).get(field)
        if val and val not in allowed:
            errors.append(f"{field}: '{val}' not in {allowed}")
    
    # Patterns
    for field, pattern in schema.get("patterns", {}).items():
        if field in data and not re.match(pattern, data[field]):
            errors.append(f"{field}: pattern mismatch (expected {pattern})")
    
    return len(errors) == 0, errors


def validate_todo(filepath: str) -> Tuple[bool, List[str]]:
    """Validate todo file."""
    with open(filepath) as f:
        data = json.load(f)
    
    # Handle list of todos
    if isinstance(data, list):
        all_errors = []
        for i, todo in enumerate(data):
            valid, errors = validate_schema(todo, "todo")
            all_errors.extend([f"Todo[{i}]: {e}" for e in errors])
        return len(all_errors) == 0, all_errors
    
    return validate_schema(data, "todo")


def validate_evidence(filepath: str, claim: str) -> Tuple[bool, List[str]]:
    """Validate evidence file contains claim."""
    errors = []
    
    path = Path(filepath)
    if not path.exists():
        errors.append(f"Evidence file not found: {filepath}")
        return False, errors
    
    content = path.read_text()
    
    # Check claim present
    if claim.lower() not in content.lower():
        errors.append(f"Claim not found in evidence: '{claim}'")
    
    # Check for errors
    error_patterns = ["error", "exception", "traceback", "failed"]
    for pattern in error_patterns:
        if pattern in content.lower():
            errors.append(f"Error indicator found: '{pattern}'")
    
    return len(errors) == 0, errors


def validate_quality_gate(stage: str, outputs: List[Dict]) -> Tuple[str, List[str]]:
    """Validate quality gate for stage."""
    if stage not in QUALITY_GATES:
        return "PROCEED", []
    
    required = QUALITY_GATES[stage]
    checked = []
    errors = []
    
    # Validate each output
    for output in outputs:
        # Detect schema
        for schema_name in SCHEMAS:
            if schema_name in output:
                valid, schema_errors = validate_schema(output, schema_name)
                checked.append(schema_name)
                errors.extend([f"[{schema_name}] {e}" for e in schema_errors])
                break
    
    # Check required present
    for req in required:
        if req not in checked:
            errors.append(f"Missing required schema: {req}")
    
    # Determine action
    if not errors:
        action = "PROCEED"
    elif len(errors) > 10:
        action = "STOP"
    else:
        action = "REVISE"
    
    return action, errors


def main():
    parser = argparse.ArgumentParser(description="Validation utilities")
    parser.add_argument("--todo", help="Validate todo file")
    parser.add_argument("--evidence", help="Validate evidence file")
    parser.add_argument("--claim", help="Claim to verify in evidence")
    parser.add_argument("--gate", help="Quality gate stage")
    parser.add_argument("--file", help="Outputs file for gate validation")
    
    args = parser.parse_args()
    
    if args.todo:
        valid, errors = validate_todo(args.todo)
        print(f"Todo validation: {'PASS' if valid else 'FAIL'}")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(0 if valid else 1)
    
    if args.evidence and args.claim:
        valid, errors = validate_evidence(args.evidence, args.claim)
        print(f"Evidence validation: {'PASS' if valid else 'FAIL'}")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(0 if valid else 1)
    
    if args.gate and args.file:
        with open(args.file) as f:
            outputs = json.load(f)
        if not isinstance(outputs, list):
            outputs = [outputs]
        
        action, errors = validate_quality_gate(args.gate, outputs)
        print(f"Quality gate {args.gate}: {action}")
        for e in errors:
            print(f"  ❌ {e}")
        sys.exit(0 if action == "PROCEED" else 1)
    
    parser.print_help()


if __name__ == "__main__":
    main()
