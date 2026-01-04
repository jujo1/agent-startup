#!/usr/bin/env python3
"""
AGENTS 4.0 - Configuration Generator

Generates configuration files for different Claude platforms:
- VSCode (Copilot Agent mode)
- Cursor (Agent mode)
- Claude Code (native)
- MCP server configs

Usage:
    python gen_all.py                    # Generate all configs
    python gen_all.py --platform vscode  # VSCode only
    python gen_all.py --platform cursor  # Cursor only
    python gen_all.py --output ./configs # Custom output dir
"""

import os
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any


class ConfigGenerator:
    """Base configuration generator"""
    
    def __init__(self, source_dir: str = "~/.claude", output_dir: str = "./configs"):
        self.source_dir = Path(source_dir).expanduser()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def discover_agents(self) -> List[Dict[str, Any]]:
        """Discover agent YAML files"""
        agents_dir = self.source_dir / "agents"
        if not agents_dir.exists():
            return []
        
        agents = []
        for agent_file in agents_dir.rglob("*.yaml"):
            agents.append({
                "name": agent_file.stem,
                "path": str(agent_file),
                "category": agent_file.parent.name
            })
        return agents
    
    def discover_mcp_servers(self) -> List[Dict[str, Any]]:
        """Discover MCP server scripts"""
        mcp_dir = self.source_dir / "mcp" / "servers"
        if not mcp_dir.exists():
            return []
        
        servers = []
        for server_file in mcp_dir.glob("*.py"):
            servers.append({
                "name": server_file.stem,
                "path": str(server_file),
                "command": f"python {server_file}"
            })
        return servers


class VSCodeGenerator(ConfigGenerator):
    """Generate VSCode Copilot Agent configuration"""
    
    def generate(self) -> Path:
        """Generate VSCode agent config"""
        agents = self.discover_agents()
        
        config = {
            "version": "1.0.0",
            "agents": {
                agent["name"]: {
                    "instructions": f"file:{agent['path']}",
                    "model": "claude-sonnet-4-5"
                }
                for agent in agents
            },
            "mcp": {
                "servers": self._generate_mcp_config()
            }
        }
        
        output_file = self.output_dir / "vscode_agent_config.json"
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Generated VSCode config: {output_file}")
        return output_file
    
    def _generate_mcp_config(self) -> Dict[str, Any]:
        """Generate MCP server configuration"""
        servers = self.discover_mcp_servers()
        
        mcp_config = {}
        for server in servers:
            mcp_config[server["name"]] = {
                "command": "python",
                "args": [server["path"]]
            }
        
        return mcp_config


class CursorGenerator(ConfigGenerator):
    """Generate Cursor Agent configuration"""
    
    def generate(self) -> Path:
        """Generate Cursor agent config"""
        # Similar to VSCode but with Cursor-specific format
        agents = self.discover_agents()
        
        config = {
            "agentMode": {
                "enabled": True,
                "agents": [
                    {
                        "name": agent["name"],
                        "instructions": Path(agent["path"]).read_text(),
                        "model": "claude-sonnet-4-5"
                    }
                    for agent in agents
                ]
            }
        }
        
        output_file = self.output_dir / "cursor_agent_config.json"
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Generated Cursor config: {output_file}")
        return output_file


class MCPConfigGenerator(ConfigGenerator):
    """Generate standalone MCP configuration"""
    
    def generate(self) -> Path:
        """Generate MCP config for Claude Code"""
        servers = self.discover_mcp_servers()
        
        config = {
            "mcpServers": {
                server["name"]: {
                    "command": "python",
                    "args": [server["path"]],
                    "env": {}
                }
                for server in servers
            }
        }
        
        output_file = self.output_dir / "mcp_config.json"
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Generated MCP config: {output_file}")
        return output_file


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Generate AGENTS 4.0 configurations")
    parser.add_argument("--platform", choices=["vscode", "cursor", "mcp", "all"], 
                       default="all", help="Platform to generate config for")
    parser.add_argument("--source", default="~/.claude", 
                       help="Source directory with agents and MCP servers")
    parser.add_argument("--output", default="./configs", 
                       help="Output directory for configs")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("AGENTS 4.0 - Configuration Generator")
    print("=" * 60)
    print()
    
    generators = []
    
    if args.platform in ["vscode", "all"]:
        generators.append(("VSCode", VSCodeGenerator(args.source, args.output)))
    
    if args.platform in ["cursor", "all"]:
        generators.append(("Cursor", CursorGenerator(args.source, args.output)))
    
    if args.platform in ["mcp", "all"]:
        generators.append(("MCP", MCPConfigGenerator(args.source, args.output)))
    
    for name, generator in generators:
        print(f"\n{name} Configuration:")
        print("-" * 40)
        generator.generate()
    
    print()
    print("=" * 60)
    print(f"✅ Generation complete! Configs in: {args.output}")
    print("=" * 60)


if __name__ == "__main__":
    main()
