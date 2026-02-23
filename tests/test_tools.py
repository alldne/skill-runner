"""Tests for tool implementations."""

import json
import os
import tempfile

from skill_runner.tools import (
    bash,
    execute_tool,
    file_patch,
    file_read,
    file_write,
    get_tool_schemas,
    glob_search,
    grep,
)


class TestFileRead:
    def test_read_file(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("line1\nline2\nline3\n")
        result = file_read(str(p))
        assert "1\tline1" in result
        assert "3\tline3" in result

    def test_read_with_offset(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("line1\nline2\nline3\n")
        result = file_read(str(p), offset=1, limit=1)
        assert "2\tline2" in result
        assert "line1" not in result

    def test_read_nonexistent(self):
        result = file_read("/nonexistent/file.txt")
        assert "[ERROR]" in result


class TestFileWrite:
    def test_write_file(self, tmp_path):
        p = tmp_path / "output.txt"
        result = file_write(str(p), "hello world")
        assert "[OK]" in result
        assert p.read_text() == "hello world"

    def test_write_creates_dirs(self, tmp_path):
        p = tmp_path / "sub" / "dir" / "file.txt"
        result = file_write(str(p), "nested")
        assert "[OK]" in result
        assert p.read_text() == "nested"


class TestFilePatch:
    def test_patch_unique(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("hello world")
        result = file_patch(str(p), "hello", "goodbye")
        assert "[OK]" in result
        assert p.read_text() == "goodbye world"

    def test_patch_not_found(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("hello world")
        result = file_patch(str(p), "missing", "replacement")
        assert "[ERROR]" in result
        assert "not found" in result

    def test_patch_multiple_matches(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("aaa aaa")
        result = file_patch(str(p), "aaa", "bbb")
        assert "[ERROR]" in result
        assert "2 times" in result


class TestBash:
    def test_simple_command(self):
        result = bash("echo hello")
        assert "hello" in result

    def test_blocked_rm_rf(self):
        result = bash("rm -rf /")
        assert "[BLOCKED]" in result

    def test_blocked_force_push(self):
        result = bash("git push --force")
        assert "[BLOCKED]" in result

    def test_timeout(self):
        result = bash("sleep 10", timeout=1)
        assert "[ERROR]" in result
        assert "timed out" in result

    def test_stderr_captured(self):
        result = bash("ls /nonexistent_dir_12345 2>&1 || true")
        # Should have some output (error message)
        assert result  # non-empty


class TestGrep:
    def test_grep_file(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("hello world\nfoo bar\nhello again\n")
        result = grep("hello", str(p))
        assert "1:" in result
        assert "3:" in result

    def test_grep_no_match(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("nothing here\n")
        result = grep("missing", str(p))
        assert "[NO MATCHES]" in result

    def test_grep_directory(self, tmp_path):
        (tmp_path / "a.py").write_text("import os\n")
        (tmp_path / "b.py").write_text("import sys\n")
        result = grep("import", str(tmp_path), include="*.py")
        assert "a.py" in result
        assert "b.py" in result


class TestGlob:
    def test_glob_pattern(self, tmp_path):
        (tmp_path / "a.py").write_text("")
        (tmp_path / "b.py").write_text("")
        (tmp_path / "c.txt").write_text("")
        result = glob_search("*.py", str(tmp_path))
        assert "a.py" in result
        assert "b.py" in result
        assert "c.txt" not in result

    def test_glob_no_match(self, tmp_path):
        result = glob_search("*.xyz", str(tmp_path))
        assert "[NO MATCHES]" in result


class TestExecuteTool:
    def test_execute_known_tool(self, tmp_path):
        p = tmp_path / "test.txt"
        p.write_text("content")
        result = execute_tool("file_read", json.dumps({"path": str(p)}))
        assert "content" in result

    def test_execute_unknown_tool(self):
        result = execute_tool("unknown", "{}")
        assert "[ERROR]" in result
        assert "Unknown tool" in result

    def test_execute_invalid_json(self):
        result = execute_tool("file_read", "not json")
        assert "[ERROR]" in result


class TestGetToolSchemas:
    def test_all_tools(self):
        schemas = get_tool_schemas(["file_read", "file_write", "file_patch", "bash", "grep", "glob"])
        assert len(schemas) == 6

    def test_filtered_tools(self):
        schemas = get_tool_schemas(["file_read", "bash"])
        assert len(schemas) == 2
        names = {s["function"]["name"] for s in schemas}
        assert names == {"file_read", "bash"}
