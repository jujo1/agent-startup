#!/usr/bin/env python3
"""
AGENTS 4.0 - Setup Verification Script
Verifies installation and reports status
"""

import os
import sys
import json
from pathlib import Path
from typing import List, Tuple

# Color codes
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
BLUE = '\033[0;34m'
NC = '\033[0m'  # No Color


def check_mark(passed: bool) -> str:
    """Return checkmark or cross based on status."""
    return f"{GREEN}✓{NC}" if passed else f"{RED}✗{NC}"


def check_directory_structure() -> Tuple[bool, List[str]]:
    """Verify directory structure exists."""
    home = Path.home()
    claude_home = home / ".claude"
    workflow_home = home / ".workflow"
    
    errors = []
    required_dirs = [
        claude_home,
        claude_home / "agents",
        claude_home / "mcp" / "servers",
        claude_home / "schemas",
        workflow_home,
        workflow_home / "todo",
        workflow_home / "evidence",
        workflow_home / "logs",
    ]
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            errors.append(f"Missing directory: {dir_path}")
    
    return len(errors) == 0, errors


def check_core_files() -> Tuple[bool, List[str]]:
    """Verify core instruction files exist."""
    home = Path.home()
    claude_home = home / ".claude"
    
    errors = []
    required_files = [
        claude_home / "AGENTS_3.md",
        claude_home / "CLAUDE_2.md",
        claude_home / "SCHEMAS.md",
    ]
    
    for file_path in required_files:
        if not file_path.exists():
            errors.append(f"Missing file: {file_path}")
    
    return len(errors) == 0, errors


def check_agent_definitions() -> Tuple[bool, List[str]]:
    """Verify agent YAML files exist."""
    home = Path.home()
    agents_dir = home / ".claude" / "agents"
    
    if not agents_dir.exists():
        return False, ["Agents directory does not exist"]
    
    # Count agent files
    agent_files = list(agents_dir.rglob("*.yaml"))
    
    if len(agent_files) == 0:
        return False, ["No agent YAML files found"]
    
    return True, []


def check_mcp_servers() -> Tuple[bool, List[str]]:
    """Verify MCP servers are present."""
    home = Path.home()
    mcp_dir = home / ".claude" / "mcp" / "servers"
    
    errors = []
    
    if not mcp_dir.exists():
        errors.append("MCP servers directory does not exist")
        return False, errors
    
    # Check for workflow_validator
    validator = mcp_dir / "workflow_validator.py"
    if not validator.exists():
        errors.append("workflow_validator.py not found (MANDATORY)")
    
    return len(errors) == 0, errors


def check_settings_json() -> Tuple[bool, List[str]]:
    """Verify settings.json exists and has MCP configuration."""
    home = Path.home()
    settings_file = home / ".claude" / "settings.json"
    
    errors = []
    
    if not settings_file.exists():
        errors.append("settings.json not found")
        return False, errors
    
    try:
        with open(settings_file, 'r') as f:
            settings = json.load(f)
        
        if "mcpServers" not in settings:
            errors.append("No mcpServers configuration in settings.json")
        elif "workflow-validator" not in settings["mcpServers"]:
            errors.append("workflow-validator not configured in settings.json")
    
    except json.JSONDecodeError:
        errors.append("settings.json is not valid JSON")
    except Exception as e:
        errors.append(f"Error reading settings.json: {e}")
    
    return len(errors) == 0, errors


def check_schemas() -> Tuple[bool, List[str]]:
    """Verify schema files exist."""
    home = Path.home()
    schemas_dir = home / ".claude" / "schemas"
    
    if not schemas_dir.exists():
        return False, ["Schemas directory does not exist"]
    
    # Count schema files
    schema_files = list(schemas_dir.glob("*.yaml")) + list(schemas_dir.glob("*.json"))
    
    if len(schema_files) == 0:
        return False, ["No schema files found"]
    
    return True, []


def print_section(title: str):
    """Print section header."""
    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"{BLUE}{title}{NC}")
    print(f"{BLUE}{'=' * 60}{NC}")


def main():
    """Run all verification checks."""
    print(f"\n{BLUE}AGENTS 4.0 - Setup Verification{NC}")
    print(f"{BLUE}Version: 1.0.0{NC}\n")
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Core Files", check_core_files),
        ("Agent Definitions", check_agent_definitions),
        ("MCP Servers", check_mcp_servers),
        ("Settings Configuration", check_settings_json),
        ("Schemas", check_schemas),
    ]
    
    results = []
    
    for check_name, check_func in checks:
        passed, errors = check_func()
        results.append((check_name, passed, errors))
        
        status = check_mark(passed)
        print(f"{status} {check_name}")
        
        if errors:
            for error in errors:
                print(f"    {RED}→{NC} {error}")
    
    # Summary
    print_section("Summary")
    
    total = len(checks)
    passed_count = sum(1 for _, passed, _ in results if passed)
    
    print(f"\nPassed: {passed_count}/{total}")
    
    if passed_count == total:
        print(f"\n{GREEN}✓ All checks passed! Ready for workflow execution.{NC}\n")
        print("Next steps:")
        print("  1. Read ~/.claude/QUICKSTART.md")
        print("  2. Start Claude (Web, Desktop, or Code)")
        print("  3. Initiate first workflow")
        return 0
    else:
        print(f"\n{RED}✗ Some checks failed. Please fix issues above.{NC}\n")
        print("Troubleshooting:")
        print("  1. Re-run ./setup.sh")
        print("  2. Check ~/.claude/MCP_SETUP.md")
        print("  3. Verify file permissions")
        return 1


if __name__ == "__main__":
    sys.exit(main())
