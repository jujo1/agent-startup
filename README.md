# Agent Startup

Complete agent startup files for Claude Web/Cloud - instruction sets, skills, scripts, tools.

## Quick Start (Web Agents)

### 1. Clone Startup Files
```bash
git clone https://github.com/jujo1/agent-startup.git
```

### 2. Connect MCP Gateway

Add to Claude MCP servers (Settings → Integrations):

| Field | Value |
|-------|-------|
| **Name** | `cabin_mcp` |
| **URL** | `https://cabin-pc.tail1a496.ts.net/sse` |

### 3. Verify Connection
```
Use MPC-Gateway:ping
```

### 4. Read Entry Point
Reference `instructions/CLAUDE.md`

---

**📖 Full Setup Guide: [WEB_AGENT_SETUP.md](WEB_AGENT_SETUP.md)**

---

## Alternative: Claude Code

```bash
git clone https://github.com/jujo1/agent-startup.git ~/.claude/agent-startup
```

## Structure

```
agent-startup/
├── instructions/           # Agent instruction sets
│   ├── CLAUDE.md          # Entry point (AGENTS_6)
│   ├── WORKFLOW.md        # 8-stage workflow
│   ├── INFRASTRUCTURE.md  # Nodes, MCP, Docker
│   ├── SCHEMAS.md         # JSON schemas
│   ├── RULES.md           # R01-R54 enforcement
│   └── agents/            # Individual agent definitions
│       ├── planner.md
│       ├── reviewer.md
│       ├── disruptor.md
│       ├── executor.md
│       ├── tester.md
│       ├── validator.md
│       ├── learner.md
│       └── observer.md
├── skills/                # Claude skills
│   └── workflow-enforcement/
│       ├── SKILL.md
│       ├── startup_validator.py
│       ├── stage_gate_validator.py
│       ├── verification_hook.py
│       ├── evidence_validator.py
│       ├── todo_enforcer.py
│       ├── memory_gate.py
│       └── third_party_hook.py
├── scripts/               # Startup & utility scripts
│   ├── startup.py         # Full startup sequence
│   └── validate.py        # Validation utilities
├── tools/                 # MCP tools & integrations
│   ├── mcp_ping.py        # MCP server health check
│   └── third_party.py     # Third-party review integration
├── config/                # Configuration files
│   ├── settings.json      # Default settings
│   └── schemas.json       # JSON schema definitions
└── templates/             # Output templates
    ├── reprompt.md        # Quality gate failure template
    └── REPROMPT_TEMPLATE.md
```

## Workflow

```
PLAN → REVIEW → DISRUPT → IMPLEMENT → TEST → REVIEW → VALIDATE → LEARN
```

Every stage has a quality gate with required schemas:

| Stage | Required | Third-Party |
|-------|----------|-------------|
| PLAN | todo, evidence | No |
| REVIEW | review_gate, evidence | No |
| DISRUPT | conflict, evidence | **GPT-5.2** |
| IMPLEMENT | todo, evidence | No |
| TEST | evidence, metrics | No |
| REVIEW | review_gate, evidence | No |
| VALIDATE | review_gate, evidence | **GPT-5.2** |
| LEARN | skill, metrics | No |

## Agents

| Agent | Model | Stage | Responsibilities |
|-------|-------|-------|------------------|
| **Planner** | Opus 4.5 | PLAN | Research, 17-field todos, test design |
| **Reviewer** | Opus 4.5 | REVIEW | Validation, gap detection |
| **Disruptor** | Opus 4.5 | DISRUPT | Assumption testing, third-party |
| **Executor** | Sonnet 4.5 | IMPLEMENT | Parallel execution, no placeholders |
| **Tester** | Sonnet 4.5 | TEST | Unit/integration/full tests |
| **Validator** | GPT-5.2 | VALIDATE | Third-party approval |
| **Learner** | Haiku 4.5 | LEARN | Memory storage, indexing |
| **Observer** | Opus 4.5 | ALL | Stall detection, reprompts |

## Todo Schema (17 Fields)

Every todo requires these 17 fields:

**Base (4):**
- `id` - Unique identifier
- `content` - Task description
- `status` - pending/in_progress/completed/blocked/failed
- `priority` - high/medium/low

**Metadata (13):**
- `objective` - What this achieves
- `success_criteria` - How to verify success
- `fail_criteria` - What indicates failure
- `evidence_required` - Type of evidence needed
- `evidence_location` - Where evidence will be stored
- `agent_model` - Which model executes
- `workflow` - Workflow path
- `blocked_by` - Dependencies
- `parallel` - Can run in parallel
- `workflow_stage` - Current stage
- `instructions_set` - Which instructions apply
- `time_budget` - Time limit
- `reviewer` - Who reviews

## Evidence Requirements

5-step evidence verification:

1. **IDENTIFY** - Name the command/tool
2. **RUN** - Execute with full logging
3. **READ** - Check output for errors
4. **VERIFY** - Confirm success criteria met
5. **STATE** - Summarize findings with evidence path

## Usage

### Run Startup

```bash
python scripts/startup.py
```

### Validate Todo

```bash
python scripts/validate.py --todo todo.json
```

### Check MCP Servers

```bash
python tools/mcp_ping.py
```

### Third-Party Review

```bash
python tools/third_party.py --stage VALIDATE --file outputs.json
```

## Morality (Non-Negotiable)

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
- Updated: 2026-01-04
- Related: [claude-instructions AGENTS_6](https://github.com/jujo1/claude-instructions/tree/AGENTS_6)

## License

MIT
