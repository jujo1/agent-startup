# MCP Funnel - Secure Remote MCP Access

> **AGENTS 4.0** - Cloud Agent Gateway via Tailscale Funnel

## Overview

MCP Funnel provides secure, authenticated remote access to local MCP servers via Tailscale Funnel. This enables Claude Web and remote Claude Code instances to interact with your local development environment.

## Architecture

```
┌─────────────────────┐     HTTPS/443     ┌──────────────────────┐
│   Claude Web/Code   │ ─────────────────▶│   Tailscale Funnel   │
│   (Cloud Agent)     │                   │   (Public Endpoint)  │
└─────────────────────┘                   └──────────┬───────────┘
                                                     │
                                          Internal Traffic
                                                     │
                                          ┌──────────▼───────────┐
                                          │   MCP Auth Proxy     │
                                          │   (localhost:8081)   │
                                          └──────────┬───────────┘
                                                     │ Tool Whitelist
                                                     │ Rate Limiting
                                                     │ Authentication
                                          ┌──────────▼───────────┐
                                          │   Local MCP Servers  │
                                          │   (localhost:8080)   │
                                          └──────────────────────┘
```

## Quick Start

### Option 1: Bootstrap Script (Recommended)

```bash
# Download and run bootstrap
curl -sL https://raw.githubusercontent.com/jujo1/agent-startup/main/mcp-funnel/bootstrap.sh | bash
```

### Option 2: Manual Setup

```bash
# 1. Create directories
mkdir -p ~/.claude/mcp-funnel
mkdir -p ~/.credentials

# 2. Download files
cd ~/.claude/mcp-funnel
curl -sLO https://raw.githubusercontent.com/jujo1/agent-startup/main/mcp-funnel/mcp_auth_proxy.py
curl -sLO https://raw.githubusercontent.com/jujo1/agent-startup/main/mcp-funnel/generate_tokens.py
curl -sLO https://raw.githubusercontent.com/jujo1/agent-startup/main/mcp-funnel/config.yaml
curl -sLO https://raw.githubusercontent.com/jujo1/agent-startup/main/mcp-funnel/requirements.txt

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate tokens
python generate_tokens.py --count 3

# 5. Start proxy
python mcp_auth_proxy.py
```

### Option 3: PowerShell (Windows)

```powershell
# Create directories
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.claude\mcp-funnel"
New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.credentials"

# Download files
cd "$env:USERPROFILE\.claude\mcp-funnel"
$baseUrl = "https://raw.githubusercontent.com/jujo1/agent-startup/main/mcp-funnel"
Invoke-WebRequest "$baseUrl/mcp_auth_proxy.py" -OutFile mcp_auth_proxy.py
Invoke-WebRequest "$baseUrl/generate_tokens.py" -OutFile generate_tokens.py
Invoke-WebRequest "$baseUrl/config.yaml" -OutFile config.yaml
Invoke-WebRequest "$baseUrl/requirements.txt" -OutFile requirements.txt

# Install dependencies
pip install -r requirements.txt

# Generate tokens
python generate_tokens.py --count 3

# Start proxy
python mcp_auth_proxy.py
```

## Configuration

Edit `~/.claude/mcp-funnel/config.yaml`:

```yaml
# Your device hostname
funnel:
  hostname: your-device.tail12345.ts.net
  port: 443

# Proxy settings
proxy:
  backend_port: 8080   # Your MCP server port
  listen_port: 8081    # Auth proxy listens here
  listen_host: "127.0.0.1"

# Allowed tools (whitelist)
allowed_tools:
  - ping
  - health
  - read_file
  - list_directory
  - semantic_search
  - git_status
  - git_diff

# Rate limiting
rate_limit:
  requests_per_minute: 60
  burst: 10
```

## Token Management

### Generate Tokens

```bash
# Generate 3 tokens (default)
python generate_tokens.py

# Generate 5 tokens with 30-day expiry
python generate_tokens.py --count 5 --expires 30

# Add to existing tokens
python generate_tokens.py --append --count 2
```

### List Tokens

```bash
python generate_tokens.py --list
```

### Revoke Token

```bash
# Revoke by token prefix
python generate_tokens.py --revoke "D8V6nXe"
```

## Tailscale Setup

### Enable Funnel

```bash
# Configure serve (proxies to auth proxy)
tailscale serve --bg --https=443 http://localhost:8081

# Enable public Funnel
tailscale funnel 443 on

# Verify
tailscale funnel status
```

### Test Connectivity

```bash
# Health check (no auth required)
curl https://your-device.ts.net/health

# Authenticated tool call
curl -X POST \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"tool": "ping"}' \
  https://your-device.ts.net/mcp
```

## API Reference

### Endpoints

| Endpoint      | Method | Auth     | Description          |
| ------------- | ------ | -------- | -------------------- |
| `/health`     | GET    | None     | Health check         |
| `/mcp`        | POST   | Bearer   | Tool invocation      |
| `/mcp/tools`  | GET    | Bearer   | List available tools |

### Request Format

```json
{
  "tool": "semantic_search",
  "params": {
    "query": "authentication",
    "limit": 10
  }
}
```

### Response Format

```json
{
  "success": true,
  "tool": "semantic_search",
  "result": {
    "matches": [...]
  },
  "metadata": {
    "execution_time_ms": 145,
    "timestamp": "2026-01-08T10:30:00Z"
  }
}
```

### Error Responses

```json
{
  "success": false,
  "error": {
    "code": "TOOL_NOT_ALLOWED",
    "message": "Tool 'delete_file' not in whitelist",
    "allowed_tools": ["ping", "read_file", ...]
  }
}
```

## Security

### Best Practices

1. **Token Rotation**: Rotate tokens every 30 days
2. **Whitelist Only**: Only enable tools you need
3. **Rate Limiting**: Keep limits reasonable
4. **Never Commit Tokens**: Add to `.gitignore`
5. **Monitor Logs**: Check `~/.claude/mcp-funnel/mcp_proxy.log`

### Forbidden Tools

These are NEVER allowed remotely (hardcoded block):

- `delete_file`
- `rm_rf`
- `format_drive`
- `sudo_*`
- `admin_*`
- `shell_exec`

## Troubleshooting

### Common Issues

| Issue              | Cause                  | Solution                         |
| ------------------ | ---------------------- | -------------------------------- |
| 401 Unauthorized   | Invalid/expired token  | Regenerate token                 |
| 403 Forbidden      | Tool not whitelisted   | Add to config.yaml               |
| 502 Bad Gateway    | Proxy not running      | Start mcp_auth_proxy.py          |
| Connection refused | Funnel not enabled     | `tailscale funnel 443 on`        |
| Timeout            | Network/firewall issue | Check Tailscale status           |

### Diagnostic Commands

```bash
# Check proxy logs
tail -f ~/.claude/mcp-funnel/mcp_proxy.log

# Check Tailscale status
tailscale status

# Check Funnel status
tailscale funnel status

# Test local proxy
curl http://localhost:8081/health
```

## Files

| File                 | Purpose                           |
| -------------------- | --------------------------------- |
| `mcp_auth_proxy.py`  | Authentication proxy server       |
| `generate_tokens.py` | Token generation/management       |
| `config.yaml`        | Proxy configuration               |
| `requirements.txt`   | Python dependencies               |
| `bootstrap.sh`       | Automated setup script            |

## Requirements

- Python 3.10+
- Tailscale with Funnel capability
- Local MCP server(s)
- `aiohttp` and `PyYAML` packages

---

**Version**: 1.0.0  
**Repository**: https://github.com/jujo1/agent-startup  
**Documentation**: See `instructions_new/rules/cloud_agent.md`
