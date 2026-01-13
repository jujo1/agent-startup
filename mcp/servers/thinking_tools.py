"""
Sequential Thinking Tools for Cloud Agent MCP.
Implements structured thought chain management for complex reasoning.

Tools:
- sequential_think: Process a single thought in a chain
"""

from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field


@dataclass
class Thought:
    """Single thought in reasoning chain."""
    number: int
    content: str
    total_thoughts: int
    next_action: str  # continue, revise, branch, conclude
    flags: list[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    revision_of: Optional[int] = None
    branch_from: Optional[int] = None
    branch_id: Optional[str] = None


class ThinkingSession:
    """Manages a sequential thinking session."""
    
    def __init__(self):
        self.thoughts: list[Thought] = []
        self.branches: dict[str, list[Thought]] = {}
        self.current_branch: Optional[str] = None
        self.started_at: Optional[str] = None
        self.problem: Optional[str] = None
    
    def start(self, problem: str, total_thoughts: int) -> dict:
        """Initialize thinking session."""
        self.thoughts = []
        self.branches = {}
        self.current_branch = None
        self.started_at = datetime.now(timezone.utc).isoformat()
        self.problem = problem
        
        return {
            "status": "started",
            "problem": problem,
            "total_thoughts": total_thoughts,
            "started_at": self.started_at
        }
    
    def add_thought(
        self,
        thought: str,
        thought_number: int,
        total_thoughts: int,
        next_action: str,
        revision_of: Optional[int] = None,
        branch_from: Optional[int] = None,
        branch_id: Optional[str] = None
    ) -> dict:
        """Add a thought to the chain."""
        
        # Build flags
        flags = []
        if revision_of:
            flags.append(f"🔄 Revision of #{revision_of}")
        if branch_from:
            flags.append(f"🌿 Branch {branch_id or 'A'} from #{branch_from}")
        if next_action == "conclude":
            flags.append("✓ CONCLUSION")
        
        t = Thought(
            number=thought_number,
            content=thought,
            total_thoughts=total_thoughts,
            next_action=next_action,
            flags=flags,
            revision_of=revision_of,
            branch_from=branch_from,
            branch_id=branch_id
        )
        
        # Store in appropriate location
        if branch_id and branch_id != "main":
            if branch_id not in self.branches:
                self.branches[branch_id] = []
            self.branches[branch_id].append(t)
        else:
            self.thoughts.append(t)
        
        response = {
            "thought_number": thought_number,
            "total_thoughts": total_thoughts,
            "flags": flags,
            "next_action": next_action,
            "recorded": True
        }
        
        # Add summary on conclusion
        if next_action == "conclude":
            response["session_summary"] = {
                "problem": self.problem,
                "total_thoughts": len(self.thoughts),
                "branches": list(self.branches.keys()),
                "duration_thoughts": thought_number
            }
        
        return response
    
    def get_chain(self) -> dict:
        """Get current thought chain."""
        return {
            "problem": self.problem,
            "started_at": self.started_at,
            "thoughts": [
                {
                    "number": t.number,
                    "content": t.content[:200] + "..." if len(t.content) > 200 else t.content,
                    "flags": t.flags,
                    "next_action": t.next_action
                }
                for t in self.thoughts
            ],
            "branches": {
                k: [{"number": t.number, "content": t.content[:100]} for t in v]
                for k, v in self.branches.items()
            },
            "count": len(self.thoughts)
        }


# Global session
_session: Optional[ThinkingSession] = None


def get_session() -> ThinkingSession:
    """Get or create global thinking session."""
    global _session
    if _session is None:
        _session = ThinkingSession()
    return _session


def register_thinking_tools(mcp):
    """Register sequential thinking tools with FastMCP server."""
    
    @mcp.tool()
    def sequentialthinking(
        thought: str,
        thoughtNumber: int,
        totalThoughts: int,
        nextThoughtNeeded: bool,
        isRevision: bool = False,
        revisesThought: Optional[int] = None,
        branchFromThought: Optional[int] = None,
        branchId: Optional[str] = None,
        needsMoreThoughts: bool = False
    ) -> dict:
        """Process a single thought in sequential reasoning chain.
        
        Args:
            thought: Content of current thought
            thoughtNumber: Current thought number (1-indexed)
            totalThoughts: Estimated total thoughts needed
            nextThoughtNeeded: Whether more thoughts are needed
            isRevision: Whether this revises a previous thought
            revisesThought: Which thought number this revises
            branchFromThought: Which thought to branch from
            branchId: Identifier for this branch
            needsMoreThoughts: Whether to extend total
        """
        session = get_session()
        
        # Start session on first thought
        if thoughtNumber == 1 and not session.problem:
            session.start(thought[:100], totalThoughts)
        
        # Determine next action
        if not nextThoughtNeeded:
            next_action = "conclude"
        elif isRevision:
            next_action = "revise"
        elif branchFromThought:
            next_action = "branch"
        else:
            next_action = "continue"
        
        # Update total if extending
        if needsMoreThoughts:
            totalThoughts = max(totalThoughts, thoughtNumber + 2)
        
        result = session.add_thought(
            thought=thought,
            thought_number=thoughtNumber,
            total_thoughts=totalThoughts,
            next_action=next_action,
            revision_of=revisesThought if isRevision else None,
            branch_from=branchFromThought,
            branch_id=branchId
        )
        
        result["nextThoughtNeeded"] = nextThoughtNeeded
        return result
    
    @mcp.tool()
    def get_thinking_chain() -> dict:
        """Get current sequential thinking chain and branches."""
        return get_session().get_chain()
    
    @mcp.tool()
    def reset_thinking() -> dict:
        """Reset thinking session for new problem."""
        global _session
        _session = ThinkingSession()
        return {"status": "reset", "timestamp": datetime.now(timezone.utc).isoformat()}
