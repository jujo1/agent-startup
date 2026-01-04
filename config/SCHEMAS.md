VERSION: 2.0
MODIFIED: 2026-01-04T06:00:00Z
VALIDATOR: hooks/output_validator.py
IMPORTS: None

---

## 1. TODO SCHEMA

```python
SCHEMAS["todo"] = {
    "required": ["id", "content", "status", "priority", "metadata"],
    
    "metadata_required": [
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
    ],
    
    "enums": {
        "status": ["pending", "in_progress", "completed", "blocked", "failed"],
        "priority": ["high", "medium", "low"],
        "evidence_required": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
        "workflow_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"],
        "agent_model": ["Claude", "GPT", "Ollama"]
    }
}
```

---

## 2. EVIDENCE SCHEMA

```python
SCHEMAS["evidence"] = {
    "required": ["id", "type", "claim", "location", "timestamp", "verified", "verified_by"],
    
    "patterns": {
        "id": r"^E-[A-Z]+-[\w.]+-\d{3}$"  # E-STAGE-TASK-SEQ
    },
    
    "enums": {
        "type": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
        "verified_by": ["agent", "third-party", "user"]
    }
}
```

---

## 3. REVIEW_GATE SCHEMA

```python
SCHEMAS["review_gate"] = {
    "required": ["stage", "agent", "timestamp", "criteria_checked", "approved", "action"],
    
    "enums": {
        "action": ["proceed", "revise", "escalate"],
        "stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"]
    }
}
```

---

## 4. QUALITY_GATES

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
```

See full SCHEMAS.md specification for complete schema definitions.
