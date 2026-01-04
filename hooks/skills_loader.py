#!/usr/bin/env python3
"""
Skills Loader - Loads superpowers skills at agent startup.

Installation: ~/.claude/hooks/skills_loader.py

Skills loaded (from obra/superpowers):
  - verification-before-completion
  - executing-plans
  - test-driven-development
  - systematic-debugging
  - brainstorming
  - requesting-code-review
  - receiving-code-review
  - subagent-driven-development
  - dispatching-parallel-agents

Stage-to-Skills mapping:
  PLAN:     brainstorming, writing-plans
  REVIEW:   verification-before-completion
  DISRUPT:  brainstorming
  IMPLEMENT: executing-plans, test-driven-development
  TEST:     test-driven-development, systematic-debugging
  REVIEW_POST: verification-before-completion, requesting-code-review
  VALIDATE: verification-before-completion
  LEARN:    writing-skills

Usage:
  python skills_loader.py --load-all
  python skills_loader.py --stage IMPLEMENT
  python skills_loader.py --check
"""

import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import argparse


# Skills configuration
SKILLS = {
    "verification-before-completion": {
        "source": "superpowers",
        "description": "Evidence before claims, always. Run verification before claiming work is complete.",
        "triggers": ["before claim", "before commit", "before PR", "work complete"],
        "core_principle": "If you haven't run the verification command in this message, you cannot claim it passes.",
        "checklist": [
            "IDENTIFY: What command proves this claim?",
            "RUN: Execute the FULL command (fresh, complete)",
            "READ: Full output, check exit code, count failures",
            "VERIFY: Does output confirm the claim?",
            "STATE: Actual status with evidence"
        ]
    },
    "executing-plans": {
        "source": "superpowers",
        "description": "Execute plans in batches with verification at each step.",
        "triggers": ["execute plan", "implement", "follow plan"],
        "workflow": [
            "Announce: Using executing-plans skill",
            "Read plan file",
            "Review critically - identify concerns",
            "Create TodoWrite for tasks",
            "For each task: mark in_progress, follow steps, run verifications, mark completed",
            "Show verification output",
            "Say: Ready for feedback"
        ]
    },
    "test-driven-development": {
        "source": "superpowers",
        "description": "RED-GREEN-REFACTOR: Write failing test, make it pass, refactor.",
        "triggers": ["write test", "TDD", "test first", "red-green"],
        "core_principle": "Write failing test FIRST, watch it fail, then write minimal code to pass.",
        "phases": ["RED: Write failing test", "GREEN: Write minimal code to pass", "REFACTOR: Clean up"]
    },
    "systematic-debugging": {
        "source": "superpowers",
        "description": "4-phase root cause process for debugging.",
        "triggers": ["debug", "fix bug", "error", "not working", "broken"],
        "phases": [
            "ISOLATE: Reproduce the issue",
            "ANALYZE: Find root cause (not symptoms)",
            "FIX: Minimal targeted change",
            "VERIFY: Confirm fix doesn't break anything"
        ]
    },
    "brainstorming": {
        "source": "superpowers",
        "description": "Refine rough ideas through questions, explore alternatives.",
        "triggers": ["brainstorm", "design", "plan", "what should", "how should"],
        "workflow": [
            "Ask clarifying questions",
            "Explore alternatives",
            "Present design in sections",
            "Get validation before implementing",
            "Save design document"
        ]
    },
    "requesting-code-review": {
        "source": "superpowers",
        "description": "Request code review with proper context.",
        "triggers": ["request review", "PR ready", "need review"],
        "checklist": [
            "Summarize what changed and why",
            "List areas needing attention",
            "Provide testing evidence",
            "Note any concerns or tradeoffs"
        ]
    },
    "receiving-code-review": {
        "source": "superpowers",
        "description": "Handle code review feedback with technical rigor.",
        "triggers": ["review feedback", "reviewer said", "code review"],
        "core_principle": "Verify before implementing. Ask before assuming. Technical correctness over social comfort.",
        "workflow": [
            "READ: Complete feedback without reacting",
            "UNDERSTAND: Restate requirement in own words",
            "VERIFY: Test claims independently",
            "IMPLEMENT: Only after understanding",
            "CONFIRM: Run verification"
        ]
    },
    "subagent-driven-development": {
        "source": "superpowers",
        "description": "Dispatch fresh subagents per task with two-stage review.",
        "triggers": ["dispatch agent", "subagent", "parallel tasks"],
        "workflow": [
            "Create task specification",
            "Dispatch fresh subagent",
            "Two-stage review: spec compliance, then code quality",
            "Aggregate results"
        ]
    },
    "dispatching-parallel-agents": {
        "source": "superpowers",
        "description": "Coordinate multiple agents working in parallel.",
        "triggers": ["parallel", "multiple agents", "concurrent"],
        "requirements": [
            "Tasks must be independent",
            "Clear boundaries between tasks",
            "Aggregation strategy defined"
        ]
    },
    "writing-plans": {
        "source": "superpowers",
        "description": "Break work into bite-sized tasks (2-5 minutes each).",
        "triggers": ["write plan", "create plan", "planning"],
        "task_requirements": [
            "Exact file paths",
            "Complete code (no placeholders)",
            "Verification steps"
        ]
    },
    "writing-skills": {
        "source": "superpowers",
        "description": "Create reusable skills for future Claude instances.",
        "triggers": ["create skill", "write skill", "document pattern"],
        "structure": [
            "name: Skill-Name-With-Hyphens",
            "description: Use when [triggers]",
            "Overview, When to Use, Core Pattern",
            "Quick Reference, Implementation",
            "Common Mistakes"
        ]
    }
}

# Stage to skills mapping
STAGE_SKILLS = {
    "PLAN": ["brainstorming", "writing-plans"],
    "REVIEW": ["verification-before-completion"],
    "DISRUPT": ["brainstorming"],
    "IMPLEMENT": ["executing-plans", "test-driven-development"],
    "TEST": ["test-driven-development", "systematic-debugging"],
    "REVIEW_POST": ["verification-before-completion", "requesting-code-review"],
    "VALIDATE": ["verification-before-completion"],
    "LEARN": ["writing-skills"]
}


@dataclass
class LoadedSkill:
    """Represents a loaded skill."""
    name: str
    source: str
    description: str
    content: dict
    loaded_at: str = field(default_factory=lambda: __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat())
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "source": self.source,
            "description": self.description,
            "content": self.content,
            "loaded_at": self.loaded_at
        }


class SkillsLoader:
    """Loads and manages superpowers skills."""
    
    def __init__(self, skills_dir: Optional[Path] = None):
        self.skills_dir = skills_dir or Path.home() / ".claude" / "skills"
        self.loaded_skills: dict[str, LoadedSkill] = {}
        self.skill_locations = [
            self.skills_dir,
            Path.home() / ".claude" / "plugins" / "cache" / "superpowers-marketplace" / "superpowers",
            Path("/mnt/skills/user"),
            Path("/mnt/skills/examples"),
        ]
    
    def _find_skill_file(self, skill_name: str) -> Optional[Path]:
        """Find SKILL.md file for a skill."""
        for base_path in self.skill_locations:
            if not base_path.exists():
                continue
            
            # Direct path
            direct = base_path / skill_name / "SKILL.md"
            if direct.exists():
                return direct
            
            # Search in subdirectories (for versioned plugins)
            for version_dir in base_path.glob("*"):
                if version_dir.is_dir():
                    skill_path = version_dir / "skills" / skill_name / "SKILL.md"
                    if skill_path.exists():
                        return skill_path
        
        return None
    
    def load_skill(self, skill_name: str) -> Optional[LoadedSkill]:
        """Load a single skill."""
        if skill_name in self.loaded_skills:
            return self.loaded_skills[skill_name]
        
        # Check if skill is in our config
        skill_config = SKILLS.get(skill_name)
        if not skill_config:
            print(f"Unknown skill: {skill_name}")
            return None
        
        # Try to find and load the skill file
        skill_file = self._find_skill_file(skill_name)
        content = skill_config.copy()
        
        if skill_file:
            try:
                content["file_path"] = str(skill_file)
                content["file_content"] = skill_file.read_text()[:5000]  # Truncate for memory
            except Exception as e:
                print(f"Warning: Could not read skill file: {e}")
        
        loaded = LoadedSkill(
            name=skill_name,
            source=skill_config.get("source", "unknown"),
            description=skill_config.get("description", ""),
            content=content
        )
        
        self.loaded_skills[skill_name] = loaded
        return loaded
    
    def load_skills_for_stage(self, stage: str) -> list[LoadedSkill]:
        """Load all skills required for a stage."""
        skill_names = STAGE_SKILLS.get(stage.upper(), [])
        loaded = []
        
        for name in skill_names:
            skill = self.load_skill(name)
            if skill:
                loaded.append(skill)
        
        return loaded
    
    def load_all_skills(self) -> list[LoadedSkill]:
        """Load all available skills."""
        loaded = []
        for name in SKILLS:
            skill = self.load_skill(name)
            if skill:
                loaded.append(skill)
        return loaded
    
    def check_skills(self) -> dict:
        """Check which skills are available."""
        results = {}
        
        for skill_name in SKILLS:
            skill_file = self._find_skill_file(skill_name)
            results[skill_name] = {
                "available": skill_file is not None,
                "path": str(skill_file) if skill_file else None,
                "source": SKILLS[skill_name].get("source", "unknown"),
                "description": SKILLS[skill_name].get("description", "")
            }
        
        return results
    
    def get_skill_prompt(self, skill_name: str) -> str:
        """Get formatted prompt for using a skill."""
        skill = self.load_skill(skill_name)
        if not skill:
            return f"Skill '{skill_name}' not found."
        
        content = skill.content
        prompt = f"""
## Using Skill: {skill.name}

**Description:** {skill.description}

"""
        
        if "core_principle" in content:
            prompt += f"**Core Principle:** {content['core_principle']}\n\n"
        
        if "triggers" in content:
            prompt += f"**Triggers:** {', '.join(content['triggers'])}\n\n"
        
        if "checklist" in content:
            prompt += "**Checklist:**\n"
            for item in content["checklist"]:
                prompt += f"  - [ ] {item}\n"
            prompt += "\n"
        
        if "workflow" in content:
            prompt += "**Workflow:**\n"
            for i, step in enumerate(content["workflow"], 1):
                prompt += f"  {i}. {step}\n"
            prompt += "\n"
        
        if "phases" in content:
            prompt += "**Phases:**\n"
            for phase in content["phases"]:
                prompt += f"  - {phase}\n"
            prompt += "\n"
        
        return prompt
    
    def generate_stage_prompt(self, stage: str) -> str:
        """Generate a prompt with all skills for a stage."""
        skills = self.load_skills_for_stage(stage)
        
        if not skills:
            return f"No skills defined for stage {stage}."
        
        prompt = f"""
# Skills for {stage} Stage

The following skills should be applied during this stage:

"""
        
        for skill in skills:
            prompt += self.get_skill_prompt(skill.name)
            prompt += "---\n\n"
        
        return prompt
    
    def save_loaded_skills(self, output_path: Path) -> None:
        """Save loaded skills to JSON."""
        data = {
            "loaded_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
            "skills": {name: skill.to_dict() for name, skill in self.loaded_skills.items()}
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Skills Loader")
    parser.add_argument("--load-all", action="store_true", help="Load all skills")
    parser.add_argument("--stage", help="Load skills for specific stage")
    parser.add_argument("--check", action="store_true", help="Check skill availability")
    parser.add_argument("--skill", help="Load specific skill")
    parser.add_argument("--prompt", help="Generate prompt for skill")
    parser.add_argument("--output", type=Path, help="Output file for loaded skills")
    parser.add_argument("--skills-dir", type=Path, help="Skills directory")
    args = parser.parse_args()
    
    loader = SkillsLoader(skills_dir=args.skills_dir)
    
    if args.check:
        results = loader.check_skills()
        print("\n=== Skill Availability ===\n")
        for name, info in results.items():
            status = "✅" if info["available"] else "❌"
            print(f"{status} {name}")
            if info["available"]:
                print(f"   Path: {info['path']}")
            print(f"   {info['description'][:60]}...")
            print()
        return 0
    
    if args.load_all:
        skills = loader.load_all_skills()
        print(f"\nLoaded {len(skills)} skills:")
        for skill in skills:
            print(f"  - {skill.name}: {skill.description[:50]}...")
        
        if args.output:
            loader.save_loaded_skills(args.output)
            print(f"\nSaved to {args.output}")
        return 0
    
    if args.stage:
        skills = loader.load_skills_for_stage(args.stage)
        print(f"\n=== Skills for {args.stage} Stage ===\n")
        for skill in skills:
            print(f"  - {skill.name}")
        print()
        print(loader.generate_stage_prompt(args.stage))
        return 0
    
    if args.prompt:
        print(loader.get_skill_prompt(args.prompt))
        return 0
    
    if args.skill:
        skill = loader.load_skill(args.skill)
        if skill:
            print(json.dumps(skill.to_dict(), indent=2))
        return 0 if skill else 1
    
    # Default: show help
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
