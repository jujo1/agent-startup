#!/bin/bash
# Agent Startup Script
# Repository: https://github.com/jujo1/agent-startup
# Purpose: Initialize Claude agent environment with MCP servers and configuration
#
# Usage:
#   ./start.sh
#   ./start.sh --validate-only

set -e

# ============================================================================
# CONFIGURATION
# ============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE_ROOT="${WORKSPACE_ROOT:-$HOME/.claude}"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================================================
# BANNER
# ============================================================================

echo -e "${BLUE}"
cat << 'EOF'
   _                    _     ____  _             _
  / \   __ _  ___ _ __ | |_  / ___|| |_ __ _ _ __| |_ _   _ _ __
 / _ \ / _` |/ _ \ '_ \| __| \___ \| __/ _` | '__| __| | | | '_ \
/ ___ \ (_| |  __/ | | | |_   ___) | || (_| | |  | |_| |_| | |_) |
/_/   \_\__, |\___|_| |_|\__| |____/ \__\__,_|_|   \__|\__,_| .__/
        |___/                                                |_|

         MCP Agent Environment Initialization v1.0
EOF
echo -e "${NC}"

# ============================================================================
# VALIDATE ONLY MODE
# ============================================================================

if [[ "$1" == "--validate-only" ]]; then
    log_info "Validation mode - checking environment only"
    
    # Check Node.js
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version)
        log_success "Node.js: $NODE_VERSION"
    else
        log_error "Node.js not installed"
    fi
    
    # Check Python
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 --version)
        log_success "Python: $PYTHON_VERSION"
    else
        log_error "Python not installed"
    fi
    
    # Check Tailscale
    if command -v tailscale &> /dev/null; then
        log_success "Tailscale installed"
    else
        log_error "Tailscale not installed"
    fi
    
    exit 0
fi

# ============================================================================
# STEP 1: COPY CONFIGURATION FILES
# ============================================================================

log_info "Copying configuration files..."

# Copy AGENTS.md
if [ -f "$SCRIPT_DIR/config/AGENTS.md" ]; then
    cp "$SCRIPT_DIR/config/AGENTS.md" "$WORKSPACE_ROOT/AGENTS.md"
    log_success "Copied AGENTS.md"
fi

# Copy CLAUDE.md
if [ -f "$SCRIPT_DIR/config/CLAUDE.md" ]; then
    cp "$SCRIPT_DIR/config/CLAUDE.md" "$WORKSPACE_ROOT/CLAUDE.md"
    log_success "Copied CLAUDE.md"
fi

# Copy SCHEMAS.md
if [ -f "$SCRIPT_DIR/config/SCHEMAS.md" ]; then
    cp "$SCRIPT_DIR/config/SCHEMAS.md" "$WORKSPACE_ROOT/SCHEMAS.md"
    log_success "Copied SCHEMAS.md"
fi

# Copy settings.json (MCP server configuration)
if [ -f "$SCRIPT_DIR/config/settings.json" ]; then
    cp "$SCRIPT_DIR/config/settings.json" "$WORKSPACE_ROOT/settings.json"
    log_success "Copied settings.json"
fi

# ============================================================================
# STEP 2: INSTALL MCP SERVERS
# ============================================================================

log_info "Installing MCP servers..."

# Install from packages.txt if present
if [ -f "$SCRIPT_DIR/config/mcp-packages.txt" ]; then
    while IFS= read -r package; do
        # Skip comments and empty lines
        [[ "$package" =~ ^#.*$ ]] && continue
        [[ -z "$package" ]] && continue
        
        log_info "Installing $package..."
        npm install -g "$package" || log_warn "Failed to install $package"
    done < "$SCRIPT_DIR/config/mcp-packages.txt"
fi

log_success "MCP servers installed"

# ============================================================================
# STEP 3: SETUP HOOKS
# ============================================================================

log_info "Setting up hooks..."

if [ -d "$SCRIPT_DIR/hooks" ]; then
    cp -r "$SCRIPT_DIR/hooks/"* "$WORKSPACE_ROOT/hooks/" 2>/dev/null || true
    
    # Make hooks executable
    chmod +x "$WORKSPACE_ROOT/hooks/"*.sh 2>/dev/null || true
    chmod +x "$WORKSPACE_ROOT/hooks/"*.py 2>/dev/null || true
    
    log_success "Hooks installed"
fi

# ============================================================================
# STEP 4: SETUP SKILLS
# ============================================================================

log_info "Setting up skills..."

if [ -d "$SCRIPT_DIR/skills" ]; then
    cp -r "$SCRIPT_DIR/skills/"* "$WORKSPACE_ROOT/skills/" 2>/dev/null || true
    log_success "Skills installed"
fi

# ============================================================================
# STEP 5: INITIALIZE MEMORY
# ============================================================================

log_info "Initializing memory systems..."

# Create memory directories
mkdir -p "$WORKSPACE_ROOT/shared-memory"
mkdir -p "$HOME/.caches/memory"

# Initialize memory if memory MCP is available
if command -v npx &> /dev/null; then
    log_info "Testing memory MCP server..."
    # Test memory server is accessible
    timeout 5s npx @modelcontextprotocol/server-memory --version &>/dev/null && \
        log_success "Memory MCP server available" || \
        log_warn "Memory MCP server not responding"
fi

# ============================================================================
# STEP 6: VALIDATE INSTALLATION
# ============================================================================

log_info "Validating installation..."

# Check critical files
CRITICAL_FILES=(
    "$WORKSPACE_ROOT/AGENTS.md"
    "$WORKSPACE_ROOT/CLAUDE.md"
    "$WORKSPACE_ROOT/SCHEMAS.md"
    "$WORKSPACE_ROOT/settings.json"
)

VALIDATION_PASSED=true

for file in "${CRITICAL_FILES[@]}"; do
    if [ -f "$file" ]; then
        log_success "$(basename "$file") present"
    else
        log_error "$(basename "$file") MISSING"
        VALIDATION_PASSED=false
    fi
done

# Validate settings.json structure
if [ -f "$WORKSPACE_ROOT/settings.json" ]; then
    if command -v python3 &> /dev/null; then
        python3 -c "import json; json.load(open('$WORKSPACE_ROOT/settings.json'))" &>/dev/null && \
            log_success "settings.json valid JSON" || \
            log_error "settings.json INVALID JSON"
    fi
fi

# ============================================================================
# STEP 7: CREATE STARTUP SUMMARY
# ============================================================================

SUMMARY_FILE="$WORKSPACE_ROOT/.startup-summary"

cat > "$SUMMARY_FILE" << EOF
# Agent Startup Summary
# Generated: $(date -u +"%Y-%m-%dT%H:%M:%SZ")

WORKSPACE_ROOT=$WORKSPACE_ROOT
AGENT_STARTUP_DIR=$SCRIPT_DIR

# Files Installed:
$(ls -1 "$WORKSPACE_ROOT" | sed 's/^/  - /')

# MCP Servers:
$(npm list -g --depth=0 2>/dev/null | grep modelcontextprotocol | sed 's/^/  - /')

# Validation:
PASSED=$VALIDATION_PASSED
EOF

# ============================================================================
# COMPLETION
# ============================================================================

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
if [ "$VALIDATION_PASSED" = true ]; then
    echo -e "${GREEN}  ✓ Agent startup completed successfully${NC}"
else
    echo -e "${YELLOW}  ⚠ Agent startup completed with warnings${NC}"
fi
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}Workspace:${NC} $WORKSPACE_ROOT"
echo -e "${BLUE}Summary:${NC} $SUMMARY_FILE"
echo ""
echo -e "${BLUE}Next Steps:${NC}"
echo "  1. Review configuration in $WORKSPACE_ROOT/settings.json"
echo "  2. Start Claude Desktop or Claude Code"
echo "  3. MCP servers will auto-load from settings.json"
echo ""
