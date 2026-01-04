# CLAUDE.md

**Version:** 4.0.0  
**Modified:** 2026-01-04T07:30:00Z  
**References:** `WORKFLOW.md`, `INFRASTRUCTURE.md`, `SCHEMAS.md`, `RULES.md`

---

## Web Agent Setup

### 1. Clone Startup
```bash
git clone https://github.com/jujo1/agent-startup.git
```

### 2. Establish Funnel Connection
```
Funnel URL: https://cabin-pc.tail1a496.ts.net
SSE Endpoint: https://cabin-pc.tail1a496.ts.net/sse
Internal IP: 100.121.56.65:3000
```

### 3. Connect MCP Gateway

Add to Claude MCP servers (Settings → Integrations):

| Field | Value |
|-------|-------|
| Name | `cabin_mcp` or `MPC-Gateway` |
| URL | `https://cabin-pc.tail1a496.ts.net/sse` |
| Transport | SSE |

### 4. Verify Connection
```
MPC-Gateway:ping → {"status": "pong", "host": "cabin-pc"}
MPC-Gateway:get_status → {"platform": "Windows", "python": "3.13.7"}
MPC-Gateway:list_nodes → cabin-pc, office-pc, homeassistant
```

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
| `WORKFLOW.md` | 8-stage workflow procedures |
| `INFRASTRUCTURE.md` | Nodes, MCP, Docker, credentials |
| `SCHEMAS.md` | Todo, evidence, handoff, metrics schemas |
| `RULES.md` | R01-R54 enforcement rules |
| `agents/*.md` | Agent definitions |

---

## 3. Startup (BLOCKING)

```python
PROCEDURE startup():
    # 3.1 MCP Verification (via MCP Gateway)
    ping_result = CALL MPC-Gateway:ping
    IF ping_result.status != "pong": TERMINATE("MCP Gateway failed")
    
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

**Hook:** `startup_validator.py`

---

## 4. MCP Servers

| Server | Purpose | Via Gateway |
|--------|---------|-------------|
| `MPC-Gateway` | Main gateway | Direct |
| `memory` | Storage | Yes |
| `todo` | Task management | Yes |
| `sequential-thinking` | Reasoning | Yes |
| `git` | Version control | Yes |
| `github` | GitHub API | Yes |
| `scheduler` | Timers | Yes |
| `openai-chat` | Third-party review | Yes |
| `credentials` | Secure storage | Yes |
| `claude-context` | Semantic search | Yes |

### Gateway Tools

```python
GATEWAY_TOOLS = [
    "ping",           # Test connectivity
    "get_status",     # Platform info
    "list_nodes",     # Available nodes
    "node_status",    # Check node
    "remote_exec",    # Execute on node
    "remote_mcp",     # Proxy MCP call
    "remote_file_read",
    "remote_file_write",
    "read_file",
    "list_directory",
    "grep",
    "glob_files"
]
```

---

## 5. Main Loop

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

## 6. Quality Gates (BLOCKING)

| Stage | Required Schemas | Reviewer | Third-Party |
|-------|-----------------|----------|-------------|
| PLAN | todo, evidence | User | No |
| REVIEW | review_gate, evidence | Opus | No |
| DISRUPT | conflict, evidence | Opus | **GPT-5.2** |
| IMPLEMENT | todo, evidence | Agent | No |
| TEST | evidence, metrics | Agent | No |
| REVIEW | review_gate, evidence | Opus | No |
| VALIDATE | review_gate, evidence | Opus | **GPT-5.2** |
| LEARN | skill, metrics | Haiku | No |

**Hook:** `stage_gate_validator.py`

---

## 7. Agents

| Agent | Model | Stage | Trigger |
|-------|-------|-------|---------|
| Planner | Opus 4.5 | PLAN | Task start |
| Reviewer | Opus 4.5 | REVIEW | After PLAN/TEST |
| Disruptor | Opus 4.5 | DISRUPT | After REVIEW |
| Executor | Sonnet 4.5 | IMPLEMENT | After DISRUPT |
| Tester | Sonnet 4.5 | TEST | After IMPLEMENT |
| Validator | GPT-5.2 | VALIDATE | After REVIEW |
| Learner | Haiku 4.5 | LEARN | After VALIDATE |
| Observer | Opus 4.5 | ALL | Complex tasks |

---

## 8. Todo Schema (17 Fields)

```python
TODO = {
    # Base (4)
    "id": "1.1",
    "content": "Task description",
    "status": "pending",  # pending|in_progress|completed|blocked|failed
    "priority": "high",   # high|medium|low
    
    # Metadata (13)
    "metadata": {
        "objective": "What this achieves",
        "success_criteria": "How to verify",
        "fail_criteria": "What indicates failure",
        "evidence_required": "log",  # log|output|test_result|diff|screenshot
        "evidence_location": ".workflow/evidence/1.1.log",
        "agent_model": "Claude",  # Claude|GPT|Ollama
        "workflow": "PLAN→IMPLEMENT→TEST",
        "blocked_by": [],
        "parallel": False,
        "workflow_stage": "IMPLEMENT",
        "instructions_set": "CLAUDE.md",
        "time_budget": "≤15m",
        "reviewer": "GPT-5.2"
    }
}
```

**Hook:** `todo_enforcer.py`

---

## 9. Evidence Requirements

5-step verification:

```python
1. IDENTIFY  # Name command/tool
2. RUN       # Execute with logging
3. READ      # Check for errors
4. VERIFY    # Confirm success criteria
5. STATE     # Summarize with evidence path
```

**Hook:** `evidence_validator.py`

---

## 10. Network Topology

```
CLAUDE WEB/CLOUD
       │
       │ SSE
       ▼
┌──────────────────────────────────────┐
│ https://cabin-pc.tail1a496.ts.net/sse│  Funnel
└──────────────────┬───────────────────┘
                   │
                   ▼
        ┌─────────────────┐
        │    cabin-pc     │  MASTER
        │  100.121.56.65  │
        │   MCP Gateway   │
        └────────┬────────┘
                 │
      ┌──────────┼──────────┐
      ▼          ▼          ▼
 office-pc  homeassistant  [MCP Servers]
 40 agents    8 agents      10 servers
```

---

## 11. Parallel Execution (M40)

```python
IF len(tasks) >= PARALLEL_THRESHOLD:
    MUST execute_parallel(tasks)
```

---

## 12. Reprompt Template

```
================================================================================
⛔ QUALITY GATE FAILED
================================================================================
STAGE:   {stage}
ACTION:  {action}
ERRORS:  {count}
--------------------------------------------------------------------------------
{errors}
--------------------------------------------------------------------------------
REQUIRED: {schemas}
FIX:     Address errors, resubmit
================================================================================
```

---

## 13. Morality (Non-Negotiable)

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

---

## 14. Quick Reference

### Commands

```bash
# Startup
python scripts/startup.py

# Validate todo
python scripts/validate.py --todo todo.json

# Check MCP
python tools/mcp_ping.py

# Third-party review
python tools/third_party.py --stage VALIDATE --file outputs.json
```

### MCP Gateway Calls

```
MPC-Gateway:ping
MPC-Gateway:get_status
MPC-Gateway:list_nodes
MPC-Gateway:node_status node="cabin-pc"
MPC-Gateway:remote_exec command="ls" node="office-pc"
MPC-Gateway:read_file path="/path/to/file"
```

---

## 15. Files

```
agent-startup/
├── instructions/
│   ├── CLAUDE.md          ← YOU ARE HERE
│   ├── WORKFLOW.md
│   ├── INFRASTRUCTURE.md
│   ├── SCHEMAS.md
│   ├── RULES.md
│   └── agents/
├── skills/workflow-enforcement/
├── scripts/
├── tools/
├── config/
└── templates/
```

---

## END OF CLAUDE.md
