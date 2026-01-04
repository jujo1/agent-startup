# REPROMPT TEMPLATE

**Version:** 4.0.0  
**Trigger:** quality_gate.action IN ["REVISE", "ESCALATE", "STOP"]

---

## Template

```
================================================================================
⛔ QUALITY GATE FAILED
================================================================================

STAGE:      {stage}
ATTEMPT:    {retry}/{max_retry}
TIMESTAMP:  {timestamp}
ACTION:     {action}

--------------------------------------------------------------------------------
ERRORS ({error_count}):
--------------------------------------------------------------------------------
{for error in errors}
  ❌ {error}
{endfor}

--------------------------------------------------------------------------------
REQUIRED SCHEMAS:
--------------------------------------------------------------------------------
{for schema in required_schemas}
  ⚠️ {schema}
{endfor}

--------------------------------------------------------------------------------
SCHEMAS CHECKED:
--------------------------------------------------------------------------------
{for schema in checked_schemas}
  {✅ if valid else ❌} {schema}
{endfor}

================================================================================
CORRECTIVE ACTION
================================================================================

{if action == "REVISE"}
INSTRUCTION: Fix errors and resubmit.

CHECKLIST:
  [ ] All required fields present
  [ ] Enum values valid
  [ ] Evidence file exists
  [ ] Timestamps ISO8601

COMMAND:
  python hooks/stage_gate_validator.py --stage {stage} --file outputs.json --retry {retry+1}

{elif action == "ESCALATE"}
INSTRUCTION: Max retries exceeded. Escalating to Opus.

HANDOFF:
  {
    "from_agent": "{agent}",
    "to_agent": "Opus",
    "context": {
      "current_stage": "{stage}",
      "blockers": {errors}
    }
  }

{elif action == "STOP"}
INSTRUCTION: Critical failure. Workflow terminated.

RECOVERY:
  {
    "id": "R-{timestamp}",
    "trigger": "quality_gate_critical",
    "resume_stage": "{stage}"
  }

{endif}
================================================================================
```

---

## Implementation

```python
def generate_reprompt(gate_result):
    return f"""
================================================================================
⛔ QUALITY GATE FAILED
================================================================================
STAGE:      {gate_result['stage']}
ATTEMPT:    {gate_result.get('retry', 0)}/{MAX_RETRY}
ACTION:     {gate_result['action']}

ERRORS:
{chr(10).join(f"  ❌ {e}" for e in gate_result['errors'])}

REQUIRED: {GATES[gate_result['stage']]}
FIX: Address errors and resubmit
================================================================================
"""
```

---

## END
