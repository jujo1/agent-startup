# SCHEMAS.md

**Keywords:** schema, JSON, evidence, handoff, conflict, recovery, metrics  
**Created:** 2026-01-04T06:00:00Z  
**Modified:** 2026-01-04T06:00:00Z  
**References:** `AGENTS_2.md`, `CLAUDE_2.md`

---

## Index

1. [Todo Schema](#1-todo-schema)
2. [Evidence Schema](#2-evidence-schema)
3. [Handoff Schema](#3-handoff-schema)
4. [Recovery Schema](#4-recovery-schema)
5. [Conflict Schema](#5-conflict-schema)
6. [Metrics Schema](#6-metrics-schema)
7. [Review Gate Schema](#7-review-gate-schema)
8. [Skill Schema](#8-skill-schema)
9. [Startup Schema](#9-startup-schema)

---

## 1. Todo Schema

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
    "evidence_location": "abs_path",
    "agent_model": "Claude|GPT|Ollama",
    "workflow": "string",
    "blocked_by": ["task_id"],
    "parallel": true|false,
    "workflow_stage": "PLAN|REVIEW|DISRUPT|IMPLEMENT|TEST|VALIDATE|LEARN",
    "instructions_set": "string",
    "time_budget": "â‰¤60m",
    "reviewer": "string"
  }
}
```

**Example:**
```json
{"id":"1.1","content":"Create venv","status":"pending","priority":"high","metadata":{"objective":"Python isolation","success_criteria":"venv activates","fail_criteria":"Activation fails","evidence_required":"log","evidence_location":"./logs/stage1_venv.log","agent_model":"Claude","workflow":"Planâ†’Implâ†’Test","blocked_by":[],"parallel":false,"workflow_stage":"IMPLEMENT","instructions_set":"AGENTS_2.md","time_budget":"â‰¤15m","reviewer":"Infra"}}
```

---

## 2. Evidence Schema

```json
{
  "evidence": {
    "id": "E-{stage}-{task}-{seq}",
    "type": "log|output|test_result|diff|screenshot|api_response",
    "claim": "string",
    "location": "abs_path",
    "timestamp": "ISO8601",
    "hash": "sha256",
    "verified": true|false,
    "verified_by": "agent|third-party|user",
    "verification_method": "execution|inspection|comparison"
  }
}
```

**Example:**
```json
{"evidence":{"id":"E-IMPL-1.1-001","type":"log","claim":"venv activates","location":"./logs/stage1_venv.log","timestamp":"2026-01-04T06:00:00Z","hash":"a1b2c3...","verified":true,"verified_by":"Tester","verification_method":"execution"}}
```

---

## 3. Handoff Schema

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
{"ack":{"from":"receiving_agent","handoff_id":"string","understood":true|false,"questions":["string"],"eta":"ISO8601"}}
```

---

## 4. Recovery Schema

```json
{
  "recovery": {
    "id": "R-{timestamp}",
    "trigger": "string",
    "rollback_to": "checkpoint_id",
    "state_before": "path",
    "state_after": "path",
    "success": true|false,
    "resume_stage": "string"
  }
}
```

---

## 5. Conflict Schema

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

## 6. Metrics Schema

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

## 7. Review Gate Schema

```json
{
  "review_gate": {
    "stage": "string",
    "agent": "string",
    "timestamp": "ISO8601",
    "criteria_checked": [
      {
        "criterion": "string",
        "pass": true|false,
        "evidence": "path",
        "issue": "string if fail"
      }
    ],
    "approved": true|false,
    "action": "proceed|revise|escalate",
    "feedback": "string"
  }
}
```

---

## 8. Skill Schema

```json
{
  "skill": {
    "name": "string",
    "source": "string",
    "purpose": "string",
    "interface": "string",
    "tested": true|false,
    "evidence_location": "string"
  }
}
```

---

## 9. Startup Schema

```json
{
  "startup": {
    "mcp_verified": true,
    "scheduler_active": true,
    "memory_ok": true,
    "env_ready": true,
    "workflow_dir": "./.workflow/{id}/",
    "timestamp": "ISO8601"
  }
}
```
