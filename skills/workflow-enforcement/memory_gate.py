#!/usr/bin/env python3
"""
Memory Gate Hook
Enforces M35: Memory-first startup - Query memory before tasks.
Enforces M40: Parallel mandate - Parallelize when 3+ items.

Usage:
    python memory_gate.py --query "previous sessions"
    python memory_gate.py --store key value
    python memory_gate.py --startup
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


# ============================================================================
# MEMORY PATHS (from CLAUDE_2.md)
# ============================================================================

MEMORY_PATHS = {
    "mcp_memory": Path.home() / ".caches" / "memory" / "memory.json",
    "shared_memory": Path.home() / ".claude" / "shared-memory",
    "episodic_memory": Path.home() / ".config" / "superpowers" / "conversation-archive"
}


# ============================================================================
# MEMORY OPERATIONS
# ============================================================================

def get_memory_path(memory_type: str = "mcp_memory") -> Path:
    """Get path for memory type."""
    path = MEMORY_PATHS.get(memory_type)
    if path:
        return path
    return MEMORY_PATHS["mcp_memory"]


def ensure_memory_exists() -> dict:
    """Ensure memory file exists."""
    path = get_memory_path("mcp_memory")
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not path.exists():
        with open(path, "w") as f:
            json.dump({"created": datetime.now(timezone.utc).isoformat()}, f)
        return {"created": True, "path": str(path)}
    
    return {"created": False, "path": str(path)}


def read_memory(key: Optional[str] = None) -> dict:
    """Read from memory."""
    path = get_memory_path("mcp_memory")
    
    if not path.exists():
        return {"found": False, "error": "Memory file not found"}
    
    try:
        with open(path) as f:
            data = json.load(f)
        
        if key:
            if key in data:
                return {"found": True, "key": key, "value": data[key]}
            return {"found": False, "key": key}
        
        return {"found": True, "data": data}
    
    except json.JSONDecodeError as e:
        return {"found": False, "error": f"Invalid JSON: {e}"}


def write_memory(key: str, value: any) -> dict:
    """Write to memory."""
    path = get_memory_path("mcp_memory")
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Read existing
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
        except:
            data = {}
    else:
        data = {}
    
    # Update
    data[key] = value
    data["_updated"] = datetime.now(timezone.utc).isoformat()
    
    # Write
    with open(path, "w") as f:
        json.dump(data, f, indent=2, default=str)
    
    return {"written": True, "key": key, "path": str(path)}


def search_memory(query: str) -> dict:
    """Search memory for query."""
    results = []
    
    # Search MCP memory
    mcp_result = read_memory()
    if mcp_result.get("found") and mcp_result.get("data"):
        for key, value in mcp_result["data"].items():
            if key.startswith("_"):
                continue
            value_str = json.dumps(value) if isinstance(value, (dict, list)) else str(value)
            if query.lower() in key.lower() or query.lower() in value_str.lower():
                results.append({"source": "mcp_memory", "key": key, "value": value})
    
    # Search shared memory
    shared_path = get_memory_path("shared_memory")
    if shared_path.exists() and shared_path.is_dir():
        for file in shared_path.glob("*.md"):
            content = file.read_text()
            if query.lower() in content.lower():
                results.append({
                    "source": "shared_memory",
                    "file": str(file),
                    "excerpt": content[:200]
                })
    
    # Search episodic memory
    episodic_path = get_memory_path("episodic_memory")
    if episodic_path.exists() and episodic_path.is_dir():
        for file in episodic_path.glob("**/*.json"):
            try:
                with open(file) as f:
                    content = f.read()
                if query.lower() in content.lower():
                    results.append({
                        "source": "episodic_memory",
                        "file": str(file),
                        "excerpt": content[:200]
                    })
            except:
                continue
    
    return {
        "query": query,
        "found": len(results) > 0,
        "count": len(results),
        "results": results
    }


# ============================================================================
# STARTUP GATE
# ============================================================================

def memory_startup_gate() -> dict:
    """
    BLOCKING memory gate at startup.
    M35: Must query memory before starting tasks.
    """
    result = {
        "gate": "memory_startup",
        "passed": False,
        "memory_status": {},
        "last_session": None,
        "pending_todos": [],
        "errors": []
    }
    
    # 1. Ensure memory exists
    ensure_result = ensure_memory_exists()
    result["memory_status"]["created"] = ensure_result
    
    # 2. Read last session
    last_session = read_memory("last_session")
    if last_session.get("found"):
        result["last_session"] = last_session["value"]
    
    # 3. Check for pending todos
    todos = read_memory("pending_todos")
    if todos.get("found") and todos.get("value"):
        result["pending_todos"] = todos["value"]
    
    # 4. Search for relevant context
    context_search = search_memory("workflow")
    result["memory_status"]["context_found"] = context_search["found"]
    result["memory_status"]["context_count"] = context_search["count"]
    
    # Gate passes if memory is accessible
    result["passed"] = True
    
    # Store startup in memory
    write_memory("last_startup", {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gate_result": "PASS"
    })
    
    return result


# ============================================================================
# PARALLEL GATE
# ============================================================================

def parallel_gate(items: list, threshold: int = 3) -> dict:
    """
    M40: Parallel mandate - 3+ items must be parallelized.
    """
    count = len(items)
    must_parallel = count >= threshold
    
    return {
        "gate": "parallel",
        "item_count": count,
        "threshold": threshold,
        "must_parallel": must_parallel,
        "action": "PARALLEL" if must_parallel else "SEQUENTIAL"
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Memory Gate")
    parser.add_argument("--startup", action="store_true", help="Run startup gate")
    parser.add_argument("--query", help="Search memory")
    parser.add_argument("--read", help="Read key from memory")
    parser.add_argument("--store", nargs=2, metavar=("KEY", "VALUE"), help="Store to memory")
    parser.add_argument("--parallel-check", type=int, help="Check if count requires parallel")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    
    args = parser.parse_args()
    
    if args.startup:
        result = memory_startup_gate()
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print("=" * 60)
            print("MEMORY STARTUP GATE")
            print("=" * 60)
            status = "✅ PASSED" if result["passed"] else "❌ FAILED"
            print(f"Status: {status}")
            
            if result["last_session"]:
                print(f"\nLast session: {result['last_session']}")
            
            if result["pending_todos"]:
                print(f"\nPending todos: {len(result['pending_todos'])}")
                for todo in result["pending_todos"][:5]:
                    print(f"  - {todo}")
        
        return 0 if result["passed"] else 1
    
    elif args.query:
        result = search_memory(args.query)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Search: {args.query}")
            print(f"Found: {result['count']} results")
            for r in result["results"]:
                print(f"  [{r['source']}] {r.get('key', r.get('file', ''))}")
        
        return 0
    
    elif args.read:
        result = read_memory(args.read)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            if result.get("found"):
                print(f"{args.read}: {result['value']}")
            else:
                print(f"Key not found: {args.read}")
        
        return 0 if result.get("found") else 1
    
    elif args.store:
        key, value = args.store
        result = write_memory(key, value)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Stored: {key}")
        
        return 0
    
    elif args.parallel_check:
        items = list(range(args.parallel_check))
        result = parallel_gate(items)
        
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            print(f"Items: {result['item_count']}")
            print(f"Action: {result['action']}")
        
        return 0
    
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
