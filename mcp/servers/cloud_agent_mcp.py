#!/usr/bin/env python3
"""
Cloud Agent MCP Server
Lightweight MCP server using FastMCP for cloud agents.
Replicates core gateway tools without infrastructure dependencies.

Usage:
    python cloud_agent_mcp.py              # stdio transport (Claude Desktop)
    python cloud_agent_mcp.py --sse        # SSE transport (Claude Web)
    python cloud_agent_mcp.py --http       # HTTP transport

Environment Variables:
    MCP_PORT          - Port for SSE/HTTP (default: 8000)
    MCP_HOST          - Host binding (default: 0.0.0.0)
    MCP_ALLOWED_PATHS - Comma-separated allowed path prefixes (empty = all)
    MCP_LOG_LEVEL     - Logging level (default: INFO)
"""

from fastmcp import FastMCP, Context
import subprocess
import os
import sys
import platform
import glob as glob_module
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

# Configuration
PORT = int(os.getenv("MCP_PORT", "8000"))
HOST = os.getenv("MCP_HOST", "0.0.0.0")
ALLOWED_PATHS = [p.strip() for p in os.getenv("MCP_ALLOWED_PATHS", "").split(",") if p.strip()]
LOG_LEVEL = os.getenv("MCP_LOG_LEVEL", "INFO")

# Initialize FastMCP server
mcp = FastMCP(
    name="CloudAgentMCP",
    instructions="Lightweight MCP gateway for cloud agents. Provides file access, command execution, and search tools."
)


def _validate_path(path: str) -> bool:
    """Check if path is within allowed prefixes."""
    if not ALLOWED_PATHS:
        return True
    resolved = str(Path(path).resolve())
    return any(resolved.startswith(str(Path(allowed).resolve())) for allowed in ALLOWED_PATHS)


@mcp.tool()
def ping() -> dict:
    """Test connectivity to MCP server. Returns pong with timestamp and host info."""
    return {
        "status": "pong",
        "host": platform.node(),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "platform": platform.system()
    }


@mcp.tool()
def get_status() -> dict:
    """Get MCP gateway status including platform, Python version, and configuration."""
    return {
        "platform": platform.platform(),
        "python_version": platform.python_version(),
        "host": platform.node(),
        "port": PORT,
        "allowed_paths": ALLOWED_PATHS or ["*"],
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


@mcp.tool()
def read_file(path: str) -> dict:
    """Read contents of a file.
    
    Args:
        path: Absolute or relative path to file
    """
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}", "allowed": ALLOWED_PATHS}
    
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return {"error": f"File not found: {path}"}
        if not p.is_file():
            return {"error": f"Not a file: {path}"}
        
        content = p.read_text(encoding="utf-8", errors="replace")
        return {
            "path": str(p.resolve()),
            "content": content,
            "size": p.stat().st_size,
            "modified": datetime.fromtimestamp(p.stat().st_mtime, timezone.utc).isoformat()
        }
    except Exception as e:
        return {"error": str(e), "path": path}


@mcp.tool()
def list_directory(path: str, max_depth: int = 2) -> dict:
    """List directory contents.
    
    Args:
        path: Directory path to list
        max_depth: Maximum recursion depth (default: 2)
    """
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}", "allowed": ALLOWED_PATHS}
    
    try:
        p = Path(path).expanduser()
        if not p.exists():
            return {"error": f"Directory not found: {path}"}
        if not p.is_dir():
            return {"error": f"Not a directory: {path}"}
        
        items = []
        for item in sorted(p.iterdir()):
            if item.name.startswith('.'):
                continue
            items.append({
                "name": item.name,
                "type": "dir" if item.is_dir() else "file",
                "size": item.stat().st_size if item.is_file() else None
            })
        
        return {"path": str(p.resolve()), "items": items, "count": len(items)}
    except Exception as e:
        return {"error": str(e), "path": path}


@mcp.tool()
def exec_command(command: str, cwd: Optional[str] = None, timeout: int = 30) -> dict:
    """Execute a shell command.
    
    Args:
        command: Shell command to execute
        cwd: Working directory (optional)
        timeout: Timeout in seconds (default: 30)
    """
    try:
        if cwd and not _validate_path(cwd):
            return {"error": f"Working directory not allowed: {cwd}"}
        
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd
        )
        return {
            "command": command,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode,
            "success": result.returncode == 0
        }
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s", "command": command}
    except Exception as e:
        return {"error": str(e), "command": command}


@mcp.tool()
def grep(path: str, pattern: str, recursive: bool = True) -> dict:
    """Search file contents using regex pattern.
    
    Args:
        path: File or directory to search
        pattern: Regex pattern to match
        recursive: Search subdirectories (default: True)
    """
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    
    try:
        p = Path(path).expanduser()
        regex = re.compile(pattern)
        matches = []
        
        files = p.rglob("*") if p.is_dir() and recursive else [p]
        
        for f in files:
            if not f.is_file():
                continue
            try:
                for i, line in enumerate(f.read_text(errors="ignore").splitlines(), 1):
                    if regex.search(line):
                        matches.append({
                            "file": str(f),
                            "line": i,
                            "content": line.strip()[:200]
                        })
                        if len(matches) >= 100:
                            return {"matches": matches, "truncated": True, "pattern": pattern}
            except:
                continue
        
        return {"matches": matches, "count": len(matches), "pattern": pattern}
    except Exception as e:
        return {"error": str(e), "pattern": pattern}


@mcp.tool()
def glob_files(path: str, pattern: str) -> dict:
    """Find files matching glob pattern.
    
    Args:
        path: Base directory
        pattern: Glob pattern (e.g., "*.py", "**/*.md")
    """
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    
    try:
        p = Path(path).expanduser()
        matches = list(p.glob(pattern))
        return {
            "path": str(p),
            "pattern": pattern,
            "matches": [str(m) for m in matches[:100]],
            "count": len(matches),
            "truncated": len(matches) > 100
        }
    except Exception as e:
        return {"error": str(e), "pattern": pattern}


@mcp.tool()
def write_file(path: str, content: str, append: bool = False) -> dict:
    """Write content to a file.
    
    Args:
        path: File path to write
        content: Content to write
        append: Append instead of overwrite (default: False)
    """
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    
    try:
        p = Path(path).expanduser()
        p.parent.mkdir(parents=True, exist_ok=True)
        
        mode = "a" if append else "w"
        p.write_text(content) if not append else p.open(mode).write(content)
        
        return {
            "path": str(p.resolve()),
            "size": p.stat().st_size,
            "action": "appended" if append else "written"
        }
    except Exception as e:
        return {"error": str(e), "path": path}


def main():
    """Main entry point with transport selection."""
    transport = "stdio"
    
    if "--sse" in sys.argv:
        transport = "sse"
    elif "--http" in sys.argv:
        transport = "streamable-http"
    
    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(transport=transport, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
