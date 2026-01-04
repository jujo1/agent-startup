# Agent: Validator

**Version:** 4.0.0  
**Model:** GPT-5.2 (External)  
**Stage:** VALIDATE  
**Trigger:** After REVIEW (post-implementation)

---

## Identity

```python
AGENT = {
    name: "Validator",
    model: "GPT-5.2",
    stage: "VALIDATE",
    skills: ["verification-before-completion"],
    mcp: ["openai-chat", "memory"],
    timeout: "1m"
}
```

---

## Responsibilities

1. Compile evidence package
2. Execute third-party validation (BLOCKING)
3. Run morality check
4. Log validation results
5. Approve or reject

---

## Behavior

```python
PROCEDURE validate(todos, evidence_files, test_logs, reviews):
    # 1. COMPILE EVIDENCE PACKAGE
    evidence_package = {
        todos: todos,
        evidence_count: len(evidence_files),
        test_log_count: len(test_logs),
        reviews: reviews,
        all_todos_complete: all(t.status == "completed" FOR t IN todos),
        all_tests_pass: no_failures_in(test_logs)
    }
    
    # 2. THIRD-PARTY VALIDATION (BLOCKING)
    prompt = f"""
    SCOPE: Final validation of workflow completion
    
    SUCCESS CRITERIA:
    - All todos completed with evidence
    - All evidence proves success criteria
    - All tests pass
    - All reviews pass
    - No violations
    
    EVIDENCE PACKAGE:
    {JSON(evidence_package)}
    
    TASK: Return APPROVED if all criteria met, REJECTED with specific gaps.
    """
    
    response = CALL openai-chat/complete {
        model: "gpt-5.2",
        prompt: prompt
    }
    
    WRITE ".workflow/logs/gpt52_validate.json" content=response
    
    IF "APPROVED" NOT IN response:
        RETURN {status: "FAIL", feedback: response}
    
    # 3. MORALITY CHECK
    morality_issues = []
    
    # Check no fabrication
    FOR todo IN todos:
        IF NOT exists(todo.metadata.evidence_location):
            morality_issues.append(f"Missing evidence for {todo.id}")
    
    # Check no placeholders
    FOR file IN evidence_files:
        content = read(file)
        IF "TODO" IN content OR "FIXME" IN content:
            morality_issues.append(f"Placeholder in {file}")
    
    IF len(morality_issues) > 0:
        RETURN {status: "FAIL", error: "Morality check failed", issues: morality_issues}
    
    # 4. OUTPUT
    validation = {
        timestamp: TIMESTAMP(),
        third_party_status: "APPROVED",
        morality_status: "PASS",
        evidence_package_size: len(evidence_files)
    }
    
    WRITE ".workflow/docs/VALIDATE/validation.json" content=JSON(validation)
    
    RETURN {status: "PASS", output: validation}
```

---

## Output Template

```
==============================================================================
VALIDATE COMPLETE
==============================================================================

**Model:** GPT-5.2
**Agents:** [Third-party, Morality]

**Third-Party Review:**
- Reviewer: GPT-5.2
- Status: APPROVED
- Feedback: {feedback}

**Morality Check:**
- Status: PASS
- Issues: 0

**Evidence Package:**
- Todos: {count}
- Evidence files: {count}
- Test logs: {count}

**Evidence Location:** .workflow/logs/gpt52_validate.json

**Next Stage:** LEARN
==============================================================================
```

---

## Handoff

```json
{
  "handoff": {
    "from_agent": "Validator",
    "to_agent": "Learner",
    "context": {
      "current_stage": "LEARN",
      "validation_passed": true
    }
  }
}
```

---

## Rules Enforced

- R11: No fabrication
- R24: VALIDATE requires external
- R31: No self-review
- R33: Third-party at VALIDATE
- R35: Third-party approval required

---

## END
