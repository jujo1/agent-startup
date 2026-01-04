# INFRASTRUCTURE.md

**Version:** 4.0.0  
**Modified:** 2026-01-04T07:30:00Z  
**References:** `CLAUDE.md`, `WORKFLOW.md`

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

## 1. System Identity

```python
SYSTEM = {
    hostname: "CABIN-PC",
    tailscale_ip: "100.121.56.65",
    role: "Master Node",
    mcp_gateway: "https://cabin-pc.tail1a496.ts.net:8081",
    agent_capacity: 25,
    os: "Windows 11",
    shell: "pwsh.exe",
    python: "3.13.7"
}
```

---

## 2. Network Topology

```
cabin-pc (MASTER) ─── MCP Gateway ───┬─── office-pc (40 agents)
     │                               └─── homeassistant (8 agents)
     │
     └─── DBs: Milvus (19530), Qdrant (6333)
          office-pc: PostgreSQL (5432, 5433), Redis (6379)
```

---

## 3. Nodes

```python
NODES = {
    "cabin-pc": {
        ip: "100.121.56.65",
        capacity: 25,
        status: "active",
        user: "julia",
        password: "Th0mas@13"
    },
    "office-pc": {
        ip: "100.84.172.79",
        capacity: 40,
        status: "active",
        user: "julia",
        password: "Th0mas@13"
    },
    "homeassistant": {
        ip: "100.116.245.37",
        capacity: 8,
        status: "active",
        user: "jjones",
        password: "Th0mas13"
    },
    "eg-workstation": {
        ip: "100.78.245.37",
        capacity: 0,
        status: "disabled",
        user: "jjones",
        password: "mK7tB0%iACxwDa3n"
    },
    "boca-spm-dev1": {
        ip: "100.67.169.120",
        capacity: 0,
        status: "disabled",
        user: "jjones",
        password: "mK7tB0%iACxwDa3n"
    },
    "boca-spm-dev2": {
        ip: "100.92.235.102",
        capacity: 0,
        status: "disabled",
        user: "jjones",
        password: "mK7tB0%iACxwDa3n"
    }
}
```

---

## 4. Load Balancing

```python
LOAD_BALANCE = {
    "office-pc": 54.8,   # 40/73
    "cabin-pc": 34.2,    # 25/73
    "homeassistant": 11.0  # 8/73
}

PROCEDURE allocate_agent(task):
    # Sort by available capacity
    nodes = SORT(NODES, key=lambda n: n.capacity - n.active_agents, reverse=TRUE)
    
    FOR node IN nodes:
        IF node.status == "active" AND node.active_agents < node.capacity:
            RETURN node
    
    RETURN NULL  # No capacity
```

---

## 5. Docker Containers

```python
CONTAINERS = {
    "milvus-standalone": {
        node: "cabin-pc",
        port: 19530,
        purpose: "Vector embeddings",
        failover: "office-pc",
        failover_trigger: "3 failures (60s)"
    },
    "qdrant": {
        node: "cabin-pc",
        port: 6333,
        purpose: "Vector search",
        failover: "office-pc",
        failover_trigger: "3 failures (60s)"
    },
    "mcp-gateway": {
        node: "cabin-pc",
        port: 8081,
        purpose: "MCP routing",
        failover: "office-pc",
        failover_trigger: "3 failures (60s)"
    },
    "postgres-claude": {
        node: "office-pc",
        port: 5432,
        purpose: "General storage",
        failover: "cabin-pc",
        failover_trigger: "3 failures (60s)"
    },
    "postgres-credentials": {
        node: "office-pc",
        port: 5433,
        purpose: "Encrypted creds",
        failover: "cabin-pc",
        failover_trigger: "3 failures (60s)"
    },
    "redis": {
        node: "office-pc",
        port: 6379,
        purpose: "Cache, queues",
        failover: "cabin-pc",
        failover_trigger: "3 failures (60s)"
    }
}
```

---

## 6. MCP Servers

```python
MCP_SERVERS = {
    "memory": {
        purpose: "Persistent storage",
        tools: ["write", "read", "search", "delete"]
    },
    "todo": {
        purpose: "Task management",
        tools: ["create", "list", "get", "update", "complete", "assign", "get_tree", "get_by_agent", "sync"]
    },
    "sequential-thinking": {
        purpose: "Chain of thought",
        tools: ["analyze", "decompose", "synthesize"]
    },
    "git": {
        purpose: "Version control",
        tools: ["status", "add", "commit", "push", "pull", "branch", "checkout"]
    },
    "github": {
        purpose: "Repository operations",
        tools: ["create_repo", "create_pr", "merge_pr", "list_issues", "create_issue"]
    },
    "scheduler": {
        purpose: "Timers, cron",
        tools: ["create", "list", "delete", "update"]
    },
    "openai-chat": {
        purpose: "Third-party review",
        tools: ["complete", "chat"]
    },
    "credentials": {
        purpose: "Secrets management",
        tools: ["get", "set", "delete", "list"]
    },
    "mcp-gateway": {
        purpose: "Multi-node routing",
        tools: ["ping", "get_status", "list_nodes", "node_status", "remote_exec", "remote_mcp", "remote_file_read", "remote_file_write"]
    },
    "claude-context": {
        purpose: "Semantic search",
        tools: ["search", "index", "delete"]
    }
}
```

---

## 7. Tailscale Serve

```python
TAILSCALE_SERVE = {
    "cabin-pc": {
        "/": "claude-flow",
        "/mcp": "MCP Gateway",
        "tcp://22": "SSH",
        "tcp://5432": "PostgreSQL"
    }
}
```

---

## 8. MCP Gateway

```python
MCP_GATEWAY = {
    endpoint: "https://cabin-pc.tail1a496.ts.net",
    paths: {
        "/health": {auth: FALSE, method: "GET", description: "Status"},
        "/tools": {auth: TRUE, method: "GET", description: "List tools"},
        "/mcp": {auth: TRUE, method: "POST", description: "Execute"},
        "/sse": {auth: "OAuth 2.1", method: "SSE", description: "Claude Web"}
    },
    tools: [
        "ping", "get_status", "list_nodes", "node_status",
        "remote_exec", "remote_mcp", "remote_file_read", "remote_file_write",
        "read_file", "list_directory", "grep", "glob"
    ],
    tokens: {
        "Claude Web": "D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k",
        "Claude Code": "BrdjN6ALPRbNRhcfOs1C-dRMeq4EbMLJsDAL3A9UN8M",
        "Backup": "65QE33Np7dsER73IUc2kZevfZv1WZvNc-q1-Z5pvHms"
    }
}
```

---

## 9. Memory Systems

```python
MEMORY_SYSTEMS = {
    "mcp_memory": {
        location: "~/.caches/memory/memory.json",
        mcp_server: "memory"
    },
    "shared_memory": {
        location: "~/.claude/shared-memory/",
        mcp_server: "memory-bank"
    },
    "episodic_memory": {
        location: "~/.config/superpowers/conversation-archive/",
        mcp_server: "episodic-memory"
    }
}

MEMORY_WORKFLOW = [
    "Startup: Query shared-memory + todo",
    "Before questions: Search episodic-memory",
    "After task: Store to memory-bank",
    "Infrastructure changes: Update both systems"
]
```

---

## 10. Credentials

```python
CREDENTIALS = {
    primary: "~/.credentials/credentials.json",
    mcp_tokens: "~/.credentials/mcp_tokens.json",
    mcp_configs: "~/.claude/settings.json"
}
```

---

## 11. Routing Rules

```python
ROUTING = {
    "Vector write": "cabin-pc",
    "Vector read": "cabin-pc",
    "Relational write": "office-pc",
    "Relational read": "office-pc",
    "Cache": "office-pc"
}
```

---

## 12. Health Check

```python
PROCEDURE health_check(container, node):
    result = ssh(node, f"docker ps --filter name={container} --format '{{.Status}}'")
    RETURN "Up" IN result
```

---

## 13. Paths

```python
PATHS = {
    settings: "~/.claude/settings.json",
    instructions: "~/.claude/CLAUDE.md",
    infrastructure: "~/.claude/docs/INFRASTRUCTURE.md",
    credentials: "~/.credentials/credentials.json",
    mcp_tokens: "~/.credentials/mcp_tokens.json",
    shared_memory: "~/.claude/shared-memory/",
    mcp_funnel: "~/.claude/mcp-funnel/",
    distributed_agents: "~/.claude/distributed-agents/",
    skills: "~/.claude/skills/",
    hooks: "~/.claude/hooks/",
    logs: "~/.claude/logs/",
    workflow: "~/.claude/.workflow/"
}
```

---

## 14. Execution Tools

```python
EXECUTION_TOOLS = {
    "Read": "mcp_claude-code_Read",
    "Edit": "mcp_claude-code_Edit",
    "Shell": "mcp_claude-code_Bash",
    "Find": "mcp_claude-code_Glob",
    "Search": "mcp_claude-code_Grep",
    "Agent": "mcp_claude-code_Task",
    "Web": "mcp_claude-code_WebFetch"
}
```

---

## END OF INFRASTRUCTURE.md
