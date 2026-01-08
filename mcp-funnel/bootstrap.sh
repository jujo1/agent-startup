#!/bin/bash
# MCP Funnel Bootstrap Script
# AGENTS 4.0 - Cloud Agent Gateway
#
# This script sets up the MCP Funnel authentication proxy
# for secure remote access via Tailscale.
#
# Usage:
#   curl -sL https://raw.githubusercontent.com/jujo1/agent-startup/main/mcp-funnel/bootstrap.sh | bash
#   OR
#   ./bootstrap.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       AGENTS 4.0 - MCP Funnel Bootstrap                       ║"
echo "║       Secure Remote Access via Tailscale                      ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Configuration
GITHUB_REPO="jujo1/agent-startup"
BRANCH="main"
DEST_DIR="${HOME}/.claude/mcp-funnel"
CREDENTIALS_DIR="${HOME}/.credentials"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        return 1
    fi
    return 0
}

# Check prerequisites
echo -e "\n${BLUE}Checking prerequisites...${NC}"

# Check for required tools
MISSING=""
for cmd in curl python3 pip3; do
    if ! check_command "$cmd"; then
        MISSING="$MISSING $cmd"
    fi
done

if [ -n "$MISSING" ]; then
    log_error "Missing required tools:$MISSING"
    log_error "Please install them and try again."
    exit 1
fi

log_info "All prerequisites met ✓"

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
log_info "Python version: $PYTHON_VERSION"

# Create directories
echo -e "\n${BLUE}Creating directories...${NC}"

mkdir -p "$DEST_DIR"
mkdir -p "$CREDENTIALS_DIR"
mkdir -p "${HOME}/.claude/config"
mkdir -p "${HOME}/.claude/logs"

log_info "Created: $DEST_DIR"
log_info "Created: $CREDENTIALS_DIR"

# Download files from GitHub
echo -e "\n${BLUE}Downloading MCP Funnel files...${NC}"

BASE_URL="https://raw.githubusercontent.com/${GITHUB_REPO}/${BRANCH}/mcp-funnel"

# Download each file
FILES=(
    "mcp_auth_proxy.py"
    "generate_tokens.py"
    "config.yaml"
    "requirements.txt"
    "README.md"
)

for file in "${FILES[@]}"; do
    echo -n "  Downloading $file... "
    if curl -sL "${BASE_URL}/${file}" -o "${DEST_DIR}/${file}" 2>/dev/null; then
        echo -e "${GREEN}✓${NC}"
    else
        echo -e "${YELLOW}skipped (not found)${NC}"
    fi
done

# Make scripts executable
chmod +x "${DEST_DIR}/mcp_auth_proxy.py" 2>/dev/null || true
chmod +x "${DEST_DIR}/generate_tokens.py" 2>/dev/null || true

log_info "Files downloaded successfully"

# Install Python dependencies
echo -e "\n${BLUE}Installing Python dependencies...${NC}"

if [ -f "${DEST_DIR}/requirements.txt" ]; then
    pip3 install -q -r "${DEST_DIR}/requirements.txt" --user 2>/dev/null || \
    pip3 install -q aiohttp pyyaml --user
else
    pip3 install -q aiohttp pyyaml --user
fi

log_info "Dependencies installed"

# Generate initial tokens if needed
echo -e "\n${BLUE}Setting up authentication tokens...${NC}"

if [ ! -f "${CREDENTIALS_DIR}/mcp_tokens.json" ]; then
    log_info "Generating initial bearer tokens..."
    python3 "${DEST_DIR}/generate_tokens.py" --output "${CREDENTIALS_DIR}/mcp_tokens.json" --count 3
else
    log_info "Token file already exists, skipping generation"
fi

# Check Tailscale status
echo -e "\n${BLUE}Checking Tailscale...${NC}"

if check_command "tailscale"; then
    TAILSCALE_STATUS=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('BackendState', 'unknown'))" 2>/dev/null || echo "unknown")
    
    if [ "$TAILSCALE_STATUS" = "Running" ]; then
        log_info "Tailscale is running ✓"
        
        # Get device name
        DEVICE_NAME=$(tailscale status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('Self', {}).get('DNSName', 'unknown').split('.')[0])" 2>/dev/null || echo "unknown")
        log_info "Device name: $DEVICE_NAME"
        
        # Check Funnel status
        if tailscale funnel status 2>/dev/null | grep -q "on"; then
            log_info "Tailscale Funnel is enabled ✓"
        else
            log_warn "Tailscale Funnel is not enabled"
            log_warn "Enable with: tailscale funnel 443 on"
        fi
    else
        log_warn "Tailscale is not running (status: $TAILSCALE_STATUS)"
        log_warn "Start Tailscale and run: tailscale funnel 443 on"
    fi
else
    log_warn "Tailscale not installed"
    log_warn "Install from: https://tailscale.com/download"
fi

# Summary
echo -e "\n${BLUE}"
echo "╔═══════════════════════════════════════════════════════════════╗"
echo "║       Setup Complete!                                         ║"
echo "╚═══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

echo -e "${GREEN}Installed files:${NC}"
echo "  • ${DEST_DIR}/mcp_auth_proxy.py"
echo "  • ${DEST_DIR}/generate_tokens.py"
echo "  • ${DEST_DIR}/config.yaml"
echo "  • ${CREDENTIALS_DIR}/mcp_tokens.json"

echo -e "\n${GREEN}Next steps:${NC}"
echo "  1. Edit config:     nano ${DEST_DIR}/config.yaml"
echo "  2. Start proxy:     python3 ${DEST_DIR}/mcp_auth_proxy.py"
echo "  3. Enable funnel:   tailscale serve --bg --https=443 http://localhost:8081"
echo "  4.                  tailscale funnel 443 on"
echo "  5. Test:            curl https://YOUR-DEVICE.ts.net/health"

echo -e "\n${GREEN}To list your tokens:${NC}"
echo "  python3 ${DEST_DIR}/generate_tokens.py --list"

echo -e "\n${YELLOW}⚠️  Remember: Keep your tokens secure and never commit them to git!${NC}"
