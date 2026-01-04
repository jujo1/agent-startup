# Agent Startup

**Version:** 5.0  
**Last Updated:** 2026-01-04  
**Author:** jujo1

A complete Claude agent instruction set with workflow enforcement, schema validation, quality gates, and hooks for maximum compliance and reliability.

---

## Quick Start

```bash
# Clone the repository
git clone https://github.com/jujo1/agent-startup.git

# Install to Claude directory
cp -r agent-startup/* ~/.claude/

# Run startup check
python ~/.claude/hooks/startup_validator.py --check

# Start a new workflow
python ~/.claude/scripts/workflow_main.py --start --objective "Your objective here"
```

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLAUDE.md                               │
│                      (Entry Point)                              │
├─────────────────────────────────────────────────────────────────┤
│                            │                                    │
│  ┌────────────┐ ┌─────────┴──────────┐ ┌────────────┐          │
│  │ AGENTS.md  │ │     SCHEMAS.md     │ │ SKILLS.md  │          │
│  │ (Workflow) │ │ (9 Schemas)        │ │ (9 Skills) │          │
│  └─────┬──────┘ └─────────┬──────────┘ └─────┬──────┘          │
│        │                  │                  │                  │
│        ▼                  ▼                  ▼                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   WORKFLOW ENGINE                         │  │
│  │  PLAN → REVIEW → DISRUPT → IMPLEMENT → TEST → VALIDATE   │  │
│  │                    → LEARN                                │  │
│  └──────────────────────────────────────────────────────────┘  │
│                            │                                    │
│  ┌─────────────────────────┴────────────────────────────────┐  │
│  │                    HOOKS.md                               │  │
│  │  startup_validator | reprompt_timer | pre_compaction     │  │
│  │  skills_loader | stage_gate_validator | output_validator │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```
agent-startup/
├── instructions/           # Core instruction documents
│   ├── CLAUDE.md          # Entry point - infrastructure
│   ├── AGENTS.md          # Workflow, agents, rules
│   ├── SCHEMAS.md         # 9 validation schemas
│   ├── SKILLS.md          # Superpowers skills
│   └── HOOKS.md           # Hook definitions
├── agents/                 # Agent YAML definitions
│   ├── planner.yaml
│   ├── reviewer.yaml
│   ├── debate.yaml
│   ├── third_party.yaml
│   ├── executor.yaml
│   ├── observer.yaml
│   ├── tester.yaml
│   ├── morality.yaml
│   ├── learn.yaml
│   └── research.yaml
├── hooks/                  # Python hook implementations
│   ├── startup_validator.py
│   ├── reprompt_timer.py
│   ├── pre_compaction_hook.py
│   ├── skills_loader.py
│   └── ...
├── scripts/                # Main workflow scripts
│   ├── workflow_state_machine.py
│   └── workflow_main.py
├── templates/              # Output templates
│   └── PLAN_OUTPUT_TEMPLATE.md
├── tests/                  # Test suite
│   └── test_workflow.py
└── README.md
```

---

## 8-Stage Workflow

| Stage | Model | Agents | Quality Gate |
|-------|-------|--------|--------------|
| PLAN | Opus | Planner, Research | todo, evidence |
| REVIEW | Opus | Reviewer | review_gate, evidence |
| DISRUPT | Opus, gpt-5.2 | Debate, Third-party | conflict, evidence |
| IMPLEMENT | Sonnet | Executor, Observer | todo, evidence |
| TEST | Sonnet | Tester | evidence, metrics |
| REVIEW | Opus | Reviewer | review_gate, evidence |
| VALIDATE | gpt-5.2, Opus | Third-party, Morality | review_gate, evidence |
| LEARN | Haiku | Learn | skill, metrics |

---

## 9 Validation Schemas

1. **todo** - 17-field task with metadata
2. **evidence** - Proof with location and verification
3. **review_gate** - Stage approval record
4. **handoff** - Agent-to-agent context transfer
5. **conflict** - Disagreement documentation
6. **metrics** - Workflow performance data
7. **skill** - Learned capability
8. **startup** - Session initialization
9. **recovery** - Error recovery state

---

## 10 Agents

| Agent | Model | Stage | Purpose |
|-------|-------|-------|---------|
| Planner | Opus | PLAN | Define solution path |
| Research | Opus | PLAN | Acquire domain knowledge |
| Reviewer | Opus | REVIEW | Validate quality |
| Debate | Opus | DISRUPT | Challenge assumptions |
| Third-party | gpt-5.2 | DISRUPT, VALIDATE | External validation |
| Executor | Sonnet | IMPLEMENT | Deliver code |
| Observer | Sonnet | IMPLEMENT | Monitor progress |
| Tester | Sonnet | TEST | Verify correctness |
| Morality | Opus | VALIDATE | Ensure integrity |
| Learn | Haiku | LEARN | Capture learnings |

---

## 9 Superpowers Skills

1. **verification-before-completion** - Evidence before claims
2. **executing-plans** - Batch execution with verification
3. **test-driven-development** - RED-GREEN-REFACTOR
4. **systematic-debugging** - 4-phase root cause
5. **brainstorming** - Idea refinement
6. **requesting-code-review** - Structured review requests
7. **receiving-code-review** - Technical feedback handling
8. **subagent-driven-development** - Fresh agents per task
9. **dispatching-parallel-agents** - Parallel coordination

---

## 7 Hooks

| Hook | Trigger | Purpose |
|------|---------|---------|
| startup_validator | session_start | Validate startup requirements |
| reprompt_timer | interval_5m | Periodic quality checks |
| pre_compaction_hook | pre_compact | Export before context loss |
| skills_loader | stage_enter | Load skills for stage |
| stage_gate_validator | stage_exit | Validate stage outputs |
| evidence_validator | evidence_create | Validate evidence |
| output_validator | output_create | Validate any output |

---

## 20 Rules

### Evidence (R01-R05)
- R01: Semantic search before grep
- R02: Logging present
- R03: No error hiding
- R04: Paths tracked
- R05: Evidence exists

### Code (R06-R10)
- R06: Types present
- R07: Absolute paths
- R08: No placeholders
- R09: No fabrication
- R10: Complete code

### Workflow (R11-R15)
- R11: Parallel for 3+ tasks
- R12: Memory stored
- R13: Auto transition
- R14: Observer for complex
- R15: Workflow followed

### Validation (R16-R20)
- R16: Checklist complete
- R17: Reprompt timer active
- R18: Review gate passed
- R19: Quality 100%
- R20: Third-party approved

---

## Morality

```
NEVER fabricate.
NEVER hide errors.
NEVER use placeholders.
NEVER skip validation.
NEVER claim without evidence.
ALWAYS execute before claim.
ALWAYS validate against schema.
ALWAYS pass quality gate.
ALWAYS follow workflow stages.
ALWAYS store evidence.
```

---

## Usage Examples

### Start New Workflow
```bash
python scripts/workflow_main.py --start --objective "Build authentication system"
```

### Check Quality Gate
```bash
python hooks/reprompt_timer.py --check
```

### Load Skills for Stage
```bash
python hooks/skills_loader.py --stage IMPLEMENT
```

### Run Tests
```bash
python tests/test_workflow.py -v
```

### Export Before Compaction
```bash
python hooks/pre_compaction_hook.py --export --force
```

---

## Installation

### For Claude Web/Cloud

1. Download this repository
2. Create a Claude Project
3. Upload instruction files to Project Knowledge
4. Reference CLAUDE.md as the entry point

### For Claude Code

```bash
# Clone to Claude directory
git clone https://github.com/jujo1/agent-startup.git ~/.claude/agent-startup

# Symlink instructions
ln -s ~/.claude/agent-startup/instructions/CLAUDE.md ~/.claude/CLAUDE.md

# Add to settings
echo '{"instructionsPath": "~/.claude/CLAUDE.md"}' > ~/.claude/settings.json
```

---

## Testing

```bash
# Run all tests
cd agent-startup
python tests/test_workflow.py

# Expected: 22 tests, all passing
```

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 5.0 | 2026-01-04 | Complete rewrite with state machine |
| 4.0 | 2026-01-03 | AGENTS_3 procedural format |
| 3.5 | 2026-01-02 | Personalization v3.5 |
| 3.0 | 2026-01-01 | Agent personas v1.0 |
| 2.0 | 2025-12-30 | Mandatory rules v1.2 |
| 1.0 | 2025-12-28 | Initial version |

---

## License

MIT License - See LICENSE file

---

## Related Repositories

- [claude-instructions](https://github.com/jujo1/claude-instructions) - Full instruction set history
- [superpowers](https://github.com/obra/superpowers) - Skills source
