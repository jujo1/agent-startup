# Cloud Agent MCP Server

Lightweight Python MCP server for cloud agents. Replicates core MCP tools without Tailscale/local infrastructure.

## Features

**25 tools across 4 categories:**

| Category | Tools | Purpose |
|----------|-------|---------|
| Filesystem | 8 | File ops, exec, search |
| Memory | 9 | Knowledge graph (entities/relations/observations) |
| Thinking | 3 | Sequential reasoning chains |
| Todo | 5 | Task management |

## Installation

```bash
pip install fastmcp>=2.0
```

## Usage

```bash
# stdio (Claude Desktop)
python cloud_agent_mcp.py

# SSE (Claude Web) 
python cloud_agent_mcp.py --sse

# HTTP
python cloud_agent_mcp.py --http
```

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MCP_PORT` | 8000 | SSE/HTTP port |
| `MCP_HOST` | 0.0.0.0 | Host binding |
| `MCP_ALLOWED_PATHS` | (empty=all) | Restrict file access |
| `MEMORY_FILE_PATH` | ~/.claude/memory.jsonl | Knowledge graph storage |
| `TODO_FILE_PATH` | ~/.claude/todos.json | Todo storage |

## Claude Desktop Config

```json
{
  "mcpServers": {
    "cloud-agent": {
      "command": "python",
      "args": ["path/to/cloud_agent_mcp.py"],
      "env": {
        "MEMORY_FILE_PATH": "C:\\Users\\you\\.claude\\memory.jsonl"
      }
    }
  }
}
```

## Tools Reference

### Filesystem (8)
- `ping` - Connectivity test
- `get_status` - Platform info
- `read_file` - Read file contents
- `write_file` - Write/append files
- `list_directory` - List directory
- `exec_command` - Execute shell commands
- `grep` - Regex search in files
- `glob_files` - Glob pattern matching

### Memory (9)
- `create_entities` - Create graph nodes
- `create_relations` - Create edges
- `add_observations` - Add facts to entities
- `delete_entities` - Remove nodes
- `delete_relations` - Remove edges
- `delete_observations` - Remove facts
- `read_graph` - Get full graph
- `search_nodes` - Semantic search
- `open_nodes` - Get specific nodes

### Thinking (3)
- `sequentialthinking` - Process thought chain
- `get_thinking_chain` - View current chain
- `reset_thinking` - Start new session

### Todo (5)
- `create_todo` - Create task
- `list_todos` - List with filters
- `update_todo` - Modify task
- `complete_todo` - Mark done
- `delete_todo` - Remove task

## Files

- `cloud_agent_mcp.py` - Main server + filesystem tools
- `memory_tools.py` - Knowledge graph implementation
- `thinking_tools.py` - Sequential thinking
- `todo_tools.py` - Task management
- `requirements.txt` - Dependencies
