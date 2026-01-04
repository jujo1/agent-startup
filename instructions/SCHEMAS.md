# SCHEMAS.md

```yaml
VERSION: 5.0
MODIFIED: 2026-01-04T07:00:00Z
VALIDATOR: hooks/output_validator.py
SCHEMAS: [todo, evidence, review_gate, handoff, conflict, metrics, skill, startup, recovery]
```

---

## 0. VALIDATION FUNCTION

```python
def validate(data: dict, schema_name: str) -> tuple[bool, list[str]]:
    """Validate data against schema. Returns (valid, errors)."""
    
    IF schema_name NOT IN SCHEMAS:
        RETURN (False, [f"Unknown schema: {schema_name}"])
    
    schema = SCHEMAS[schema_name]
    errors = []
    
    # Unwrap nested (e.g., {"evidence": {...}} -> {...})
    IF schema_name IN data AND isinstance(data[schema_name], dict):
        data = data[schema_name]
    
    # Required fields
    FOR field IN schema.get("required", []):
        IF field NOT IN data OR data[field] IN [None, ""]:
            errors.append(f"Missing required: {field}")
    
    # Nested required (metadata, context)
    FOR nested IN ["metadata", "context"]:
        IF f"{nested}_required" IN schema:
            FOR field IN schema[f"{nested}_required"]:
                IF field NOT IN data.get(nested, {}):
                    errors.append(f"Missing: {nested}.{field}")
    
    # Enum validation
    FOR field, allowed IN schema.get("enums", {}).items():
        val = data.get(field) OR data.get("metadata", {}).get(field)
        IF val AND val NOT IN allowed:
            errors.append(f"{field}: '{val}' not in {allowed}")
    
    # Pattern validation
    FOR field, pattern IN schema.get("patterns", {}).items():
        IF field IN data AND data[field]:
            IF NOT re.match(pattern, str(data[field])):
                errors.append(f"{field}: pattern mismatch (expected {pattern})")
    
    # Type validation
    FOR field, expected IN schema.get("types", {}).items():
        val = data.get(field) OR data.get("metadata", {}).get(field)
        IF val IS NOT None AND NOT isinstance(val, expected):
            errors.append(f"{field}: expected {expected.__name__}, got {type(val).__name__}")
    
    RETURN (len(errors) == 0, errors)


def detect_schema(data: dict) -> str | None:
    """Auto-detect schema type from data structure."""
    IF "evidence" IN data: RETURN "evidence"
    IF "handoff" IN data: RETURN "handoff"
    IF "review_gate" IN data: RETURN "review_gate"
    IF "conflict" IN data: RETURN "conflict"
    IF "metrics" IN data: RETURN "metrics"
    IF "skill" IN data: RETURN "skill"
    IF "startup" IN data: RETURN "startup"
    IF "recovery" IN data: RETURN "recovery"
    IF "metadata" IN data AND "objective" IN data.get("metadata", {}):
        RETURN "todo"
    RETURN None
```

---

## 1. TODO (17 fields)

```python
SCHEMAS["todo"] = {
    "required": ["id", "content", "status", "priority", "metadata"],
    
    "metadata_required": [
        "objective",           # What this achieves
        "success_criteria",    # How to verify success
        "fail_criteria",       # What indicates failure
        "evidence_required",   # Type of evidence needed
        "evidence_location",   # Absolute path to evidence file
        "agent_model",         # Claude, GPT, Ollama
        "workflow",            # Stage sequence
        "blocked_by",          # Dependencies (list of todo IDs)
        "parallel",            # Can run in parallel (bool)
        "workflow_stage",      # Current stage
        "instructions_set",    # AGENTS.md
        "time_budget",         # Max time allowed
        "reviewer"             # Who reviews (gpt-5.2)
    ],
    
    "enums": {
        "status": ["pending", "in_progress", "completed", "blocked", "failed"],
        "priority": ["high", "medium", "low"],
        "evidence_required": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
        "workflow_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"],
        "agent_model": ["Claude", "GPT", "Ollama"]
    },
    
    "types": {
        "blocked_by": list,
        "parallel": bool
    }
}
```

### Example

```json
{
  "id": "1.1",
  "content": "Create workflow state machine",
  "status": "pending",
  "priority": "high",
  "metadata": {
    "objective": "Implement 8-stage workflow enforcement",
    "success_criteria": "All stages execute with quality gates",
    "fail_criteria": "Any stage fails validation",
    "evidence_required": "log",
    "evidence_location": "/home/user/.workflow/evidence/1.1.log",
    "agent_model": "Claude",
    "workflow": "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
    "blocked_by": [],
    "parallel": false,
    "workflow_stage": "PLAN",
    "instructions_set": "AGENTS.md",
    "time_budget": "≤60m",
    "reviewer": "gpt-5.2"
  }
}
```

---

## 2. EVIDENCE

```python
SCHEMAS["evidence"] = {
    "required": ["id", "type", "claim", "location", "timestamp", "verified", "verified_by"],
    
    "optional": ["hash", "verification_method"],
    
    "patterns": {
        "id": r"^E-[A-Z]+-[\w.]+-\d{3}$"  # E-STAGE-SESSION-SEQ
    },
    
    "enums": {
        "type": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
        "verified_by": ["agent", "third-party", "user"],
        "verification_method": ["execution", "inspection", "comparison"]
    },
    
    "types": {
        "verified": bool
    }
}
```

### Example

```json
{
  "evidence": {
    "id": "E-IMPL-abc12345-001",
    "type": "log",
    "claim": "Workflow state machine implemented with all 8 stages",
    "location": "/home/user/.workflow/evidence/workflow_impl.log",
    "timestamp": "2026-01-04T07:00:00Z",
    "hash": "sha256:a1b2c3d4...",
    "verified": true,
    "verified_by": "agent",
    "verification_method": "execution"
  }
}
```

---

## 3. REVIEW_GATE

```python
SCHEMAS["review_gate"] = {
    "required": ["stage", "agent", "timestamp", "criteria_checked", "approved", "action"],
    
    "optional": ["feedback"],
    
    "enums": {
        "action": ["proceed", "revise", "escalate"],
        "stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"]
    },
    
    "types": {
        "criteria_checked": list,
        "approved": bool
    }
}
```

### Example

```json
{
  "review_gate": {
    "stage": "REVIEW",
    "agent": "Opus",
    "timestamp": "2026-01-04T07:00:00Z",
    "criteria_checked": [
      {"criterion": "17 fields present", "pass": true, "evidence": ".workflow/todo/"},
      {"criterion": "No placeholders", "pass": true, "evidence": "grep -r TODO"}
    ],
    "approved": true,
    "action": "proceed",
    "feedback": "All criteria met"
  }
}
```

---

## 4. HANDOFF

```python
SCHEMAS["handoff"] = {
    "required": ["from_agent", "to_agent", "timestamp", "context"],
    
    "context_required": [
        "user_objective",
        "current_stage",
        "completed_stages",
        "todos_remaining",
        "evidence_collected",
        "blockers",
        "assumptions",
        "memory_refs"
    ],
    
    "optional": ["instructions", "expected_output", "deadline"],
    
    "types": {
        "completed_stages": list,
        "todos_remaining": list,
        "evidence_collected": list,
        "blockers": list,
        "assumptions": list,
        "memory_refs": list
    }
}
```

### Example

```json
{
  "handoff": {
    "from_agent": "Sonnet",
    "to_agent": "Opus",
    "timestamp": "2026-01-04T07:00:00Z",
    "context": {
      "user_objective": "Build workflow enforcement system",
      "current_stage": "IMPLEMENT",
      "completed_stages": ["PLAN", "REVIEW", "DISRUPT"],
      "todos_remaining": [{"id": "1.3", "content": "..."}],
      "evidence_collected": ["E-IMPL-abc12345-001"],
      "blockers": ["Test failure in state machine"],
      "assumptions": ["Python 3.13 available"],
      "memory_refs": ["session_123_plan"]
    },
    "instructions": "Fix test failure and continue implementation",
    "expected_output": "All tests passing",
    "deadline": "2026-01-04T08:00:00Z"
  }
}
```

---

## 5. CONFLICT

```python
SCHEMAS["conflict"] = {
    "required": ["id", "type", "parties", "positions"],
    
    "optional": ["resolution", "acknowledged"],
    
    "patterns": {
        "id": r"^C-\d{8}T\d{6}$"  # C-YYYYMMDDTHHMMSS
    },
    
    "enums": {
        "type": ["plan_disagreement", "evidence_dispute", "priority_conflict", "resource_conflict"]
    },
    
    "types": {
        "parties": list,
        "positions": list,
        "acknowledged": list
    }
}
```

### Example

```json
{
  "conflict": {
    "id": "C-20260104T070000",
    "type": "plan_disagreement",
    "parties": ["Planner", "Disruptor", "Third-party"],
    "positions": [
      {"agent": "Planner", "position": "Use async", "evidence": ".workflow/plans/"},
      {"agent": "Disruptor", "position": "Use sync for simplicity", "evidence": ".workflow/disrupt/"},
      {"agent": "Third-party", "position": "Async with fallback", "evidence": "API response"}
    ],
    "resolution": {
      "decided_by": "gpt-5.2",
      "decision": "Use async with sync fallback",
      "rationale": "Performance benefits with reliability guarantee",
      "timestamp": "2026-01-04T07:30:00Z"
    },
    "acknowledged": ["Planner", "Disruptor"]
  }
}
```

---

## 6. METRICS

```python
SCHEMAS["metrics"] = {
    "required": [
        "workflow_id",
        "timestamp",
        "total_time_min",
        "stages",
        "agents",
        "evidence",
        "quality"
    ],
    
    "optional": ["rollbacks", "conflicts"],
    
    "types": {
        "total_time_min": int,
        "rollbacks": int,
        "conflicts": int
    }
}
```

### Example

```json
{
  "metrics": {
    "workflow_id": "20260104_070000_abc12345",
    "timestamp": "2026-01-04T08:00:00Z",
    "total_time_min": 60,
    "stages": {
      "completed": 8,
      "failed": 0,
      "review_rejections": 1
    },
    "agents": {
      "tasks_assigned": 10,
      "tasks_completed": 10,
      "first_pass_success": 8
    },
    "evidence": {
      "claims": 15,
      "verified": 15
    },
    "quality": {
      "reality_tests_passed": 5,
      "rules_followed": 20,
      "review_gates_passed": 3
    },
    "rollbacks": 0,
    "conflicts": 1
  }
}
```

---

## 7. SKILL

```python
SCHEMAS["skill"] = {
    "required": ["name", "source", "purpose", "interface", "tested", "evidence_location"],
    
    "types": {
        "tested": bool
    }
}
```

### Example

```json
{
  "skill": {
    "name": "workflow-enforcement",
    "source": "LEARN stage",
    "purpose": "Enforce 8-stage workflow with quality gates",
    "interface": "python scripts/workflow_main.py",
    "tested": true,
    "evidence_location": ".workflow/test/skill_test.log"
  }
}
```

---

## 8. STARTUP

```python
SCHEMAS["startup"] = {
    "required": [
        "mcp_verified",
        "scheduler_active",
        "memory_ok",
        "env_ready",
        "workflow_dir",
        "timestamp"
    ],
    
    "types": {
        "mcp_verified": bool,
        "scheduler_active": bool,
        "memory_ok": bool,
        "env_ready": bool
    }
}
```

### Example

```json
{
  "startup": {
    "mcp_verified": true,
    "scheduler_active": true,
    "memory_ok": true,
    "env_ready": true,
    "workflow_dir": ".workflow/20260104_070000_abc12345/",
    "timestamp": "2026-01-04T07:00:00Z"
  }
}
```

---

## 9. RECOVERY

```python
SCHEMAS["recovery"] = {
    "required": [
        "id",
        "trigger",
        "rollback_to",
        "state_before",
        "state_after",
        "success",
        "resume_stage"
    ],
    
    "patterns": {
        "id": r"^R-\d{8}T\d{6}$"  # R-YYYYMMDDTHHMMSS
    },
    
    "enums": {
        "resume_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"]
    },
    
    "types": {
        "success": bool
    }
}
```

### Example

```json
{
  "recovery": {
    "id": "R-20260104T073000",
    "trigger": "quality_gate_stop",
    "rollback_to": "checkpoint_impl_001",
    "state_before": ".workflow/state/implement/before.json",
    "state_after": ".workflow/state/implement/after.json",
    "success": false,
    "resume_stage": "IMPLEMENT"
  }
}
```

---

## 10. QUALITY GATES

```python
QUALITY_GATES = {
    "PLAN":      ["todo", "evidence"],
    "REVIEW":    ["review_gate", "evidence"],
    "DISRUPT":   ["conflict", "evidence"],
    "IMPLEMENT": ["todo", "evidence"],
    "TEST":      ["evidence", "metrics"],
    "VALIDATE":  ["review_gate", "evidence"],
    "LEARN":     ["skill", "metrics"]
}

def gate_check(stage: str, outputs: list) -> GateResult:
    """Check quality gate for a stage."""
    required = QUALITY_GATES[stage]
    checked = []
    errors = []
    
    FOR output IN outputs:
        schema = detect_schema(output)
        IF schema:
            valid, errs = validate(output, schema)
            checked.append(schema)
            errors.extend(errs)
    
    FOR req IN required:
        IF req NOT IN checked:
            errors.append(f"Missing required: {req}")
    
    RETURN GateResult(
        valid=len(errors) == 0,
        checked=checked,
        errors=errors,
        action="PROCEED" IF len(errors) == 0 ELSE "REVISE"
    )
```
