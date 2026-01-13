"""
Knowledge Graph Memory Tools for Cloud Agent MCP.
Implements entity-relation-observation graph with JSONL persistence.

Tools:
- create_entities, create_relations, add_observations
- delete_entities, delete_relations, delete_observations  
- read_graph, search_nodes, open_nodes
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional
from dataclasses import dataclass, field, asdict


@dataclass
class Entity:
    """Node in knowledge graph."""
    name: str
    entityType: str
    observations: list[str] = field(default_factory=list)


@dataclass
class Relation:
    """Directed edge between entities."""
    from_entity: str
    to_entity: str
    relationType: str


class KnowledgeGraph:
    """In-memory knowledge graph with JSONL persistence."""
    
    def __init__(self, file_path: str = None):
        self.file_path = file_path or os.getenv(
            "MEMORY_FILE_PATH", 
            os.path.expanduser("~/.claude/memory.jsonl")
        )
        self.entities: dict[str, Entity] = {}
        self.relations: list[Relation] = []
        self._load()
    
    def _load(self):
        """Load graph from JSONL file."""
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
                        e = Entity(
                            name=data["name"],
                            entityType=data.get("entityType", "unknown"),
                            observations=data.get("observations", [])
                        )
                        self.entities[e.name] = e
                    elif data.get("type") == "relation":
                        r = Relation(
                            from_entity=data["from"],
                            to_entity=data["to"],
                            relationType=data["relationType"]
                        )
                        self.relations.append(r)
        except Exception as e:
            print(f"Error loading memory: {e}")
    
    def _save(self):
        """Persist graph to JSONL file."""
        path = Path(self.file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            for entity in self.entities.values():
                f.write(json.dumps({
                    "type": "entity",
                    "name": entity.name,
                    "entityType": entity.entityType,
                    "observations": entity.observations
                }) + "\n")
            for rel in self.relations:
                f.write(json.dumps({
                    "type": "relation",
                    "from": rel.from_entity,
                    "to": rel.to_entity,
                    "relationType": rel.relationType
                }) + "\n")
    
    def create_entities(self, entities: list[dict]) -> dict:
        """Create multiple entities."""
        created = []
        for e in entities:
            name = e.get("name")
            if not name:
                continue
            if name not in self.entities:
                self.entities[name] = Entity(
                    name=name,
                    entityType=e.get("entityType", "unknown"),
                    observations=e.get("observations", [])
                )
                created.append(name)
            else:
                # Merge observations
                existing = self.entities[name]
                for obs in e.get("observations", []):
                    if obs not in existing.observations:
                        existing.observations.append(obs)
                created.append(f"{name} (merged)")
        self._save()
        return {"created": created, "count": len(created)}
    
    def create_relations(self, relations: list[dict]) -> dict:
        """Create multiple relations."""
        created = []
        for r in relations:
            rel = Relation(
                from_entity=r.get("from", ""),
                to_entity=r.get("to", ""),
                relationType=r.get("relationType", "relates_to")
            )
            # Check for duplicates
            exists = any(
                x.from_entity == rel.from_entity and 
                x.to_entity == rel.to_entity and 
                x.relationType == rel.relationType
                for x in self.relations
            )
            if not exists:
                self.relations.append(rel)
                created.append(f"{rel.from_entity} -{rel.relationType}-> {rel.to_entity}")
        self._save()
        return {"created": created, "count": len(created)}
    
    def add_observations(self, entity_name: str, observations: list[str]) -> dict:
        """Add observations to existing entity."""
        if entity_name not in self.entities:
            return {"error": f"Entity not found: {entity_name}"}
        
        entity = self.entities[entity_name]
        added = []
        for obs in observations:
            if obs not in entity.observations:
                entity.observations.append(obs)
                added.append(obs)
        self._save()
        return {"entity": entity_name, "added": added, "total": len(entity.observations)}
    
    def delete_entities(self, names: list[str]) -> dict:
        """Delete entities and their relations."""
        deleted = []
        for name in names:
            if name in self.entities:
                del self.entities[name]
                # Remove related relations
                self.relations = [
                    r for r in self.relations 
                    if r.from_entity != name and r.to_entity != name
                ]
                deleted.append(name)
        self._save()
        return {"deleted": deleted, "count": len(deleted)}
    
    def delete_relations(self, relations: list[dict]) -> dict:
        """Delete specific relations."""
        deleted = []
        for r in relations:
            before = len(self.relations)
            self.relations = [
                x for x in self.relations
                if not (x.from_entity == r.get("from") and 
                       x.to_entity == r.get("to") and 
                       x.relationType == r.get("relationType"))
            ]
            if len(self.relations) < before:
                deleted.append(f"{r.get('from')} -{r.get('relationType')}-> {r.get('to')}")
        self._save()
        return {"deleted": deleted, "count": len(deleted)}
    
    def delete_observations(self, entity_name: str, observations: list[str]) -> dict:
        """Delete observations from entity."""
        if entity_name not in self.entities:
            return {"error": f"Entity not found: {entity_name}"}
        
        entity = self.entities[entity_name]
        deleted = []
        for obs in observations:
            if obs in entity.observations:
                entity.observations.remove(obs)
                deleted.append(obs)
        self._save()
        return {"entity": entity_name, "deleted": deleted, "remaining": len(entity.observations)}
    
    def read_graph(self) -> dict:
        """Return complete graph structure."""
        return {
            "entities": [
                {"name": e.name, "entityType": e.entityType, "observations": e.observations}
                for e in self.entities.values()
            ],
            "relations": [
                {"from": r.from_entity, "to": r.to_entity, "relationType": r.relationType}
                for r in self.relations
            ],
            "stats": {
                "entity_count": len(self.entities),
                "relation_count": len(self.relations)
            }
        }
    
    def search_nodes(self, query: str) -> dict:
        """Search entities by name, type, or observation content."""
        query_lower = query.lower()
        matches = []
        
        for entity in self.entities.values():
            score = 0
            if query_lower in entity.name.lower():
                score += 10
            if query_lower in entity.entityType.lower():
                score += 5
            for obs in entity.observations:
                if query_lower in obs.lower():
                    score += 2
            
            if score > 0:
                matches.append({
                    "name": entity.name,
                    "entityType": entity.entityType,
                    "observations": entity.observations,
                    "score": score
                })
        
        # Sort by score descending
        matches.sort(key=lambda x: x["score"], reverse=True)
        
        # Get related relations
        match_names = {m["name"] for m in matches}
        related_relations = [
            {"from": r.from_entity, "to": r.to_entity, "relationType": r.relationType}
            for r in self.relations
            if r.from_entity in match_names or r.to_entity in match_names
        ]
        
        return {
            "query": query,
            "matches": matches,
            "relations": related_relations,
            "count": len(matches)
        }
    
    def open_nodes(self, names: list[str]) -> dict:
        """Retrieve specific entities by name."""
        found = []
        not_found = []
        
        for name in names:
            if name in self.entities:
                e = self.entities[name]
                found.append({
                    "name": e.name,
                    "entityType": e.entityType,
                    "observations": e.observations
                })
            else:
                not_found.append(name)
        
        # Get relations between found entities
        found_names = {f["name"] for f in found}
        relations = [
            {"from": r.from_entity, "to": r.to_entity, "relationType": r.relationType}
            for r in self.relations
            if r.from_entity in found_names and r.to_entity in found_names
        ]
        
        return {
            "entities": found,
            "relations": relations,
            "not_found": not_found
        }


# Global instance
_graph: Optional[KnowledgeGraph] = None


def get_graph() -> KnowledgeGraph:
    """Get or create global knowledge graph instance."""
    global _graph
    if _graph is None:
        _graph = KnowledgeGraph()
    return _graph


def register_memory_tools(mcp):
    """Register all memory tools with FastMCP server."""
    
    @mcp.tool()
    def create_entities(entities: list[dict]) -> dict:
        """Create new entities in knowledge graph.
        
        Args:
            entities: List of {name, entityType, observations[]}
        """
        return get_graph().create_entities(entities)
    
    @mcp.tool()
    def create_relations(relations: list[dict]) -> dict:
        """Create relations between entities.
        
        Args:
            relations: List of {from, to, relationType}
        """
        return get_graph().create_relations(relations)
    
    @mcp.tool()
    def add_observations(entityName: str, observations: list[str]) -> dict:
        """Add observations to existing entity.
        
        Args:
            entityName: Name of entity
            observations: List of observation strings
        """
        return get_graph().add_observations(entityName, observations)
    
    @mcp.tool()
    def delete_entities(entityNames: list[str]) -> dict:
        """Delete entities and their relations.
        
        Args:
            entityNames: List of entity names to delete
        """
        return get_graph().delete_entities(entityNames)
    
    @mcp.tool()
    def delete_relations(relations: list[dict]) -> dict:
        """Delete specific relations.
        
        Args:
            relations: List of {from, to, relationType}
        """
        return get_graph().delete_relations(relations)
    
    @mcp.tool()
    def delete_observations(entityName: str, observations: list[str]) -> dict:
        """Delete observations from entity.
        
        Args:
            entityName: Name of entity
            observations: List of observations to remove
        """
        return get_graph().delete_observations(entityName, observations)
    
    @mcp.tool()
    def read_graph() -> dict:
        """Return complete knowledge graph with all entities and relations."""
        return get_graph().read_graph()
    
    @mcp.tool()
    def search_nodes(query: str) -> dict:
        """Search nodes by name, type, or observation content.
        
        Args:
            query: Search string
        """
        return get_graph().search_nodes(query)
    
    @mcp.tool()
    def open_nodes(names: list[str]) -> dict:
        """Retrieve specific entities by name.
        
        Args:
            names: List of entity names
        """
        return get_graph().open_nodes(names)
