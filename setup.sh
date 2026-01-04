#!/bin/bash
# AGENTS 4.0 - Automated Setup Script
# Version: 1.0.0

set -e

echo "════════════════════════════════════════════════════════"
echo "  AGENTS 4.0 - Automated Setup"
echo "  Version: 1.0.0"
echo "════════════════════════════════════════════════════════"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Detect OS
OS="$(uname -s)"
case "${OS}" in
    Linux*)     MACHINE=Linux;;
    Darwin*)    MACHINE=Mac;;
    CYGWIN*|MINGW*|MSYS*) MACHINE=Windows;;
    *)          MACHINE="UNKNOWN:${OS}"
esac

echo -e "${GREEN}✓${NC} Detected OS: ${MACHINE}"
echo ""

# Set home directory
if [[ "$MACHINE" == "Windows" ]]; then
    CLAUDE_HOME="${USERPROFILE}/.claude"
    WORKFLOW_HOME="${USERPROFILE}/.workflow"
else
    CLAUDE_HOME="${HOME}/.claude"
    WORKFLOW_HOME="${HOME}/.workflow"
fi

# Step 1: Create directory structure
echo "Step 1/5: Creating directory structure..."
mkdir -p "${CLAUDE_HOME}"/{agents,mcp/servers,schemas,workflows,skills,logs}
mkdir -p "${WORKFLOW_HOME}"/{todo,evidence,logs,plans,parallel}
mkdir -p "${CLAUDE_HOME}/agents"/{base,core,specialized,observers}
echo -e "${GREEN}✓${NC} Directories created"
echo ""

# Step 2: Copy core files
echo "Step 2/5: Copying core instruction files..."
cp AGENTS_3.md "${CLAUDE_HOME}/"
cp CLAUDE_2.md "${CLAUDE_HOME}/"
cp SCHEMAS.md "${CLAUDE_HOME}/"
cp QUICKSTART.md "${CLAUDE_HOME}/"
cp MCP_SETUP.md "${CLAUDE_HOME}/"
echo -e "${GREEN}✓${NC} Core files copied"
echo ""

# Step 3: Copy agent definitions
echo "Step 3/5: Copying agent definitions..."
if [ -d "agents" ]; then
    cp -r agents/* "${CLAUDE_HOME}/agents/"
    echo -e "${GREEN}✓${NC} Agent definitions copied"
else
    echo -e "${YELLOW}⚠${NC} No agents directory found, creating templates..."
    # Create template
    cat > "${CLAUDE_HOME}/agents/base/BASE.agent.yaml" << 'AGENT_EOF'
# BASE Agent Template
metadata:
  name: BASE
  version: "1.0.0"
  description: "Root agent for inheritance"

identity:
  role: "Foundational behavior template"
  trust_level: ZERO

# See AGENTS_3.md for complete structure
AGENT_EOF
    echo -e "${GREEN}✓${NC} Template created"
fi
echo ""

# Step 4: Copy MCP servers
echo "Step 4/5: Installing MCP servers..."
if [ -d "mcp/servers" ]; then
    cp -r mcp/servers/* "${CLAUDE_HOME}/mcp/servers/"
    
    # Install Python dependencies
    if [ -f "mcp/servers/requirements.txt" ]; then
        echo "Installing Python dependencies..."
        if command -v pip3 &> /dev/null; then
            pip3 install --break-system-packages -r mcp/servers/requirements.txt || \
            pip3 install --user -r mcp/servers/requirements.txt || \
            echo -e "${YELLOW}⚠${NC} Could not install Python deps (install manually)"
        else
            echo -e "${YELLOW}⚠${NC} pip3 not found, skipping Python deps"
        fi
    fi
    echo -e "${GREEN}✓${NC} MCP servers copied"
else
    echo -e "${YELLOW}⚠${NC} No MCP servers found, creating placeholder..."
    mkdir -p "${CLAUDE_HOME}/mcp/servers"
    echo "# Install MCP servers manually - see MCP_SETUP.md" > "${CLAUDE_HOME}/mcp/servers/README.txt"
fi
echo ""

# Step 5: Copy schemas
echo "Step 5/5: Copying schemas..."
if [ -d "schemas" ]; then
    cp -r schemas/* "${CLAUDE_HOME}/schemas/"
    echo -e "${GREEN}✓${NC} Schemas copied"
else
    echo -e "${YELLOW}⚠${NC} No schemas directory found"
fi
echo ""

# Create settings.json template if it doesn't exist
echo "Creating Claude settings template..."
SETTINGS_FILE="${CLAUDE_HOME}/settings.json"
if [ ! -f "${SETTINGS_FILE}" ]; then
    cat > "${SETTINGS_FILE}" << 'SETTINGS_EOF'
{
  "mcpServers": {
    "workflow-validator": {
      "command": "python3",
      "args": ["~/.claude/mcp/servers/workflow_validator.py"],
      "env": {
        "WORKFLOW_DB": "~/.workflow/workflow_state.db"
      }
    },
    "todo": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-todo"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
SETTINGS_EOF
    echo -e "${GREEN}✓${NC} Settings template created"
else
    echo -e "${YELLOW}⚠${NC} Settings file exists, not overwriting"
fi
echo ""

# Summary
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Installation locations:"
echo "  • Claude config: ${CLAUDE_HOME}"
echo "  • Workflows:     ${WORKFLOW_HOME}"
echo ""
echo "Next steps:"
echo "  1. Review ${CLAUDE_HOME}/settings.json"
echo "  2. Run: python3 verify_setup.py"
echo "  3. Read: ${CLAUDE_HOME}/QUICKSTART.md"
echo "  4. Start first workflow!"
echo ""
echo "Documentation:"
echo "  • AGENTS_3.md  - Complete workflow specification"
echo "  • CLAUDE_2.md  - Infrastructure configuration"
echo "  • MCP_SETUP.md - MCP server setup guide"
echo ""
echo -e "${GREEN}Ready to start using AGENTS 4.0!${NC}"
