# PLAN_OUTPUT_TEMPLATE.md

```
VERSION: 1.0
STAGE: PLAN
REQUIRED_SCHEMAS: [todo, evidence]
```

---

## Template

```
================================================================================
PLAN OUTPUT
================================================================================

## 1. Startup Checklist

| Item | Status |
|------|--------|
| MCP Servers (10) | {mcp_status} |
| Reprompt Timer | {scheduler_status} |
| Memory | {memory_status} |
| Workflow Directory | {workflow_dir_status} |

## 2. Objective

**User Request:** {user_input}
**Restated:** {objective}

## 3. Success Criteria

| # | Criterion | Pass Condition | Fail Condition |
|---|-----------|----------------|----------------|
{for i, c in enumerate(success_criteria, 1)}
| {i} | {c.description} | {c.pass_condition} | {c.fail_condition} |
{endfor}

## 4. Evidence Required

| Criterion | Type | Verify Command |
|-----------|------|----------------|
{for c in success_criteria}
| {c.description} | {c.evidence_type} | {c.verify_command} |
{endfor}

## 5. Evidence Locations

| Evidence | Path |
|----------|------|
{for e in evidence_locations}
| {e.name} | {e.path} |
{endfor}

## 6. Workflow Stages

| Stage | Model | Agents | Skills | MCP |
|-------|-------|--------|--------|-----|
| PLAN | Opus | Planner, Research | brainstorming, writing-plans | memory, todo, semantic-index |
| REVIEW | Opus | Reviewer | verification-before-completion | memory, todo |
| DISRUPT | Opus | Debate, Third-party | brainstorming | sequential-thinking, openai-chat |
| IMPLEMENT | Sonnet | Executor, Observer | executing-plans, TDD | git, github, memory |
| TEST | Sonnet | Tester | TDD, systematic-debugging | git, memory |
| REVIEW | Opus | Reviewer | verification-before-completion | github, openai-chat |
| VALIDATE | gpt-5.2 | Third-party, Morality | verification-before-completion | openai-chat |
| LEARN | Haiku | Learn | writing-skills | memory, semantic-index |

## 7. Quality Gates

| Gate | Condition | Fail Action |
|------|-----------|-------------|
| Template Gate | Output matches template | RESTART_AGENT |
| Evidence Gate | Evidence file exists | RESTART_AGENT |
| Proof Gate | Evidence proves claim | RESTART_AGENT |
| Third-party Gate | gpt-5.2 APPROVED | RESTART_AGENT |
| Test Gate | All tests pass | Return to IMPLEMENT |

## 8. Todos

| id | content | status | priority | objective | success_criteria | evidence_location | agent | stage | time |
|----|---------|--------|----------|-----------|------------------|-------------------|-------|-------|------|
{for t in todos}
| {t.id} | {t.content} | {t.status} | {t.priority} | {t.metadata.objective} | {t.metadata.success_criteria} | {t.metadata.evidence_location} | {t.metadata.agent_model} | {t.metadata.workflow_stage} | {t.metadata.time_budget} |
{endfor}

## 9. Third-Party Review

**Status:** {third_party_status}
**Reviewer:** gpt-5.2

## 10. Changes & Justifications

| Change | Justification |
|--------|---------------|
{for c in changes}
| {c.description} | {c.justification} |
{endfor}

================================================================================
AWAITING USER APPROVAL: Reply APPROVED or REJECTED with feedback
================================================================================
```

---

## Schema Requirements

### Required: todo (per task)

```json
{
  "id": "string",
  "content": "string",
  "status": "pending",
  "priority": "high|medium|low",
  "metadata": {
    "objective": "string",
    "success_criteria": "string",
    "fail_criteria": "string",
    "evidence_required": "log|output|test_result|diff|screenshot|api_response",
    "evidence_location": "absolute_path",
    "agent_model": "Claude|GPT|Ollama",
    "workflow": "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
    "blocked_by": [],
    "parallel": false,
    "workflow_stage": "PLAN",
    "instructions_set": "AGENTS_3.md",
    "time_budget": "≤60m",
    "reviewer": "gpt-5.2"
  }
}
```

### Required: evidence

```json
{
  "evidence": {
    "id": "E-PLAN-{session}-{seq:03d}",
    "type": "output",
    "claim": "Plan created with N todos",
    "location": ".workflow/plans/plan.json",
    "timestamp": "ISO8601",
    "verified": true,
    "verified_by": "agent"
  }
}
```

---

## Validation

Output is valid when:
1. All sections 1-10 present
2. All todos have 17 fields
3. Evidence record created
4. Evidence file exists at location
5. No placeholders (TODO, ..., pass)
6. Timestamps in ISO8601
7. Paths are absolute
