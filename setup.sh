#!/bin/bash
# AGENTS 4.0 - Automated Setup Script
# Version: 1.1.0

set -e

echo "════════════════════════════════════════════════════════"
echo "  AGENTS 4.0 - Automated Setup"
echo "  Version: 1.1.0"
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
echo "Step 1/6: Creating directory structure..."
mkdir -p "${CLAUDE_HOME}"/{agents,mcp/servers,schemas,workflows,skills,logs,data}
mkdir -p "${WORKFLOW_HOME}"/{todo,evidence,logs,plans,parallel}
mkdir -p "${CLAUDE_HOME}/agents"/{base,core,specialized,observers}
echo -e "${GREEN}✓${NC} Directories created"
echo ""

# Step 2: Set up persistent data paths
echo "Step 2/6: Configuring persistent storage..."
MEMORY_FILE="${CLAUDE_HOME}/data/memory.jsonl"
TODO_FILE="${CLAUDE_HOME}/data/todos.json"

# Create empty files if they don't exist
touch "${MEMORY_FILE}"
touch "${TODO_FILE}"
[ ! -s "${TODO_FILE}" ] && echo "[]" > "${TODO_FILE}"

echo -e "${GREEN}✓${NC} Persistent storage configured:"
echo "    Memory: ${MEMORY_FILE}"
echo "    Todos:  ${TODO_FILE}"
echo ""

# Step 3: Copy core files
echo "Step 3/6: Copying core instruction files..."
cp AGENTS_3.md "${CLAUDE_HOME}/" 2>/dev/null || true
cp AGENTS_4.md "${CLAUDE_HOME}/" 2>/dev/null || true
cp CLAUDE_2.md "${CLAUDE_HOME}/" 2>/dev/null || true
cp SCHEMAS.md "${CLAUDE_HOME}/" 2>/dev/null || true
cp QUICKSTART.md "${CLAUDE_HOME}/" 2>/dev/null || true
cp MCP_SETUP.md "${CLAUDE_HOME}/" 2>/dev/null || true
echo -e "${GREEN}✓${NC} Core files copied"
echo ""

# Step 4: Copy agent definitions
echo "Step 4/6: Copying agent definitions..."
if [ -d "agents" ]; then
    cp -r agents/* "${CLAUDE_HOME}/agents/"
    echo -e "${GREEN}✓${NC} Agent definitions copied"
else
    echo -e "${YELLOW}⚠${NC} No agents directory found, creating templates..."
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

# Step 5: Copy MCP servers
echo "Step 5/6: Installing MCP servers..."
if [ -d "mcp/servers" ]; then
    cp -r mcp/servers/* "${CLAUDE_HOME}/mcp/servers/"
    
    # Install Python dependencies
    if [ -f "mcp/servers/requirements.txt" ]; then
        echo "Installing Python dependencies..."
        if command -v pip3 &> /dev/null; then
            pip3 install --break-system-packages -r mcp/servers/requirements.txt 2>/dev/null || \
            pip3 install --user -r mcp/servers/requirements.txt 2>/dev/null || \
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

# Step 6: Copy schemas
echo "Step 6/6: Copying schemas..."
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
    cat > "${SETTINGS_FILE}" << SETTINGS_EOF
{
  "mcpServers": {
    "cloud-agent": {
      "command": "python3",
      "args": ["${CLAUDE_HOME}/mcp/servers/cloud_agent_mcp.py"],
      "env": {
        "MEMORY_FILE_PATH": "${MEMORY_FILE}",
        "TODO_FILE_PATH": "${TODO_FILE}",
        "MCP_ALLOWED_PATHS": ""
      }
    }
  }
}
SETTINGS_EOF
    echo -e "${GREEN}✓${NC} Settings template created"
else
    echo -e "${YELLOW}⚠${NC} Settings file exists, not overwriting"
    echo "    Add these env vars to your MCP server config:"
    echo "    MEMORY_FILE_PATH=${MEMORY_FILE}"
    echo "    TODO_FILE_PATH=${TODO_FILE}"
fi
echo ""

# Create shell profile exports
PROFILE_EXPORTS="
# Claude Agent MCP Persistence Paths
export MEMORY_FILE_PATH=\"${MEMORY_FILE}\"
export TODO_FILE_PATH=\"${TODO_FILE}\"
"

echo "Adding environment variables to shell profile..."
for PROFILE in "${HOME}/.bashrc" "${HOME}/.zshrc" "${HOME}/.profile"; do
    if [ -f "$PROFILE" ]; then
        if ! grep -q "MEMORY_FILE_PATH" "$PROFILE" 2>/dev/null; then
            echo "$PROFILE_EXPORTS" >> "$PROFILE"
            echo -e "${GREEN}✓${NC} Added to $PROFILE"
        else
            echo -e "${YELLOW}⚠${NC} Already in $PROFILE"
        fi
    fi
done
echo ""

# Export for current session
export MEMORY_FILE_PATH="${MEMORY_FILE}"
export TODO_FILE_PATH="${TODO_FILE}"

# Summary
echo "════════════════════════════════════════════════════════"
echo -e "${GREEN}✓ Setup Complete!${NC}"
echo "════════════════════════════════════════════════════════"
echo ""
echo "Installation locations:"
echo "  • Claude config: ${CLAUDE_HOME}"
echo "  • Workflows:     ${WORKFLOW_HOME}"
echo "  • Memory file:   ${MEMORY_FILE}"
echo "  • Todo file:     ${TODO_FILE}"
echo ""
echo "Environment variables (exported for this session):"
echo "  • MEMORY_FILE_PATH=${MEMORY_FILE}"
echo "  • TODO_FILE_PATH=${TODO_FILE}"
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
