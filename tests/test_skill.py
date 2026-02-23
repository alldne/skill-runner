"""Tests for skill.md parser."""

import os
import tempfile

from skill_runner.skill import ALL_TOOLS, DEFAULT_MAX_TURNS, load_skill


def _write_tmp(content: str) -> str:
    fd, path = tempfile.mkstemp(suffix=".md")
    with os.fdopen(fd, "w") as f:
        f.write(content)
    return path


def test_plain_markdown():
    """Skill with no front matter — entire file is system prompt."""
    path = _write_tmp("# Hello\n\nDo something useful.")
    skill = load_skill(path)
    assert skill.system_prompt == "# Hello\n\nDo something useful."
    assert skill.allowed_tools == ALL_TOOLS
    assert skill.max_turns == DEFAULT_MAX_TURNS
    os.unlink(path)


def test_front_matter_tools():
    """Skill with tools restriction in front matter."""
    path = _write_tmp("---\ntools: [file_read, bash]\n---\n# Review\nReview code.")
    skill = load_skill(path)
    assert skill.allowed_tools == ["file_read", "bash"]
    assert skill.system_prompt == "# Review\nReview code."
    os.unlink(path)


def test_front_matter_max_turns():
    """Skill with max_turns in front matter."""
    path = _write_tmp("---\nmax_turns: 10\n---\n# Short\nQuick task.")
    skill = load_skill(path)
    assert skill.max_turns == 10
    assert skill.allowed_tools == ALL_TOOLS
    os.unlink(path)


def test_front_matter_both():
    """Skill with both tools and max_turns."""
    path = _write_tmp("---\ntools: [grep, glob]\nmax_turns: 5\n---\n# Search\nFind files.")
    skill = load_skill(path)
    assert skill.allowed_tools == ["grep", "glob"]
    assert skill.max_turns == 5
    os.unlink(path)


def test_invalid_tool_raises():
    """Unknown tool name in front matter raises ValueError."""
    path = _write_tmp("---\ntools: [file_read, unknown_tool]\n---\n# Bad\nFail.")
    try:
        load_skill(path)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "unknown_tool" in str(e)
    finally:
        os.unlink(path)
