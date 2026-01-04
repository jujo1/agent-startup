# Web Agents Setup Guide - AGENTS 4.0

**For**: Claude.ai Web, Claude Mobile App  
**Purpose**: Connect to cabin-pc infrastructure via MCP Gateway  
**Last Updated**: 2026-01-04T09:00:00Z

---

## 🌐 Overview

Web agents (Claude.ai, Claude mobile) cannot directly access local filesystems or SSH. Instead, they connect to your infrastructure through **MCP Gateway** running on cabin-pc.

**Architecture**:
```
Claude Web → MCP Gateway (cabin-pc) → Local Resources
             ↓
             - File system access
             - MCP servers (workflow-validator, todo, etc.)
             - SSH to other nodes
             - Memory systems
```

---

## ⚡ Quick Start (3 Steps)

### 📌 The 3 Required Steps for All Web Agents

**Every web agent must complete these steps in order**:

#### Step 1: Clone Startup
**What**: Access agent-startup repository  
**How**: Reference https://github.com/jujo1/agent-startup  
**Verify**: Claude confirms access to AGENTS_3.md, CLAUDE_2.md

#### Step 2: Establish Funnel Connection to cabin-pc
**What**: Create secure tunnel via Tailscale  
**How**: Use gateway https://cabin-pc.tail1a496.ts.net  
**Verify**: Funnel connection to cabin-pc (100.121.56.65) active

#### Step 3: Connect MPC-Gateway MCP
**What**: Enable MPC-Gateway MCP server  
**How**: Connect to endpoint /sse with auth token  
**Verify**: Tools available (ping, get_status, read_file)

**Detailed Guide**: See [WEB_AGENT_3_STEPS.md](WEB_AGENT_3_STEPS.md) for step-by-step instructions.

---

### Step 1: Clone Startup Repository

In Claude.ai chat, say:

```
Please help me set up AGENTS 4.0:

1. Clone the agent-startup repository from GitHub:
   https://github.com/jujo1/agent-startup.git

2. Review the files and prepare for MCP Gateway connection.
```

Claude will acknowledge the repository exists but cannot clone directly. Continue to Step 2.

---

### Step 2: Establish Funnel Connection to cabin-pc

**Required Information**:
- **Gateway URL**: `https://cabin-pc.tail1a496.ts.net`
- **MCP Endpoint**: `https://cabin-pc.tail1a496.ts.net/sse`
- **Auth Token**: `D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k`

Tell Claude:

```
I need to connect to my cabin-pc infrastructure via MCP Gateway.

Connection details:
- Gateway URL: https://cabin-pc.tail1a496.ts.net
- MCP Endpoint: https://cabin-pc.tail1a496.ts.net/sse
- Auth Type: Bearer token
- Token: D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k

Please test the connection using the MPC-Gateway MCP server.
```

---

### Step 3: Connect MCP-Gateway MCP

Claude.ai should already have access to the MPC-Gateway MCP server in your connected apps. Verify:

```
Please verify you have access to these MCP-Gateway tools:

1. ping - Test connectivity
2. get_status - Get gateway status
3. list_nodes - List available Tailscale nodes
4. read_file - Read files from cabin-pc
5. remote_exec - Execute commands on remote nodes
6. remote_mcp - Call MCP tools on remote nodes

Test each tool to confirm connectivity.
```

---

## 🔧 Detailed Setup Instructions

### A. Understanding MCP Gateway

**MPC-Gateway** is an MCP server that acts as a bridge between Claude.ai and your private infrastructure.

**Key Capabilities**:
- **File Access**: Read files from cabin-pc filesystem
- **Command Execution**: Run bash/PowerShell commands remotely
- **MCP Proxy**: Call MCP tools on remote nodes
- **Node Management**: Access office-pc, homeassistant via Tailscale
- **Secure**: Authentication via Bearer token

**Available Nodes**:
```
cabin-pc        100.121.56.65 (master, 25 capacity)
office-pc       100.84.172.79 (worker, 40 capacity)
homeassistant   100.116.245.37 (worker, 8 capacity)
```

---

### B. Testing Gateway Connection

#### Test 1: Ping Gateway

```
Please use the MPC-Gateway ping tool to verify connectivity to cabin-pc.
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-01-04T09:00:00Z",
  "host": "cabin-pc",
  "message": "pong"
}
```

#### Test 2: Get Status

```
Please use MPC-Gateway get_status tool to check gateway information.
```

Expected response:
```json
{
  "platform": "Windows 11",
  "python_version": "3.13.7",
  "nodes_available": ["cabin-pc", "office-pc", "homeassistant"],
  "status": "healthy"
}
```

#### Test 3: List Nodes

```
Please use MPC-Gateway list_nodes to see all Tailscale nodes.
```

Expected response:
```json
{
  "nodes": {
    "cabin-pc": {
      "ip": "100.121.56.65",
      "mcp_port": 8081,
      "status": "online"
    },
    "office-pc": {
      "ip": "100.84.172.79",
      "mcp_port": 8082,
      "status": "online"
    }
  }
}
```

---

### C. Accessing AGENTS 4.0 Files

Once connected, Claude can access files on cabin-pc:

#### Read Core Instructions

```
Please read these files from cabin-pc using MPC-Gateway read_file:

1. ~/.claude/AGENTS_3.md
2. ~/.claude/CLAUDE_2.md
3. ~/.claude/SCHEMAS.md

Then confirm you understand the workflow specification.
```

#### List Directory Contents

```
Please use MPC-Gateway list_directory to show:

1. ~/.claude/agents/
2. ~/.claude/mcp/servers/
3. ~/.workflow/

This will help verify the installation.
```

---

### D. Setting Up Workflow Directory

Web agents need to create workflow directories on cabin-pc:

```
Please use MPC-Gateway remote_exec to run these commands on cabin-pc:

1. Create workflow directory:
   mkdir -p ~/.workflow/$(date +%Y%m%d_%H%M%S)_web_agent/{todo,evidence,logs,plans}

2. Verify creation:
   ls -la ~/.workflow/

3. Set permissions:
   chmod -R 755 ~/.workflow/
```

---

### E. Calling Remote MCP Servers

Web agents can call MCP servers running on cabin-pc:

#### Call workflow-validator

```
Please use MPC-Gateway remote_mcp tool to call workflow-validator:

Node: cabin-pc
Tool: workflow_validator_create
Params: {
  "workflow_id": "web_agent_001",
  "user_request": "Test workflow from web"
}
```

#### Call todo MCP

```
Please use MPC-Gateway remote_mcp to create a todo:

Node: cabin-pc
Tool: mcp_todo_create
Params: {
  "content": "Test todo from web agent",
  "status": "pending",
  "priority": "high",
  "metadata": {
    "objective": "Verify remote MCP works",
    "success_criteria": "Todo created successfully",
    "fail_criteria": "Connection error",
    "evidence_required": "log",
    "evidence_location": "~/.workflow/evidence/web_test.log",
    "agent_model": "Sonnet",
    "workflow": "TEST",
    "blocked_by": [],
    "parallel": false,
    "workflow_stage": "test",
    "instructions_set": "AGENTS_4.md",
    "time_budget": "5m",
    "reviewer": "VALIDATOR"
  }
}
```

---

## 🚀 Complete Web Agent Workflow

Here's a complete workflow for web agents:

### 1. Initial Setup

```markdown
**User**: I want to use AGENTS 4.0 from Claude.ai web. Please help me connect to my cabin-pc infrastructure.

**Connection Details**:
- Gateway: https://cabin-pc.tail1a496.ts.net
- Token: D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k
- Repository: https://github.com/jujo1/agent-startup

**Steps**:
1. Test MPC-Gateway connection (ping, get_status)
2. List available nodes
3. Read AGENTS_3.md from ~/.claude/ on cabin-pc
4. Verify workflow directory exists
5. Confirm ready for workflow execution
```

### 2. Execute Workflow

```markdown
**User**: Create a simple Python calculator following AGENTS 4.0 workflow.

Use cabin-pc for execution via MPC-Gateway.

**Expected**:
1. Claude uses remote_exec to create workflow directory
2. Claude uses remote_mcp to call workflow-validator
3. Claude reads AGENTS_3.md for instructions
4. Claude executes all 12 workflow stages remotely
5. Claude provides evidence from ~/.workflow/ on cabin-pc
```

### 3. Retrieve Results

```markdown
**User**: Show me the evidence from the calculator workflow.

**Claude should**:
1. Use read_file to get evidence logs
2. Use list_directory to show structure
3. Use grep to search for specific evidence
4. Present complete evidence trail
```

---

## 📋 Web Agent Checklist

Before starting workflow, verify:

- [ ] MPC-Gateway ping succeeds
- [ ] get_status shows all nodes online
- [ ] list_nodes shows cabin-pc, office-pc, homeassistant
- [ ] read_file successfully reads ~/.claude/AGENTS_3.md
- [ ] remote_exec can create directories
- [ ] remote_mcp can call workflow-validator
- [ ] Workflow directory exists on cabin-pc
- [ ] Token authentication works

---

## 🔍 Troubleshooting

### Issue: "Cannot connect to MPC-Gateway"

**Solution**:
1. Verify gateway URL: `https://cabin-pc.tail1a496.ts.net`
2. Check token is correct
3. Ensure cabin-pc is online (check Tailscale)
4. Try ping tool first

### Issue: "File not found" when reading AGENTS_3.md

**Solution**:
1. Verify file exists: Use `remote_exec` with `ls ~/.claude/AGENTS_3.md`
2. Check permissions: `remote_exec` with `ls -la ~/.claude/`
3. Try reading other files first to test connection

### Issue: "MCP server not responding"

**Solution**:
1. Check if MCP servers are running on cabin-pc
2. Use `remote_exec` with `ps aux | grep mcp`
3. Restart MCP servers if needed
4. Verify MCP port (8081) is accessible

### Issue: "Token expired or invalid"

**Solution**:
1. Verify token: `D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k`
2. Check if new token needed (ask user)
3. Update token in MCP configuration

---

## 🎯 Web Agent Capabilities

What web agents CAN do via MPC-Gateway:

✅ **File Operations**
- Read files from cabin-pc
- List directories
- Search files (grep, glob)
- Create directories

✅ **Command Execution**
- Run bash commands on cabin-pc
- Execute Python scripts remotely
- Run workflow stages
- Collect evidence

✅ **MCP Integration**
- Call workflow-validator remotely
- Use todo MCP server
- Access memory systems
- Trigger scheduled tasks

✅ **Multi-Node Access**
- SSH to office-pc via cabin-pc
- Access homeassistant
- Coordinate distributed workflows
- Parallel execution across nodes

---

## 🎓 Advanced Usage

### Multi-Node Workflow

```markdown
**User**: Execute parallel tasks across cabin-pc and office-pc.

**Claude uses**:
1. remote_mcp on cabin-pc for task 1
2. remote_exec to SSH to office-pc for task 2
3. Coordinate results via workflow-validator
4. Collect evidence from both nodes
```

### Memory Persistence

```markdown
**User**: Store workflow learnings to memory.

**Claude uses**:
1. remote_mcp to call memory MCP server
2. Write learnings to ~/.claude/shared-memory/
3. Verify with read_file
4. Index for future retrieval
```

### Third-Party Validation

```markdown
**User**: Get GPT-5.2 validation via OpenAI MCP.

**Claude uses**:
1. remote_mcp to call openai-chat MCP
2. Pass workflow evidence for review
3. Collect validation response
4. Store in evidence trail
```

---

## 📞 Getting Help

If web agent connection fails:

1. **Check Connectivity**: Verify cabin-pc is online
2. **Verify Token**: Confirm authentication token
3. **Test Tools**: Start with ping, then progress to complex tools
4. **Review Logs**: Check cabin-pc MCP gateway logs
5. **Ask User**: Request updated connection info if needed

---

## 🔐 Security Notes

- **Token Security**: Never expose token in chat history (use securely)
- **Network**: Tailscale provides encrypted tunnel
- **Authentication**: Bearer token required for all requests
- **Scope**: MPC-Gateway only accesses allowed directories
- **Audit**: All operations logged on cabin-pc

---

## ✅ Success Criteria

Web agent setup is complete when:

1. ✅ MPC-Gateway ping returns "pong"
2. ✅ All nodes (cabin-pc, office-pc, homeassistant) visible
3. ✅ Can read AGENTS_3.md from ~/.claude/
4. ✅ Can create workflow directory
5. ✅ Can call workflow-validator via remote_mcp
6. ✅ Can execute remote commands
7. ✅ Ready to run complete workflows

---

## 📚 Related Documentation

- **AGENTS_3.md**: Complete workflow specification
- **CLAUDE_2.md**: Infrastructure details (MCP servers, nodes)
- **QUICKSTART.md**: General setup (for local agents)
- **MCP_SETUP.md**: MCP server configuration

---

**For Web Agents**: Always use MPC-Gateway tools  
**For Local Agents**: Use setup.sh for direct installation  
**For Claude Code**: Use native file access

---

**Version**: 1.0.0  
**Last Updated**: 2026-01-04T09:00:00Z  
**Status**: Production-Ready
