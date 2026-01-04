VERSION: 3.0
MODIFIED: 2026-01-04T06:00:00Z
IMPORTS: SCHEMAS.md, CLAUDE.md
HOOKS: stage_gate_validator.py, pre_compaction_hook.py, output_validator.py

---

## 0. CONSTANTS

```python
WORKFLOW = ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "REVIEW", "VALIDATE", "LEARN"]

MODELS = {
    "planning": "Opus",
    "execution": "Sonnet", 
    "review": "GPT-5.2",
    "learn": "Haiku"
}

GATES = {
    "PLAN":      ["todo", "evidence"],
    "REVIEW":    ["review_gate", "evidence"],
    "DISRUPT":   ["conflict", "evidence"],
    "IMPLEMENT": ["todo", "evidence"],
    "TEST":      ["evidence", "metrics"],
    "VALIDATE":  ["review_gate", "evidence"],
    "LEARN":     ["skill", "metrics"]
}

MAX_RETRY = 3
TIMEOUT = "60m"
```

---

## 1. MAIN

```python
def main(user_input: str) -> Result:
    
    # 1.1 STARTUP [BLOCKING]
    startup = startup_sequence()
    ASSERT startup.status == "PASS", f"Startup failed: {startup.error}"
    
    # 1.2 PLAN [BLOCKING]
    plan = create_plan(user_input)
    gate = quality_gate("PLAN", plan.outputs)
    ASSERT gate.action == "PROCEED", gate.errors
    
    # 1.3 APPROVAL [BLOCKING]
    approval = await_user("APPROVED|REJECTED")
    IF approval == "REJECTED":
        RETURN Result(status="REJECTED", feedback=approval.feedback)
    
    # 1.4 EXECUTE WORKFLOW
    FOR stage IN WORKFLOW[1:]:  # Skip PLAN (already done)
        output = execute_stage(stage)
        gate = quality_gate(stage, output)
        
        IF gate.action == "REVISE":
            output = retry_stage(stage, gate.errors, retry=1)
            gate = quality_gate(stage, output)
        
        IF gate.action == "ESCALATE":
            handoff = create_handoff(stage, gate)
            output = invoke_agent("Opus", handoff)
            gate = quality_gate(stage, output)
        
        IF gate.action == "STOP":
            recovery = create_recovery(stage, gate)
            RAISE WorkflowTerminated(recovery)
        
        ASSERT gate.action == "PROCEED"
    
    # 1.5 COMPLETE
    RETURN Result(status="COMPLETE", evidence=collect_all_evidence())
```

See full AGENTS.md specification for complete workflow implementation details.
