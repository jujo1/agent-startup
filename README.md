# Agent Startup - AGENTS 4.0

**Production-ready agent orchestration system for Claude**

[![Status](https://img.shields.io/badge/status-production--ready-brightgreen)]()
[![Tests](https://img.shields.io/badge/tests-99%2B%20passing-success)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

---

## 🎯 What is AGENTS 4.0?

A reality-tested, production-ready agent orchestration system that provides:

- **State Machine Enforcement** - 99+ tests, 0 failures
- **Bypass Prevention** - Prevents workflow shortcuts
- **Field Compliance** - 17-field todo schema enforcement
- **Rule Enforcement** - M1-M45 rules verified in production

Built for Claude Web, Claude Desktop, and Claude Code.

---

## ⚡ Quick Start

### 🌐 For Web/Mobile Users (Claude.ai)

**Can't install locally? No problem!** Connect via MPC-Gateway:

1. **Copy Template**: Open [FIRST_CONVERSATION_TEMPLATE.md](FIRST_CONVERSATION_TEMPLATE.md)
2. **Paste in Claude.ai**: Start new conversation and paste template
3. **Auto-Connect**: Claude connects to your cabin-pc infrastructure
4. **Start Building**: Execute workflows remotely via MPC-Gateway

**Setup time**: ~2 minutes | **Guide**: [WEB_AGENTS_SETUP.md](WEB_AGENTS_SETUP.md)

---

### 💻 For Desktop/Code Users (Local Installation)

```bash
# 1. Clone repository
git clone https://github.com/jujo1/agent-startup.git
cd agent-startup

# 2. Run automated setup
chmod +x setup.sh
./setup.sh

# 3. Verify installation
python3 verify_setup.py

# 4. Start using!
# Open Claude and reference AGENTS_3.md
```

**Setup time**: ~5 minutes | **Guide**: [QUICKSTART.md](QUICKSTART.md)

---

## 📦 What's Included

```
agent-startup/
├── QUICKSTART.md           # 1-minute setup guide
├── setup.sh                # Automated installation
├── verify_setup.py         # Verification script
│
├── AGENTS_3.md             # Complete workflow specification
├── CLAUDE_2.md             # Infrastructure configuration
├── SCHEMAS.md              # Data structure definitions
├── MCP_SETUP.md            # MCP server setup guide
│
├── agents/                 # Agent YAML definitions
│   ├── base/
│   ├── core/
│   └── specialized/
│
├── mcp/                    # MCP servers
│   └── servers/
│       ├── workflow_validator.py
│       └── requirements.txt
│
├── schemas/                # Schema definitions
├── scripts/                # Generator scripts
├── workflows/              # Workflow handlers
└── examples/               # Usage examples
```

---

## 🚀 Features

### Core Features (Production-Ready)

✅ **State Machine** - Tracks and validates workflow state  
✅ **Bypass Prevention** - Blocks invalid tool access  
✅ **Field Compliance** - Enforces 17-field todo structure  
✅ **Rule Enforcement** - M9, M13, M18, M22 verified  
✅ **Reality Testing** - 99+ tests, 100% pass rate  

### Advanced Features (Optional)

⚠️ **Third-Party Validation** - GPT-5.2 integration  
⚠️ **Parallel Execution** - Tested, needs benchmarking  
⚠️ **Observer Monitoring** - Background compliance checks  
⚠️ **Memory Persistence** - 3 memory systems  

---

## 📖 Documentation

### Essential Reading (Start Here)
- **[README_WEB_AGENTS.md](README_WEB_AGENTS.md)** - **WEB USERS START HERE**
- **[FIRST_CONVERSATION_TEMPLATE.md](FIRST_CONVERSATION_TEMPLATE.md)** - Copy-paste to connect
- **[WEB_AGENTS_SETUP.md](WEB_AGENTS_SETUP.md)** - Complete web agent guide
- **[QUICKSTART.md](QUICKSTART.md)** - Local installation (5 minutes)
- **[AGENTS_3.md](AGENTS_3.md)** - Complete workflow specification
- **[MCP_SETUP.md](MCP_SETUP.md)** - MCP server installation

### Reference Documentation
- **[CLAUDE_2.md](CLAUDE_2.md)** - Infrastructure details
- **[SCHEMAS.md](SCHEMAS.md)** - Data structure reference
- **[TODO_SCHEMA.md](TODO_SCHEMA.md)** - Todo field requirements

### Verification & Testing
- **[REALITY_TESTING_RESULTS.md](REALITY_TESTING_RESULTS.md)** - Test evidence
- **[MASTER_INDEX.md](MASTER_INDEX.md)** - Complete file index

---

## 🧪 Testing Status

| Component | Tests | Status | Evidence |
|-----------|-------|--------|----------|
| workflow_validator.py | 99+ | ✅ PASS | REALITY_TESTING_RESULTS.md |
| todo-mcp | 53 | ✅ PASS | Field compliance tests |
| workflow-gateway | 42 | ✅ PASS | Bypass prevention tests |
| State transitions | All | ✅ PASS | State machine tests |

**Overall**: Production-ready core features

---

## 💡 Usage Examples

### Example 1: Simple Task

```markdown
User: "Create a Python calculator"

Agent executes:
1. STARTUP → S0-S20 checklist
2. PLAN → Break into tasks
3. REVIEW → Validate plan
4. IMPLEMENT → Write code
5. TEST → Run tests
6. VALIDATE → Quality gate
7. LEARN → Store learnings
```

### Example 2: Complex Project

```markdown
User: "Build REST API with authentication"

Workflow triggers:
- Parallel DEBATE (3+ disruptors)
- Parallel IMPLEMENT (multiple agents)
- Sequential TESTS (unit → scoped → full)
- Multi-agent REVIEW (3+ reviewers)
```

See `/examples` directory for more.

---

## 🔧 Configuration

### Minimal Configuration (Required)

**~/.claude/settings.json**:
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

### Full Configuration (Recommended)

See `MCP_SETUP.md` for complete configuration options.

---

## 🎓 Learning Resources

### For Beginners
1. [QUICKSTART.md](QUICKSTART.md) - 5 min setup
2. [Simple Example](examples/calculator_workflow.md) - First workflow
3. [Common Mistakes](docs/COMMON_MISTAKES.md) - What to avoid

### For Advanced Users
1. [Custom Agents](docs/CUSTOM_AGENTS.md) - Create your own
2. [Parallel Execution](docs/PARALLEL_EXECUTION.md) - Optimize performance
3. [Third-Party Integration](docs/THIRD_PARTY_VALIDATION.md) - GPT-5.2 setup

---

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create feature branch
3. Add tests
4. Submit pull request

See `CONTRIBUTING.md` for guidelines.

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/[YOUR-USERNAME]/agent-startup/issues)
- **Discussions**: [GitHub Discussions](https://github.com/[YOUR-USERNAME]/agent-startup/discussions)
- **Documentation**: See `/docs` directory

---

## 🗺️ Roadmap

### ✅ Completed (v4.0.0)
- Core enforcement system
- State machine validation
- Bypass prevention
- Field compliance

### 🚧 In Progress (v4.1.0)
- VSCode extension UI
- Additional agent YAMLs
- Performance benchmarks

### 📅 Planned (v4.2.0)
- E2E scenario tests
- Multi-project support
- Cloud deployment guides

---

## 🏆 Acknowledgments

Built with:
- Claude (Anthropic)
- MCP (Model Context Protocol)
- Reality testing methodology

---

## ⚠️ Important Notes

1. **Production-Ready**: Core features verified with 99+ tests
2. **Optional Features**: Some features require additional setup
3. **Active Development**: VSCode extension in progress
4. **Community**: Contributions welcome!

---

**Version**: 4.0.0  
**Status**: Production-Ready (Core)  
**Last Updated**: 2026-01-04  
**Maintainer**: [YOUR-USERNAME]

---

## 🚀 Get Started Now

```bash
git clone https://github.com/[YOUR-USERNAME]/agent-startup.git
cd agent-startup
./setup.sh
```

Questions? See [QUICKSTART.md](QUICKSTART.md) or open an issue!
