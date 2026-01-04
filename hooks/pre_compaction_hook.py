#!/usr/bin/env python3
"""
Pre-Compaction Hook - Exports chat history and validates state before context compaction.

Installation: ~/.claude/hooks/pre_compaction_hook.py

Triggers:
  - Claude Code compaction event
  - Manual invocation
  - Context threshold (80% by default)

Actions:
  1. Run quality gate on current stage
  2. Export chat history to CSV (36 columns)
  3. Archive todos and evidence
  4. Store handoff context for continuation
  5. Update memory with session summary

Usage:
  # Auto-trigger on compaction
  COMPACTION_THRESHOLD=0.8 python pre_compaction_hook.py --auto
  
  # Manual export
  python pre_compaction_hook.py --export --output ./exports/

  # Force export regardless of threshold
  python pre_compaction_hook.py --force --tokens 180000

Environment:
  COMPACTION_THRESHOLD=0.8     # Trigger at 80% context
  MAX_CONTEXT_TOKENS=200000    # Context window size
  CHAT_EXPORT_DIR=~/.claude/exports
  WORKFLOW_DIR=.workflow
"""

import csv
import json
import os
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
import argparse
import hashlib


# CSV Schema (36 columns from chat-export skill)
CSV_COLUMNS = [
    "timestamp", "duration_seconds", "response_time_ms", "session_start", "elapsed_from_start",
    "role", "agent_model", "agent_persona", "user_id", "session_id", "chat_id", "message",
    "message_type", "word_count", "token_count", "language", "tools_invoked", "tool_count",
    "mcp_servers_used", "files_created", "files_modified", "workflow_stage", "todo_ids",
    "parent_message_id", "thread_depth", "contains_code", "contains_evidence", "violations",
    "u1_u8_compliance", "compaction_occurred", "context_tokens_used", "attachments",
    "references", "action_taken", "user_approved", "requires_followup", "blockers"
]


class PreCompactionHook:
    """Handles pre-compaction export and validation."""
    
    def __init__(
        self,
        workflow_dir: Optional[Path] = None,
        export_dir: Optional[Path] = None,
        threshold: float = 0.8,
        max_tokens: int = 200000
    ):
        self.workflow_dir = workflow_dir or Path(os.environ.get("WORKFLOW_DIR", ".workflow"))
        self.export_dir = export_dir or Path(os.environ.get("CHAT_EXPORT_DIR", Path.home() / ".claude" / "exports"))
        self.threshold = threshold
        self.max_tokens = max_tokens
        
        self.timestamp = datetime.now(timezone.utc)
        self.export_id = self.timestamp.strftime("%Y%m%d_%H%M%S")
    
    def _log(self, message: str, level: str = "INFO") -> None:
        """Log message."""
        ts = datetime.now(timezone.utc).isoformat()
        log_entry = f"[{ts}] [COMPACTION] [{level}] {message}"
        print(log_entry)
        
        log_path = self.workflow_dir / "logs" / "compaction.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with open(log_path, "a") as f:
            f.write(log_entry + "\n")
    
    def should_export(self, current_tokens: Optional[int] = None) -> bool:
        """Check if export should trigger based on token count."""
        if current_tokens is None:
            # Try to read from environment or state
            current_tokens = int(os.environ.get("CONTEXT_TOKENS_USED", 0))
        
        if current_tokens == 0:
            return False
        
        ratio = current_tokens / self.max_tokens
        self._log(f"Context usage: {current_tokens}/{self.max_tokens} ({ratio:.1%})")
        
        return ratio >= self.threshold
    
    def run_quality_gate(self) -> dict:
        """Run quality gate before compaction."""
        self._log("Running pre-compaction quality gate...")
        
        # Import and run quality gate
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from reprompt_timer import RepromptTimer
            
            timer = RepromptTimer(workflow_dir=self.workflow_dir)
            result = timer.check()
            
            if result:
                return result.to_dict()
            return {"status": "no_check_needed"}
        except Exception as e:
            self._log(f"Quality gate failed: {e}", "ERROR")
            return {"status": "error", "error": str(e)}
    
    def export_chat_history(self, messages: Optional[list] = None) -> Path:
        """Export chat history to CSV."""
        self._log("Exporting chat history...")
        
        export_path = self.export_dir / self.export_id
        export_path.mkdir(parents=True, exist_ok=True)
        
        # If no messages provided, try to load from workflow
        if messages is None:
            messages = self._load_messages_from_workflow()
        
        # Write combined CSV
        combined_csv = export_path / "combined_messages.csv"
        with open(combined_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            
            for msg in messages:
                row = self._message_to_row(msg)
                writer.writerow(row)
        
        # Write user-only CSV
        user_csv = export_path / "user_messages.csv"
        with open(user_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            
            for msg in messages:
                if msg.get("role") == "user":
                    writer.writerow(self._message_to_row(msg))
        
        # Write agent-only CSV
        agent_csv = export_path / "agent_messages.csv"
        with open(agent_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
            writer.writeheader()
            
            for msg in messages:
                if msg.get("role") == "assistant":
                    writer.writerow(self._message_to_row(msg))
        
        self._log(f"Exported {len(messages)} messages to {export_path}")
        return export_path
    
    def _load_messages_from_workflow(self) -> list:
        """Load messages from workflow logs."""
        messages = []
        
        # Try to load from various sources
        sources = [
            self.workflow_dir / "logs" / "messages.json",
            self.workflow_dir / "logs" / "chat_history.json",
            Path.home() / ".config" / "superpowers" / "conversation-archive" / "current.json"
        ]
        
        for source in sources:
            if source.exists():
                try:
                    with open(source) as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            messages.extend(data)
                        elif isinstance(data, dict) and "messages" in data:
                            messages.extend(data["messages"])
                except Exception:
                    pass
        
        return messages
    
    def _message_to_row(self, msg: dict) -> dict:
        """Convert message to CSV row."""
        content = msg.get("content", "")
        if isinstance(content, list):
            # Handle structured content
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        
        return {
            "timestamp": msg.get("timestamp", self.timestamp.isoformat()),
            "duration_seconds": msg.get("duration_seconds", 0),
            "response_time_ms": msg.get("response_time_ms", 0),
            "session_start": msg.get("session_start", ""),
            "elapsed_from_start": msg.get("elapsed_from_start", 0),
            "role": msg.get("role", "unknown"),
            "agent_model": msg.get("model", os.environ.get("AGENT_MODEL", "")),
            "agent_persona": msg.get("persona", ""),
            "user_id": msg.get("user_id", ""),
            "session_id": msg.get("session_id", os.environ.get("SESSION_ID", "")),
            "chat_id": msg.get("chat_id", ""),
            "message": content[:10000],  # Truncate very long messages
            "message_type": msg.get("type", "text"),
            "word_count": len(content.split()),
            "token_count": msg.get("token_count", len(content) // 4),  # Rough estimate
            "language": msg.get("language", "en"),
            "tools_invoked": json.dumps(msg.get("tools", [])),
            "tool_count": len(msg.get("tools", [])),
            "mcp_servers_used": json.dumps(msg.get("mcp_servers", [])),
            "files_created": json.dumps(msg.get("files_created", [])),
            "files_modified": json.dumps(msg.get("files_modified", [])),
            "workflow_stage": msg.get("workflow_stage", ""),
            "todo_ids": json.dumps(msg.get("todo_ids", [])),
            "parent_message_id": msg.get("parent_id", ""),
            "thread_depth": msg.get("thread_depth", 0),
            "contains_code": "```" in content,
            "contains_evidence": "evidence" in content.lower() or "E-" in content,
            "violations": json.dumps(msg.get("violations", [])),
            "u1_u8_compliance": msg.get("compliance", ""),
            "compaction_occurred": True,
            "context_tokens_used": msg.get("context_tokens", 0),
            "attachments": json.dumps(msg.get("attachments", [])),
            "references": json.dumps(msg.get("references", [])),
            "action_taken": msg.get("action", ""),
            "user_approved": msg.get("approved", ""),
            "requires_followup": msg.get("requires_followup", False),
            "blockers": json.dumps(msg.get("blockers", []))
        }
    
    def archive_workflow(self) -> Path:
        """Archive current workflow state."""
        self._log("Archiving workflow state...")
        
        archive_path = self.export_dir / self.export_id / "workflow_archive.zip"
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Archive all workflow files
            if self.workflow_dir.exists():
                for file_path in self.workflow_dir.rglob("*"):
                    if file_path.is_file():
                        arcname = file_path.relative_to(self.workflow_dir.parent)
                        zf.write(file_path, arcname)
        
        self._log(f"Archived workflow to {archive_path}")
        return archive_path
    
    def create_handoff(self) -> dict:
        """Create handoff context for continuation after compaction."""
        self._log("Creating handoff context...")
        
        # Load current state
        state_path = self.workflow_dir / "state" / "current.json"
        state = {}
        if state_path.exists():
            with open(state_path) as f:
                state = json.load(f)
        
        # Load todos
        todos_path = self.workflow_dir / "todo" / "todos.json"
        todos = []
        if todos_path.exists():
            with open(todos_path) as f:
                todos = json.load(f)
        
        # Load evidence
        evidence = []
        evidence_dir = self.workflow_dir / "evidence"
        if evidence_dir.exists():
            for file_path in evidence_dir.glob("*.json"):
                with open(file_path) as f:
                    evidence.append(json.load(f))
        
        # Create handoff
        handoff = {
            "handoff": {
                "from_agent": os.environ.get("AGENT_ID", "Sonnet"),
                "to_agent": "continuation",
                "timestamp": self.timestamp.isoformat(),
                "context": {
                    "user_objective": state.get("user_objective", ""),
                    "current_stage": state.get("current_stage", "PLAN"),
                    "completed_stages": state.get("completed_stages", []),
                    "todos_remaining": [t for t in todos if t.get("status") != "completed"],
                    "evidence_collected": [e.get("evidence", {}).get("id") for e in evidence if "evidence" in e],
                    "blockers": [],
                    "assumptions": [],
                    "memory_refs": [f"compaction_{self.export_id}"]
                },
                "instructions": "Continue from compaction point. Review archived state before proceeding.",
                "expected_output": f"Complete {state.get('current_stage', 'PLAN')} stage",
                "archive_location": str(self.export_dir / self.export_id)
            }
        }
        
        # Save handoff
        handoff_path = self.export_dir / self.export_id / "handoff.json"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        with open(handoff_path, "w") as f:
            json.dump(handoff, f, indent=2)
        
        self._log(f"Created handoff at {handoff_path}")
        return handoff
    
    def update_memory(self) -> None:
        """Update memory with session summary."""
        self._log("Updating memory with session summary...")
        
        summary = {
            "event": "compaction",
            "timestamp": self.timestamp.isoformat(),
            "export_id": self.export_id,
            "export_location": str(self.export_dir / self.export_id),
            "workflow_dir": str(self.workflow_dir),
        }
        
        # In real impl, would call memory MCP
        # CALL memory/write {key: f"compaction_{self.export_id}", value: summary}
        
        # Save locally
        memory_path = self.export_dir / self.export_id / "memory_update.json"
        with open(memory_path, "w") as f:
            json.dump(summary, f, indent=2)
    
    def create_manifest(self) -> Path:
        """Create export manifest."""
        manifest = {
            "export_id": self.export_id,
            "timestamp": self.timestamp.isoformat(),
            "workflow_dir": str(self.workflow_dir),
            "export_dir": str(self.export_dir / self.export_id),
            "files": [
                "combined_messages.csv",
                "user_messages.csv",
                "agent_messages.csv",
                "workflow_archive.zip",
                "handoff.json",
                "memory_update.json",
                "manifest.json"
            ],
            "checksums": {}
        }
        
        # Calculate checksums
        export_path = self.export_dir / self.export_id
        for filename in manifest["files"]:
            file_path = export_path / filename
            if file_path.exists():
                with open(file_path, "rb") as f:
                    manifest["checksums"][filename] = hashlib.sha256(f.read()).hexdigest()
        
        manifest_path = export_path / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        return manifest_path
    
    def run_full_export(self, force: bool = False, current_tokens: Optional[int] = None) -> dict:
        """Run full pre-compaction export."""
        result = {
            "export_id": self.export_id,
            "timestamp": self.timestamp.isoformat(),
            "triggered": False,
            "quality_gate": None,
            "export_path": None,
            "archive_path": None,
            "handoff": None,
            "errors": []
        }
        
        # Check if export should trigger
        if not force and not self.should_export(current_tokens):
            self._log("Export not triggered (below threshold)")
            return result
        
        result["triggered"] = True
        self._log("=" * 60)
        self._log("PRE-COMPACTION EXPORT STARTING")
        self._log("=" * 60)
        
        try:
            # 1. Run quality gate
            result["quality_gate"] = self.run_quality_gate()
            
            # 2. Export chat history
            result["export_path"] = str(self.export_chat_history())
            
            # 3. Archive workflow
            result["archive_path"] = str(self.archive_workflow())
            
            # 4. Create handoff
            result["handoff"] = self.create_handoff()
            
            # 5. Update memory
            self.update_memory()
            
            # 6. Create manifest
            self.create_manifest()
            
            self._log("=" * 60)
            self._log("PRE-COMPACTION EXPORT COMPLETE")
            self._log(f"Export location: {self.export_dir / self.export_id}")
            self._log("=" * 60)
            
        except Exception as e:
            self._log(f"Export failed: {e}", "ERROR")
            result["errors"].append(str(e))
        
        return result


def main():
    parser = argparse.ArgumentParser(description="Pre-Compaction Hook")
    parser.add_argument("--auto", action="store_true", help="Auto-trigger based on threshold")
    parser.add_argument("--export", action="store_true", help="Run full export")
    parser.add_argument("--force", action="store_true", help="Force export regardless of threshold")
    parser.add_argument("--tokens", type=int, help="Current token count")
    parser.add_argument("--output", type=Path, help="Output directory")
    parser.add_argument("--workflow-dir", type=Path, help="Workflow directory")
    parser.add_argument("--threshold", type=float, default=0.8, help="Trigger threshold (0-1)")
    args = parser.parse_args()
    
    hook = PreCompactionHook(
        workflow_dir=args.workflow_dir,
        export_dir=args.output,
        threshold=args.threshold
    )
    
    if args.auto or args.export:
        result = hook.run_full_export(force=args.force, current_tokens=args.tokens)
        print(json.dumps(result, indent=2, default=str))
        return 0 if not result["errors"] else 1
    
    # Default: check if should export
    if hook.should_export(args.tokens):
        print("Export recommended")
        return 0
    else:
        print("Export not needed")
        return 0


if __name__ == "__main__":
    sys.exit(main())
