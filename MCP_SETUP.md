# MCP Server Setup Guide

## Overview

This guide walks through setting up the required MCP servers for AGENTS_4.

## Required MCP Servers

### 1. workflow-validator (MANDATORY)

**Purpose**: State machine enforcement, transition validation

**Installation**:
```bash
# Copy to MCP servers directory
mkdir -p ~/.claude/mcp/servers
cp mcp/servers/workflow_validator.py ~/.claude/mcp/servers/

# Install dependencies
pip install --break-system-packages sqlite3
```

**Configuration** (add to `~/.claude/settings.json`):
```json
{
  "mcpServers": {
    "workflow-validator": {
      "command": "python3",
      "args": ["~/.claude/mcp/servers/workflow_validator.py"]
    }
  }
}
```

**Test**:
```python
# Should return workflow created
workflow_validator_create(workflow_id="test_001")
```

---

### 2. todo (MANDATORY)

**Purpose**: Task management with 17-field schema enforcement

**Installation**:
```bash
# Install via npm
npm install -g @modelcontextprotocol/server-todo

# Or use Python version
pip install --break-system-packages mcp-server-todo
```

**Configuration**:
```json
{
  "mcpServers": {
    "todo": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-todo"]
    }
  }
}
```

---

### 3. memory (RECOMMENDED)

**Purpose**: Persistent memory across conversations

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-memory
```

**Configuration**:
```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

---

### 4. sequential-thinking (RECOMMENDED)

**Purpose**: Complex reasoning and analysis

**Installation**:
```bash
npm install -g @modelcontextprotocol/server-sequential-thinking
```

---

### 5-10. Additional Servers (OPTIONAL)

- **git**: Version control operations
- **github**: GitHub API access
- **scheduler**: Timed operations
- **openai-chat**: Third-party model access
- **credentials**: Secure credential storage
- **mcp-gateway**: Tool routing

See official MCP documentation for installation.

---

## Verification

After installation, verify all servers:

```bash
# List available MCP tools
mcp list

# Should show:
# - workflow_validator_*
# - mcp_todo_*
# - mcp_memory_*
# (etc.)
```

---

## Troubleshooting

### Server Not Responding

1. Check logs: `~/.claude/logs/mcp/[server].log`
2. Restart Claude
3. Verify configuration in settings.json

### Tool Not Found

1. Verify server is in settings.json
2. Check server command path
3. Test server independently

---

## Advanced Configuration

### Custom Paths

```json
{
  "mcpServers": {
    "workflow-validator": {
      "command": "python3",
      "args": ["~/.claude/mcp/servers/workflow_validator.py"],
      "env": {
        "WORKFLOW_DB": "~/.workflow/state.db"
      }
    }
  }
}
```

### Multiple Environments

Use different settings.json files for dev/prod:

```bash
# Development
cp settings.dev.json ~/.claude/settings.json

# Production  
cp settings.prod.json ~/.claude/settings.json
```
