# AGENTS 4.0 - Production-Ready Agent Orchestration System

**Version**: 4.0.0  
**Status**: PRODUCTION-READY (Core enforcement verified)  
**Last Updated**: 2026-01-04T08:00:00Z  
**Repository**: claude-instructions/AGENTS_4

---

## 🎯 OVERVIEW

AGENTS_4 is a reality-tested, production-ready agent orchestration system with:
- **State machine enforcement** (99+ tests, 0 failures)
- **Bypass prevention** (42/42 tests passed)
- **Field compliance** (53/53 tests passed)
- **Rule enforcement** (M9, M13, M18, M22 verified)

---

## 📋 QUICK START

### Prerequisites
- Claude Code or Claude.ai Projects
- MCP servers configured (see MCP_SETUP.md)
- GitHub access (for skill installation)

### Installation

```bash
# Clone repository
git clone https://github.com/[USER]/claude-instructions.git
cd claude-instructions
git checkout AGENTS_4

# Copy to Claude directory
cp -r agents ~/.claude/agents
cp -r mcp ~/.claude/mcp
cp -r schemas ~/.claude/schemas
cp AGENTS_4.md ~/.claude/
cp CLAUDE_2.md ~/.claude/
cp SCHEMAS.md ~/.claude/

# Install MCP servers
cd ~/.claude/mcp/servers
pip install -r requirements.txt --break-system-packages

# Test workflow enforcement
python3 workflow_validator.py --test
```

---

## 📁 REPOSITORY STRUCTURE

```
AGENTS_4/
├── README.md                    # This file
├── AGENTS_4.md                  # Main agent instructions
├── CLAUDE_2.md                  # Infrastructure configuration
├── SCHEMAS.md                   # Data schemas
├── MASTER_INDEX.md              # Complete file index
├── TODO_SCHEMA.md               # Todo field specifications
├── REALITY_TESTING_RESULTS.md  # Verification evidence
│
├── agents/                      # Agent definitions
│   ├── base/
│   │   └── BASE.agent.yaml
│   ├── core/
│   │   └── ORCHESTRATOR.agent.yaml
│   └── specialized/
│       ├── DISRUPTOR.agent.yaml
│       ├── VALIDATOR.agent.yaml
│       ├── REVIEW.agent.yaml
│       └── QUESTIONS.agent.yaml
│
├── mcp/                         # MCP servers
│   └── servers/
│       ├── workflow_validator.py
│       └── requirements.txt
│
├── schemas/                     # Schema definitions
│   ├── agent.schema.yaml
│   ├── agent.schema.json
│   ├── workflow.schema.yaml
│   ├── questions.schema.yaml
│   └── criteria.schema.yaml
│
├── scripts/                     # Generator scripts
│   ├── generate_copilot_agent.ps1
│   ├── generate_cursor_agent.ps1
│   ├── generate_native_agent.ps1
│   └── generators/
│       ├── gen_claude_code.py
│       └── gen_all.py
│
├── workflows/                   # Workflow handlers
│   ├── handlers.py
│   ├── questions.py
│   └── question_templates.py
│
├── prompts/                     # Prompt templates
│   └── plan_review_critical_template.md
│
└── templates/                   # Question templates
    └── questions/
        └── all_stages_questions.yaml
```

---

## 🚀 CORE FEATURES

### 1. State Machine Enforcement
- **File**: `mcp/servers/workflow_validator.py`
- **Status**: ✅ PRODUCTION-READY (99+ tests)
- **Capabilities**:
  - Track workflow state
  - Validate transitions
  - Block invalid progressions
  - Persist state across sessions
  - M20 restart with context

### 2. Bypass Prevention
- **File**: `mcp/servers/workflow_gateway.py`
- **Status**: ✅ VERIFIED (42/42 tests)
- **Prevents**: Direct tool access bypassing workflow

### 3. Field Compliance
- **File**: `TODO_SCHEMA.md`
- **Status**: ✅ ENFORCED (53/53 tests)
- **Validates**: 17-field todo structure

### 4. Rule Enforcement
- **Rules**: M1-M45 (see AGENTS_4.md)
- **Verified**: M9, M13, M18, M22
- **Evidence**: REALITY_TESTING_RESULTS.md

---

## 📖 DOCUMENTATION INDEX

| Document | Purpose | Status |
|----------|---------|--------|
| AGENTS_4.md | Main workflow & rules | ✅ Complete |
| CLAUDE_2.md | Infrastructure config | ⚠️ Partially verified |
| SCHEMAS.md | Data schemas | ✅ Complete |
| TODO_SCHEMA.md | Todo field spec | ✅ Complete |
| MASTER_INDEX.md | File index | ✅ Complete |
| REALITY_TESTING_RESULTS.md | Test evidence | ✅ Complete |

---

## 🧪 TESTING STATUS

### Core Components (Verified)
- ✅ workflow_validator.py - 99+ tests, 0 failures
- ✅ todo-mcp - 53/53 tests passed
- ✅ workflow-gateway - 42/42 tests passed
- ✅ State transitions - All valid paths tested

### Infrastructure (Pending Verification)
- ⚠️ MCP server availability (10 servers)
- ⚠️ Memory systems (3 systems)
- ⚠️ Agent capacity (73 claimed)
- ⚠️ Hook activation (9 hooks)

---

## 🛠️ USAGE EXAMPLES

### Example 1: Start a Workflow

```python
# In Claude Code or Claude.ai

# 1. Startup
workflow = workflow_validator_create(workflow_id="task_001")

# 2. Plan
plan = planner.create_plan(user_request="Build todo tracker")

# 3. Transition
workflow_validator_transition(
    workflow_id="task_001",
    to_state="review_pre"
)
```

### Example 2: Create Compliant Todo

```json
{
  "id": "T001",
  "content": "Implement user authentication",
  "status": "pending",
  "priority": "high",
  "metadata": {
    "objective": "Secure API endpoints",
    "success_criteria": "All tests pass, JWT working",
    "fail_criteria": "Auth bypass possible",
    "evidence_required": "test_output",
    "evidence_location": ".workflow/evidence/T001.log",
    "agent_model": "Sonnet",
    "workflow": "IMPLEMENT→TEST",
    "blocked_by": [],
    "parallel": false,
    "workflow_stage": "implement",
    "instructions_set": "AGENTS_4.md",
    "time_budget": "≤2h",
    "reviewer": "VALIDATOR"
  }
}
```

---

## 🔧 CONFIGURATION

### MCP Servers Required

1. **workflow-validator** (MANDATORY)
2. **todo** (MANDATORY)
3. memory
4. sequential-thinking
5. git
6. github
7. scheduler
8. openai-chat
9. credentials
10. mcp-gateway

### Environment Variables

```bash
# GitHub token (for repo operations)
export GH_TOKEN="ghp_..."

# OpenAI token (for gpt-5.2 validation, optional)
export OPENAI_API_KEY="sk-..."

# Workspace
export CLAUDE_HOME="$HOME/.claude"
```

---

## ⚠️ KNOWN LIMITATIONS

1. **VSCode Extension**: UI layer in progress (non-blocking)
2. **E2E Scenarios**: Deferred to Phase 6
3. **Third-party Validation**: gpt-5.2 integration optional
4. **Full Agent Set**: 7 agents need creation (see HANDOFF.md)

---

## 📞 SUPPORT

- **Issues**: GitHub Issues on this repo
- **Documentation**: See `/docs` directory
- **Testing**: See `REALITY_TESTING_RESULTS.md`
- **Contributing**: See `CONTRIBUTING.md` (TBD)

---

## 📜 LICENSE

MIT License - See LICENSE file

---

## 🎯 ROADMAP

### ✅ Phase 1-4: Complete
- Core enforcement system
- State machine
- Bypass prevention
- Field compliance

### ⏳ Phase 5: In Progress
- VSCode extension UI
- Additional agent YAMLs

### 📅 Phase 6: Planned
- E2E scenario tests
- Performance benchmarks
- Multi-project support

---

**Status**: PRODUCTION-READY (Core features)  
**Last Verified**: 2026-01-04  
**Next Review**: 2026-02-01
