# Web Agent Connection Guide - 3 Required Steps

**For**: Claude.ai Web & Mobile  
**Purpose**: Connect to cabin-pc infrastructure and access AGENTS 4.0  
**Time**: 5 minutes

---

## ✅ The 3 Required Steps

Every web agent MUST complete these steps before using AGENTS 4.0:

1. **Clone Startup** - Access the agent-startup repository
2. **Establish Funnel Connection** - Connect to cabin-pc via Tailscale/MCP-Gateway
3. **Connect MCP-Gateway MCP** - Enable the MPC-Gateway MCP server

---

## 📋 Step 1: Clone Startup

### What This Means
Web agents cannot use `git clone` directly. Instead, you reference the GitHub repository and have Claude read the documentation.

### How to Do It

**Say to Claude**:
```
I need to access the AGENTS 4.0 system. Please reference the agent-startup repository:

Repository: https://github.com/jujo1/agent-startup

Key files to understand:
1. AGENTS_3.md - Complete workflow specification
2. CLAUDE_2.md - Infrastructure details
3. WEB_AGENTS_SETUP.md - Web agent setup guide
4. FIRST_CONVERSATION_TEMPLATE.md - Connection template

Please confirm you can access this repository.
```

### Expected Response
```
✅ I can access the agent-startup repository on GitHub.

Key files identified:
- AGENTS_3.md (37KB) - Workflow specification
- CLAUDE_2.md (9.9KB) - Infrastructure
- WEB_AGENTS_SETUP.md - Web setup guide
- FIRST_CONVERSATION_TEMPLATE.md - Connection template

Ready to proceed to connection setup.
```

### Verification
- [ ] Claude confirms repository access
- [ ] Claude lists key files
- [ ] Ready to proceed to Step 2

---

## 🔗 Step 2: Establish Funnel Connection to cabin-pc

### What This Means
Create a secure tunnel from Claude.ai → cabin-pc via Tailscale network using the MPC-Gateway endpoint.

### Connection Details

**Gateway Information**:
```yaml
Gateway URL:    https://cabin-pc.tail1a496.ts.net
MCP Endpoint:   https://cabin-pc.tail1a496.ts.net/sse
Protocol:       SSE (Server-Sent Events)
Auth Type:      Bearer Token
Auth Token:     D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k
Network:        Tailscale (tail1a496.ts.net)
Node:           cabin-pc
Node IP:        100.121.56.65
```

### How to Do It

**Say to Claude**:
```
Please establish a funnel connection to my cabin-pc infrastructure:

TAILSCALE FUNNEL CONNECTION:
- Gateway URL: https://cabin-pc.tail1a496.ts.net
- MCP Endpoint: https://cabin-pc.tail1a496.ts.net/sse
- Auth Token: D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k
- Network: Tailscale (tail1a496.ts.net)
- Target Node: cabin-pc (100.121.56.65)

This connection will allow you to:
1. Access files on cabin-pc
2. Execute remote commands
3. Call MCP servers running on cabin-pc
4. Access other nodes via cabin-pc (office-pc, homeassistant)

Please confirm the funnel connection is ready.
```

### Expected Response
```
✅ Funnel connection to cabin-pc established.

Connection verified:
- Gateway URL: https://cabin-pc.tail1a496.ts.net ✓
- Network: Tailscale (tail1a496.ts.net) ✓
- Authentication: Bearer token configured ✓
- Target node: cabin-pc (100.121.56.65) ✓

The secure tunnel is active and ready for MCP-Gateway access.
```

### Verification
- [ ] Claude confirms funnel connection
- [ ] Gateway URL accessible
- [ ] Auth token configured
- [ ] Ready to proceed to Step 3

---

## 🔌 Step 3: Connect MPC-Gateway MCP

### What This Means
Activate the MPC-Gateway MCP server in Claude.ai to enable tools for remote access.

### Available MPC-Gateway Tools

Once connected, these tools become available:

| Tool | Purpose |
|------|---------|
| `ping` | Test connection to gateway |
| `get_status` | Get gateway and node status |
| `list_nodes` | List all Tailscale nodes |
| `node_status` | Check specific node status |
| `read_file` | Read files from cabin-pc |
| `list_directory` | List directory contents |
| `grep` | Search file contents |
| `glob_files` | Find files by pattern |
| `remote_exec` | Execute commands on cabin-pc |
| `remote_file_read` | Read files from remote nodes |
| `remote_file_write` | Write files to remote nodes |
| `remote_mcp` | Call MCP servers on remote nodes |

### How to Do It

**Say to Claude**:
```
Please connect to the MPC-Gateway MCP server using the funnel connection.

MCP Server: MPC-Gateway
Endpoint: https://cabin-pc.tail1a496.ts.net/sse
Auth: Bearer D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k

After connecting, please test the connection by:
1. Using the 'ping' tool to verify connectivity
2. Using 'get_status' to check gateway status
3. Using 'list_nodes' to show available nodes
4. Using 'read_file' to read ~/.claude/AGENTS_3.md from cabin-pc

Confirm all tests pass.
```

### Expected Response
```
✅ MPC-Gateway MCP server connected successfully.

Connection Test Results:
1. ✅ ping → "pong" (response time: 45ms)
2. ✅ get_status → Gateway online, 3 nodes available
3. ✅ list_nodes → cabin-pc, office-pc, homeassistant
4. ✅ read_file → AGENTS_3.md loaded (37KB)

MPC-Gateway Tools Available:
- ping, get_status, list_nodes ✓
- read_file, list_directory, grep ✓
- remote_exec, remote_mcp ✓

All systems operational. Ready for workflow execution.
```

### Verification
- [ ] MPC-Gateway MCP connected
- [ ] ping tool works
- [ ] get_status shows nodes online
- [ ] list_nodes shows all 3 nodes
- [ ] read_file can access cabin-pc files
- [ ] All 12 tools available
- [ ] AGENTS_3.md successfully loaded

---

## 🎯 Complete Setup Verification

Once all 3 steps are complete, verify with this checklist:

### Final Verification Checklist

```
STEP 1: CLONE STARTUP
- [ ] Repository URL confirmed: https://github.com/jujo1/agent-startup
- [ ] Key files identified (AGENTS_3.md, CLAUDE_2.md, etc.)
- [ ] Claude acknowledges access to documentation

STEP 2: ESTABLISH FUNNEL CONNECTION
- [ ] Gateway URL: https://cabin-pc.tail1a496.ts.net
- [ ] Tailscale network: tail1a496.ts.net
- [ ] Auth token configured
- [ ] Connection to cabin-pc (100.121.56.65) verified
- [ ] Funnel tunnel active

STEP 3: CONNECT MPC-GATEWAY MCP
- [ ] MPC-Gateway MCP server connected
- [ ] Endpoint: https://cabin-pc.tail1a496.ts.net/sse
- [ ] All 12 tools available (ping, get_status, read_file, etc.)
- [ ] Test ping successful
- [ ] Can read files from cabin-pc
- [ ] Can execute remote commands
- [ ] Can call remote MCP servers

READY FOR WORKFLOWS
- [ ] All 3 steps completed
- [ ] All verifications passed
- [ ] AGENTS_3.md loaded and understood
- [ ] Workflow directory accessible
- [ ] MCP servers accessible
```

---

## 🚀 Quick Start Template

**Copy this entire message into Claude.ai**:

```
Hi Claude! I need to set up AGENTS 4.0 with the 3 required steps:

STEP 1: CLONE STARTUP
Repository: https://github.com/jujo1/agent-startup
Please confirm you can access and identify these key files:
- AGENTS_3.md (workflow specification)
- CLAUDE_2.md (infrastructure)
- WEB_AGENTS_SETUP.md (setup guide)

STEP 2: ESTABLISH FUNNEL CONNECTION TO CABIN-PC
Please establish a funnel connection with these details:
- Gateway URL: https://cabin-pc.tail1a496.ts.net
- MCP Endpoint: https://cabin-pc.tail1a496.ts.net/sse
- Auth Token: D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k
- Network: Tailscale (tail1a496.ts.net)
- Target: cabin-pc (100.121.56.65)

STEP 3: CONNECT MPC-GATEWAY MCP
Please connect to MPC-Gateway MCP server and test:
1. Use ping tool
2. Use get_status tool
3. Use list_nodes tool
4. Use read_file to read ~/.claude/AGENTS_3.md

After completing all 3 steps, please confirm:
"✅ All 3 steps complete. MPC-Gateway connected to cabin-pc. AGENTS 4.0 ready for workflows."
```

---

## 🔍 Troubleshooting

### Step 1 Issues: Cannot Access Repository

**Problem**: Claude says it cannot access GitHub  
**Solution**: Claude.ai can view public GitHub repos. Verify URL is correct and repository is public.

```
Try: "Please visit https://github.com/jujo1/agent-startup and confirm it's accessible"
```

### Step 2 Issues: Funnel Connection Failed

**Problem**: Cannot establish funnel connection  
**Solution**: 
1. Verify cabin-pc is online (check Tailscale admin panel)
2. Verify gateway URL: https://cabin-pc.tail1a496.ts.net
3. Check if Tailscale funnel is active on cabin-pc
4. Verify auth token is correct

```
Try: "Please test the gateway URL accessibility first, then configure auth"
```

### Step 3 Issues: MPC-Gateway MCP Not Connecting

**Problem**: MCP server connection fails  
**Solution**:
1. Verify funnel connection is established (Step 2 must be complete)
2. Check if MPC-Gateway MCP server is in your Claude.ai connected apps
3. Verify endpoint URL includes /sse: https://cabin-pc.tail1a496.ts.net/sse
4. Check auth token format (Bearer token)

```
Try: "Please list available MCP servers and confirm MPC-Gateway is present"
```

### Step 3 Issues: Tools Not Available

**Problem**: MPC-Gateway connected but tools don't work  
**Solution**:
1. Test ping first (simplest tool)
2. Check if cabin-pc MCP gateway is running
3. Verify firewall allows port 8081
4. Check logs on cabin-pc: ~/.claude/logs/mcp-gateway.log

```
Try: "Use ping tool first. If that fails, cabin-pc gateway may be down."
```

---

## 📞 Getting Help

If any step fails:

1. **Check Prerequisites**:
   - Is cabin-pc powered on?
   - Is Tailscale connected?
   - Is MPC-Gateway process running?

2. **Verify Each Step**:
   - Complete Step 1 before Step 2
   - Complete Step 2 before Step 3
   - Don't skip verification checkboxes

3. **Test Components**:
   - Test funnel URL in browser: https://cabin-pc.tail1a496.ts.net
   - Should show "MPC-Gateway" or health status
   - If timeout, cabin-pc is unreachable

4. **Review Logs**:
   - cabin-pc: `~/.claude/logs/mcp-gateway.log`
   - Tailscale: Tailscale admin panel logs
   - Claude.ai: Check MCP connection status

---

## ✅ Success Criteria

Setup is complete when:

1. ✅ **Step 1**: Repository access confirmed
2. ✅ **Step 2**: Funnel connection established
3. ✅ **Step 3**: MPC-Gateway MCP connected and all tools working
4. ✅ **Verification**: Can read AGENTS_3.md from cabin-pc
5. ✅ **Ready**: Claude confirms "ready for workflows"

---

## 🎓 What Happens Next

After completing these 3 steps, you can:

1. **Execute Workflows**: Ask Claude to run AGENTS 4.0 workflows
2. **Access Files**: Read/write files on cabin-pc remotely
3. **Run Commands**: Execute scripts on cabin-pc
4. **Call MCP Servers**: Use workflow-validator, todo, memory, etc.
5. **Multi-Node Access**: SSH to office-pc, homeassistant via cabin-pc

**Example First Workflow**:
```
Create a simple Python calculator following AGENTS 4.0 workflow.
Execute all 12 stages (STARTUP → LEARN) on cabin-pc via MPC-Gateway.
```

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-04T09:45:00Z  
**Required For**: All web agents (Claude.ai, Claude mobile)  
**Status**: Production-Ready

---

## 📚 Related Documentation

- **Full Guide**: WEB_AGENTS_SETUP.md
- **Template**: FIRST_CONVERSATION_TEMPLATE.md
- **Quick Ref**: README_WEB_AGENTS.md
- **Workflow Spec**: AGENTS_3.md
- **Infrastructure**: CLAUDE_2.md
