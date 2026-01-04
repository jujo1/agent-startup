# SKILL.md - Workflow Enforcement

**Name:** workflow-enforcement  
**Version:** 4.0.0  
**Triggers:** Any task, workflow, plan, implement, review

---

## Overview

100% workflow enforcement with blocking quality gates at every stage transition.

```
WORKFLOW: PLAN → REVIEW → DISRUPT → IMPLEMENT → TEST → REVIEW → VALIDATE → LEARN
```

---

## Core Principle

**Evidence before claims, always.**  
Violating the letter = violating the spirit.

---

## Hooks

| Hook | File | Enforces | Blocking |
|------|------|----------|----------|
| Startup | `startup_validator.py` | S0-S20, M35 | YES |
| Stage Gate | `stage_gate_validator.py` | M04, M19 | YES |
| Verification | `verification_hook.py` | M02, M03 | YES |
| Evidence | `evidence_validator.py` | M03 | YES |
| Todo | `todo_enforcer.py` | 17 fields | YES |
| Memory | `memory_gate.py` | M35, M40 | YES |
| Third-Party | `third_party_hook.py` | M07 | YES |

---

## Quality Gates

| Stage | Required | Reviewer |
|-------|----------|----------|
| PLAN | todo, evidence | User |
| REVIEW | review_gate, evidence | Opus |
| DISRUPT | conflict, evidence | GPT-5.2 |
| IMPLEMENT | todo, evidence | Agent |
| TEST | evidence, metrics | Agent |
| REVIEW | review_gate, evidence | Opus |
| VALIDATE | review_gate, evidence | GPT-5.2 |
| LEARN | skill, metrics | Haiku |

---

## Todo Schema (17 Fields)

**Base (4):** id, content, status, priority

**Metadata (13):**
- objective, success_criteria, fail_criteria
- evidence_required, evidence_location
- agent_model, workflow, blocked_by, parallel
- workflow_stage, instructions_set, time_budget, reviewer

---

## Usage

```bash
# Startup
python hooks/startup_validator.py

# Validate todo
python hooks/todo_enforcer.py --validate todo.json

# Validate evidence
python hooks/evidence_validator.py --evidence-path log.log --claim "Tests pass"

# Quality gate
python hooks/stage_gate_validator.py --stage IMPLEMENT --file outputs.json

# Third-party review
python hooks/third_party_hook.py --review outputs.json --stage VALIDATE

# Full workflow
python lib/workflow_orchestrator.py --run "Task description"
```

---

## END
