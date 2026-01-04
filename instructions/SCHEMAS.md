# SCHEMAS.md

**Version:** 4.0.0  
**Modified:** 2026-01-04T07:30:00Z  
**References:** `CLAUDE.md`, `WORKFLOW.md`

---

## Validation

```python
PROCEDURE validate(data, schema_name):
    schema = SCHEMAS[schema_name]
    errors = []
    
    # Check required fields
    FOR field IN schema.required:
        IF field NOT IN data:
            errors.append(f"Missing required field: {field}")
    
    # Check enums
    FOR field, allowed IN schema.enums.items():
        IF field IN data AND data[field] NOT IN allowed:
            errors.append(f"Invalid value for {field}: {data[field]}")
    
    # Check patterns
    FOR field, pattern IN schema.patterns.items():
        IF field IN data AND NOT regex_match(pattern, data[field]):
            errors.append(f"Invalid format for {field}: {data[field]}")
    
    RETURN {valid: len(errors) == 0, errors: errors}
```

---

## 1. Todo Schema (17 Fields)

```python
TODO_SCHEMA = {
    name: "todo",
    required: [
        "id", "content", "status", "priority",
        "metadata.objective",
        "metadata.success_criteria",
        "metadata.fail_criteria",
        "metadata.evidence_required",
        "metadata.evidence_location",
        "metadata.agent_model",
        "metadata.workflow",
        "metadata.blocked_by",
        "metadata.parallel",
        "metadata.workflow_stage",
        "metadata.instructions_set",
        "metadata.time_budget",
        "metadata.reviewer"
    ],
    enums: {
        "status": ["pending", "in_progress", "completed", "blocked", "failed"],
        "priority": ["high", "medium", "low"],
        "metadata.evidence_required": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
        "metadata.agent_model": ["Claude", "GPT", "Ollama"],
        "metadata.workflow_stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"]
    },
    patterns: {
        "metadata.evidence_location": "^(/|\\./|~/)",  # Must be path
        "metadata.time_budget": "^≤?\\d+m$"  # e.g., ≤15m
    },
    validators: {
        "metadata.blocked_by": lambda x: isinstance(x, list),
        "metadata.parallel": lambda x: isinstance(x, bool)
    }
}
```

**JSON:**
```json
{
  "id": "string",
  "content": "string",
  "status": "pending|in_progress|completed|blocked|failed",
  "priority": "high|medium|low",
  "metadata": {
    "objective": "string",
    "success_criteria": "string",
    "fail_criteria": "string",
    "evidence_required": "log|output|test_result|diff|screenshot|api_response",
    "evidence_location": "absolute_path",
    "agent_model": "Claude|GPT|Ollama",
    "workflow": "string",
    "blocked_by": ["task_id"],
    "parallel": boolean,
    "workflow_stage": "PLAN|REVIEW|DISRUPT|IMPLEMENT|TEST|VALIDATE|LEARN",
    "instructions_set": "string",
    "time_budget": "≤60m",
    "reviewer": "string"
  }
}
```

**Example:**
```json
{
  "id": "1.1",
  "content": "Create virtual environment",
  "status": "pending",
  "priority": "high",
  "metadata": {
    "objective": "Python isolation",
    "success_criteria": "venv activates successfully",
    "fail_criteria": "Activation fails or import errors",
    "evidence_required": "log",
    "evidence_location": "./logs/stage1_venv.log",
    "agent_model": "Claude",
    "workflow": "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
    "blocked_by": [],
    "parallel": false,
    "workflow_stage": "IMPLEMENT",
    "instructions_set": "CLAUDE.md",
    "time_budget": "≤15m",
    "reviewer": "Infra"
  }
}
```

---

## 2. Evidence Schema

```python
EVIDENCE_SCHEMA = {
    name: "evidence",
    required: [
        "id", "type", "claim", "location",
        "timestamp", "hash", "verified"
    ],
    enums: {
        "type": ["log", "output", "test_result", "diff", "screenshot", "api_response"],
        "verified_by": ["agent", "third-party", "user"],
        "verification_method": ["execution", "inspection", "comparison"]
    },
    patterns: {
        "id": "^E-[A-Z]+-[0-9.]+-[0-9]+$",  # E-STAGE-TASK-SEQ
        "timestamp": "^\\d{4}-\\d{2}-\\d{2}T\\d{2}:\\d{2}:\\d{2}",
        "hash": "^[a-f0-9]{64}$"  # SHA256
    }
}
```

**JSON:**
```json
{
  "evidence": {
    "id": "E-{STAGE}-{TASK}-{SEQ}",
    "type": "log|output|test_result|diff|screenshot|api_response",
    "claim": "string",
    "location": "absolute_path",
    "timestamp": "ISO8601",
    "hash": "sha256",
    "verified": boolean,
    "verified_by": "agent|third-party|user",
    "verification_method": "execution|inspection|comparison"
  }
}
```

**Example:**
```json
{
  "evidence": {
    "id": "E-IMPL-1.1-001",
    "type": "log",
    "claim": "venv activates successfully",
    "location": "./logs/stage1_venv.log",
    "timestamp": "2026-01-04T07:30:00Z",
    "hash": "a1b2c3d4e5f6...",
    "verified": true,
    "verified_by": "agent",
    "verification_method": "execution"
  }
}
```

---

## 3. Review Gate Schema

```python
REVIEW_GATE_SCHEMA = {
    name: "review_gate",
    required: [
        "stage", "agent", "timestamp",
        "criteria_checked", "approved", "action", "feedback"
    ],
    enums: {
        "action": ["proceed", "revise", "escalate", "stop"]
    }
}
```

**JSON:**
```json
{
  "review_gate": {
    "stage": "string",
    "agent": "string",
    "timestamp": "ISO8601",
    "criteria_checked": [
      {
        "criterion": "string",
        "pass": boolean,
        "evidence": "path",
        "issue": "string if fail"
      }
    ],
    "approved": boolean,
    "action": "proceed|revise|escalate|stop",
    "feedback": "string"
  }
}
```

---

## 4. Handoff Schema

```python
HANDOFF_SCHEMA = {
    name: "handoff",
    required: [
        "from_agent", "to_agent", "timestamp",
        "context", "instructions", "expected_output"
    ]
}
```

**JSON:**
```json
{
  "handoff": {
    "from_agent": "string",
    "to_agent": "string",
    "timestamp": "ISO8601",
    "context": {
      "user_objective": "string",
      "current_stage": "string",
      "completed_stages": ["string"],
      "todos_remaining": [{}],
      "evidence_collected": [{}],
      "blockers": ["string"],
      "assumptions": ["string"],
      "memory_refs": ["memory_key"]
    },
    "instructions": "string",
    "expected_output": "string",
    "deadline": "ISO8601"
  }
}
```

**Acknowledgment:**
```json
{
  "ack": {
    "from": "receiving_agent",
    "handoff_id": "string",
    "understood": boolean,
    "questions": ["string"],
    "eta": "ISO8601"
  }
}
```

---

## 5. Recovery Schema

```python
RECOVERY_SCHEMA = {
    name: "recovery",
    required: [
        "id", "trigger", "rollback_to",
        "state_before", "state_after", "success", "resume_stage"
    ],
    patterns: {
        "id": "^R-\\d{8}T\\d{6}$"
    }
}
```

**JSON:**
```json
{
  "recovery": {
    "id": "R-{timestamp}",
    "trigger": "string",
    "rollback_to": "checkpoint_id",
    "state_before": "path",
    "state_after": "path",
    "success": boolean,
    "resume_stage": "string"
  }
}
```

---

## 6. Conflict Schema

```python
CONFLICT_SCHEMA = {
    name: "conflict",
    required: [
        "id", "type", "parties", "positions"
    ],
    enums: {
        "type": ["plan_disagreement", "evidence_dispute", "priority_conflict", "resource_conflict"]
    }
}
```

**JSON:**
```json
{
  "conflict": {
    "id": "C-{timestamp}",
    "type": "plan_disagreement|evidence_dispute|priority_conflict|resource_conflict",
    "parties": ["agent"],
    "positions": [
      {
        "agent": "string",
        "position": "string",
        "evidence": "path"
      }
    ],
    "resolution": {
      "decided_by": "string",
      "decision": "string",
      "rationale": "string",
      "timestamp": "ISO8601"
    },
    "acknowledged": ["agent"]
  }
}
```

---

## 7. Metrics Schema

```python
METRICS_SCHEMA = {
    name: "metrics",
    required: [
        "workflow_id", "timestamp", "total_time_min",
        "stages", "agents", "evidence", "quality"
    ]
}
```

**JSON:**
```json
{
  "metrics": {
    "workflow_id": "string",
    "timestamp": "ISO8601",
    "total_time_min": 0,
    "stages": {
      "completed": 0,
      "failed": 0,
      "review_rejections": 0
    },
    "agents": {
      "tasks_assigned": 0,
      "tasks_completed": 0,
      "first_pass_success": 0
    },
    "evidence": {
      "claims": 0,
      "verified": 0
    },
    "quality": {
      "reality_tests_passed": 0,
      "rules_followed": 0,
      "review_gates_passed": 0
    },
    "rollbacks": 0,
    "conflicts": 0
  }
}
```

---

## 8. Skill Schema

```python
SKILL_SCHEMA = {
    name: "skill",
    required: [
        "name", "source", "purpose", "interface", "tested"
    ]
}
```

**JSON:**
```json
{
  "skill": {
    "name": "string",
    "source": "string",
    "purpose": "string",
    "interface": "string",
    "tested": boolean,
    "evidence_location": "string"
  }
}
```

---

## 9. Startup Schema

```python
STARTUP_SCHEMA = {
    name: "startup",
    required: [
        "mcp_verified", "scheduler_active", "memory_ok",
        "env_ready", "workflow_dir", "timestamp"
    ]
}
```

**JSON:**
```json
{
  "startup": {
    "mcp_verified": boolean,
    "scheduler_active": boolean,
    "memory_ok": boolean,
    "env_ready": boolean,
    "workflow_dir": ".workflow/{id}/",
    "timestamp": "ISO8601"
  }
}
```

---

## 10. Stage Output Schema

```python
STAGE_OUTPUT_SCHEMA = {
    name: "stage_output",
    required: [
        "stage", "model", "agents", "status",
        "evidence_location", "next_stage"
    ],
    enums: {
        "stage": ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "VALIDATE", "LEARN"],
        "status": ["PASS", "FAIL"]
    }
}
```

**JSON:**
```json
{
  "stage_output": {
    "stage": "string",
    "model": "string",
    "agents": ["string"],
    "skills": ["string"],
    "mcp": ["string"],
    "input_files": ["string"],
    "process_summary": "string",
    "status": "PASS|FAIL",
    "evidence_location": "string",
    "evidence_tail": "string",
    "next_stage": "string"
  }
}
```

---

## Schema Registry

```python
SCHEMAS = {
    "todo": TODO_SCHEMA,
    "evidence": EVIDENCE_SCHEMA,
    "review_gate": REVIEW_GATE_SCHEMA,
    "handoff": HANDOFF_SCHEMA,
    "recovery": RECOVERY_SCHEMA,
    "conflict": CONFLICT_SCHEMA,
    "metrics": METRICS_SCHEMA,
    "skill": SKILL_SCHEMA,
    "startup": STARTUP_SCHEMA,
    "stage_output": STAGE_OUTPUT_SCHEMA
}

PROCEDURE get_schema(name):
    IF name NOT IN SCHEMAS:
        RAISE ValueError(f"Unknown schema: {name}")
    RETURN SCHEMAS[name]
```

---

## Validation Examples

```python
# Validate todo
todo = {"id": "1.1", "content": "Test", ...}
result = validate(todo, "todo")
IF NOT result.valid:
    FOR error IN result.errors:
        PRINT(f"❌ {error}")

# Validate evidence
evidence = {"id": "E-IMPL-1.1-001", ...}
result = validate(evidence, "evidence")
ASSERT result.valid

# Validate stage output
output = {"stage": "IMPLEMENT", ...}
result = validate(output, "stage_output")
IF NOT result.valid:
    RESTART_AGENT(errors=result.errors)
```

---

## END OF SCHEMAS.md
