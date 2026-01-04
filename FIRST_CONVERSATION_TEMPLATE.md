# First Conversation Template - Web Agents

**Copy and paste this into Claude.ai to get started with AGENTS 4.0**

---

## 📋 Template (Copy Everything Below)

```
Hi Claude! I want to use AGENTS 4.0 from the web interface. Please help me connect to my infrastructure and set up the workflow system.

CONNECTION DETAILS:
- Gateway URL: https://cabin-pc.tail1a496.ts.net
- MCP Endpoint: https://cabin-pc.tail1a496.ts.net/sse
- Auth Token: D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k
- Repository: https://github.com/jujo1/agent-startup

SETUP STEPS:
1. Test MPC-Gateway connection (use ping tool)
2. Verify gateway status (use get_status tool)
3. List available nodes (use list_nodes tool)
4. Read AGENTS_3.md from ~/.claude/ on cabin-pc
5. Verify ~/.workflow/ directory exists
6. Confirm you understand the workflow specification

VERIFICATION:
After setup, please confirm:
- You can read files from cabin-pc
- You can execute remote commands
- You understand the 12-stage workflow (STARTUP → PLAN → ... → LEARN)
- You're ready to execute workflows via MPC-Gateway

Once verified, please say "AGENTS 4.0 web setup complete and ready for workflows."
```

---

## 🎯 What This Does

When you paste this into Claude.ai, Claude will:

1. **Connect to MPC-Gateway** - Establishes secure connection to cabin-pc
2. **Test Tools** - Verifies all MPC-Gateway tools work
3. **Read Instructions** - Loads AGENTS_3.md, CLAUDE_2.md, SCHEMAS.md
4. **Verify Environment** - Checks workflow directory, MCP servers
5. **Confirm Ready** - Reports setup complete

---

## 📝 Expected Response

Claude should respond with something like:

```
I've successfully connected to your cabin-pc infrastructure via MPC-Gateway!

✅ Connection Status:
- Gateway: https://cabin-pc.tail1a496.ts.net ✓
- Ping: SUCCESS (response in 45ms)
- Status: All nodes online
- Available nodes: cabin-pc, office-pc, homeassistant

✅ Files Loaded:
- AGENTS_3.md (37KB) - Workflow specification
- CLAUDE_2.md (9.9KB) - Infrastructure config
- SCHEMAS.md (5.2KB) - Data structures

✅ Environment Verified:
- Workflow directory: ~/.workflow/ exists
- MCP servers: workflow-validator, todo detected
- Permissions: Read/write access confirmed

✅ Workflow Understanding:
I understand the 12-stage workflow:
STARTUP → PLAN → CRITERIA → REVIEW_PRE → DEBATE → 
IMPLEMENT → UNITTEST → SCOPEDINT → FULLINT → 
REVIEW_POST → VALIDATE → LEARN

AGENTS 4.0 web setup complete and ready for workflows.

What would you like to build?
```

---

## 🚀 Next Steps After Setup

Once Claude confirms setup is complete, try:

### Example 1: Simple Task
```
Create a Python calculator with add, subtract, multiply, and divide functions.
Follow the complete AGENTS 4.0 workflow from STARTUP through LEARN.
```

### Example 2: Check Workflow Status
```
Show me the current workflow state from cabin-pc.
List all files in ~/.workflow/ and show the most recent workflow.
```

### Example 3: Review Evidence
```
Read the evidence logs from the last workflow execution.
Show me what stages completed and what the quality scores were.
```

---

## 🔧 Troubleshooting

### If Connection Fails

Claude might say:
```
I cannot connect to the MPC-Gateway. Let me help troubleshoot...
```

**Your Response**:
```
Please try these steps:
1. Use the ping tool with no parameters
2. Check if the gateway URL is correct
3. Verify the auth token
4. Try get_status to see detailed error

If still failing, cabin-pc might be offline. Please confirm error message.
```

### If Files Not Found

Claude might say:
```
I cannot read AGENTS_3.md from ~/.claude/
```

**Your Response**:
```
Please use remote_exec to check if the file exists:

Command: ls -la ~/.claude/AGENTS_3.md

If file doesn't exist, we need to run the setup.sh script first.
```

### If MCP Servers Not Responding

Claude might say:
```
workflow-validator MCP server is not responding
```

**Your Response**:
```
Please check if MCP servers are running:

Use remote_exec with command: ps aux | grep workflow_validator

If not running, start them with:
python ~/.claude/mcp/servers/workflow_validator.py
```

---

## 📚 Advanced Setup (Optional)

After basic setup works, you can configure:

### A. Enable Memory Systems

```
Please verify memory systems are configured:

1. Check ~/.claude/shared-memory/ exists
2. Read ~/.claude/settings.json for memory MCP config
3. Test memory read/write via remote_mcp
```

### B. Configure Third-Party Validation

```
Please set up OpenAI MCP for third-party validation:

1. Check if openai-chat MCP server is configured
2. Verify API key is set
3. Test with a simple chat completion
```

### C. Enable Parallel Execution

```
Please verify parallel execution capability:

1. Check office-pc is accessible via remote_exec
2. Test spawning multiple agents
3. Verify observer monitoring is configured
```

---

## 🎓 Learning Path

### Day 1: First Setup (This Template)
- Connect to MPC-Gateway
- Read core documentation
- Verify environment
- Understand workflow stages

### Day 2: First Workflow
- Execute simple calculator example
- Review evidence logs
- Understand quality gates
- See reality testing in action

### Day 3: Advanced Features
- Multi-node parallel execution
- Memory persistence
- Third-party validation
- Custom agent creation

---

## ✅ Setup Verification

Before considering setup complete, verify:

- [ ] MPC-Gateway ping succeeds
- [ ] All 3 nodes visible (cabin-pc, office-pc, homeassistant)
- [ ] Can read AGENTS_3.md
- [ ] Can list ~/.workflow/ directory
- [ ] Can execute remote commands
- [ ] Can call workflow-validator via remote_mcp
- [ ] Claude confirms understanding of workflow
- [ ] Ready message received

---

## 📞 Need Help?

If this template doesn't work:

1. **Check Prerequisites**:
   - Is cabin-pc online?
   - Is MPC-Gateway running?
   - Is token correct?

2. **Manual Verification**:
   - Try each MPC-Gateway tool individually
   - Start with `ping`, then `get_status`
   - Progress to `read_file` and `remote_exec`

3. **Review Documentation**:
   - WEB_AGENTS_SETUP.md (detailed guide)
   - CLAUDE_2.md (infrastructure details)
   - MCP_SETUP.md (MCP server setup)

---

**Template Version**: 1.0.0  
**Last Updated**: 2026-01-04T09:15:00Z  
**Tested With**: Claude Sonnet 4.5 (Web)
