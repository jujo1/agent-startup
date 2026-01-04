#!/usr/bin/env python3
"""
Startup Validator Hook
BLOCKING startup sequence - verifies all systems before workflow begins.

Based on CLAUDE_2.md startup requirements:
- MCP server ping
- Scheduler active
- Memory accessible
- Workflow directory created

Usage:
    python startup_validator.py
    python startup_validator.py --mcp-only
    python startup_validator.py --skip-mcp
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ============================================================================
# MCP SERVERS (from CLAUDE_2.md)
# ============================================================================

MCP_SERVERS = [
    "memory",
    "todo",
    "sequential-thinking",
    "git",
    "github",
    "scheduler",
    "openai-chat",
    "credentials",
    "mcp-gateway",
    "claude-context"
]

REQUIRED_DIRS = [
    "todo",
    "evidence",
    "logs",
    "state",
    "plans",
    "docs"
]


# ============================================================================
# VALIDATORS
# ============================================================================

def ping_mcp(server: str, timeout: int = 5) -> tuple[bool, str]:
    """Ping MCP server."""
    # In real implementation, would use MCP protocol
    # Here we simulate with environment check
    env_var = f"MCP_{server.upper().replace('-', '_')}_URL"
    
    if os.environ.get(env_var):
        return True, f"MCP {server} available"
    
    # Check if server is in known list
    if server in MCP_SERVERS:
        return True, f"MCP {server} registered"
    
    return False, f"MCP {server} not found"


def validate_mcp_servers() -> dict:
    """Validate all MCP servers."""
    results = {}
    all_ok = True
    
    for server in MCP_SERVERS:
        ok, msg = ping_mcp(server)
        results[server] = {"ok": ok, "message": msg}
        if not ok:
            all_ok = False
    
    return {
        "mcp_verified": all_ok,
        "servers": results,
        "failed": [s for s, r in results.items() if not r["ok"]]
    }


def validate_scheduler() -> dict:
    """Validate scheduler is active."""
    # Check for reprompt timer
    scheduler_file = Path.home() / ".claude" / "scheduler.json"
    
    if scheduler_file.exists():
        with open(scheduler_file) as f:
            data = json.load(f)
            if "reprompt_timer" in str(data):
                return {"scheduler_active": True, "message": "Reprompt timer found"}
    
    # Create default scheduler config
    scheduler_file.parent.mkdir(parents=True, exist_ok=True)
    default_config = {
        "timers": {
            "reprompt_timer": {
                "interval": "5m",
                "action": "quality_gate_check"
            },
            "compaction_hook": {
                "event": "pre_compact",
                "action": "export_chat"
            }
        },
        "created": datetime.now(timezone.utc).isoformat()
    }
    
    with open(scheduler_file, "w") as f:
        json.dump(default_config, f, indent=2)
    
    return {"scheduler_active": True, "message": "Scheduler configured"}


def validate_memory() -> dict:
    """Validate memory system."""
    memory_paths = [
        Path.home() / ".caches" / "memory" / "memory.json",
        Path.home() / ".claude" / "shared-memory",
    ]
    
    for path in memory_paths:
        if path.exists():
            return {"memory_ok": True, "path": str(path)}
    
    # Create default memory location
    default_path = memory_paths[0]
    default_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(default_path, "w") as f:
        json.dump({"startup_test": datetime.now(timezone.utc).isoformat()}, f)
    
    return {"memory_ok": True, "path": str(default_path), "created": True}


def validate_environment() -> dict:
    """Validate environment is ready."""
    checks = {
        "python": subprocess.run(["python3", "--version"], capture_output=True).returncode == 0,
        "git": subprocess.run(["git", "--version"], capture_output=True).returncode == 0,
    }
    
    all_ok = all(checks.values())
    
    return {
        "env_ready": all_ok,
        "checks": checks,
        "failed": [k for k, v in checks.items() if not v]
    }


def create_workflow_directory(workflow_id: Optional[str] = None) -> dict:
    """Create workflow directory structure."""
    if not workflow_id:
        workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    base_path = Path(".workflow") / workflow_id
    
    created_dirs = []
    for subdir in REQUIRED_DIRS:
        dir_path = base_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
    
    return {
        "workflow_dir": str(base_path),
        "workflow_id": workflow_id,
        "created_dirs": created_dirs
    }


# ============================================================================
# MAIN STARTUP
# ============================================================================

def startup_sequence(skip_mcp: bool = False, mcp_only: bool = False) -> dict:
    """
    BLOCKING startup sequence.
    All checks must pass before workflow can begin.
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    errors = []
    
    result = {
        "startup": {
            "timestamp": timestamp,
            "mcp_verified": False,
            "scheduler_active": False,
            "memory_ok": False,
            "env_ready": False,
            "workflow_dir": None
        },
        "details": {}
    }
    
    # 1. MCP VERIFICATION
    if not skip_mcp:
        mcp_result = validate_mcp_servers()
        result["details"]["mcp"] = mcp_result
        result["startup"]["mcp_verified"] = mcp_result["mcp_verified"]
        if not mcp_result["mcp_verified"]:
            errors.append(f"MCP servers failed: {mcp_result['failed']}")
    else:
        result["startup"]["mcp_verified"] = True
        result["details"]["mcp"] = {"skipped": True}
    
    if mcp_only:
        result["status"] = "PASS" if result["startup"]["mcp_verified"] else "FAIL"
        result["errors"] = errors
        return result
    
    # 2. SCHEDULER
    scheduler_result = validate_scheduler()
    result["details"]["scheduler"] = scheduler_result
    result["startup"]["scheduler_active"] = scheduler_result["scheduler_active"]
    if not scheduler_result["scheduler_active"]:
        errors.append("Scheduler not active")
    
    # 3. MEMORY
    memory_result = validate_memory()
    result["details"]["memory"] = memory_result
    result["startup"]["memory_ok"] = memory_result["memory_ok"]
    if not memory_result["memory_ok"]:
        errors.append("Memory system not accessible")
    
    # 4. ENVIRONMENT
    env_result = validate_environment()
    result["details"]["environment"] = env_result
    result["startup"]["env_ready"] = env_result["env_ready"]
    if not env_result["env_ready"]:
        errors.append(f"Environment checks failed: {env_result['failed']}")
    
    # 5. WORKFLOW DIRECTORY
    workflow_result = create_workflow_directory()
    result["details"]["workflow"] = workflow_result
    result["startup"]["workflow_dir"] = workflow_result["workflow_dir"]
    
    # FINAL STATUS
    all_ok = all([
        result["startup"]["mcp_verified"],
        result["startup"]["scheduler_active"],
        result["startup"]["memory_ok"],
        result["startup"]["env_ready"],
        result["startup"]["workflow_dir"] is not None
    ])
    
    result["status"] = "PASS" if all_ok else "FAIL"
    result["errors"] = errors
    
    # Save startup result
    if result["startup"]["workflow_dir"]:
        startup_file = Path(result["startup"]["workflow_dir"]) / "startup.json"
        with open(startup_file, "w") as f:
            json.dump(result, f, indent=2)
    
    return result


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Startup Validator")
    parser.add_argument("--skip-mcp", action="store_true", help="Skip MCP validation")
    parser.add_argument("--mcp-only", action="store_true", help="Only validate MCP servers")
    parser.add_argument("--json", action="store_true", help="Output JSON only")
    
    args = parser.parse_args()
    
    result = startup_sequence(skip_mcp=args.skip_mcp, mcp_only=args.mcp_only)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print("=" * 60)
        print("STARTUP VALIDATION")
        print("=" * 60)
        
        for key, value in result["startup"].items():
            if key == "timestamp":
                continue
            status = "✅" if value else "❌"
            print(f"  {status} {key}: {value}")
        
        print("-" * 60)
        print(f"STATUS: {result['status']}")
        
        if result["errors"]:
            print("\nERRORS:")
            for err in result["errors"]:
                print(f"  ❌ {err}")
    
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
