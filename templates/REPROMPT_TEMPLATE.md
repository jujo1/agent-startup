# REPROMPT_TEMPLATE.md

```
VERSION: 1.0
TRIGGER: quality_gate.action IN ["STOP", "REVISE", "ESCALATE"]
HOOK: hooks/stage_gate_validator.py
```

---

## TEMPLATE

```
================================================================================
⛔ QUALITY GATE FAILED
================================================================================

STAGE:        {stage}
ATTEMPT:      {retry_count}/{max_retry}
TIMESTAMP:    {timestamp}
ACTION:       {action}

--------------------------------------------------------------------------------
ERRORS ({error_count}):
--------------------------------------------------------------------------------
{for error in errors}
  ❌ {error}
{endfor}

--------------------------------------------------------------------------------
REQUIRED SCHEMAS NOT SATISFIED:
--------------------------------------------------------------------------------
{for schema in missing_schemas}
  ⚠️  {schema}: {schema_description}
{endfor}

--------------------------------------------------------------------------------
SCHEMAS CHECKED:
--------------------------------------------------------------------------------
{for schema in checked_schemas}
  {✅ if valid else ❌} {schema}
{endfor}

================================================================================
CORRECTIVE ACTION REQUIRED
================================================================================

{if action == "REVISE"}
INSTRUCTION: Fix errors and resubmit stage output.

CHECKLIST:
  [ ] All required fields present
  [ ] Enum values valid
  [ ] Paths absolute
  [ ] Evidence file exists at location
  [ ] Timestamps ISO8601

RESUBMIT:
  python stage_gate_validator.py --stage {stage} --file {output_file} --retry {retry_count + 1}

{elif action == "ESCALATE"}
INSTRUCTION: Max retries exceeded. Escalating to Opus.

HANDOFF:
  {{
    "handoff": {{
      "from_agent": "{current_agent}",
      "to_agent": "Opus",
      "timestamp": "{timestamp}",
      "context": {{
        "user_objective": "{objective}",
        "current_stage": "{stage}",
        "completed_stages": {completed_stages},
        "todos_remaining": {todos_remaining},
        "evidence_collected": {evidence_collected},
        "blockers": {errors},
        "assumptions": [],
        "memory_refs": []
      }},
      "instructions": "Quality gate failed after {max_retry} attempts. Review and fix.",
      "expected_output": "Valid {stage} output passing all schema validations",
      "deadline": "{deadline}"
    }}
  }}

{elif action == "STOP"}
INSTRUCTION: Critical failure. Workflow terminated.

RECOVERY:
  {{
    "recovery": {{
      "id": "R-{timestamp_compact}",
      "trigger": "quality_gate_critical_failure",
      "rollback_to": "{last_checkpoint}",
      "state_before": "{state_path}/before.json",
      "state_after": "{state_path}/after.json",
      "success": false,
      "resume_stage": "{stage}"
    }}
  }}

{endif}
================================================================================
```

---

## SCHEMA_DESCRIPTIONS

```python
SCHEMA_DESCRIPTIONS = {
    "todo": "Task with 17 fields: id, content, status, priority, metadata.*",
    "evidence": "Proof with id (E-{stage}-{task}-{seq}), type, claim, location, verified",
    "review_gate": "Gate result with stage, agent, criteria_checked[], approved, action",
    "conflict": "Dispute with id, type, parties[], positions[], resolution",
    "metrics": "Stats with workflow_id, stages.*, agents.*, evidence.*, quality.*",
    "skill": "Capability with name, source, purpose, interface, tested, evidence_location",
    "handoff": "Transfer with from_agent, to_agent, context.*, instructions",
    "startup": "Init check with mcp_verified, scheduler_active, memory_ok, env_ready",
    "recovery": "Rollback with id, trigger, rollback_to, state_before/after, resume_stage"
}
```

---

## IMPLEMENTATION

```python
def generate_reprompt(gate_result: dict) -> str:
    """Generate reprompt from quality gate failure."""
    
    template = load_template("REPROMPT_TEMPLATE.md")
    
    context = {
        "stage": gate_result["stage"],
        "retry_count": gate_result.get("retry", 0),
        "max_retry": 3,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "timestamp_compact": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S"),
        "action": gate_result["action"],
        "errors": gate_result["errors"],
        "error_count": len(gate_result["errors"]),
        "checked_schemas": gate_result.get("checked", []),
        "missing_schemas": [
            s for s in QUALITY_GATES[gate_result["stage"]] 
            if s not in gate_result.get("checked", [])
        ],
        "schema_description": SCHEMA_DESCRIPTIONS,
        "output_file": f".workflow/{gate_result['stage'].lower()}_output.json",
        "current_agent": os.environ.get("AGENT_ID", "Sonnet"),
        "objective": os.environ.get("USER_OBJECTIVE", ""),
        "completed_stages": get_completed_stages(),
        "todos_remaining": get_pending_todos(),
        "evidence_collected": get_evidence_list(),
        "last_checkpoint": get_last_checkpoint(),
        "state_path": f".workflow/state/{gate_result['stage'].lower()}",
        "deadline": (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
    }
    
    return render_template(template, context)


def on_quality_gate_fail(gate_result: dict) -> None:
    """Hook called when quality gate fails."""
    
    reprompt = generate_reprompt(gate_result)
    
    # Log to workflow
    log_path = Path(f".workflow/logs/gate_failures.jsonl")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a") as f:
        f.write(json.dumps({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "gate_result": gate_result,
            "reprompt_generated": True
        }) + "\n")
    
    # Output reprompt
    print(reprompt)
    
    # Take action
    if gate_result["action"] == "REVISE":
        # Continue in same agent
        raise ReviseRequired(reprompt)
    
    elif gate_result["action"] == "ESCALATE":
        # Handoff to Opus
        handoff = create_handoff(gate_result)
        invoke_agent("Opus", handoff)
    
    elif gate_result["action"] == "STOP":
        # Critical failure
        recovery = create_recovery(gate_result)
        save_recovery(recovery)
        raise WorkflowTerminated(reprompt)
```

---

## QUALITY_GATES

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

MAX_RETRY = 3

def quality_gate(stage: str, outputs: list[dict], retry: int = 0) -> GateResult:
    """Execute quality gate validation."""
    
    required = QUALITY_GATES[stage]
    result = GateResult(stage=stage, valid=True, checked=[], errors=[])
    
    # Validate each output
    for output in outputs:
        schema = detect_schema(output)
        if schema:
            valid, errors = validate_schema(output, schema)
            result.checked.append(schema)
            if not valid:
                result.valid = False
                result.errors.extend([f"[{schema}] {e}" for e in errors])
    
    # Check required present
    for req in required:
        if req not in result.checked:
            result.valid = False
            result.errors.append(f"Missing required schema: {req}")
    
    # Determine action
    if not result.valid:
        if retry >= MAX_RETRY:
            result.action = "ESCALATE"
        elif len(result.errors) > 10:
            result.action = "STOP"
        else:
            result.action = "REVISE"
    else:
        result.action = "PROCEED"
    
    result.retry = retry
    
    # Trigger reprompt on failure
    if result.action != "PROCEED":
        on_quality_gate_fail(result.to_dict())
    
    return result
```

---

## EXAMPLE_OUTPUT

```
================================================================================
⛔ QUALITY GATE FAILED
================================================================================

STAGE:        IMPLEMENT
ATTEMPT:      1/3
TIMESTAMP:    2026-01-04T06:30:00Z
ACTION:       REVISE

--------------------------------------------------------------------------------
ERRORS (2):
--------------------------------------------------------------------------------
  ❌ [todo] Missing: metadata.success_criteria
  ❌ Missing required schema: evidence

--------------------------------------------------------------------------------
REQUIRED SCHEMAS NOT SATISFIED:
--------------------------------------------------------------------------------
  ⚠️  evidence: Proof with id (E-{stage}-{task}-{seq}), type, claim, location, verified

--------------------------------------------------------------------------------
SCHEMAS CHECKED:
--------------------------------------------------------------------------------
  ❌ todo

================================================================================
CORRECTIVE ACTION REQUIRED
================================================================================

INSTRUCTION: Fix errors and resubmit stage output.

CHECKLIST:
  [ ] All required fields present
  [ ] Enum values valid
  [ ] Paths absolute
  [ ] Evidence file exists at location
  [ ] Timestamps ISO8601

RESUBMIT:
  python stage_gate_validator.py --stage IMPLEMENT --file .workflow/implement_output.json --retry 2

================================================================================
```
