# Web Agent Setup

Complete setup instructions for Claude Web/Cloud agents to connect to the infrastructure.

## Quick Start

```bash
# 1. Clone startup files
git clone https://github.com/jujo1/agent-startup.git

# 2. Connect to MCP Gateway
# Use Tailscale Funnel URL: https://cabin-pc.tail1a496.ts.net/sse
```

## Step 1: Clone Startup Repository

### Option A: Download ZIP
```bash
curl -L https://github.com/jujo1/agent-startup/archive/main.zip -o agent-startup.zip
unzip agent-startup.zip
```

### Option B: Git Clone
```bash
git clone https://github.com/jujo1/agent-startup.git
cd agent-startup
```

### Option C: Direct File Access
Add these URLs to Claude project knowledge:
- Entry Point: `https://raw.githubusercontent.com/jujo1/agent-startup/main/instructions/CLAUDE.md`
- Workflow: `https://raw.githubusercontent.com/jujo1/agent-startup/main/instructions/WORKFLOW.md`
- Schemas: `https://raw.githubusercontent.com/jujo1/agent-startup/main/instructions/SCHEMAS.md`

---

## Step 2: Establish Funnel Connection to cabin-pc

### Tailscale Funnel Endpoint

The MCP Gateway is exposed via Tailscale Funnel:

| Property | Value |
|----------|-------|
| **Funnel URL** | `https://cabin-pc.tail1a496.ts.net` |
| **SSE Endpoint** | `https://cabin-pc.tail1a496.ts.net/sse` |
| **Health Check** | `https://cabin-pc.tail1a496.ts.net/health` |
| **Internal IP** | `100.121.56.65` |
| **Port** | `3000` (internal), `443` (funnel) |

### Verify Connection

```bash
# Health check
curl https://cabin-pc.tail1a496.ts.net/health

# Expected response:
# {"status": "ok", "node": "cabin-pc", "timestamp": "..."}
```

### Connection Parameters

For Claude Web MCP configuration:

```json
{
  "name": "cabin-mcp",
  "url": "https://cabin-pc.tail1a496.ts.net/sse",
  "transport": "sse"
}
```

---

## Step 3: Connect MCP Gateway

### MCP Gateway Configuration

Add to Claude's MCP servers (Settings → Integrations → MCP):

| Field | Value |
|-------|-------|
| **Name** | `MPC-Gateway` or `cabin_mcp` |
| **URL** | `https://cabin-pc.tail1a496.ts.net/sse` |
| **Transport** | SSE |

### Available Tools via Gateway

Once connected, these tools become available:

| Tool | Description |
|------|-------------|
| `ping` | Test connectivity |
| `get_status` | Gateway status with platform info |
| `list_nodes` | List all Tailscale nodes |
| `node_status` | Check specific node connectivity |
| `remote_exec` | Execute commands on remote nodes |
| `remote_mcp` | Proxy MCP calls to remote nodes |
| `remote_file_read` | Read files from remote nodes |
| `remote_file_write` | Write files to remote nodes |
| `read_file` | Read local file on cabin-pc |
| `list_directory` | List directory on cabin-pc |
| `grep` | Search file contents |
| `glob_files` | Find files by pattern |

### Verify MCP Connection

After adding the MCP server, test with:

```
Use MPC-Gateway:ping to test connectivity
```

Expected response:
```json
{
  "status": "pong",
  "host": "cabin-pc",
  "timestamp": "2026-01-04T07:30:00Z"
}
```

---

## Step 4: Network Topology

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLAUDE WEB/CLOUD                          │
│                                                                   │
│  ┌─────────────┐                                                 │
│  │ Claude Web  │                                                 │
│  │   Agent     │                                                 │
│  └──────┬──────┘                                                 │
│         │                                                        │
│         │ SSE Connection                                         │
│         ▼                                                        │
│  ┌─────────────────────────────────────────┐                    │
│  │ https://cabin-pc.tail1a496.ts.net/sse   │  Tailscale Funnel  │
│  └──────────────────┬──────────────────────┘                    │
└─────────────────────┼────────────────────────────────────────────┘
                      │
                      │ Funnel (443)
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│                      TAILSCALE NETWORK                           │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │                      cabin-pc (MASTER)                      │ │
│  │                      100.121.56.65                          │ │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │ │
│  │  │ MCP Gateway │  │   Milvus    │  │   Qdrant    │         │ │
│  │  │  :3000      │  │   :19530    │  │   :6333     │         │ │
│  │  └──────┬──────┘  └─────────────┘  └─────────────┘         │ │
│  │         │                                                    │ │
│  │         │ Proxy                                              │ │
│  │         ▼                                                    │ │
│  │  ┌─────────────────────────────────────────────────────┐   │ │
│  │  │                  MCP Servers                         │   │ │
│  │  │  memory, todo, sequential-thinking, git, github     │   │ │
│  │  │  scheduler, openai-chat, credentials, claude-context │   │ │
│  │  └─────────────────────────────────────────────────────┘   │ │
│  └────────────────────────────────────────────────────────────┘ │
│                              │                                   │
│                              │ Tailscale Mesh                    │
│                              ▼                                   │
│  ┌──────────────────┐  ┌──────────────────┐                     │
│  │    office-pc     │  │   homeassistant  │                     │
│  │  100.84.172.79   │  │  100.116.245.37  │                     │
│  │   40 agents      │  │    8 agents      │                     │
│  └──────────────────┘  └──────────────────┘                     │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 5: Verify Full Setup

### Checklist

```
[ ] 1. Cloned agent-startup repository
[ ] 2. Added MCP Gateway to Claude (cabin_mcp or MPC-Gateway)
[ ] 3. Verified ping response
[ ] 4. Read instructions/CLAUDE.md as entry point
```

### Test Commands

```bash
# 1. Test gateway
Use MPC-Gateway:ping

# 2. Get status
Use MPC-Gateway:get_status

# 3. List available nodes
Use MPC-Gateway:list_nodes

# 4. Check node status
Use MPC-Gateway:node_status with node="cabin-pc"
```

### Expected Outputs

**ping:**
```json
{"status": "pong", "host": "cabin-pc", "timestamp": "..."}
```

**get_status:**
```json
{
  "platform": "Windows",
  "python": "3.13.7",
  "nodes": ["cabin-pc", "office-pc", "homeassistant"]
}
```

**list_nodes:**
```json
{
  "nodes": [
    {"name": "cabin-pc", "ip": "100.121.56.65", "port": 3000, "status": "active"},
    {"name": "office-pc", "ip": "100.84.172.79", "port": 3000, "status": "active"},
    {"name": "homeassistant", "ip": "100.116.245.37", "port": 3000, "status": "active"}
  ]
}
```

---

## Troubleshooting

### Connection Failed

1. Check funnel is running:
```bash
# On cabin-pc
tailscale funnel status
```

2. Verify URL is correct:
```
https://cabin-pc.tail1a496.ts.net/sse
```

3. Check firewall allows port 3000 internally

### MCP Not Responding

1. Verify MCP gateway container is running:
```bash
docker ps | grep mcp-gateway
```

2. Check logs:
```bash
docker logs mcp-gateway
```

### Authentication Issues

The funnel endpoint is public but tools may require tokens. Check:
- OAuth token in credentials store
- MCP gateway token configuration

---

## OAuth Tokens (Reference)

| Token | Purpose |
|-------|---------|
| `D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k` | claude_web |
| `BrdjN6ALPRbNRhcfOs1C-dRMeq4EbMLJsDAL3A9UN8M` | claude_code |
| `65QE33Np7dsER73IUc2kZevfZv1WZvNc-q1-Z5pvHms` | backup |

---

## Next Steps

After connection is established:

1. **Read Entry Point**: `instructions/CLAUDE.md`
2. **Run Startup**: `python scripts/startup.py`
3. **Begin Workflow**: PLAN → REVIEW → DISRUPT → IMPLEMENT → TEST → VALIDATE → LEARN

---

## Version

- Version: 4.0.0
- Updated: 2026-01-04
- Gateway: cabin-pc.tail1a496.ts.net
