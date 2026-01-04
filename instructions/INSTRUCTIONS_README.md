# Claude Instructions v4.0

Complete workflow enforcement system with 100% blocking quality gates.

## Structure

```
claude-instructions/
├── CLAUDE.md                    # ENTRY POINT
├── docs/
│   ├── WORKFLOW.md              # 8-stage workflow procedures
│   ├── INFRASTRUCTURE.md        # Nodes, MCP, Docker
│   ├── SCHEMAS.md               # All JSON schemas
│   └── RULES.md                 # R01-R54 enforcement rules
├── agents/
│   ├── planner.md               # PLAN stage
│   ├── reviewer.md              # REVIEW stage
│   ├── disruptor.md             # DISRUPT stage
│   ├── executor.md              # IMPLEMENT stage
│   ├── tester.md                # TEST stage
│   ├── validator.md             # VALIDATE stage
│   ├── learner.md               # LEARN stage
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
│   └── workflow-enforcement/    # Skill documentation
├── templates/
│   └── reprompt.md              # Gate failure template
└── schemas/
    └── schemas.json             # JSON schema definitions
```

## Workflow

```
PLAN → REVIEW → DISRUPT → IMPLEMENT → TEST → REVIEW → VALIDATE → LEARN
```

## Quality Gates

Every stage exit requires schema validation:

| Stage | Required Schemas | Third-Party |
|-------|-----------------|-------------|
| PLAN | todo, evidence | No |
| REVIEW | review_gate, evidence | No |
| DISRUPT | conflict, evidence | Yes (GPT-5.2) |
| IMPLEMENT | todo, evidence | No |
| TEST | evidence, metrics | No |
| REVIEW | review_gate, evidence | No |
| VALIDATE | review_gate, evidence | Yes (GPT-5.2) |
| LEARN | skill, metrics | No |

## Quick Start

```bash
# 1. Startup
python hooks/startup_validator.py

# 2. Full workflow
python lib/workflow_orchestrator.py --run "Your task"
```

## Agents

| Agent | Model | Stage |
|-------|-------|-------|
| Planner | Opus 4.5 | PLAN |
| Reviewer | Opus 4.5 | REVIEW |
| Disruptor | Opus 4.5 | DISRUPT |
| Executor | Sonnet 4.5 | IMPLEMENT |
| Tester | Sonnet 4.5 | TEST |
| Validator | GPT-5.2 | VALIDATE |
| Learner | Haiku 4.5 | LEARN |
| Observer | Opus 4.5 | ALL |

## Morality

```
NEVER fabricate
NEVER hide errors
NEVER use placeholders
NEVER claim without evidence
NEVER self-review
ALWAYS execute before claim
ALWAYS validate against schema
ALWAYS pass quality gate
```

## Version

- Version: 4.0.0
- Modified: 2026-01-04
