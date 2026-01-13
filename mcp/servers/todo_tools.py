"""
Todo Management Tools for Cloud Agent MCP.
Implements task tracking with JSON persistence.

Tools:
- create_todo, list_todos, update_todo, complete_todo, delete_todo
"""

import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict
import uuid


@dataclass
class Todo:
    """Task item."""
    id: str
    title: str
    status: str = "pending"  # pending, in_progress, blocked, complete, failed
    priority: str = "P1"  # P0, P1, P2
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None
    description: Optional[str] = None
    blockers: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)


class TodoManager:
    """Manages todo list with file persistence."""
    
    def __init__(self, file_path: str = None):
        self.file_path = file_path or os.getenv(
            "TODO_FILE_PATH",
            os.path.expanduser("~/.claude/todos.json")
        )
        self.todos: dict[str, Todo] = {}
        self._load()
    
    def _load(self):
        """Load todos from JSON file."""
        path = Path(self.file_path)
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            return
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("todos", []):
                    t = Todo(
                        id=item["id"],
                        title=item["title"],
                        status=item.get("status", "pending"),
                        priority=item.get("priority", "P1"),
                        created_at=item.get("created_at", ""),
                        updated_at=item.get("updated_at", ""),
                        completed_at=item.get("completed_at"),
                        description=item.get("description"),
                        blockers=item.get("blockers", []),
                        tags=item.get("tags", [])
                    )
                    self.todos[t.id] = t
        except Exception as e:
            print(f"Error loading todos: {e}")
    
    def _save(self):
        """Persist todos to JSON file."""
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({
                "todos": [asdict(t) for t in self.todos.values()],
                "updated_at": datetime.now(timezone.utc).isoformat()
            }, f, indent=2)
    
    def create(self, title: str, priority: str = "P1", description: str = None, tags: list[str] = None) -> dict:
        """Create new todo."""
        todo_id = f"TODO-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
        t = Todo(
            id=todo_id,
            title=title,
            priority=priority,
            description=description,
            tags=tags or []
        )
        self.todos[todo_id] = t
        self._save()
        return {"created": asdict(t)}
    
    def list_all(self, status: str = None, priority: str = None) -> dict:
        """List todos with optional filters."""
        results = list(self.todos.values())
        
        if status:
            results = [t for t in results if t.status == status]
        if priority:
            results = [t for t in results if t.priority == priority]
        
        # Sort by priority then created_at
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        results.sort(key=lambda x: (priority_order.get(x.priority, 9), x.created_at))
        
        return {
            "todos": [asdict(t) for t in results],
            "count": len(results),
            "by_status": {
                s: len([t for t in self.todos.values() if t.status == s])
                for s in ["pending", "in_progress", "blocked", "complete", "failed"]
            }
        }
    
    def update(self, todo_id: str, **kwargs) -> dict:
        """Update todo fields."""
        if todo_id not in self.todos:
            return {"error": f"Todo not found: {todo_id}"}
        
        t = self.todos[todo_id]
        for key, value in kwargs.items():
            if hasattr(t, key) and value is not None:
                setattr(t, key, value)
        t.updated_at = datetime.now(timezone.utc).isoformat()
        self._save()
        return {"updated": asdict(t)}
    
    def complete(self, todo_id: str) -> dict:
        """Mark todo as complete."""
        if todo_id not in self.todos:
            return {"error": f"Todo not found: {todo_id}"}
        
        t = self.todos[todo_id]
        t.status = "complete"
        t.completed_at = datetime.now(timezone.utc).isoformat()
        t.updated_at = t.completed_at
        self._save()
        return {"completed": asdict(t)}
    
    def delete(self, todo_id: str) -> dict:
        """Delete todo."""
        if todo_id not in self.todos:
            return {"error": f"Todo not found: {todo_id}"}
        
        deleted = self.todos.pop(todo_id)
        self._save()
        return {"deleted": asdict(deleted)}


# Global instance
_manager: Optional[TodoManager] = None


def get_manager() -> TodoManager:
    """Get or create global todo manager."""
    global _manager
    if _manager is None:
        _manager = TodoManager()
    return _manager


def register_todo_tools(mcp):
    """Register todo tools with FastMCP server."""
    
    @mcp.tool()
    def create_todo(title: str, priority: str = "P1", description: str = None, tags: list[str] = None) -> dict:
        """Create a new todo item.
        
        Args:
            title: Task title
            priority: P0 (critical), P1 (high), P2 (normal)
            description: Optional details
            tags: Optional list of tags
        """
        return get_manager().create(title, priority, description, tags)
    
    @mcp.tool()
    def list_todos(status: str = None, priority: str = None) -> dict:
        """List todos with optional filters.
        
        Args:
            status: Filter by status (pending, in_progress, blocked, complete, failed)
            priority: Filter by priority (P0, P1, P2)
        """
        return get_manager().list_all(status, priority)
    
    @mcp.tool()
    def update_todo(
        todoId: str,
        title: str = None,
        status: str = None,
        priority: str = None,
        description: str = None,
        blockers: list[str] = None,
        tags: list[str] = None
    ) -> dict:
        """Update todo fields.
        
        Args:
            todoId: ID of todo to update
            title: New title
            status: New status
            priority: New priority
            description: New description
            blockers: List of blockers
            tags: List of tags
        """
        return get_manager().update(
            todoId,
            title=title,
            status=status,
            priority=priority,
            description=description,
            blockers=blockers,
            tags=tags
        )
    
    @mcp.tool()
    def complete_todo(todoId: str) -> dict:
        """Mark todo as complete.
        
        Args:
            todoId: ID of todo to complete
        """
        return get_manager().complete(todoId)
    
    @mcp.tool()
    def delete_todo(todoId: str) -> dict:
        """Delete a todo.
        
        Args:
            todoId: ID of todo to delete
        """
        return get_manager().delete(todoId)
