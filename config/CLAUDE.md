VERSION: 2.0
MODIFIED: 2026-01-04T06:00:00Z
IMPORTS: AGENTS.md, SCHEMAS.md
NODE: cabin-pc (MASTER)

---

## 0. IDENTITY

```python
SYSTEM = {
    "hostname": "CABIN-PC",
    "ip": "100.121.56.65",
    "role": "MASTER_ORCHESTRATOR",
    "gateway": "https://cabin-pc.tail1a496.ts.net",
    "capacity": 25,
    "os": "Windows 11",
    "shell": "pwsh.exe",
    "python": "3.13.7"
}
```

---

## 1. NETWORK

```python
NODES = {
    "cabin-pc": {
        "ip": "100.121.56.65",
        "capacity": 25,
        "status": "ACTIVE",
        "role": "master"
    },
    "office-pc": {
        "ip": "100.84.172.79",
        "capacity": 40,
        "status": "ACTIVE",
        "role": "worker"
    }
}

TOTAL_CAPACITY = sum(n["capacity"] FOR n IN NODES.values() IF n["status"] == "ACTIVE")
```

---

## 2. MCP_SERVERS

```python
MCP_SERVERS = [
    "memory",
    "todo", 
    "sequential-thinking",
    "git",
    "github",
    "scheduler",
    "openai-chat",
    "credentials",
    "mcp-gateway"
]
```

---

## 3. PATHS

```python
PATHS = {
    "settings":      "~/.claude/settings.json",
    "agents":        "~/.claude/AGENTS.md",
    "infrastructure":"~/.claude/CLAUDE.md",
    "schemas":       "~/.claude/SCHEMAS.md",
    "credentials":   "~/.credentials/credentials.json",
    "shared_memory": "~/.claude/shared-memory/",
    "skills":        "~/.claude/skills/",
    "hooks":         "~/.claude/hooks/",
    "logs":          "~/.claude/logs/",
    "workflow":      "~/.claude/.workflow/"
}
```

See full CLAUDE.md specification for complete infrastructure details.
