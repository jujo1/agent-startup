# CLAUDE.md

**Version:** 4.0.0  
**Modified:** 2026-01-04T07:30:00Z  
**References:** `docs/WORKFLOW.md`, `docs/INFRASTRUCTURE.md`, `docs/SCHEMAS.md`, `docs/RULES.md`

---

## Entry Point

```
main(user_input) → startup() → plan() → WORKFLOW → final_output()
```

---

## 1. Constants

```python
VERSION = "4.0.0"
WORKFLOW = ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "REVIEW", "VALIDATE", "LEARN"]
MAX_RETRY = 3
TIMEOUT_MINUTES = 20
PARALLEL_THRESHOLD = 3
TODO_FIELDS = 17
```

---

## 2. Imports

| Document | Purpose |
|----------|---------|
| `docs/WORKFLOW.md` | 8-stage workflow procedures |
| `docs/INFRASTRUCTURE.md` | Nodes, MCP, Docker, credentials |
| `docs/SCHEMAS.md` | Todo, evidence, handoff, metrics schemas |
| `docs/RULES.md` | R01-R54 enforcement rules |
| `agents/*.md` | Agent definitions |
| `hooks/*.py` | Enforcement hooks |
| `skills/*/SKILL.md` | Skill documentation |

---

## 3. Startup (BLOCKING)

```python
PROCEDURE startup():
    # 3.1 MCP Verification
    FOR server IN MCP_SERVERS:
        IF NOT ping(server): TERMINATE("MCP {server} failed")
    
    # 3.2 Scheduler Setup
    scheduler.create("reprompt_timer", interval="5m")
    compaction.register_hook("quality_gate_check")
    
    # 3.3 Memory Test
    memory.write("startup_test", TIMESTAMP)
    IF NOT memory.read("startup_test"): TERMINATE("Memory failed")
    
    # 3.4 Workflow Directory
    workflow_id = "{YYYYMMDD}_{HHMMSS}_{chat_id}"
    FOR dir IN ["todo", "docs", "test", "plans", "evidence", "logs", "parallel"]:
        mkdir(".workflow/{workflow_id}/{dir}")
    
    RETURN {status: "PASS", workflow_id, base_path}
```

**Hook:** `hooks/startup_validator.py`

---

## 4. Main Loop

```python
PROCEDURE main(user_input):
    startup_result = startup()
    ASSERT startup_result.status == "PASS"
    
    plan_result = plan(user_input)
    ASSERT plan_result.status == "APPROVED"
    
    current_stage = "REVIEW"
    WHILE current_stage != "COMPLETE":
        output = execute_stage(current_stage)
        gate = quality_gate(current_stage, output)
        
        SWITCH gate.action:
            CASE "PROCEED": current_stage = next_stage(current_stage)
            CASE "REVISE": retry_count += 1; IF retry_count > MAX_RETRY: ESCALATE
            CASE "ESCALATE": handoff_to_opus(current_stage, output)
            CASE "STOP": TERMINATE(gate.reason)
    
    RETURN final_output()
```

---

## 5. Quality Gates (BLOCKING)

| Stage | Required Schemas | Reviewer | Hook |
|-------|-----------------|----------|------|
| PLAN | todo, evidence | User | stage_gate_validator |
| REVIEW | review_gate, evidence | Opus | stage_gate_validator |
| DISRUPT | conflict, evidence | GPT-5.2 | third_party_hook |
| IMPLEMENT | todo, evidence | Agent | stage_gate_validator |
| TEST | evidence, metrics | Agent | stage_gate_validator |
| REVIEW | review_gate, evidence | Opus | stage_gate_validator |
| VALIDATE | review_gate, evidence | GPT-5.2 | third_party_hook |
| LEARN | skill, metrics | Haiku | stage_gate_validator |

```python
PROCEDURE quality_gate(stage, output):
    # Validate schema
    FOR schema IN REQUIRED_SCHEMAS[stage]:
        IF NOT validate(output, schema):
            RETURN {action: "REVISE", errors: validation_errors}
    
    # Check evidence exists
    FOR claim IN extract_claims(output):
        IF NOT exists(claim.evidence_location):
            RETURN {action: "REVISE", error: "Missing evidence"}
    
    # Third-party review (DISRUPT, VALIDATE)
    IF stage IN ["DISRUPT", "VALIDATE"]:
        review = call_third_party(stage, output)
        IF NOT review.approved:
            RETURN {action: "REVISE", feedback: review.feedback}
    
    RETURN {action: "PROCEED"}
```

**Hook:** `hooks/stage_gate_validator.py`

---

## 6. Agents

| Agent | Model | Stages | Skills |
|-------|-------|--------|--------|
| Planner | Opus 4.5 | PLAN | planning, research |
| Reviewer | Opus 4.5 | REVIEW | verification |
| Disruptor | Opus 4.5 | DISRUPT | brainstorming |
| Executor | Sonnet 4.5 | IMPLEMENT | executing-plans |
| Tester | Sonnet 4.5 | TEST | test-driven-development |
| Validator | GPT-5.2 | VALIDATE | verification |
| Learner | Haiku 4.5 | LEARN | memory-search |
| Observer | Opus 4.5 | ALL | monitoring |

**Definitions:** `agents/*.md`

---

## 7. MCP Servers

| Server | Purpose |
|--------|---------|
| memory | Persistent storage |
| todo | Task management |
| sequential-thinking | Chain of thought |
| git | Version control |
| github | Repository operations |
| scheduler | Timers, cron |
| openai-chat | Third-party review |
| credentials | Secrets management |
| mcp-gateway | Multi-node routing |
| claude-context | Semantic search |

---

## 8. Hooks

| Hook | File | Enforces | Blocking |
|------|------|----------|----------|
| Startup | `startup_validator.py` | S0-S20 | YES |
| Stage Gate | `stage_gate_validator.py` | M04, M19 | YES |
| Verification | `verification_hook.py` | M02, M03 | YES |
| Evidence | `evidence_validator.py` | M03 | YES |
| Todo | `todo_enforcer.py` | 17 fields | YES |
| Memory | `memory_gate.py` | M35, M40 | YES |
| Third-Party | `third_party_hook.py` | M07 | YES |

---

## 9. Skills

| Skill | Directory | Purpose |
|-------|-----------|---------|
| workflow-enforcement | `skills/workflow-enforcement/` | 100% gate enforcement |
| verification-before-completion | `skills/verification/` | Evidence before claims |
| test-driven-development | `skills/tdd/` | RED-GREEN-REFACTOR |
| systematic-debugging | `skills/debugging/` | 4-phase root cause |
| executing-plans | `skills/executing/` | Batch with checkpoints |
| brainstorming | `skills/brainstorming/` | Socratic refinement |
| chat-export | `skills/chat-export/` | 36-column CSV export |
| todo-tracker | `skills/todo-tracker/` | 17-field extraction |

---

## 10. Todo Schema (17 Fields)

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
    "workflow": "PLAN→REVIEW→DISRUPT→IMPLEMENT→TEST→REVIEW→VALIDATE→LEARN",
    "blocked_by": ["task_id"],
    "parallel": boolean,
    "workflow_stage": "PLAN|REVIEW|DISRUPT|IMPLEMENT|TEST|VALIDATE|LEARN",
    "instructions_set": "CLAUDE.md",
    "time_budget": "≤60m",
    "reviewer": "agent_name"
  }
}
```

**Hook:** `hooks/todo_enforcer.py`

---

## 11. Evidence Requirements

```python
PROCEDURE verify_claim(claim, command, evidence_path):
    # 1. IDENTIFY
    command = determine_verification_command(claim)
    
    # 2. RUN
    result = execute(command)
    write(evidence_path, result.stdout + result.stderr)
    
    # 3. READ
    content = read(evidence_path)
    exit_code = result.exit_code
    
    # 4. VERIFY
    IF exit_code != 0: RETURN FAIL
    IF contains(content, FAILURE_PATTERNS): RETURN FAIL
    IF NOT contains(content, claim.success_criteria): RETURN FAIL
    
    # 5. STATE
    RETURN {verified: TRUE, evidence: evidence_path, hash: sha256(content)}
```

**Hook:** `hooks/verification_hook.py`

---

## 12. Parallel Execution

```python
PROCEDURE execute_tasks(tasks):
    IF len(tasks) >= PARALLEL_THRESHOLD:
        # M40: 3+ items MUST parallelize
        WITH ThreadPoolExecutor(max_workers=5) AS executor:
            futures = [executor.submit(execute_task, t) FOR t IN tasks]
            results = [f.result() FOR f IN futures]
    ELSE:
        results = [execute_task(t) FOR t IN tasks]
    
    RETURN results
```

---

## 13. Reprompt Template

```
================================================================================
⛔ QUALITY GATE FAILED
================================================================================
STAGE:      {stage}
ATTEMPT:    {retry}/{MAX_RETRY}
ACTION:     {REVISE|ESCALATE|STOP}

ERRORS:
{FOR error IN errors}
  ❌ {error.message}
{ENDFOR}

REQUIRED SCHEMAS: {required_schemas}
CHECKED SCHEMAS:  {checked_schemas}

FIX: Address errors above and resubmit stage output
================================================================================
```

---

## 14. Morality (NON-NEGOTIABLE)

```
NEVER fabricate evidence
NEVER hide errors
NEVER use placeholders (TODO, FIXME, ..., pass)
NEVER claim without execution
NEVER self-review
NEVER skip quality gates
ALWAYS execute before claim
ALWAYS validate against schema
ALWAYS use third-party review
ALWAYS provide evidence with claims
```

---

## 15. Quick Reference

```bash
# Startup
python hooks/startup_validator.py

# Plan
python lib/workflow_orchestrator.py --stage PLAN --input "Task"

# Validate todo
python hooks/todo_enforcer.py --validate todo.json

# Verify claim
python hooks/verification_hook.py --claim "Tests pass" --command "pytest"

# Quality gate
python hooks/stage_gate_validator.py --stage IMPLEMENT --file outputs.json

# Third-party review
python hooks/third_party_hook.py --review outputs.json --stage VALIDATE

# Full workflow
python lib/workflow_orchestrator.py --run "Complete task description"
```

---

## 16. File Structure

```
claude-instructions/
├── CLAUDE.md                    # THIS FILE - Entry point
├── docs/
│   ├── WORKFLOW.md              # 8-stage workflow procedures
│   ├── INFRASTRUCTURE.md        # Nodes, MCP, Docker
│   ├── SCHEMAS.md               # All JSON schemas
│   └── RULES.md                 # R01-R54 rules
├── agents/
│   ├── planner.md               # PLAN stage agent
│   ├── reviewer.md              # REVIEW stage agent
│   ├── disruptor.md             # DISRUPT stage agent
│   ├── executor.md              # IMPLEMENT stage agent
│   ├── tester.md                # TEST stage agent
│   ├── validator.md             # VALIDATE stage agent
│   ├── learner.md               # LEARN stage agent
│   └── observer.md              # Cross-stage monitor
├── hooks/
│   ├── startup_validator.py     # Startup enforcement
│   ├── stage_gate_validator.py  # Stage exit gates
│   ├── verification_hook.py     # Evidence verification
│   ├── evidence_validator.py    # Evidence schema
│   ├── todo_enforcer.py         # 17-field validation
│   ├── memory_gate.py           # Memory-first enforcement
│   └── third_party_hook.py      # External review
├── lib/
│   └── workflow_orchestrator.py # Main execution engine
├── skills/
│   ├── workflow-enforcement/    # Gate enforcement
│   ├── verification/            # Evidence skills
│   ├── tdd/                     # Test-driven development
│   ├── debugging/               # Systematic debugging
│   ├── executing/               # Plan execution
│   ├── brainstorming/           # Idea generation
│   ├── chat-export/             # Conversation export
│   └── todo-tracker/            # Task extraction
├── templates/
│   ├── plan_output.md           # PLAN stage template
│   ├── stage_output.md          # Generic stage template
│   └── reprompt.md              # Gate failure template
└── schemas/
    ├── todo.json                # Todo schema
    ├── evidence.json            # Evidence schema
    ├── handoff.json             # Agent handoff schema
    └── metrics.json             # Workflow metrics schema
```

---

## 17. Execution Flow

```
USER INPUT
    │
    ▼
┌─────────┐
│ STARTUP │──────────────────────────────────────┐
└────┬────┘                                      │
     │ PASS                                      │ FAIL → TERMINATE
     ▼                                           │
┌─────────┐                                      │
│  PLAN   │◄─────────────────────────────────────┤
└────┬────┘                                      │
     │ APPROVED                                  │ REJECTED → REVISE
     ▼                                           │
┌─────────┐     ┌──────────────┐                 │
│ REVIEW  │────►│ QUALITY GATE │─────────────────┤
└────┬────┘     └──────────────┘                 │
     │ PROCEED                                   │ REVISE/ESCALATE/STOP
     ▼                                           │
┌─────────┐     ┌──────────────┐                 │
│ DISRUPT │────►│ QUALITY GATE │─────────────────┤
└────┬────┘     └──────────────┘                 │
     │ PROCEED                                   │
     ▼                                           │
┌───────────┐   ┌──────────────┐                 │
│ IMPLEMENT │──►│ QUALITY GATE │─────────────────┤
└────┬──────┘   └──────────────┘                 │
     │ PROCEED                                   │
     ▼                                           │
┌─────────┐     ┌──────────────┐                 │
│  TEST   │────►│ QUALITY GATE │─────────────────┤
└────┬────┘     └──────────────┘                 │
     │ PROCEED                                   │
     ▼                                           │
┌─────────┐     ┌──────────────┐                 │
│ REVIEW  │────►│ QUALITY GATE │─────────────────┤
└────┬────┘     └──────────────┘                 │
     │ PROCEED                                   │
     ▼                                           │
┌──────────┐    ┌──────────────┐                 │
│ VALIDATE │───►│ QUALITY GATE │─────────────────┘
└────┬─────┘    └──────────────┘
     │ PROCEED
     ▼
┌─────────┐
│  LEARN  │
└────┬────┘
     │
     ▼
  COMPLETE
```

---

## END OF CLAUDE.md
