# AGENTS 4.0 - Web Agents Quick Start

**For Claude.ai Web & Mobile Users**

---

## 🌐 I'm Using Claude.ai Web/Mobile

If you're using Claude through the web browser or mobile app, you cannot directly install files. Instead, you'll connect to your infrastructure via **MPC-Gateway**.

### ⚡ 3-Step Setup

#### 1️⃣ Copy First Conversation Template

Open [FIRST_CONVERSATION_TEMPLATE.md](FIRST_CONVERSATION_TEMPLATE.md) and copy the entire template into a new conversation with Claude.

#### 2️⃣ Claude Connects to Your Infrastructure

Claude will automatically:
- Connect to cabin-pc via MPC-Gateway
- Read AGENTS_3.md, CLAUDE_2.md, SCHEMAS.md
- Verify workflow environment
- Confirm ready for workflows

#### 3️⃣ Start Building

Once connected, ask Claude:
```
Create a simple Python calculator following AGENTS 4.0 workflow.
Use cabin-pc for execution.
```

---

## 📚 Documentation for Web Agents

| Document | Purpose |
|----------|---------|
| **[WEB_AGENTS_SETUP.md](WEB_AGENTS_SETUP.md)** | Complete web agent setup guide |
| **[FIRST_CONVERSATION_TEMPLATE.md](FIRST_CONVERSATION_TEMPLATE.md)** | Copy-paste to start |
| **[AGENTS_3.md](AGENTS_3.md)** | Full workflow specification |
| **[CLAUDE_2.md](CLAUDE_2.md)** | Infrastructure details |

---

## 🔧 Prerequisites

Before using web agents, ensure:

✅ **cabin-pc is online**  
✅ **MPC-Gateway is running** (`https://cabin-pc.tail1a496.ts.net`)  
✅ **Auth token is valid** (`D8V6nXegr2P1fd9PfLHNiVbLBCyG1N6jR0vTfI18b_k`)  
✅ **AGENTS_4 files installed on cabin-pc** (run `setup.sh` if not)

---

## ❓ Which Setup Guide?

| If you're using... | Use this guide |
|--------------------|----------------|
| Claude.ai Web | ➡️ **WEB_AGENTS_SETUP.md** (this guide) |
| Claude Mobile App | ➡️ **WEB_AGENTS_SETUP.md** (this guide) |
| Claude Desktop | ➡️ QUICKSTART.md (local setup) |
| Claude Code | ➡️ QUICKSTART.md (local setup) |
| VSCode Copilot | ➡️ scripts/generators/gen_all.py |
| Cursor | ➡️ scripts/generators/gen_all.py |

---

## 🎯 Web Agent Capabilities

Via MPC-Gateway, web agents can:

✅ Execute complete workflows on cabin-pc  
✅ Create and manage files remotely  
✅ Call MCP servers (workflow-validator, todo, etc.)  
✅ Run commands on multiple nodes (cabin-pc, office-pc)  
✅ Store and retrieve workflow evidence  
✅ Access memory systems  
✅ Coordinate parallel execution  

---

## 📞 Support

- **Connection Issues**: See [WEB_AGENTS_SETUP.md](WEB_AGENTS_SETUP.md) → Troubleshooting
- **Workflow Questions**: See [AGENTS_3.md](AGENTS_3.md)
- **MCP Gateway Issues**: See [CLAUDE_2.md](CLAUDE_2.md) → MCP_GATEWAY

---

**Next**: Open [FIRST_CONVERSATION_TEMPLATE.md](FIRST_CONVERSATION_TEMPLATE.md) and start!
