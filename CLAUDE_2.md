# CLAUDE_2.md

**Keywords:** infrastructure, MCP, network, credentials, memory, docker, tailscale, nodes, capacity  
**Created:** 2026-01-03T02:30:00Z  
**Modified:** 2026-01-04T06:00:00Z  
**References:** `AGENTS_2.md`, `~/.credentials/`, `~/.claude/settings.json`

---

## Summary

| Item | Value |
|------|-------|
| Master Node | cabin-pc (100.121.56.65) |
| Total Capacity | 73 agents |
| Active Nodes | 3 |
| MCP Gateway | https://cabin-pc.tail1a496.ts.net |
| Vector DBs | Milvus (19530), Qdrant (6333) |
| Relational | PostgreSQL (5432, 5433) |
| Cache | Redis (6379) |

---

## Index

1. [System Identity](#1-system-identity)
2. [Network](#2-network)
3. [Docker](#3-docker)
4. [Memory](#4-memory)
5. [Credentials](#5-credentials)
6. [M-Rules](#6-m-rules)
7. [Enforcement](#7-enforcement)
8. [Paths](#8-paths)

---

## 1. System Identity

**This is CABIN-PC (100.121.56.65) - MASTER ORCHESTRATOR**

| Property | Value |
|----------|-------|
| Hostname | CABIN-PC |
| Tailscale IP | 100.121.56.65 |
| Role | Master Node |
| MCP Gateway | https://cabin-pc.tail1a496.ts.net (port 8081) |
| Agent Capacity | 25 concurrent |
| OS | Windows 11 |
| Shell | `pwsh.exe` |
| Python | 3.13.7 / `venv_313` |

---

## 2. Network

### 2.1 Topology

```
cabin-pc (MASTER) â”€â”€â”€ MCP Gateway â”€â”€â”€â”¬â”€â”€â”€ office-pc (40 agents)
     â”‚                               â””â”€â”€â”€ homeassistant (8 agents)
     â”‚
     â””â”€â”€â”€ DBs: Milvus (19530), Qdrant (6333)
          office-pc: PostgreSQL (5432, 5433), Redis (6379)
```

### 2.2 Nodes

| Node | IP | Capacity | Status | User | Password |
|------|-----|----------|--------|------|----------|
| cabin-pc | 100.121.56.65 | 25 | âœ… Active | julia | Th0mas@13 |
| office-pc | 100.84.172.79 | 40 | âœ… Active | julia | Th0mas@13 |
| homeassistant | 100.116.245.37 | 8 | âœ… Active | jjones | Th0mas13 |
| eg-workstation | 100.78.245.37 | 0 | âŒ Disabled | jjones | mK7tB0%iACxwDa3n |
| boca-spm-dev1 | 100.67.169.120 | 0 | âŒ Disabled | jjones | mK7tB0%iACxwDa3n |
| boca-spm-dev2 | 100.92.235.102 | 0 | âŒ Disabled | jjones | mK7tB0%iACxwDa3n |

### 2.3 Load Balancing

| Node | % Allocation |
|------|--------------|
| office-pc | 54.8% (40/73) |
| cabin-pc | 34.2% (25/73) |
| homeassistant | 11.0% (8/73) |

### 2.4 Tailscale Serve (cabin-pc)

| Service | Endpoint |
|---------|----------|
| claude-flow | https://cabin-pc.tail1a496.ts.net/ |
| MCP Gateway | https://cabin-pc.tail1a496.ts.net/mcp |
| SSH | tcp://cabin-pc.tail1a496.ts.net:22 |
| PostgreSQL | tcp://cabin-pc.tail1a496.ts.net:5432 |

---

## 3. Docker

### 3.1 Containers

| Container | Node | Port | Purpose |
|-----------|------|------|---------|
| milvus-standalone | cabin-pc | 19530 | Vector embeddings |
| qdrant | cabin-pc | 6333 | Vector search |
| mcp-gateway | cabin-pc | 8081 | MCP routing |
| postgres-claude | office-pc | 5432 | General storage |
| postgres-credentials | office-pc | 5433 | Encrypted creds |
| redis | office-pc | 6379 | Cache, queues |

### 3.2 Load Balancing

| Container | Primary | Failover | Failover Trigger |
|-----------|---------|----------|------------------|
| milvus-standalone | cabin-pc | office-pc | 3 failures (60s) |
| qdrant | cabin-pc | office-pc | 3 failures (60s) |
| mcp-gateway | cabin-pc | office-pc | 3 failures (60s) |
| postgres-claude | office-pc | cabin-pc | 3 failures (60s) |
| postgres-credentials | office-pc | cabin-pc | 3 failures (60s) |
| redis | office-pc | cabin-pc | 3 failures (60s) |

### 3.3 Health Check

```bash
ssh {node} "docker ps --filter name={container} --format '{{.Status}}'"
```

### 3.4 Routing

| Operation | Primary Node |
|-----------|--------------|
| Vector write | cabin-pc |
| Vector read | cabin-pc |
| Relational write | office-pc |
| Relational read | office-pc |
| Cache | office-pc |

---

## 4. Memory

### 4.1 Systems

| Type | Location | MCP Server |
|------|----------|------------|
| MCP Memory | `~/.caches/memory/memory.json` | `memory` |
| Shared Memory | `~/.claude/shared-memory/` | `memory-bank` |
| Episodic Memory | `~/.config/superpowers/conversation-archive/` | `episodic-memory` |

### 4.2 Workflow

1. **Startup** â†’ Query shared-memory + todo
2. **Before questions** â†’ Search episodic-memory
3. **After task** â†’ Store to memory-bank
4. **Infrastructure changes** â†’ Update both systems

---

## 5. Credentials

### 5.1 Locations

| Source | Path |
|--------|------|
| Primary | `~/.credentials/credentials.json` |
| MCP Tokens | `~/.credentials/mcp_tokens.json` |
| MCP Configs | `~/.claude/settings.json` |

### 5.2 MCP Gateway Tokens

| Client | Token |
|--------|-------|
| Claude Web | `D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k` |
| Claude Code | `BrdjN6ALPRbNRhcfOs1C-dRMeq4EbMLJsDAL3A9UN8M` |
| Backup | `65QE33Np7dsER73IUc2kZevfZv1WZvNc-q1-Z5pvHms` |

---

## 6. M-Rules

| # | Rule | Description |
|---|------|-------------|
| M1 | Semantic first | Min cmds, semantic indexes before Read/Grep |
| M2 | Verify before done | Execute and check logs |
| M3 | No fabrication | Never claim without execution |
| M4 | Workflow chain | Follow 8-stage workflow |
| M5 | Learn terminal | Every workflow ends with Learn |
| M6 | Agent vetting | Review/Morality verifies all |
| M7 | No self-review | Third-party reviews all |
| M8 | Auto-transition | Delegate next stage |
| M9 | No placeholders | No TODO/pass/... |
| M10 | No assumptions | Reality test all |
| M11 | Parallel required | 3+ steps â†’ parallel |
| M12 | Observer always | Complex needs Observer |
| M13 | Complete code | No partial impl |
| M14 | Reality testing | Execute, check errors |
| M15 | Memory creation | Store discoveries |
| M16 | Exception propagation | NO fallbacks |
| M17 | Validation logging | Console + file |
| M18 | Code requires TEST | All code tested |
| M19 | Workflow compliance | Strict rules |
| M20 | Restart with context | Preserve across restarts |
| M21 | Tool proof | Evidence for tool claims |
| M22 | #claude-code only | Designated channels |
| M23 | Factual verification | Research before claim |
| M24 | Comprehensive research | Web/GitHub/codebase |
| M25 | Git worktree | Use worktrees |
| M26 | Recursive debug | Debug protocol |
| M27 | Auto-store credentials | Store to credentials.json |
| M28 | Pre-question history | Search before asking |
| M29 | No deletion fixes | Diagnose, never delete |
| M30 | Autonomous execution | Run directly |
| M31 | GitHub private | `gh repo create --private` |
| M32 | Full paths | Always absolute |
| M33 | Auto-doc infrastructure | Document changes |
| M34 | Auto-store MCP | Store to memory MCP |
| M35 | Memory-first startup | Query before tasks |
| M36 | Credentials-first | Search creds MCP |
| M37 | Gateway todo | Multi-agent uses gateway |
| M38 | Never ask first | Execute, don't ask |
| M39 | Never break working | Preserve systems |
| M40 | Parallel mandate | Parallelize all |
| M41 | Sonnet MCP mandate | Sonnet uses seq-thinking + memory |
| M42 | Opus plan-mode | Opus for planning |
| M43 | Gateway auto-invoke | Auto-invoke Gateway |
| M44 | Auto node allocation | Distribute across nodes |
| M45 | Markdown standard | Title, Created, Modified, References, Index, Body |

---

## 7. Enforcement

### 7.1 Hooks

| Hook | Enforces |
|------|----------|
| `hooks/startup_validator.ps1` | S0-S20 |
| `hooks/evidence_validator.py` | M3 |
| `hooks/stage_gate.py` | M4/M19/M42 |
| `hooks/memory_gate.py` | M35/M40 |
| `hooks/sonnet_mcp_enforcer.py` | M41 |
| `hooks/incremental_memory.py` | M41 |
| `hooks/agent_todo_enforcer.py` | M37 |
| `hooks/markdown_validator.py` | M45 |
| `hooks/mcp_change_guard.py` | MCP backup |
| `scripts/mcp_startup_validator.py` | MCP validation |

### 7.2 Execution Tools

| Op | Tool |
|----|------|
| Read | `mcp_claude-code_Read` |
| Edit | `mcp_claude-code_Edit` |
| Shell | `mcp_claude-code_Bash` |
| Find | `mcp_claude-code_Glob` |
| Search | `mcp_claude-code_Grep` |
| Agent | `mcp_claude-code_Task` |
| Web | `mcp_claude-code_WebFetch` |

---

## 8. Paths

| Category | Path |
|----------|------|
| Settings | `~/.claude/settings.json` |
| Agent Instructions | `~/.claude/AGENTS_2.md` |
| Infrastructure | `~/.claude/CLAUDE_2.md` |
| Credentials | `~/.credentials/credentials.json` |
| MCP Tokens | `~/.credentials/mcp_tokens.json` |
| Shared Memory | `~/.claude/shared-memory/` |
| MCP Funnel Docs | `~/.claude/mcp-funnel/` |
| Distributed Agents | `~/.claude/distributed-agents/` |
| Skills | `~/.claude/skills/` |
| Hooks | `~/.claude/hooks/` |
| Logs | `~/.claude/logs/` |
| Workflow | `~/.claude/.workflow/` |

---

## MCP Gateway

### Endpoint

`https://cabin-pc.tail1a496.ts.net`

### Paths

| Path | Auth | Method | Description |
|------|------|--------|-------------|
| `/health` | No | GET | Status |
| `/tools` | Yes | GET | List tools |
| `/mcp` | Yes | POST | Execute |
| `/sse` | OAuth 2.1 | SSE | Claude Web |

### Tools

`ping`, `get_status`, `list_nodes`, `node_status`, `remote_exec`, `remote_mcp`, `remote_file_read`, `remote_file_write`, `read_file`, `list_directory`, `grep`, `glob`

---

## Todo MCP

### Tools

| Tool | Purpose |
|------|---------|
| `todo_create` | Create (with `parent_id`) |
| `todo_list` | List (filter by status/category/node) |
| `todo_get` | Get by ID |
| `todo_update` | Update fields |
| `todo_complete` | Mark complete with evidence |
| `todo_assign` | Assign to agent |
| `todo_get_tree` | Hierarchical tree |
| `todo_get_by_agent` | Agent's todos |
| `todo_sync` | Force reload |

### Agent Workflow

1. Startup â†’ `todo_sync`
2. Check â†’ `todo_get_by_agent`
3. Start â†’ `todo_assign` or `todo_update`
4. Complete â†’ `todo_complete` with evidence
5. Subtasks â†’ `todo_create` with `parent_id`

---

## Morality

```
NEVER fabricate.
NEVER hide errors.
NEVER use placeholders.
NEVER skip code.
NEVER duplicate.
NEVER claim success without evidence (running code + log tails).
ALWAYS verbatim output.
ALWAYS verify before done.
ALWAYS satisfy FULL request.
```
