#!/usr/bin/env python3
"""
Todo Enforcer Hook
Enforces 17-field todo schema and workflow compliance.

From AGENTS_3.md:
- All todos must have exactly 17 fields (4 base + 13 metadata)
- No task exit without evidence
- No placeholders in any field

Usage:
    python todo_enforcer.py --validate todo.json
    python todo_enforcer.py --validate-all .workflow/todo/
    python todo_enforcer.py --create "Task description"
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import uuid


# ============================================================================
# TODO SCHEMA (from SCHEMAS.md) - EXACTLY 17 FIELDS
# ============================================================================

BASE_FIELDS = ["id", "content", "status", "priority"]

METADATA_FIELDS = [
    "objective",
    "success_criteria",
    "fail_criteria",
    "evidence_required",
    "evidence_location",
    "agent_model",
    "workflow",
    "blocked_by",
    "parallel",
    "workflow_stage",
    "instructions_set",
    "time_budget",
    "reviewer"
]

ALL_FIELDS = BASE_FIELDS + [f"metadata.{m}" for m in METADATA_FIELDS]

ENUMS = {
    "status": ["pending", "in_progress", "completed", "blocked", "failed"],
    "priority": ["high", "medium", "low"],
    "evidence_required": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
    "workflow_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"],
    "agent_model": ["Claude", "GPT", "Ollama"]
}

PLACEHOLDER_PATTERNS = [
    r"TODO",
    r"FIXME",
    r"XXX",
    r"TBD",
    r"N/A",
    r"\.\.\.",
    r"<.*>",
    r"\[.*\]"
]


# ============================================================================
# VALIDATORS
# ============================================================================

def validate_17_fields(todo: dict) -> tuple[bool, list[str]]:
    """Validate todo has exactly 17 fields."""
    errors = []
    
    # Check base fields
    for field in BASE_FIELDS:
        if field not in todo:
            errors.append(f"Missing base field: {field}")
        elif todo[field] is None or todo[field] == "":
            errors.append(f"Empty base field: {field}")
    
    # Check metadata exists
    if "metadata" not in todo:
        errors.append("Missing metadata object")
        return False, errors
    
    metadata = todo["metadata"]
    
    # Check metadata fields
    for field in METADATA_FIELDS:
        if field not in metadata:
            errors.append(f"Missing metadata field: {field}")
        elif metadata[field] is None or (isinstance(metadata[field], str) and metadata[field] == ""):
            errors.append(f"Empty metadata field: {field}")
    
    # Count total fields
    base_count = sum(1 for f in BASE_FIELDS if f in todo)
    meta_count = sum(1 for f in METADATA_FIELDS if f in metadata)
    total = base_count + meta_count
    
    if total != 17:
        errors.append(f"Field count: {total} (expected 17)")
    
    return len(errors) == 0, errors


def validate_enums(todo: dict) -> tuple[bool, list[str]]:
    """Validate enum values."""
    errors = []
    metadata = todo.get("metadata", {})
    
    # Status
    if todo.get("status") and todo["status"] not in ENUMS["status"]:
        errors.append(f"Invalid status: {todo['status']}")
    
    # Priority
    if todo.get("priority") and todo["priority"] not in ENUMS["priority"]:
        errors.append(f"Invalid priority: {todo['priority']}")
    
    # Evidence required
    if metadata.get("evidence_required") and metadata["evidence_required"] not in ENUMS["evidence_required"]:
        errors.append(f"Invalid evidence_required: {metadata['evidence_required']}")
    
    # Workflow stage
    if metadata.get("workflow_stage") and metadata["workflow_stage"] not in ENUMS["workflow_stage"]:
        errors.append(f"Invalid workflow_stage: {metadata['workflow_stage']}")
    
    # Agent model
    if metadata.get("agent_model") and metadata["agent_model"] not in ENUMS["agent_model"]:
        errors.append(f"Invalid agent_model: {metadata['agent_model']}")
    
    return len(errors) == 0, errors


def validate_no_placeholders(todo: dict) -> tuple[bool, list[str]]:
    """Validate no placeholder values."""
    errors = []
    
    def check_value(value: any, path: str) -> None:
        if isinstance(value, str):
            for pattern in PLACEHOLDER_PATTERNS:
                if re.search(pattern, value):
                    errors.append(f"Placeholder found in {path}: {value}")
        elif isinstance(value, dict):
            for k, v in value.items():
                check_value(v, f"{path}.{k}")
        elif isinstance(value, list):
            for i, v in enumerate(value):
                check_value(v, f"{path}[{i}]")
    
    check_value(todo, "todo")
    
    return len(errors) == 0, errors


def validate_blocked_by_type(todo: dict) -> tuple[bool, list[str]]:
    """Validate blocked_by is a list."""
    metadata = todo.get("metadata", {})
    blocked_by = metadata.get("blocked_by")
    
    if blocked_by is not None and not isinstance(blocked_by, list):
        return False, ["blocked_by must be a list"]
    
    return True, []


def validate_parallel_type(todo: dict) -> tuple[bool, list[str]]:
    """Validate parallel is a boolean."""
    metadata = todo.get("metadata", {})
    parallel = metadata.get("parallel")
    
    if parallel is not None and not isinstance(parallel, bool):
        return False, ["parallel must be a boolean"]
    
    return True, []


def validate_evidence_location(todo: dict) -> tuple[bool, list[str]]:
    """Validate evidence_location is a valid path."""
    metadata = todo.get("metadata", {})
    location = metadata.get("evidence_location")
    
    if not location:
        return False, ["evidence_location is required"]
    
    # Should be a path-like string
    if not isinstance(location, str):
        return False, ["evidence_location must be a string"]
    
    if not (location.startswith("/") or location.startswith("./") or location.startswith("~")):
        return False, [f"evidence_location should be a path: {location}"]
    
    return True, []


# ============================================================================
# FULL VALIDATION
# ============================================================================

def validate_todo(todo: dict) -> dict:
    """Full todo validation against 17-field schema."""
    result = {
        "id": todo.get("id", "unknown"),
        "valid": True,
        "errors": [],
        "warnings": []
    }
    
    validators = [
        ("17 fields", validate_17_fields),
        ("enums", validate_enums),
        ("no placeholders", validate_no_placeholders),
        ("blocked_by type", validate_blocked_by_type),
        ("parallel type", validate_parallel_type),
        ("evidence location", validate_evidence_location),
    ]
    
    for name, validator in validators:
        valid, errors = validator(todo)
        if not valid:
            result["valid"] = False
            result["errors"].extend([f"[{name}] {e}" for e in errors])
    
    return result


def validate_all_todos(directory: str) -> dict:
    """Validate all todos in directory."""
    path = Path(directory)
    
    if not path.exists():
        return {"valid": False, "error": f"Directory not found: {directory}"}
    
    results = {
        "directory": str(path),
        "files_checked": 0,
        "valid_count": 0,
        "invalid_count": 0,
        "results": []
    }
    
    for todo_file in path.glob("*.json"):
        try:
            with open(todo_file) as f:
                data = json.load(f)
            
            # Handle array of todos
            if isinstance(data, list):
                for todo in data:
                    result = validate_todo(todo)
                    result["file"] = str(todo_file)
                    results["results"].append(result)
                    results["files_checked"] += 1
                    if result["valid"]:
                        results["valid_count"] += 1
                    else:
                        results["invalid_count"] += 1
            else:
                result = validate_todo(data)
                result["file"] = str(todo_file)
                results["results"].append(result)
                results["files_checked"] += 1
                if result["valid"]:
                    results["valid_count"] += 1
                else:
                    results["invalid_count"] += 1
        
        except json.JSONDecodeError as e:
            results["results"].append({
                "file": str(todo_file),
                "valid": False,
                "errors": [f"Invalid JSON: {e}"]
            })
            results["invalid_count"] += 1
    
    results["valid"] = results["invalid_count"] == 0
    
    return results


# ============================================================================
# TODO CREATION
# ============================================================================

def create_todo(
    content: str,
    priority: str = "medium",
    objective: Optional[str] = None,
    evidence_type: str = "log",
    workflow_stage: str = "PLAN"
) -> dict:
    """Create a valid 17-field todo."""
    todo_id = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:6]}"
    
    todo = {
        "id": todo_id,
        "content": content,
        "status": "pending",
        "priority": priority,
        "metadata": {
            "objective": objective or content,
            "success_criteria": f"{content} completes successfully",
            "fail_criteria": f"{content} fails or errors",
            "evidence_required": evidence_type,
            "evidence_location": f".workflow/evidence/{todo_id}.log",
            "agent_model": "Claude",
            "workflow": "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
            "blocked_by": [],
            "parallel": False,
            "workflow_stage": workflow_stage,
            "instructions_set": "AGENTS_3.md",
            "time_budget": "≤15m",
            "reviewer": "GPT-5.2"
        }
    }
    
    return todo


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Todo Enforcer")
    parser.add_argument("--validate", help="Validate single todo JSON file")
    parser.add_argument("--validate-json", help="Validate todo from JSON string")
    parser.add_argument("--validate-all", help="Validate all todos in directory")
    parser.add_argument("--create", help="Create new todo with content")
    parser.add_argument("--priority", default="medium", choices=["high", "medium", "low"])
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if args.validate:
        with open(args.validate) as f:
            todo = json.load(f)
        
        result = validate_todo(todo)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            status = "✅ VALID" if result["valid"] else "❌ INVALID"
            print(f"\n{status}: {args.validate}")
            
            if result["errors"]:
                print("\nErrors:")
                for err in result["errors"]:
                    print(f"  ❌ {err}")
        
        return 0 if result["valid"] else 1
    
    elif args.validate_json:
        todo = json.loads(args.validate_json)
        result = validate_todo(todo)
        print(json.dumps(result, indent=2))
        return 0 if result["valid"] else 1
    
    elif args.validate_all:
        result = validate_all_todos(args.validate_all)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"\n{'='*60}")
            print(f"TODO VALIDATION: {args.validate_all}")
            print(f"{'='*60}")
            print(f"Files checked: {result['files_checked']}")
            print(f"Valid: {result['valid_count']}")
            print(f"Invalid: {result['invalid_count']}")
            
            for r in result["results"]:
                status = "✅" if r["valid"] else "❌"
                print(f"  {status} {r.get('id', r.get('file', ''))}")
                for err in r.get("errors", []):
                    print(f"       ❌ {err}")
        
        return 0 if result["valid"] else 1
    
    elif args.create:
        todo = create_todo(args.create, priority=args.priority)
        
        if args.json:
            print(json.dumps(todo, indent=2))
        else:
            print(json.dumps(todo, indent=2))
            print(f"\n✅ Created todo: {todo['id']}")
        
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
