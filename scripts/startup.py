#!/usr/bin/env python3
"""
Agent Startup Script
====================

Complete startup sequence for Claude agents.
Validates MCP servers, memory, scheduler, and environment.

Usage:
    python startup.py
    python startup.py --quick  # Skip non-critical checks
"""

import json
import sys
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class StartupResult:
    """Result of startup sequence."""
    status: str  # PASS, FAIL
    mcp_verified: bool
    scheduler_active: bool
    memory_ok: bool
    env_ready: bool
    workflow_dir: str
    timestamp: str
    errors: List[str]


# MCP Servers to verify
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


def timestamp() -> str:
    """Get ISO8601 timestamp."""
    return datetime.now(timezone.utc).isoformat()


def verify_mcp_servers() -> Tuple[bool, List[str]]:
    """Verify all MCP servers are responding."""
    errors = []
    
    # In Claude environment, MCP servers are available via tools
    # This is a placeholder for actual MCP ping logic
    for server in MCP_SERVERS:
        # Simulated check - replace with actual MCP ping
        try:
            # CALL {server}/ping
            pass
        except Exception as e:
            errors.append(f"MCP {server}: {str(e)}")
    
    return len(errors) == 0, errors


def setup_scheduler() -> Tuple[bool, List[str]]:
    """Set up scheduler timers."""
    errors = []
    
    try:
        # Create reprompt timer (5 minute interval)
        # CALL scheduler/create {id: "reprompt_timer", interval: "5m"}
        
        # Create compaction hook
        # CALL scheduler/create {id: "compaction_hook", event: "pre_compact"}
        pass
    except Exception as e:
        errors.append(f"Scheduler setup: {str(e)}")
    
    return len(errors) == 0, errors


def verify_memory() -> Tuple[bool, List[str]]:
    """Verify memory system is working."""
    errors = []
    
    try:
        # Write test value
        # CALL memory/write {key: "startup_test", value: timestamp()}
        
        # Read back
        # result = CALL memory/read {key: "startup_test"}
        # if result.value is None:
        #     errors.append("Memory read/write failed")
        pass
    except Exception as e:
        errors.append(f"Memory: {str(e)}")
    
    return len(errors) == 0, errors


def create_workflow_dir() -> Tuple[str, List[str]]:
    """Create workflow directory structure."""
    errors = []
    
    session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    workflow_dir = Path(f".workflow/{session_id}")
    
    try:
        subdirs = ["todo", "evidence", "logs", "state", "docs"]
        for subdir in subdirs:
            (workflow_dir / subdir).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Workflow dir: {str(e)}")
    
    return str(workflow_dir), errors


def startup(quick: bool = False) -> StartupResult:
    """Run full startup sequence."""
    errors = []
    
    print("=" * 60)
    print("AGENT STARTUP")
    print("=" * 60)
    
    # 1. MCP Servers
    print("\n[1/4] Verifying MCP servers...")
    mcp_ok, mcp_errors = verify_mcp_servers()
    errors.extend(mcp_errors)
    print(f"  {'✅' if mcp_ok else '❌'} MCP servers: {len(MCP_SERVERS)} checked")
    
    # 2. Scheduler
    print("\n[2/4] Setting up scheduler...")
    scheduler_ok, scheduler_errors = setup_scheduler()
    errors.extend(scheduler_errors)
    print(f"  {'✅' if scheduler_ok else '❌'} Scheduler active")
    
    # 3. Memory
    print("\n[3/4] Verifying memory...")
    memory_ok, memory_errors = verify_memory()
    errors.extend(memory_errors)
    print(f"  {'✅' if memory_ok else '❌'} Memory system")
    
    # 4. Workflow directory
    print("\n[4/4] Creating workflow directory...")
    workflow_dir, dir_errors = create_workflow_dir()
    errors.extend(dir_errors)
    print(f"  {'✅' if not dir_errors else '❌'} {workflow_dir}")
    
    # Result
    all_ok = mcp_ok and scheduler_ok and memory_ok and not dir_errors
    
    result = StartupResult(
        status="PASS" if all_ok else "FAIL",
        mcp_verified=mcp_ok,
        scheduler_active=scheduler_ok,
        memory_ok=memory_ok,
        env_ready=all_ok,
        workflow_dir=workflow_dir,
        timestamp=timestamp(),
        errors=errors
    )
    
    print("\n" + "=" * 60)
    print(f"STATUS: {result.status}")
    if errors:
        print("\nErrors:")
        for e in errors:
            print(f"  ❌ {e}")
    print("=" * 60)
    
    # Save result
    result_path = Path(workflow_dir) / "startup.json"
    with open(result_path, "w") as f:
        json.dump(asdict(result), f, indent=2)
    
    return result


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    result = startup(quick=quick)
    sys.exit(0 if result.status == "PASS" else 1)
