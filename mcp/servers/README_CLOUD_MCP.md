# Cloud Agent MCP Server

Lightweight MCP server for cloud agents (Claude.ai, Claude mobile) that replicates MPC-Gateway tools without infrastructure dependencies.

## Purpose

Cloud agents cannot access cabin-pc/Tailscale infrastructure directly. This script provides local file/command access within the cloud container environment.

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Claude Desktop (stdio)
```bash
python cloud_agent_mcp.py
```

### Claude Web (SSE)
```bash
python cloud_agent_mcp.py --sse
```

### HTTP Transport
```bash
python cloud_agent_mcp.py --http
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_PORT` | 8000 | Port for SSE/HTTP transports |
| `MCP_HOST` | 0.0.0.0 | Host binding |
| `MCP_ALLOWED_PATHS` | (all) | Comma-separated allowed path prefixes |
| `MCP_LOG_LEVEL` | INFO | Logging level |

## Security

Restrict file access:
```bash
MCP_ALLOWED_PATHS=/home/claude,/tmp python cloud_agent_mcp.py
```

## Tools

| Tool | Description |
|------|-------------|
| `ping` | Connectivity test |
| `get_status` | Platform/config info |
| `read_file` | Read file contents |
| `list_directory` | List directory |
| `exec_command` | Execute shell command |
| `grep` | Regex search in files |
| `glob_files` | Pattern match files |
| `write_file` | Write/append to file |

## Scope

This replaces **MPC-Gateway infrastructure tools only**. Other MCP servers (workflow-validator, todo, memory) are separate implementations.

## Claude Desktop Config

Add to `~/.claude/settings.json`:
```json
{
  "mcpServers": {
    "cloud-agent": {
      "command": "python3",
      "args": ["/path/to/cloud_agent_mcp.py"]
    }
  }
}
```
