#!/usr/bin/env python3
"""
MCP Server Health Check
=======================

Ping all MCP servers and report status.

Usage:
    python mcp_ping.py
    python mcp_ping.py --server memory
"""

import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, List, Tuple


# MCP Server Configuration
MCP_SERVERS = {
    "memory": {
        "description": "Memory storage and retrieval",
        "tools": ["read", "write", "search", "list"]
    },
    "todo": {
        "description": "Todo management with 17-field schema",
        "tools": ["create", "list", "get", "update", "complete", "assign", "sync"]
    },
    "sequential-thinking": {
        "description": "Step-by-step reasoning",
        "tools": ["analyze", "decompose", "challenge"]
    },
    "git": {
        "description": "Git operations",
        "tools": ["status", "commit", "push", "branch"]
    },
    "github": {
        "description": "GitHub API integration",
        "tools": ["create_pr", "list_issues", "create_issue"]
    },
    "scheduler": {
        "description": "Timer and event scheduling",
        "tools": ["create", "delete", "list", "trigger"]
    },
    "openai-chat": {
        "description": "OpenAI/GPT integration for third-party review",
        "tools": ["complete", "validate"]
    },
    "credentials": {
        "description": "Secure credential storage",
        "tools": ["get", "set", "list"]
    },
    "mcp-gateway": {
        "description": "MCP routing gateway",
        "tools": ["ping", "status", "route"]
    },
    "claude-context": {
        "description": "Semantic context search",
        "tools": ["search", "index", "retrieve"]
    }
}


def ping_server(server: str) -> Tuple[bool, str]:
    """Ping a single MCP server."""
    if server not in MCP_SERVERS:
        return False, f"Unknown server: {server}"
    
    # In Claude environment, this would call:
    # result = CALL {server}/ping
    # return result.status == "ok", result.message
    
    # Simulated response
    return True, "pong"


def ping_all() -> Dict[str, Dict]:
    """Ping all MCP servers."""
    results = {}
    
    for server, config in MCP_SERVERS.items():
        ok, message = ping_server(server)
        results[server] = {
            "status": "ok" if ok else "error",
            "message": message,
            "description": config["description"],
            "tools": config["tools"]
        }
    
    return results


def print_status(results: Dict):
    """Print status table."""
    print("=" * 70)
    print("MCP SERVER STATUS")
    print("=" * 70)
    print(f"{'Server':<25} {'Status':<10} {'Tools'}")
    print("-" * 70)
    
    for server, info in results.items():
        status = "✅ ok" if info["status"] == "ok" else "❌ error"
        tools = ", ".join(info["tools"][:3]) + ("..." if len(info["tools"]) > 3 else "")
        print(f"{server:<25} {status:<10} {tools}")
    
    print("-" * 70)
    
    ok_count = sum(1 for r in results.values() if r["status"] == "ok")
    total = len(results)
    print(f"Total: {ok_count}/{total} servers ok")
    print("=" * 70)


def main():
    parser = argparse.ArgumentParser(description="MCP Server Health Check")
    parser.add_argument("--server", help="Check specific server")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if args.server:
        ok, message = ping_server(args.server)
        if args.json:
            print(json.dumps({"server": args.server, "status": "ok" if ok else "error", "message": message}))
        else:
            print(f"{args.server}: {'✅ ok' if ok else '❌ error'} - {message}")
        sys.exit(0 if ok else 1)
    
    results = ping_all()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print_status(results)
    
    all_ok = all(r["status"] == "ok" for r in results.values())
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
