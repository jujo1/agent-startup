# CLAUDE-WEB-STARTUP.md

> **Version**: 1.0.0 | **Priority**: P0-MANDATORY | **Scope**: CLAUDE-WEB-AGENTS
> **Execution**: BLOCKING-SEQUENTIAL | **Enforcement**: ZERO-TOLERANCE

---

## §0 CREDENTIALS (MANDATORY-DEFINE-FIRST)

**CRITICAL**: Agent MUST retrieve GH_PAT from userMemories before executing bootstrap.
Pattern: Look for `GH_PAT:` or `GitHub PAT:` in memory context.

```yaml
credentials:
  github:
    GH_PAT: "{INJECT_FROM_USER_MEMORY}"  # Claude retrieves from userMemories
    REPO: "jujo1/agent-startup"
  
  tailscale:
    network: "tail1a496.ts.net"
    nodes:
      cabin-pc: "100.121.56.65"
      office-pc: "100.84.172.79"
      eg-workstation: "100.78.245.37"
```

---

## §1 STARTUP SEQUENCE (MANDATORY-VERBATIM-EXECUTION)

**TRIGGER**: First message in ANY new Claude Web chat session.
**SCOPE**: Executes ONCE per session. Re-entry blocked by sentinel.

### 1.1 Startup Decision Tree

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  MANDATORY: Execute this sequence BEFORE any user task processing          │
│  FAILURE TO COMPLY = INVALID SESSION = RESTART REQUIRED                    │
└─────────────────────────────────────────────────────────────────────────────┘

START
  │
  ▼
┌─────────────────────────────────────┐
│ S01: Check sentinel file            │
│ Path: /home/claude/.agent_started   │
│ EXISTS? ──────────────────────────┬─┘
          │                         │
          │ YES                     │ NO
          ▼                         ▼
┌─────────────────────┐   ┌─────────────────────────────┐
│ SKIP TO USER TASK   │   │ S02: Bootstrap agent-startup │
│ (already initialized)│   │ Execute Python bootstrap    │
└─────────────────────┘   └──────────────┬──────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │ S03: Verify bootstrap       │
                          │ SC: 25 MCP tools loaded     │
                          │ SC: Persistence paths set   │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │ S04: Create sentinel        │
                          │ Write /home/claude/.agent_  │
                          │ started with timestamp      │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │ S05: Output confirmation    │
                          │ (VERBATIM TEMPLATE BELOW)   │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                          ┌─────────────────────────────┐
                          │ S06: Background planning    │
                          │ Spawn subagent to evaluate  │
                          │ skills/MCP consolidation    │
                          └──────────────┬──────────────┘
                                         │
                                         ▼
                                   PROCEED TO
                                   USER TASK
```

### 1.2 Bootstrap Code (EXECUTE VERBATIM)

**PRE-REQUISITE**: Agent MUST set GH_PAT before executing:
```python
import os
os.environ["GH_PAT"] = "{PAT_FROM_USERMEMORIES}"  # Agent injects from memory
```

```python
# S01-S04: Agent Startup Bootstrap
import os, requests, base64, json
from pathlib import Path
from datetime import datetime, timezone

SENTINEL = "/home/claude/.agent_started"
AGENT_DIR = "/tmp/agent-startup"
GH_PAT = os.environ.get("GH_PAT", "")  # INJECTED FROM CREDENTIALS/USERMEMORY
REPO = "jujo1/agent-startup"

def bootstrap():
    """Bootstrap agent-startup environment. Returns status dict."""
    
    # S01: Check sentinel
    if os.path.exists(SENTINEL):
        with open(SENTINEL) as f:
            return {"status": "already_initialized", "started_at": f.read().strip()}
    
    # S02: Download via GitHub API
    headers = {"Authorization": f"token {GH_PAT}", "Accept": "application/vnd.github.v3+json"}
    
    files_to_fetch = [
        "mcp/servers/cloud_agent_mcp.py",
        "mcp/servers/requirements.txt",
        "skills/dialectic-thinking/SKILL.md",
        "init.sh"
    ]
    
    os.makedirs(f"{AGENT_DIR}/mcp/servers", exist_ok=True)
    os.makedirs(f"{AGENT_DIR}/skills/dialectic-thinking", exist_ok=True)
    os.makedirs(f"{AGENT_DIR}/data", exist_ok=True)
    
    fetched = []
    for remote_path in files_to_fetch:
        r = requests.get(f"https://api.github.com/repos/{REPO}/contents/{remote_path}", headers=headers)
        if r.status_code == 200:
            content = base64.b64decode(r.json()["content"]).decode()
            local_path = f"{AGENT_DIR}/{remote_path}"
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            Path(local_path).write_text(content)
            fetched.append(remote_path)
    
    # S03: Install deps and verify
    os.system(f"pip install -q --break-system-packages -r {AGENT_DIR}/mcp/servers/requirements.txt 2>/dev/null")
    
    # Set persistence paths
    os.environ["MEMORY_FILE_PATH"] = f"{AGENT_DIR}/data/memory.jsonl"
    os.environ["TODO_FILE_PATH"] = f"{AGENT_DIR}/data/todos.json"
    Path(os.environ["MEMORY_FILE_PATH"]).touch()
    Path(os.environ["TODO_FILE_PATH"]).write_text("[]") if not Path(os.environ["TODO_FILE_PATH"]).exists() else None
    
    # Verify MCP loads
    import sys
    sys.path.insert(0, f"{AGENT_DIR}/mcp/servers")
    import cloud_agent_mcp as cam
    tool_count = len(list(cam.mcp._tool_manager._tools.keys()))
    
    # S04: Create sentinel
    timestamp = datetime.now(timezone.utc).isoformat()
    Path(SENTINEL).write_text(timestamp)
    
    return {
        "status": "initialized",
        "started_at": timestamp,
        "agent_dir": AGENT_DIR,
        "files_fetched": len(fetched),
        "mcp_tools": tool_count,
        "memory_path": os.environ["MEMORY_FILE_PATH"],
        "todo_path": os.environ["TODO_FILE_PATH"],
        "sc_met": tool_count == 25
    }

result = bootstrap()
print(json.dumps(result, indent=2))
```

### 1.3 Success Criteria (BINARY-MEASURABLE)

| ID | Criterion | Verification | Evidence |
|----|-----------|--------------|----------|
| SC1 | Sentinel exists after bootstrap | `os.path.exists(SENTINEL)` | File path |
| SC2 | 25 MCP tools registered | `tool_count == 25` | Integer count |
| SC3 | Persistence paths set | `MEMORY_FILE_PATH` in env | Env var value |
| SC4 | Bootstrap completes <30s | `time.time() - start < 30` | Duration |

### 1.4 Failure Criteria (BINARY-MEASURABLE)

| ID | Criterion | Detection | Recovery |
|----|-----------|-----------|----------|
| FC1 | GitHub API unreachable | `status_code != 200` | Retry 3x, then alert user |
| FC2 | MCP import fails | `ImportError` caught | Report missing deps |
| FC3 | Tool count != 25 | `tool_count != 25` | Report partial load |

### 1.5 Startup Confirmation (VERBATIM-OUTPUT-REQUIRED)

```markdown
## ✅ AGENT STARTUP COMPLETE

| Field | Value |
|-------|-------|
| Status | {status} |
| Timestamp | {started_at} |
| Agent Directory | {agent_dir} |
| MCP Tools | {mcp_tools}/25 |
| Memory Path | {memory_path} |
| Todo Path | {todo_path} |

### Compliance Check
| SC | Status | Evidence |
|----|--------|----------|
| SC1 Sentinel | {✅|❌} | `{SENTINEL}` exists |
| SC2 Tools | {✅|❌} | {tool_count}/25 |
| SC3 Persistence | {✅|❌} | Paths configured |
| SC4 Duration | {✅|❌} | {duration}s < 30s |

### Available Capabilities
- cloud_agent_mcp: filesystem, memory, thinking, todo (25 tools)
- dialectic-thinking: Multi-agent deliberation protocol
- Tailscale nodes: cabin-pc, office-pc, eg-workstation

Proceeding to user task.
```

---

## §2 POST-STARTUP BACKGROUND TASKS (is_background=true)

After startup confirmation, spawn background subagent:

```yaml
background_tasks:
  - id: EVAL-SKILLS
    trigger: First startup only
    action: |
      Evaluate /mnt/skills/user/* and /mnt/skills/public/*
      Compare to agent-startup/skills/
      Identify consolidation opportunities
    output: skills_evaluation.md in memory
    
  - id: SYNC-MEMORY
    trigger: Every 5 iterations OR 5 minutes
    action: |
      Create memory snapshot of session
      Store key decisions, learnings, context
    output: memory.jsonl append
    
  - id: STORE-HISTORY
    trigger: On session end OR user request
    action: |
      Export conversation summary to memory
      Include: problem, decisions, outcomes, learnings
    output: memory entity with session metadata
```

---

## §3 RE-ENTRY PREVENTION

```yaml
re_entry_guard:
  sentinel_path: "/home/claude/.agent_started"
  
  check_sequence:
    1. Read sentinel file
    2. If exists: return "already_initialized"
    3. If not: proceed with bootstrap
    
  critical_rules:
    - NEVER delete sentinel within session
    - NEVER re-run bootstrap if sentinel exists
    - Sentinel auto-clears on new session (ephemeral /home/claude)
```

---

## §4 INTEGRATION WITH AGENT-INSTRUCTIONS.md

This startup sequence precedes AGENT-INSTRUCTIONS.md §0:

```
EXECUTION ORDER:
1. CLAUDE-WEB-STARTUP.md §1 (this document) - Bootstrap environment
2. AGENT-INSTRUCTIONS.md §0 - Workflow startup sequence
3. User task processing
```

The bootstrap provides:
- MCP tools for AGENT-INSTRUCTIONS workflow
- Persistence for memory snapshots
- Skills for dialectic-thinking reviews

---

*Version 1.0.0 | Claude Web Specific | Declarative | Binary SC/FC*
