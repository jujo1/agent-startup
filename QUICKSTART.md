# AGENTS 4.0 - Quick Start Guide

**Last Updated**: 2026-01-04T08:00:00Z  
**For**: Claude Web, Claude Desktop, Claude Code  
**Status**: Production-Ready Core Features

---

## ⚡ 1-Minute Setup

```bash
# Clone agent-startup repository
git clone https://github.com/[YOUR-USERNAME]/agent-startup.git
cd agent-startup

# Run automated setup
chmod +x setup.sh
./setup.sh

# Verify installation
python3 verify_setup.py
```

---

## 📋 Prerequisites

- **Claude Access**: Web, Desktop, or Code
- **Python**: 3.11+ (for MCP servers)
- **Node.js**: 18+ (optional, for npm-based MCP servers)
- **Git**: For repository operations

---

## 🚀 Manual Setup (Step-by-Step)

### Step 1: Create Directory Structure

```bash
mkdir -p ~/.claude/{agents,mcp,schemas,workflows,skills}
mkdir -p ~/.workflow
```

### Step 2: Copy Core Files

```bash
# Copy instruction sets
cp AGENTS_3.md ~/.claude/
cp CLAUDE_2.md ~/.claude/
cp SCHEMAS.md ~/.claude/

# Copy agent definitions
cp -r agents/* ~/.claude/agents/

# Copy MCP servers
cp -r mcp/* ~/.claude/mcp/

# Copy schemas
cp -r schemas/* ~/.claude/schemas/
```

### Step 3: Install MCP Servers

```bash
# Install workflow validator (MANDATORY)
cd ~/.claude/mcp/servers
pip install --break-system-packages -r requirements.txt

# Test workflow validator
python3 workflow_validator.py --test
```

### Step 4: Configure Claude

**For Claude Web/Desktop**:
1. Open Settings → MCP Servers
2. Add workflow-validator configuration (see MCP_SETUP.md)
3. Restart Claude

**For Claude Code**:
1. Edit `~/.claude/settings.json`
2. Add MCP server configurations
3. Restart

### Step 5: Verify Setup

```bash
# Run verification script
python3 verify_setup.py

# Should output:
# ✅ Directory structure: OK
# ✅ Core files: OK
# ✅ MCP servers: OK
# ✅ Ready for workflow execution
```

---

## 🎯 First Workflow Execution

### Example: Simple Task

```markdown
**User Request**: "Create a simple Python calculator"

**Expected Workflow**:
1. STARTUP (S0-S20 checklist)
2. PLAN (Break down into tasks)
3. REVIEW_PRE (Validate plan)
4. DEBATE (Challenge assumptions)
5. IMPLEMENT (Write code)
6. UNITTEST (Test functions)
7. SCOPEDINT (Integration tests)
8. FULLINT (End-to-end tests)
9. REVIEW_POST (Final review)
10. VALIDATE (Quality gate)
11. LEARN (Extract learnings)
```

### How to Initiate

**In Claude Web/Desktop**:
```
I want to create a simple Python calculator following AGENTS_4 workflow.
Please start with the startup checklist (S0-S20).
```

**In Claude Code**:
```bash
# Use #claude-code execution mode
# Workflow will auto-trigger from AGENTS_3.md
```

---

## 📚 Essential Documentation

| Document | Purpose | When to Read |
|----------|---------|--------------|
| AGENTS_3.md | Complete workflow specification | Before first use |
| CLAUDE_2.md | Infrastructure & MCP setup | During setup |
| SCHEMAS.md | Data structure definitions | When creating todos |
| MCP_SETUP.md | MCP server installation | During setup |
| TODO_SCHEMA.md | Todo field requirements | When planning tasks |
| REALITY_TESTING_RESULTS.md | Evidence of testing | For verification |

---

## 🔧 Troubleshooting

### Issue: "MCP server not found"

**Solution**:
```bash
# Check MCP configuration
cat ~/.claude/settings.json | grep workflow-validator

# Restart Claude
# Verify server responds
```

### Issue: "Workflow directory not created"

**Solution**:
```bash
# Manually create structure
mkdir -p ~/.workflow/{todo,evidence,logs,plans}

# Set permissions
chmod -R 755 ~/.workflow
```

### Issue: "State machine errors"

**Solution**:
```bash
# Reset workflow state
rm ~/.workflow/workflow_state.db

# Restart workflow from IDLE
```

---

## 📊 Verification Checklist

Before starting your first workflow:

- [ ] Directory structure created (`~/.claude/`, `~/.workflow/`)
- [ ] Core files copied (AGENTS_3.md, CLAUDE_2.md, SCHEMAS.md)
- [ ] MCP server installed (workflow_validator.py)
- [ ] MCP server configured in settings.json
- [ ] MCP server responds to ping
- [ ] Agent YAML files present
- [ ] Schemas validated
- [ ] Documentation read

---

## 🎓 Learning Path

### Day 1: Setup & Basics
1. Complete setup (1 hour)
2. Read AGENTS_3.md overview (30 min)
3. Run first simple workflow (1 hour)

### Day 2: Understanding Workflow
1. Study state machine (30 min)
2. Review reality testing examples (30 min)
3. Execute medium complexity task (2 hours)

### Day 3: Advanced Features
1. Create custom agent YAML (1 hour)
2. Configure parallel execution (30 min)
3. Implement third-party validation (1 hour)

---

## 🚨 Common Mistakes

### ❌ DON'T:
- Skip S0-S20 startup checklist
- Use Sonnet for PLAN/REVIEW stages (use Opus)
- Bypass workflow stages
- Self-review your own work
- Proceed without Observer in parallel stages
- Fabricate logs or test results

### ✅ DO:
- Follow workflow strictly
- Use correct model per stage (M42)
- Create complete 17-field todos
- Reality test all claims
- Store learnings to memory
- Document evidence

---

## 📞 Support

- **Issues**: GitHub Issues on agent-startup repo
- **Documentation**: See `/docs` directory
- **Testing**: See `REALITY_TESTING_RESULTS.md`
- **Examples**: See `/examples` directory

---

## 🎯 Next Steps

After successful setup:

1. **Run Example Workflow**: `examples/calculator_workflow.md`
2. **Create Custom Agent**: `docs/CUSTOM_AGENTS.md`
3. **Configure Third-Party**: `docs/THIRD_PARTY_VALIDATION.md`
4. **Benchmark Performance**: `docs/BENCHMARKING.md`

---

## 📜 Version History

- **4.0.0** (2026-01-04): Production-ready release
  - Core enforcement verified (99+ tests)
  - State machine functional
  - Bypass prevention tested
  - Field compliance enforced

---

**Status**: PRODUCTION-READY  
**Support**: GitHub Issues  
**License**: MIT
