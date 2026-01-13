#!/usr/bin/env python3
"""Unit Tests for Cloud Agent MCP - 100% coverage target."""

import pytest
import os
import tempfile
import shutil
from pathlib import Path

import cloud_agent_mcp as cam


@pytest.fixture(autouse=True)
def reset_state():
    """Reset global state before each test."""
    cam.reset_graph()
    cam.reset_session()
    cam.reset_manager()
    yield
    cam.reset_graph()
    cam.reset_session()
    cam.reset_manager()


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp(prefix="cam_test_")
    yield d
    shutil.rmtree(d, ignore_errors=True)


@pytest.fixture
def temp_file(temp_dir):
    f = Path(temp_dir) / "test.txt"
    f.write_text("line1\nline2\ntest pattern here\nline4")
    return str(f)


# =============================================================================
# REGISTRATION TESTS
# =============================================================================

class TestRegistration:
    def test_all_tools_registered(self):
        tools = list(cam.mcp._tool_manager._tools.keys())
        assert len(tools) == 25

    def test_tool_naming_pattern(self):
        import re
        pattern = r'^cloud_agent_mcp-\w+_mcp-\w+$'
        for tool in cam.mcp._tool_manager._tools.keys():
            assert re.match(pattern, tool), f"Invalid: {tool}"

    def test_filesystem_count(self):
        assert len([t for t in cam.mcp._tool_manager._tools if 'filesystem_mcp' in t]) == 8

    def test_memory_count(self):
        assert len([t for t in cam.mcp._tool_manager._tools if 'memory_mcp' in t]) == 9

    def test_thinking_count(self):
        assert len([t for t in cam.mcp._tool_manager._tools if 'thinking_mcp' in t]) == 3

    def test_todo_count(self):
        assert len([t for t in cam.mcp._tool_manager._tools if 'todo_mcp' in t]) == 5


# =============================================================================
# FILESYSTEM TESTS
# =============================================================================

class TestFilesystem:
    def test_ping(self):
        r = cam._filesystem_ping()
        assert r["status"] == "pong"
        assert "timestamp" in r
        print(f"[LOG] ping: {r}")

    def test_get_status(self):
        r = cam._filesystem_get_status()
        assert "platform" in r
        assert "python_version" in r
        print(f"[LOG] status: {r}")

    def test_read_file(self, temp_file):
        r = cam._filesystem_read_file(temp_file)
        assert "content" in r
        assert r["lines"] == 4
        print(f"[LOG] read: {r['size']} bytes")

    def test_read_file_not_found(self, temp_dir):
        r = cam._filesystem_read_file(f"{temp_dir}/missing.txt")
        assert "error" in r

    def test_read_file_not_a_file(self, temp_dir):
        r = cam._filesystem_read_file(temp_dir)
        assert "error" in r

    def test_read_file_binary(self, temp_dir):
        f = Path(temp_dir) / "bin.dat"
        f.write_bytes(b'\x00\x01\xff')
        r = cam._filesystem_read_file(str(f))
        assert "error" in r
        assert "binary" in r["error"].lower()

    def test_write_file(self, temp_dir):
        p = f"{temp_dir}/new.txt"
        r = cam._filesystem_write_file(p, "hello")
        assert r["bytes_written"] == 5
        assert Path(p).read_text() == "hello"
        print(f"[LOG] write: {r}")

    def test_write_file_append(self, temp_file):
        r = cam._filesystem_write_file(temp_file, "\nappend", append=True)
        assert r["mode"] == "append"
        assert "append" in Path(temp_file).read_text()

    def test_list_directory(self, temp_dir):
        Path(temp_dir, "a.txt").touch()
        Path(temp_dir, "b.txt").touch()
        r = cam._filesystem_list_directory(temp_dir)
        assert r["count"] == 2
        print(f"[LOG] list: {r['count']} items")

    def test_list_directory_not_found(self, temp_dir):
        r = cam._filesystem_list_directory(f"{temp_dir}/nope")
        assert "error" in r

    def test_list_directory_not_dir(self, temp_file):
        r = cam._filesystem_list_directory(temp_file)
        assert "error" in r

    def test_exec_command(self):
        r = cam._filesystem_exec_command("echo test")
        assert r["returncode"] == 0
        assert "test" in r["stdout"]
        print(f"[LOG] exec: {r}")

    def test_exec_command_error(self):
        r = cam._filesystem_exec_command("exit 1")
        assert r["returncode"] == 1

    def test_exec_command_cwd(self, temp_dir):
        r = cam._filesystem_exec_command("pwd", cwd=temp_dir)
        assert temp_dir in r["stdout"]

    def test_exec_command_timeout(self):
        r = cam._filesystem_exec_command("sleep 5", timeout=1)
        assert "error" in r
        assert "timed out" in r["error"].lower()

    def test_grep(self, temp_file):
        r = cam._filesystem_grep(str(Path(temp_file).parent), "pattern")
        assert r["count"] >= 1
        print(f"[LOG] grep: {r['count']} matches")

    def test_grep_single_file(self, temp_file):
        r = cam._filesystem_grep(temp_file, "pattern")
        assert r["count"] >= 1

    def test_grep_no_match(self, temp_dir):
        Path(temp_dir, "x.txt").write_text("nothing")
        r = cam._filesystem_grep(temp_dir, "zzz123")
        assert r["count"] == 0

    def test_grep_invalid_regex(self, temp_dir):
        r = cam._filesystem_grep(temp_dir, "[bad")
        assert "error" in r

    def test_glob(self, temp_dir):
        Path(temp_dir, "a.py").touch()
        Path(temp_dir, "b.py").touch()
        Path(temp_dir, "c.txt").touch()
        r = cam._filesystem_glob_files(temp_dir, "*.py")
        assert r["count"] == 2
        print(f"[LOG] glob: {r['count']} matches")

    def test_glob_not_dir(self, temp_file):
        r = cam._filesystem_glob_files(temp_file, "*")
        assert "error" in r

    def test_validate_path_allowed(self):
        assert cam._validate_path("/any") is True

    def test_validate_path_restricted(self):
        orig = cam.ALLOWED_PATHS
        cam.ALLOWED_PATHS = ["/tmp"]
        try:
            assert cam._validate_path("/tmp/x") is True
            assert cam._validate_path("/home/x") is False
        finally:
            cam.ALLOWED_PATHS = orig


# =============================================================================
# MEMORY TESTS
# =============================================================================

class TestMemory:
    def test_create_entities(self):
        r = cam._memory_create_entities([{"name": "A", "entityType": "t", "observations": ["o1"]}])
        assert r["count"] == 1
        print(f"[LOG] create_entities: {r}")

    def test_create_entities_merge(self):
        cam._memory_create_entities([{"name": "B", "observations": ["x"]}])
        r = cam._memory_create_entities([{"name": "B", "observations": ["y"]}])
        assert "B (merged)" in r["created"]

    def test_create_entities_no_name(self):
        r = cam._memory_create_entities([{"entityType": "x"}])
        assert r["count"] == 0

    def test_create_relations(self):
        cam._memory_create_entities([{"name": "X"}, {"name": "Y"}])
        r = cam._memory_create_relations([{"from": "X", "to": "Y", "relationType": "knows"}])
        assert r["count"] == 1
        print(f"[LOG] create_relations: {r}")

    def test_create_relations_duplicate(self):
        cam._memory_create_entities([{"name": "P"}, {"name": "Q"}])
        cam._memory_create_relations([{"from": "P", "to": "Q", "relationType": "r"}])
        r = cam._memory_create_relations([{"from": "P", "to": "Q", "relationType": "r"}])
        assert r["count"] == 0

    def test_add_observations(self):
        cam._memory_create_entities([{"name": "E"}])
        r = cam._memory_add_observations("E", ["a", "b"])
        assert len(r["added"]) == 2
        print(f"[LOG] add_observations: {r}")

    def test_add_observations_not_found(self):
        r = cam._memory_add_observations("NoOne", ["x"])
        assert "error" in r

    def test_add_observations_duplicate(self):
        cam._memory_create_entities([{"name": "D", "observations": ["x"]}])
        r = cam._memory_add_observations("D", ["x", "y"])
        assert "x" not in r["added"]
        assert "y" in r["added"]

    def test_delete_entities(self):
        cam._memory_create_entities([{"name": "Del"}, {"name": "Keep"}])
        cam._memory_create_relations([{"from": "Del", "to": "Keep", "relationType": "x"}])
        r = cam._memory_delete_entities(["Del"])
        assert "Del" in r["deleted"]
        g = cam._memory_read_graph()
        assert len(g["relations"]) == 0
        print(f"[LOG] delete_entities: {r}")

    def test_delete_entities_not_found(self):
        r = cam._memory_delete_entities(["Ghost"])
        assert r["count"] == 0

    def test_delete_relations(self):
        cam._memory_create_entities([{"name": "R1"}, {"name": "R2"}])
        cam._memory_create_relations([{"from": "R1", "to": "R2", "relationType": "rel"}])
        r = cam._memory_delete_relations([{"from": "R1", "to": "R2", "relationType": "rel"}])
        assert r["count"] == 1
        print(f"[LOG] delete_relations: {r}")

    def test_delete_observations(self):
        cam._memory_create_entities([{"name": "O", "observations": ["a", "b", "c"]}])
        r = cam._memory_delete_observations("O", ["a", "c"])
        assert len(r["deleted"]) == 2
        print(f"[LOG] delete_observations: {r}")

    def test_delete_observations_not_found(self):
        r = cam._memory_delete_observations("NoEnt", ["x"])
        assert "error" in r

    def test_read_graph(self):
        cam._memory_create_entities([{"name": "G1"}, {"name": "G2"}])
        cam._memory_create_relations([{"from": "G1", "to": "G2", "relationType": "links"}])
        r = cam._memory_read_graph()
        assert r["stats"]["entity_count"] == 2
        assert r["stats"]["relation_count"] == 1
        print(f"[LOG] read_graph: {r['stats']}")

    def test_search_nodes_name(self):
        cam._memory_create_entities([{"name": "SearchMe", "entityType": "t"}])
        r = cam._memory_search_nodes("search")
        assert r["count"] >= 1
        print(f"[LOG] search_nodes: {r['count']}")

    def test_search_nodes_type(self):
        cam._memory_create_entities([{"name": "T", "entityType": "special_type"}])
        r = cam._memory_search_nodes("special")
        assert r["count"] >= 1

    def test_search_nodes_observation(self):
        cam._memory_create_entities([{"name": "Obs", "observations": ["unique_obs"]}])
        r = cam._memory_search_nodes("unique_obs")
        assert r["count"] >= 1

    def test_search_nodes_no_match(self):
        r = cam._memory_search_nodes("zzz_nomatch_zzz")
        assert r["count"] == 0

    def test_open_nodes(self):
        cam._memory_create_entities([{"name": "N1"}, {"name": "N2"}])
        cam._memory_create_relations([{"from": "N1", "to": "N2", "relationType": "x"}])
        r = cam._memory_open_nodes(["N1", "N2", "Missing"])
        assert len(r["entities"]) == 2
        assert "Missing" in r["not_found"]
        print(f"[LOG] open_nodes: {len(r['entities'])} found")


# =============================================================================
# THINKING TESTS
# =============================================================================

class TestThinking:
    def test_sequentialthinking_start(self):
        r = cam._thinking_sequentialthinking("First", 1, 3, True)
        assert r["recorded"] is True
        assert r["thought_number"] == 1
        print(f"[LOG] thinking start: {r}")

    def test_sequentialthinking_continue(self):
        cam._thinking_sequentialthinking("First", 1, 3, True)
        r = cam._thinking_sequentialthinking("Second", 2, 3, True)
        assert r["next_action"] == "continue"

    def test_sequentialthinking_conclude(self):
        cam._thinking_sequentialthinking("First", 1, 2, True)
        r = cam._thinking_sequentialthinking("Conclusion", 2, 2, False)
        assert r["next_action"] == "conclude"
        assert "✓ CONCLUSION" in r["flags"]
        assert "session_summary" in r
        print(f"[LOG] thinking conclude: {r}")

    def test_sequentialthinking_revision(self):
        cam._thinking_sequentialthinking("First", 1, 3, True)
        r = cam._thinking_sequentialthinking("Revised", 2, 3, True, isRevision=True, revisesThought=1)
        assert r["next_action"] == "revise"
        assert any("Revision" in f for f in r["flags"])

    def test_sequentialthinking_branch(self):
        cam._thinking_sequentialthinking("First", 1, 3, True)
        r = cam._thinking_sequentialthinking("Alt", 2, 3, True, branchFromThought=1, branchId="alt")
        assert r["next_action"] == "branch"
        assert any("Branch" in f for f in r["flags"])

    def test_get_thinking_chain(self):
        cam._thinking_sequentialthinking("T1", 1, 2, True)
        cam._thinking_sequentialthinking("T2", 2, 2, False)
        r = cam._thinking_get_thinking_chain()
        assert r["count"] == 2
        print(f"[LOG] chain: {r['count']} thoughts")

    def test_get_thinking_chain_empty(self):
        r = cam._thinking_get_thinking_chain()
        assert r["count"] == 0

    def test_reset_thinking(self):
        cam._thinking_sequentialthinking("T", 1, 1, False)
        r = cam._thinking_reset_thinking()
        assert r["status"] == "reset"
        assert cam._thinking_get_thinking_chain()["count"] == 0
        print(f"[LOG] reset: {r}")


# =============================================================================
# TODO TESTS
# =============================================================================

class TestTodo:
    def test_create_todo(self):
        r = cam._todo_create_todo("Task", priority="P0", description="desc", tags=["t"])
        assert r["created"]["title"] == "Task"
        assert r["created"]["priority"] == "P0"
        print(f"[LOG] create: {r['created']['id']}")

    def test_create_todo_defaults(self):
        r = cam._todo_create_todo("Simple")
        assert r["created"]["priority"] == "P1"
        assert r["created"]["status"] == "pending"

    def test_list_todos(self):
        cam._todo_create_todo("T1")
        cam._todo_create_todo("T2")
        r = cam._todo_list_todos()
        assert r["count"] == 2
        print(f"[LOG] list: {r['count']}")

    def test_list_todos_filter_status(self):
        t = cam._todo_create_todo("Done")
        cam._todo_complete_todo(t["created"]["id"])
        cam._todo_create_todo("Pending")
        r = cam._todo_list_todos(status="complete")
        assert r["count"] == 1

    def test_list_todos_filter_priority(self):
        cam._todo_create_todo("P0", priority="P0")
        cam._todo_create_todo("P2", priority="P2")
        r = cam._todo_list_todos(priority="P0")
        assert r["count"] == 1

    def test_list_todos_empty(self):
        r = cam._todo_list_todos()
        assert r["count"] == 0

    def test_update_todo(self):
        t = cam._todo_create_todo("Orig")
        r = cam._todo_update_todo(t["created"]["id"], title="Updated", status="in_progress",
                                  priority="P0", description="new", blockers=["b"], tags=["t"])
        assert r["updated"]["title"] == "Updated"
        assert r["updated"]["status"] == "in_progress"
        print(f"[LOG] update: {r['updated']['title']}")

    def test_update_todo_not_found(self):
        r = cam._todo_update_todo("TODO-FAKE", title="x")
        assert "error" in r

    def test_update_todo_partial(self):
        t = cam._todo_create_todo("Keep", priority="P2")
        r = cam._todo_update_todo(t["created"]["id"], priority="P0")
        assert r["updated"]["title"] == "Keep"
        assert r["updated"]["priority"] == "P0"

    def test_complete_todo(self):
        t = cam._todo_create_todo("Complete me")
        r = cam._todo_complete_todo(t["created"]["id"])
        assert r["completed"]["status"] == "complete"
        assert r["completed"]["completed_at"] is not None
        print(f"[LOG] complete: {r['completed']['status']}")

    def test_complete_todo_not_found(self):
        r = cam._todo_complete_todo("TODO-FAKE")
        assert "error" in r

    def test_delete_todo(self):
        t = cam._todo_create_todo("Delete me")
        tid = t["created"]["id"]
        r = cam._todo_delete_todo(tid)
        assert r["deleted"]["id"] == tid
        assert cam._todo_list_todos()["count"] == 0
        print(f"[LOG] delete: {tid}")

    def test_delete_todo_not_found(self):
        r = cam._todo_delete_todo("TODO-FAKE")
        assert "error" in r


# =============================================================================
# PERSISTENCE TESTS
# =============================================================================

class TestPersistence:
    def test_memory_persistence(self, temp_dir):
        """Verify memory writes to file correctly."""
        mem_file = f"{temp_dir}/mem.jsonl"
        os.environ["MEMORY_FILE_PATH"] = mem_file
        cam.reset_graph()
        cam._memory_create_entities([{"name": "Persist"}])
        # Verify file was written
        assert Path(mem_file).exists()
        content = Path(mem_file).read_text()
        assert "Persist" in content
        del os.environ["MEMORY_FILE_PATH"]

    def test_todo_persistence(self, temp_dir):
        """Verify todos write to file correctly."""
        todo_file = f"{temp_dir}/todos.json"
        os.environ["TODO_FILE_PATH"] = todo_file
        cam.reset_manager()
        t = cam._todo_create_todo("Persist")
        tid = t["created"]["id"]
        # Verify file was written
        assert Path(todo_file).exists()
        content = Path(todo_file).read_text()
        assert tid in content
        del os.environ["TODO_FILE_PATH"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
