#!/bin/bash
# Cloud Agent Initialization Script
# Source this to set up MCP environment: source /tmp/agent-startup/init.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Persistence paths
export MEMORY_FILE_PATH="${SCRIPT_DIR}/data/memory.jsonl"
export TODO_FILE_PATH="${SCRIPT_DIR}/data/todos.json"

# Create data directory and files
mkdir -p "${SCRIPT_DIR}/data"
touch "${MEMORY_FILE_PATH}"
[ ! -s "${TODO_FILE_PATH}" ] && echo "[]" > "${TODO_FILE_PATH}"

# Install dependencies quietly
pip3 install --break-system-packages -q -r "${SCRIPT_DIR}/mcp/servers/requirements.txt" 2>/dev/null || true

# Add MCP servers to PYTHONPATH
export PYTHONPATH="${SCRIPT_DIR}/mcp/servers:${PYTHONPATH}"

echo "✓ Agent environment initialized"
echo "  MEMORY_FILE_PATH=${MEMORY_FILE_PATH}"
echo "  TODO_FILE_PATH=${TODO_FILE_PATH}"
echo "  MCP servers: ${SCRIPT_DIR}/mcp/servers/"
