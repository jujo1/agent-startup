# CLAUDE.md

```yaml
VERSION: 5.0
MODIFIED: 2026-01-04T07:00:00Z
TYPE: ENTRY_POINT
IMPORTS: [AGENTS.md, SCHEMAS.md, SKILLS.md, HOOKS.md]
NODE: cabin-pc (MASTER)
REPO: github.com/jujo1/agent-startup
```

---

## 0. IDENTITY

```python
SYSTEM = {
    "hostname": "CABIN-PC",
    "ip": "100.121.56.65",
    "role": "MASTER_ORCHESTRATOR",
    "gateway": "https://cabin-pc.tail1a496.ts.net",
    "capacity": 25,
    "os": "Windows 11",
    "shell": "pwsh.exe",
    "python": "3.13.7"
}

SESSION = {
    "id": ENV["SESSION_ID"] or generate_session_id(),
    "workflow_id": None,  # Set by startup
    "start_time": TIMESTAMP(),
    "agent_model": "Claude",
    "instructions_version": "5.0"
}
```

---

## 1. STARTUP [BLOCKING]

```python
def on_session_start():
    """Execute on every new session. BLOCKING - must pass before proceeding."""
    
    # 1.1 Load instructions
    LOAD "AGENTS.md"     # Workflow, agents, rules
    LOAD "SCHEMAS.md"    # 9 validation schemas
    LOAD "SKILLS.md"     # Superpowers skills
    LOAD "HOOKS.md"      # Hook definitions
    
    # 1.2 Run startup validator
    result = CALL hooks/startup_validator.py --check
    ASSERT result.status == "PASS", f"Startup failed: {result.errors}"
    
    # 1.3 Initialize workflow
    SESSION.workflow_id = result.workflow_id
    WORKFLOW_DIR = result.workflow_dir
    
    # 1.4 Display startup report
    PRINT startup_report(result)
    
    # 1.5 Ready
    RETURN "READY"
```

### 1.1 Startup Checklist

| # | Item | Check | Pass | Fail |
|---|------|-------|------|------|
| S01 | MCP memory | ping | ✅ | ABORT |
| S02 | MCP todo | ping | ✅ | ABORT |
| S03 | MCP sequential-thinking | ping | ✅ | ABORT |
| S04 | MCP git | ping | ✅ | WARN |
| S05 | MCP github | ping | ✅ | WARN |
| S06 | MCP scheduler | ping | ✅ | ABORT |
| S07 | MCP openai-chat | ping | ✅ | WARN |
| S08 | MCP credentials | ping | ✅ | WARN |
| S09 | MCP mcp-gateway | ping | ✅ | WARN |
| S10 | Reprompt timer | scheduler/create | ✅ | ABORT |
| S11 | Compaction hook | scheduler/create | ✅ | WARN |
| S12 | Memory read/write | test | ✅ | ABORT |
| S13 | Workflow directory | mkdir | ✅ | ABORT |
| S14 | Skills available | check | ✅ | WARN |
| S15 | Credentials | exists | ✅ | WARN |

---

## 2. NETWORK

```python
NODES = {
    "cabin-pc": {
        "ip": "100.121.56.65",
        "capacity": 25,
        "status": "ACTIVE",
        "role": "master",
        "mcp_port": 3000
    },
    "office-pc": {
        "ip": "100.84.172.79",
        "capacity": 40,
        "status": "ACTIVE",
        "role": "worker",
        "mcp_port": 3000
    },
    "homeassistant": {
        "ip": "100.116.245.37",
        "capacity": 8,
        "status": "ACTIVE",
        "role": "worker",
        "mcp_port": 8123
    }
}

TOTAL_CAPACITY = sum(n["capacity"] for n in NODES.values() if n["status"] == "ACTIVE")  # 73

def allocate_task(task_type: str) -> str:
    """Allocate task to appropriate node."""
    IF task_type == "planning":
        RETURN "cabin-pc"  # Opus on master
    ELIF task_type == "execution":
        RETURN max(NODES, key=lambda n: NODES[n]["capacity"])  # office-pc
    ELIF task_type == "homeauto":
        RETURN "homeassistant"
    ELSE:
        RETURN round_robin(NODES)
```

---

## 3. DOCKER

```python
CONTAINERS = {
    "milvus-standalone": {"node": "cabin-pc", "port": 19530, "purpose": "vector_embeddings"},
    "qdrant":            {"node": "cabin-pc", "port": 6333,  "purpose": "vector_search"},
    "mcp-gateway":       {"node": "cabin-pc", "port": 8081,  "purpose": "mcp_routing"},
    "postgres-claude":   {"node": "office-pc", "port": 5432, "purpose": "general_storage"},
    "postgres-creds":    {"node": "office-pc", "port": 5433, "purpose": "encrypted_creds"},
    "redis":             {"node": "office-pc", "port": 6379, "purpose": "cache_queues"}
}

def health_check(container: str) -> bool:
    node = CONTAINERS[container]["node"]
    result = CALL mcp-gateway/remote_exec {node: node, command: f"docker ps --filter name={container}"}
    RETURN "Up" in result.stdout
```

---

## 4. MCP SERVERS

```python
MCP_SERVERS = {
    "memory":             {"type": "local",  "purpose": "Persistent memory storage"},
    "todo":               {"type": "local",  "purpose": "Task management with 17-field schema"},
    "sequential-thinking":{"type": "local",  "purpose": "Step-by-step reasoning"},
    "git":                {"type": "local",  "purpose": "Git operations"},
    "github":             {"type": "remote", "purpose": "GitHub API"},
    "scheduler":          {"type": "local",  "purpose": "Timers and scheduled tasks"},
    "openai-chat":        {"type": "remote", "purpose": "GPT-5.2 third-party review"},
    "credentials":        {"type": "local",  "purpose": "Encrypted credential storage"},
    "mcp-gateway":        {"type": "remote", "purpose": "Cross-node MCP routing"},
    "claude-context":     {"type": "local",  "purpose": "Context management"}
}

def mcp_call(server: str, method: str, params: dict) -> dict:
    """Call MCP server method."""
    IF server not in MCP_SERVERS:
        RAISE MCPError(f"Unknown server: {server}")
    RETURN CALL {server}/{method} params
```

---

## 5. MEMORY SYSTEMS

```python
MEMORY = {
    "mcp_memory": {
        "location": "~/.caches/memory/memory.json",
        "server": "memory",
        "ops": ["read", "write", "search", "delete"]
    },
    "shared_memory": {
        "location": "~/.claude/shared-memory/",
        "server": "memory-bank",
        "ops": ["read", "write", "list"]
    },
    "episodic_memory": {
        "location": "~/.config/superpowers/conversation-archive/",
        "server": "episodic-memory",
        "ops": ["search", "archive"]
    }
}

def memory_workflow(phase: str, data: dict = None) -> dict:
    """Execute memory operations for workflow phase."""
    SWITCH phase:
        CASE "startup":
            prev = CALL memory/search {query: "last_session"}
            todos = CALL todo/sync
            RETURN {"previous_session": prev, "pending_todos": todos}
        
        CASE "before_task":
            context = CALL episodic-memory/search {query: data["task"]}
            RETURN {"context": context}
        
        CASE "after_task":
            CALL memory/write {key: data["task_id"], value: data["result"]}
            CALL memory-bank/write {key: data["task_id"], value: data["result"]}
            RETURN {"stored": True}
        
        CASE "shutdown":
            summary = create_session_summary()
            CALL memory/write {key: f"session_{SESSION.id}", value: summary}
            RETURN {"summary": summary}
```

---

## 6. CREDENTIALS

```python
CREDENTIAL_PATHS = {
    "primary": "~/.credentials/credentials.json",
    "mcp_tokens": "~/.credentials/mcp_tokens.json",
    "mcp_configs": "~/.claude/settings.json"
}

MCP_GATEWAY_TOKENS = {
    "claude_web": "D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k",
    "claude_code": "BrdjN6ALPRbNRhcfOs1C-dRMeq4EbMLJsDAL3A9UN8M",
    "backup": "65QE33Np7dsER73IUc2kZevfZv1WZvNc-q1-Z5pvHms"
}

def get_credential(service: str) -> str:
    creds = CALL credentials/get {service: service}
    IF creds.error:
        RAISE CredentialError(f"Missing credential: {service}")
    RETURN creds.value
```

---

## 7. PATHS

```python
PATHS = {
    # Instructions
    "claude_md":     "~/.claude/CLAUDE.md",
    "agents_md":     "~/.claude/AGENTS.md",
    "schemas_md":    "~/.claude/SCHEMAS.md",
    "skills_md":     "~/.claude/SKILLS.md",
    "hooks_md":      "~/.claude/HOOKS.md",
    
    # Directories
    "settings":      "~/.claude/settings.json",
    "credentials":   "~/.credentials/credentials.json",
    "shared_memory": "~/.claude/shared-memory/",
    "skills":        "~/.claude/skills/",
    "hooks":         "~/.claude/hooks/",
    "logs":          "~/.claude/logs/",
    "workflow":      "~/.claude/.workflow/",
    "agents":        "~/.claude/agents/",
    "scripts":       "~/.claude/scripts/"
}

def resolve_path(key: str) -> Path:
    RETURN Path(PATHS[key]).expanduser().resolve()
```

---

## 8. WORKFLOW [→ AGENTS.md]

```python
# Workflow is defined in AGENTS.md
# Summary here for reference

WORKFLOW = ["PLAN", "REVIEW", "DISRUPT", "IMPLEMENT", "TEST", "REVIEW", "VALIDATE", "LEARN"]

MODELS = {
    "planning": "Opus",
    "execution": "Sonnet",
    "review": "gpt-5.2",
    "learn": "Haiku"
}

# See AGENTS.md for full workflow definition
```

---

## 9. HOOKS [→ HOOKS.md]

```python
# Hooks are defined in HOOKS.md
# Summary here for reference

HOOKS = {
    "startup_validator":    "hooks/startup_validator.py",
    "reprompt_timer":       "hooks/reprompt_timer.py",
    "pre_compaction_hook":  "hooks/pre_compaction_hook.py",
    "skills_loader":        "hooks/skills_loader.py",
    "stage_gate_validator": "hooks/stage_gate_validator.py",
    "evidence_validator":   "hooks/evidence_validator.py",
    "output_validator":     "hooks/output_validator.py"
}

# See HOOKS.md for full hook definitions
```

---

## 10. SKILLS [→ SKILLS.md]

```python
# Skills are defined in SKILLS.md
# Summary here for reference

SKILLS = {
    "verification-before-completion": "Evidence before claims",
    "executing-plans":                "Execute plans in batches",
    "test-driven-development":        "RED-GREEN-REFACTOR",
    "systematic-debugging":           "4-phase root cause",
    "brainstorming":                  "Refine ideas through questions",
    "requesting-code-review":         "Request review with context",
    "receiving-code-review":          "Handle feedback with rigor",
    "subagent-driven-development":    "Dispatch subagents per task",
    "dispatching-parallel-agents":    "Coordinate parallel agents"
}

# See SKILLS.md for full skill definitions
```

---

## 11. AGENTS [→ AGENTS.md §5]

```python
# Agents are defined in AGENTS.md
# Summary here for reference

AGENTS = {
    "Planner":      {"model": "Opus",   "stage": "PLAN"},
    "Research":     {"model": "Opus",   "stage": "PLAN"},
    "Reviewer":     {"model": "Opus",   "stage": "REVIEW"},
    "Debate":       {"model": "Opus",   "stage": "DISRUPT"},
    "Third-party":  {"model": "gpt-5.2","stage": "DISRUPT,VALIDATE"},
    "Executor":     {"model": "Sonnet", "stage": "IMPLEMENT"},
    "Observer":     {"model": "Sonnet", "stage": "IMPLEMENT"},
    "Tester":       {"model": "Sonnet", "stage": "TEST"},
    "Morality":     {"model": "Opus",   "stage": "VALIDATE"},
    "Learn":        {"model": "Haiku",  "stage": "LEARN"}
}

# See AGENTS.md for full agent definitions
```

---

## 12. RULES [→ AGENTS.md §7]

```python
# Rules are defined in AGENTS.md
# Summary here for reference

RULES = {
    # Evidence (R01-R05)
    "R01": "semantic_search_before_grep",
    "R02": "logging_present",
    "R03": "no_error_hiding",
    "R04": "paths_tracked",
    "R05": "evidence_exists",
    
    # Code (R06-R10)
    "R06": "types_present",
    "R07": "absolute_paths",
    "R08": "no_placeholders",
    "R09": "no_fabrication",
    "R10": "complete_code",
    
    # Workflow (R11-R15)
    "R11": "parallel_for_3plus",
    "R12": "memory_stored",
    "R13": "auto_transition",
    "R14": "observer_for_complex",
    "R15": "workflow_followed",
    
    # Validation (R16-R20)
    "R16": "checklist_complete",
    "R17": "reprompt_timer_active",
    "R18": "review_gate_passed",
    "R19": "quality_100_percent",
    "R20": "third_party_approved"
}

# See AGENTS.md for full rule definitions
```

---

## 13. MORALITY

```python
MORALITY = {
    "NEVER": [
        "fabricate",
        "hide errors",
        "use placeholders",
        "skip validation",
        "claim without evidence",
        "self-verify only",
        "break working systems"
    ],
    "ALWAYS": [
        "execute before claim",
        "validate against schema",
        "pass quality gate",
        "follow workflow stages",
        "store evidence",
        "get third-party review",
        "complete full request"
    ]
}

def morality_check(action: str, output: dict) -> bool:
    FOR forbidden in MORALITY["NEVER"]:
        IF forbidden in action.lower():
            RETURN False
    
    FOR required in MORALITY["ALWAYS"]:
        IF required == "validate against schema":
            IF NOT output.get("schema_valid"):
                RETURN False
        IF required == "pass quality gate":
            IF NOT output.get("gate_passed"):
                RETURN False
    
    RETURN True
```

---

## 14. QUICK REFERENCE

### Startup Command
```bash
python ~/.claude/hooks/startup_validator.py --check
```

### Quality Gate Check
```bash
python ~/.claude/hooks/reprompt_timer.py --check
```

### Load Skills for Stage
```bash
python ~/.claude/hooks/skills_loader.py --stage IMPLEMENT
```

### Pre-Compaction Export
```bash
python ~/.claude/hooks/pre_compaction_hook.py --export --force
```

### Run Tests
```bash
python ~/.claude/tests/test_workflow.py -v
```

---

## 15. FILE MANIFEST

```
~/.claude/
├── CLAUDE.md              # THIS FILE - Entry point
├── AGENTS.md              # Workflow, agents, rules
├── SCHEMAS.md             # 9 validation schemas
├── SKILLS.md              # Superpowers skills
├── HOOKS.md               # Hook definitions
├── hooks/
│   ├── startup_validator.py
│   ├── reprompt_timer.py
│   ├── pre_compaction_hook.py
│   ├── skills_loader.py
│   ├── stage_gate_validator.py
│   ├── evidence_validator.py
│   └── output_validator.py
├── scripts/
│   ├── workflow_state_machine.py
│   └── workflow_main.py
├── agents/
│   ├── planner.yaml
│   ├── reviewer.yaml
│   ├── executor.yaml
│   └── ...
├── skills/
│   └── (loaded from superpowers)
├── templates/
│   ├── PLAN_OUTPUT_TEMPLATE.md
│   └── ...
├── tests/
│   └── test_workflow.py
├── logs/
├── .workflow/
└── shared-memory/
```

---

## 16. VERSION HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 5.0 | 2026-01-04 | Complete rewrite with state machine |
| 4.0 | 2026-01-03 | AGENTS_3 procedural format |
| 3.5 | 2026-01-02 | Personalization v3.5 |
| 3.0 | 2026-01-01 | Agent personas v1.0 |
| 2.0 | 2025-12-30 | Mandatory rules v1.2 |
| 1.0 | 2025-12-28 | Initial version |
