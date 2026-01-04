#!/bin/bash
# Startup Validator Hook
# Purpose: Validates agent environment on startup
# Enforces: Startup rules S0-S20 from AGENTS.md

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ERRORS=0
WARNINGS=0

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  STARTUP VALIDATOR"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# S0: Check AGENTS.md exists
if [ -f "$HOME/.claude/AGENTS.md" ]; then
    echo -e "${GREEN}[✓]${NC} S0: AGENTS.md present"
else
    echo -e "${RED}[✗]${NC} S0: AGENTS.md MISSING"
    ((ERRORS++))
fi

# S1: Check CLAUDE.md exists
if [ -f "$HOME/.claude/CLAUDE.md" ]; then
    echo -e "${GREEN}[✓]${NC} S1: CLAUDE.md present"
else
    echo -e "${RED}[✗]${NC} S1: CLAUDE.md MISSING"
    ((ERRORS++))
fi

# S2: Check SCHEMAS.md exists
if [ -f "$HOME/.claude/SCHEMAS.md" ]; then
    echo -e "${GREEN}[✓]${NC} S2: SCHEMAS.md present"
else
    echo -e "${RED}[✗]${NC} S2: SCHEMAS.md MISSING"
    ((ERRORS++))
fi

# S3: Check settings.json exists
if [ -f "$HOME/.claude/settings.json" ]; then
    echo -e "${GREEN}[✓]${NC} S3: settings.json present"
    
    # Validate JSON structure
    if command -v python3 &> /dev/null; then
        if python3 -c "import json; json.load(open('$HOME/.claude/settings.json'))" &>/dev/null; then
            echo -e "${GREEN}[✓]${NC} S4: settings.json valid JSON"
        else
            echo -e "${RED}[✗]${NC} S4: settings.json INVALID JSON"
            ((ERRORS++))
        fi
    fi
else
    echo -e "${RED}[✗]${NC} S3: settings.json MISSING"
    ((ERRORS++))
fi

# S5: Check MCP servers
if command -v npx &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} S5: npx available"
    
    # Check specific MCP servers
    MCP_SERVERS=("@modelcontextprotocol/server-memory" "@modelcontextprotocol/server-filesystem")
    for server in "${MCP_SERVERS[@]}"; do
        if npm list -g "$server" &>/dev/null; then
            echo -e "${GREEN}[✓]${NC} S6: $server installed"
        else
            echo -e "${YELLOW}[!]${NC} S6: $server not installed"
            ((WARNINGS++))
        fi
    done
else
    echo -e "${RED}[✗]${NC} S5: npx NOT AVAILABLE"
    ((ERRORS++))
fi

# S7: Check workspace directories
REQUIRED_DIRS=(
    "$HOME/.claude"
    "$HOME/.claude/hooks"
    "$HOME/.claude/skills"
    "$HOME/.claude/logs"
    "$HOME/.claude/.workflow"
    "$HOME/.claude/shared-memory"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo -e "${GREEN}[✓]${NC} S7: $(basename "$dir")/ exists"
    else
        echo -e "${YELLOW}[!]${NC} S7: $(basename "$dir")/ missing (will create)"
        mkdir -p "$dir"
        ((WARNINGS++))
    fi
done

# S8: Check credentials
if [ -f "$HOME/.credentials/credentials.json" ]; then
    echo -e "${GREEN}[✓]${NC} S8: credentials.json present"
    
    # Check permissions (should be 600)
    PERMS=$(stat -c %a "$HOME/.credentials/credentials.json" 2>/dev/null || stat -f %A "$HOME/.credentials/credentials.json" 2>/dev/null || echo "unknown")
    if [ "$PERMS" = "600" ]; then
        echo -e "${GREEN}[✓]${NC} S9: credentials.json permissions correct (600)"
    else
        echo -e "${YELLOW}[!]${NC} S9: credentials.json permissions: $PERMS (should be 600)"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}[!]${NC} S8: credentials.json not found"
    ((WARNINGS++))
fi

# S10: Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version | awk '{print $2}')
    echo -e "${GREEN}[✓]${NC} S10: Python $PYTHON_VERSION available"
else
    echo -e "${RED}[✗]${NC} S10: Python NOT AVAILABLE"
    ((ERRORS++))
fi

# S11: Check Node.js
if command -v node &> /dev/null; then
    NODE_VERSION=$(node --version)
    echo -e "${GREEN}[✓]${NC} S11: Node.js $NODE_VERSION available"
else
    echo -e "${RED}[✗]${NC} S11: Node.js NOT AVAILABLE"
    ((ERRORS++))
fi

# S12: Check Tailscale (optional)
if command -v tailscale &> /dev/null; then
    echo -e "${GREEN}[✓]${NC} S12: Tailscale available"
    
    # Check if connected
    if tailscale status &>/dev/null; then
        TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "unknown")
        echo -e "${GREEN}[✓]${NC} S13: Tailscale connected ($TAILSCALE_IP)"
    else
        echo -e "${YELLOW}[!]${NC} S13: Tailscale not connected"
        ((WARNINGS++))
    fi
else
    echo -e "${YELLOW}[!]${NC} S12: Tailscale not installed (optional)"
    ((WARNINGS++))
fi

# S14: Check Git
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    echo -e "${GREEN}[✓]${NC} S14: Git $GIT_VERSION available"
else
    echo -e "${YELLOW}[!]${NC} S14: Git not available"
    ((WARNINGS++))
fi

# S15: Check environment variables
ENV_VARS=("HOME" "USER" "PATH")
for var in "${ENV_VARS[@]}"; do
    if [ -n "${!var}" ]; then
        echo -e "${GREEN}[✓]${NC} S15: $var set"
    else
        echo -e "${RED}[✗]${NC} S15: $var NOT SET"
        ((ERRORS++))
    fi
done

# ============================================================================
# SUMMARY
# ============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}  ✓ All startup checks PASSED${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}  ! Startup checks passed with $WARNINGS warning(s)${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 0
else
    echo -e "${RED}  ✗ Startup checks FAILED${NC}"
    echo -e "${RED}    Errors: $ERRORS${NC}"
    echo -e "${YELLOW}    Warnings: $WARNINGS${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi
