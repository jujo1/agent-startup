#!/usr/bin/env python3
"""
Cloud Agent MCP Server - Consolidated
25 tools: filesystem_mcp(8), memory_mcp(9), thinking_mcp(3), todo_mcp(5)

Tool Naming: cloud_agent_mcp-{server_mcp}-{tool_name}
"""

from fastmcp import FastMCP
import subprocess
import os
import platform
import re
import json
import uuid
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field, asdict

# =============================================================================
# CONFIGURATION
# =============================================================================

PORT = int(os.getenv("MCP_PORT", "8000"))
HOST = os.getenv("MCP_HOST", "0.0.0.0")
ALLOWED_PATHS = [p.strip() for p in os.getenv("MCP_ALLOWED_PATHS", "").split(",") if p.strip()]

mcp = FastMCP(name="CloudAgentMCP", instructions="Consolidated MCP: filesystem, memory, thinking, todo.")


def _validate_path(path: str) -> bool:
    """Check if path is within allowed directories."""
    if not ALLOWED_PATHS:
        return True
    abs_path = os.path.abspath(path)
    return any(abs_path.startswith(os.path.abspath(p)) for p in ALLOWED_PATHS)


# =============================================================================
# FILESYSTEM_MCP - Core Functions
# =============================================================================

def _filesystem_ping() -> dict:
    return {"status": "pong", "timestamp": datetime.now(timezone.utc).isoformat(), "host": platform.node(), "platform": platform.system()}


def _filesystem_get_status() -> dict:
    return {"platform": platform.platform(), "python_version": platform.python_version(), "host": platform.node(), "cwd": os.getcwd(), "allowed_paths": ALLOWED_PATHS or ["*"], "mcp_port": PORT}


def _filesystem_read_file(path: str) -> dict:
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    try:
        p = Path(path)
        if not p.exists():
            return {"error": f"File not found: {path}"}
        if not p.is_file():
            return {"error": f"Not a file: {path}"}
        content = p.read_text(encoding='utf-8')
        return {"path": str(p.absolute()), "content": content, "size": len(content), "lines": content.count('\n') + 1}
    except UnicodeDecodeError:
        return {"error": f"Binary file, cannot read as text: {path}"}
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": str(e)}


def _filesystem_write_file(path: str, content: str, append: bool = False) -> dict:
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = 'a' if append else 'w'
        with open(p, mode, encoding='utf-8') as f:
            f.write(content)
        return {"path": str(p.absolute()), "bytes_written": len(content), "mode": "append" if append else "write"}
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": str(e)}


def _filesystem_list_directory(path: str, max_depth: int = 2) -> dict:
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    try:
        p = Path(path)
        if not p.exists():
            return {"error": f"Directory not found: {path}"}
        if not p.is_dir():
            return {"error": f"Not a directory: {path}"}
        items = []
        for item in sorted(p.iterdir()):
            if item.name.startswith('.'):
                continue
            items.append({"name": item.name, "type": "dir" if item.is_dir() else "file", "size": item.stat().st_size if item.is_file() else None})
        return {"path": str(p.absolute()), "items": items, "count": len(items)}
    except PermissionError:
        return {"error": f"Permission denied: {path}"}
    except Exception as e:
        return {"error": str(e)}


def _filesystem_exec_command(command: str, cwd: str = None, timeout: int = 30) -> dict:
    if cwd and not _validate_path(cwd):
        return {"error": f"CWD not allowed: {cwd}"}
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout, cwd=cwd)
        return {"command": command, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
    except subprocess.TimeoutExpired:
        return {"error": f"Command timed out after {timeout}s", "command": command}
    except Exception as e:
        return {"error": str(e), "command": command}


def _filesystem_grep(path: str, pattern: str, recursive: bool = True) -> dict:
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    try:
        regex = re.compile(pattern)
        matches = []
        p = Path(path)
        if p.is_file():
            files = [p]
        elif p.is_dir():
            files = p.rglob("*") if recursive else p.glob("*")
        else:
            return {"error": f"Path not found: {path}"}
        for f in files:
            if not f.is_file():
                continue
            try:
                content = f.read_text(encoding='utf-8')
                for i, line in enumerate(content.splitlines(), 1):
                    if regex.search(line):
                        matches.append({"file": str(f), "line": i, "content": line[:200]})
            except (UnicodeDecodeError, PermissionError):
                continue
        return {"pattern": pattern, "path": str(p), "matches": matches, "count": len(matches)}
    except re.error as e:
        return {"error": f"Invalid regex: {e}"}
    except Exception as e:
        return {"error": str(e)}


def _filesystem_glob_files(path: str, pattern: str) -> dict:
    if not _validate_path(path):
        return {"error": f"Path not allowed: {path}"}
    try:
        p = Path(path)
        if not p.is_dir():
            return {"error": f"Not a directory: {path}"}
        matches = [str(m) for m in p.glob(pattern)]
        return {"path": str(p), "pattern": pattern, "matches": matches, "count": len(matches)}
    except Exception as e:
        return {"error": str(e)}


# =============================================================================
# MEMORY_MCP - Core Classes and Functions
# =============================================================================

@dataclass
class Entity:
    name: str
    entityType: str
    observations: list = field(default_factory=list)


@dataclass
class Relation:
    from_entity: str
    to_entity: str
    relationType: str


class KnowledgeGraph:
    def __init__(self, file_path: str = None):
        self.file_path = file_path or os.getenv("MEMORY_FILE_PATH", os.path.expanduser("~/.claude/memory.jsonl"))
        self.entities: dict = {}
        self.relations: list = []
        self._load()

    def _load(self):
        path = Path(self.file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    if data.get("type") == "entity":
                        self.entities[data["name"]] = Entity(name=data["name"], entityType=data.get("entityType", "unknown"), observations=data.get("observations", []))
                    elif data.get("type") == "relation":
                        self.relations.append(Relation(from_entity=data["from"], to_entity=data["to"], relationType=data["relationType"]))
        except Exception:
            pass

    def _save(self):
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            for e in self.entities.values():
                f.write(json.dumps({"type": "entity", "name": e.name, "entityType": e.entityType, "observations": e.observations}) + "\n")
            for r in self.relations:
                f.write(json.dumps({"type": "relation", "from": r.from_entity, "to": r.to_entity, "relationType": r.relationType}) + "\n")

    def reset(self):
        self.entities = {}
        self.relations = []
        if Path(self.file_path).exists():
            Path(self.file_path).unlink()


_graph: Optional[KnowledgeGraph] = None


def get_graph() -> KnowledgeGraph:
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph()
    return _graph


def reset_graph():
    global _graph
    if _graph:
        _graph.reset()
    _graph = None


def _memory_create_entities(entities: list) -> dict:
    graph = get_graph()
    created = []
    for e in entities:
        name = e.get("name")
        if not name:
            continue
        if name not in graph.entities:
            graph.entities[name] = Entity(name=name, entityType=e.get("entityType", "unknown"), observations=e.get("observations", []))
            created.append(name)
        else:
            existing = graph.entities[name]
            for obs in e.get("observations", []):
                if obs not in existing.observations:
                    existing.observations.append(obs)
            created.append(f"{name} (merged)")
    graph._save()
    return {"created": created, "count": len(created)}


def _memory_create_relations(relations: list) -> dict:
    graph = get_graph()
    created = []
    for r in relations:
        rel = Relation(from_entity=r.get("from", ""), to_entity=r.get("to", ""), relationType=r.get("relationType", "relates_to"))
        exists = any(x.from_entity == rel.from_entity and x.to_entity == rel.to_entity and x.relationType == rel.relationType for x in graph.relations)
        if not exists:
            graph.relations.append(rel)
            created.append(f"{rel.from_entity} -{rel.relationType}-> {rel.to_entity}")
    graph._save()
    return {"created": created, "count": len(created)}


def _memory_add_observations(entityName: str, observations: list) -> dict:
    graph = get_graph()
    if entityName not in graph.entities:
        return {"error": f"Entity not found: {entityName}"}
    entity = graph.entities[entityName]
    added = []
    for obs in observations:
        if obs not in entity.observations:
            entity.observations.append(obs)
            added.append(obs)
    graph._save()
    return {"entity": entityName, "added": added, "total": len(entity.observations)}


def _memory_delete_entities(entityNames: list) -> dict:
    graph = get_graph()
    deleted = []
    for name in entityNames:
        if name in graph.entities:
            del graph.entities[name]
            graph.relations = [r for r in graph.relations if r.from_entity != name and r.to_entity != name]
            deleted.append(name)
    graph._save()
    return {"deleted": deleted, "count": len(deleted)}


def _memory_delete_relations(relations: list) -> dict:
    graph = get_graph()
    deleted = []
    for r in relations:
        before = len(graph.relations)
        graph.relations = [x for x in graph.relations if not (x.from_entity == r.get("from") and x.to_entity == r.get("to") and x.relationType == r.get("relationType"))]
        if len(graph.relations) < before:
            deleted.append(f"{r.get('from')} -{r.get('relationType')}-> {r.get('to')}")
    graph._save()
    return {"deleted": deleted, "count": len(deleted)}


def _memory_delete_observations(entityName: str, observations: list) -> dict:
    graph = get_graph()
    if entityName not in graph.entities:
        return {"error": f"Entity not found: {entityName}"}
    entity = graph.entities[entityName]
    deleted = []
    for obs in observations:
        if obs in entity.observations:
            entity.observations.remove(obs)
            deleted.append(obs)
    graph._save()
    return {"entity": entityName, "deleted": deleted, "remaining": len(entity.observations)}


def _memory_read_graph() -> dict:
    graph = get_graph()
    return {
        "entities": [{"name": e.name, "entityType": e.entityType, "observations": e.observations} for e in graph.entities.values()],
        "relations": [{"from": r.from_entity, "to": r.to_entity, "relationType": r.relationType} for r in graph.relations],
        "stats": {"entity_count": len(graph.entities), "relation_count": len(graph.relations)}
    }


def _memory_search_nodes(query: str) -> dict:
    graph = get_graph()
    query_lower = query.lower()
    matches = []
    for entity in graph.entities.values():
        score = 0
        if query_lower in entity.name.lower():
            score += 10
        if query_lower in entity.entityType.lower():
            score += 5
        for obs in entity.observations:
            if query_lower in obs.lower():
                score += 2
        if score > 0:
            matches.append({"name": entity.name, "entityType": entity.entityType, "observations": entity.observations, "score": score})
    matches.sort(key=lambda x: x["score"], reverse=True)
    return {"query": query, "matches": matches, "count": len(matches)}


def _memory_open_nodes(names: list) -> dict:
    graph = get_graph()
    found, not_found = [], []
    for name in names:
        if name in graph.entities:
            e = graph.entities[name]
            found.append({"name": e.name, "entityType": e.entityType, "observations": e.observations})
        else:
            not_found.append(name)
    found_names = {f["name"] for f in found}
    relations = [{"from": r.from_entity, "to": r.to_entity, "relationType": r.relationType} for r in graph.relations if r.from_entity in found_names and r.to_entity in found_names]
    return {"entities": found, "relations": relations, "not_found": not_found}


# =============================================================================
# THINKING_MCP - Core Classes and Functions
# =============================================================================

@dataclass
class Thought:
    number: int
    content: str
    total_thoughts: int
    next_action: str
    flags: list = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ThinkingSession:
    def __init__(self):
        self.thoughts: list = []
        self.branches: dict = {}
        self.started_at: str = None
        self.problem: str = None

    def reset(self):
        self.thoughts = []
        self.branches = {}
        self.started_at = None
        self.problem = None


_session: Optional[ThinkingSession] = None


def get_session() -> ThinkingSession:
    global _session
    if _session is None:
        _session = ThinkingSession()
    return _session


def reset_session():
    global _session
    if _session:
        _session.reset()
    _session = None


def _thinking_sequentialthinking(thought: str, thoughtNumber: int, totalThoughts: int, nextThoughtNeeded: bool,
                                  isRevision: bool = False, revisesThought: int = None, branchFromThought: int = None,
                                  branchId: str = None, needsMoreThoughts: bool = False) -> dict:
    session = get_session()
    if thoughtNumber == 1 and not session.problem:
        session.started_at = datetime.now(timezone.utc).isoformat()
        session.problem = thought[:100]
    flags = []
    if isRevision and revisesThought:
        flags.append(f"🔄 Revision of #{revisesThought}")
    if branchFromThought:
        flags.append(f"🌿 Branch {branchId or 'A'} from #{branchFromThought}")
    next_action = "conclude" if not nextThoughtNeeded else "continue"
    if isRevision:
        next_action = "revise"
    elif branchFromThought:
        next_action = "branch"
    if not nextThoughtNeeded:
        flags.append("✓ CONCLUSION")
    t = Thought(number=thoughtNumber, content=thought, total_thoughts=totalThoughts, next_action=next_action, flags=flags)
    if branchId and branchId != "main":
        if branchId not in session.branches:
            session.branches[branchId] = []
        session.branches[branchId].append(t)
    else:
        session.thoughts.append(t)
    result = {"thought_number": thoughtNumber, "total_thoughts": totalThoughts, "flags": flags, "next_action": next_action, "nextThoughtNeeded": nextThoughtNeeded, "recorded": True}
    if not nextThoughtNeeded:
        result["session_summary"] = {"problem": session.problem, "total_thoughts": len(session.thoughts), "branches": list(session.branches.keys())}
    return result


def _thinking_get_thinking_chain() -> dict:
    session = get_session()
    return {
        "problem": session.problem, "started_at": session.started_at,
        "thoughts": [{"number": t.number, "content": t.content[:200], "flags": t.flags} for t in session.thoughts],
        "branches": {k: len(v) for k, v in session.branches.items()}, "count": len(session.thoughts)
    }


def _thinking_reset_thinking() -> dict:
    reset_session()
    return {"status": "reset", "timestamp": datetime.now(timezone.utc).isoformat()}


# =============================================================================
# TODO_MCP - Core Classes and Functions
# =============================================================================

@dataclass
class Todo:
    id: str
    title: str
    status: str = "pending"
    priority: str = "P1"
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: str = None
    description: str = None
    blockers: list = field(default_factory=list)
    tags: list = field(default_factory=list)


class TodoManager:
    def __init__(self, file_path: str = None):
        self.file_path = file_path or os.getenv("TODO_FILE_PATH", os.path.expanduser("~/.claude/todos.json"))
        self.todos: dict = {}
        self._load()

    def _load(self):
        path = Path(self.file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("todos", []):
                    self.todos[item["id"]] = Todo(**item)
        except Exception:
            pass

    def _save(self):
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({"todos": [asdict(t) for t in self.todos.values()], "updated_at": datetime.now(timezone.utc).isoformat()}, f, indent=2)

    def reset(self):
        self.todos = {}
        if Path(self.file_path).exists():
            Path(self.file_path).unlink()


_manager: Optional[TodoManager] = None


def get_manager() -> TodoManager:
    global _manager
    if _manager is None:
        _manager = TodoManager()
    return _manager


def reset_manager():
    global _manager
    if _manager:
        _manager.reset()
    _manager = None


def _todo_create_todo(title: str, priority: str = "P1", description: str = None, tags: list = None) -> dict:
    mgr = get_manager()
    todo_id = f"TODO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    t = Todo(id=todo_id, title=title, priority=priority, description=description, tags=tags or [])
    mgr.todos[todo_id] = t
    mgr._save()
    return {"created": asdict(t)}


def _todo_list_todos(status: str = None, priority: str = None) -> dict:
    mgr = get_manager()
    results = list(mgr.todos.values())
    if status:
        results = [t for t in results if t.status == status]
    if priority:
        results = [t for t in results if t.priority == priority]
    priority_order = {"P0": 0, "P1": 1, "P2": 2}
    results.sort(key=lambda x: (priority_order.get(x.priority, 9), x.created_at))
    return {
        "todos": [asdict(t) for t in results], "count": len(results),
        "by_status": {s: len([t for t in mgr.todos.values() if t.status == s]) for s in ["pending", "in_progress", "blocked", "complete", "failed"]}
    }


def _todo_update_todo(todoId: str, title: str = None, status: str = None, priority: str = None,
                      description: str = None, blockers: list = None, tags: list = None) -> dict:
    mgr = get_manager()
    if todoId not in mgr.todos:
        return {"error": f"Todo not found: {todoId}"}
    t = mgr.todos[todoId]
    if title is not None:
        t.title = title
    if status is not None:
        t.status = status
    if priority is not None:
        t.priority = priority
    if description is not None:
        t.description = description
    if blockers is not None:
        t.blockers = blockers
    if tags is not None:
        t.tags = tags
    t.updated_at = datetime.now(timezone.utc).isoformat()
    mgr._save()
    return {"updated": asdict(t)}


def _todo_complete_todo(todoId: str) -> dict:
    mgr = get_manager()
    if todoId not in mgr.todos:
        return {"error": f"Todo not found: {todoId}"}
    t = mgr.todos[todoId]
    t.status = "complete"
    t.completed_at = datetime.now(timezone.utc).isoformat()
    t.updated_at = t.completed_at
    mgr._save()
    return {"completed": asdict(t)}


def _todo_delete_todo(todoId: str) -> dict:
    mgr = get_manager()
    if todoId not in mgr.todos:
        return {"error": f"Todo not found: {todoId}"}
    deleted = mgr.todos.pop(todoId)
    mgr._save()
    return {"deleted": asdict(deleted)}


# =============================================================================
# MCP TOOL REGISTRATIONS (25 tools)
# =============================================================================

# FILESYSTEM_MCP (8)
@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-ping")
def filesystem_ping() -> dict:
    """Test connectivity."""
    return _filesystem_ping()

@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-get_status")
def filesystem_get_status() -> dict:
    """Get platform status."""
    return _filesystem_get_status()

@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-read_file")
def filesystem_read_file(path: str) -> dict:
    """Read file contents."""
    return _filesystem_read_file(path)

@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-write_file")
def filesystem_write_file(path: str, content: str, append: bool = False) -> dict:
    """Write or append to file."""
    return _filesystem_write_file(path, content, append)

@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-list_directory")
def filesystem_list_directory(path: str, max_depth: int = 2) -> dict:
    """List directory contents."""
    return _filesystem_list_directory(path, max_depth)

@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-exec_command")
def filesystem_exec_command(command: str, cwd: str = None, timeout: int = 30) -> dict:
    """Execute shell command."""
    return _filesystem_exec_command(command, cwd, timeout)

@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-grep")
def filesystem_grep(path: str, pattern: str, recursive: bool = True) -> dict:
    """Search for pattern in files."""
    return _filesystem_grep(path, pattern, recursive)

@mcp.tool(name="cloud_agent_mcp-filesystem_mcp-glob_files")
def filesystem_glob_files(path: str, pattern: str) -> dict:
    """Find files matching glob pattern."""
    return _filesystem_glob_files(path, pattern)


# MEMORY_MCP (9)
@mcp.tool(name="cloud_agent_mcp-memory_mcp-create_entities")
def memory_create_entities(entities: list) -> dict:
    """Create entities in knowledge graph."""
    return _memory_create_entities(entities)

@mcp.tool(name="cloud_agent_mcp-memory_mcp-create_relations")
def memory_create_relations(relations: list) -> dict:
    """Create relations between entities."""
    return _memory_create_relations(relations)

@mcp.tool(name="cloud_agent_mcp-memory_mcp-add_observations")
def memory_add_observations(entityName: str, observations: list) -> dict:
    """Add observations to entity."""
    return _memory_add_observations(entityName, observations)

@mcp.tool(name="cloud_agent_mcp-memory_mcp-delete_entities")
def memory_delete_entities(entityNames: list) -> dict:
    """Delete entities and their relations."""
    return _memory_delete_entities(entityNames)

@mcp.tool(name="cloud_agent_mcp-memory_mcp-delete_relations")
def memory_delete_relations(relations: list) -> dict:
    """Delete specific relations."""
    return _memory_delete_relations(relations)

@mcp.tool(name="cloud_agent_mcp-memory_mcp-delete_observations")
def memory_delete_observations(entityName: str, observations: list) -> dict:
    """Delete observations from entity."""
    return _memory_delete_observations(entityName, observations)

@mcp.tool(name="cloud_agent_mcp-memory_mcp-read_graph")
def memory_read_graph() -> dict:
    """Return complete knowledge graph."""
    return _memory_read_graph()

@mcp.tool(name="cloud_agent_mcp-memory_mcp-search_nodes")
def memory_search_nodes(query: str) -> dict:
    """Search entities by name, type, or observation."""
    return _memory_search_nodes(query)

@mcp.tool(name="cloud_agent_mcp-memory_mcp-open_nodes")
def memory_open_nodes(names: list) -> dict:
    """Retrieve specific entities by name."""
    return _memory_open_nodes(names)


# THINKING_MCP (3)
@mcp.tool(name="cloud_agent_mcp-thinking_mcp-sequentialthinking")
def thinking_sequentialthinking(thought: str, thoughtNumber: int, totalThoughts: int, nextThoughtNeeded: bool,
                                 isRevision: bool = False, revisesThought: int = None, branchFromThought: int = None,
                                 branchId: str = None, needsMoreThoughts: bool = False) -> dict:
    """Process thought in sequential chain."""
    return _thinking_sequentialthinking(thought, thoughtNumber, totalThoughts, nextThoughtNeeded, isRevision, revisesThought, branchFromThought, branchId, needsMoreThoughts)

@mcp.tool(name="cloud_agent_mcp-thinking_mcp-get_thinking_chain")
def thinking_get_thinking_chain() -> dict:
    """Get current thinking chain."""
    return _thinking_get_thinking_chain()

@mcp.tool(name="cloud_agent_mcp-thinking_mcp-reset_thinking")
def thinking_reset_thinking() -> dict:
    """Reset thinking session."""
    return _thinking_reset_thinking()


# TODO_MCP (5)
@mcp.tool(name="cloud_agent_mcp-todo_mcp-create_todo")
def todo_create_todo(title: str, priority: str = "P1", description: str = None, tags: list = None) -> dict:
    """Create new todo."""
    return _todo_create_todo(title, priority, description, tags)

@mcp.tool(name="cloud_agent_mcp-todo_mcp-list_todos")
def todo_list_todos(status: str = None, priority: str = None) -> dict:
    """List todos with filters."""
    return _todo_list_todos(status, priority)

@mcp.tool(name="cloud_agent_mcp-todo_mcp-update_todo")
def todo_update_todo(todoId: str, title: str = None, status: str = None, priority: str = None,
                     description: str = None, blockers: list = None, tags: list = None) -> dict:
    """Update todo fields."""
    return _todo_update_todo(todoId, title, status, priority, description, blockers, tags)

@mcp.tool(name="cloud_agent_mcp-todo_mcp-complete_todo")
def todo_complete_todo(todoId: str) -> dict:
    """Mark todo complete."""
    return _todo_complete_todo(todoId)

@mcp.tool(name="cloud_agent_mcp-todo_mcp-delete_todo")
def todo_delete_todo(todoId: str) -> dict:
    """Delete todo."""
    return _todo_delete_todo(todoId)


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Cloud Agent MCP Server")
    parser.add_argument("--sse", action="store_true")
    parser.add_argument("--http", action="store_true")
    args = parser.parse_args()
    if args.sse:
        mcp.run(transport="sse", host=HOST, port=PORT)
    elif args.http:
        mcp.run(transport="http", host=HOST, port=PORT)
    else:
        mcp.run()
