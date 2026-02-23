"""Tool definitions and execution for the agent loop.

Six tools: file_read, file_write, file_patch, bash, grep, glob.
Each tool is a plain function that returns a string result.
"""

from __future__ import annotations

import fnmatch
import json
import os
import re
import subprocess
from pathlib import Path

# ---------- blocked commands for bash tool ----------

BLOCKED_COMMANDS = [
    "rm -rf /",
    "rm -rf /*",
    "git push --force",
    "git push -f",
    "mkfs.",
    "dd if=/dev/zero",
    ":(){ :|:& };:",
    "> /dev/sda",
]

# ---------- tool implementations ----------


def file_read(path: str, offset: int = 0, limit: int = 2000) -> str:
    """Read a file and return its contents with line numbers."""
    try:
        with open(path) as f:
            lines = f.readlines()
        selected = lines[offset : offset + limit]
        numbered = [f"{offset + i + 1}\t{line}" for i, line in enumerate(selected)]
        return "".join(numbered)
    except Exception as e:
        return f"[ERROR] {e}"


def file_write(path: str, content: str) -> str:
    """Write content to a file, creating parent directories if needed."""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            f.write(content)
        return f"[OK] Wrote {len(content)} bytes to {path}"
    except Exception as e:
        return f"[ERROR] {e}"


def file_patch(path: str, old_string: str, new_string: str) -> str:
    """Replace old_string with new_string in a file."""
    try:
        with open(path) as f:
            content = f.read()
        if old_string not in content:
            return f"[ERROR] old_string not found in {path}"
        count = content.count(old_string)
        if count > 1:
            return f"[ERROR] old_string found {count} times in {path} (must be unique)"
        patched = content.replace(old_string, new_string, 1)
        with open(path, "w") as f:
            f.write(patched)
        return f"[OK] Patched {path}"
    except Exception as e:
        return f"[ERROR] {e}"


def bash(command: str, timeout: int = 30) -> str:
    """Execute a shell command with timeout and safety checks."""
    for blocked in BLOCKED_COMMANDS:
        if blocked in command:
            return f"[BLOCKED] Dangerous command detected: {blocked}"
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        if len(output) > 50000:
            output = output[:50000] + "\n[TRUNCATED]"
        return output if output else "[OK] (no output)"
    except subprocess.TimeoutExpired:
        return f"[ERROR] Command timed out after {timeout}s"
    except Exception as e:
        return f"[ERROR] {e}"


def grep(pattern: str, path: str = ".", include: str = "") -> str:
    """Search file contents using regex pattern."""
    try:
        results = []
        search_path = Path(path)

        if search_path.is_file():
            files = [search_path]
        else:
            glob_pattern = include if include else "**/*"
            files = sorted(search_path.glob(glob_pattern))

        regex = re.compile(pattern)
        for fpath in files:
            if not fpath.is_file():
                continue
            try:
                with open(fpath) as f:
                    for lineno, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append(f"{fpath}:{lineno}:{line.rstrip()}")
            except (UnicodeDecodeError, PermissionError):
                continue

        if not results:
            return "[NO MATCHES]"
        output = "\n".join(results)
        if len(output) > 50000:
            output = output[:50000] + "\n[TRUNCATED]"
        return output
    except Exception as e:
        return f"[ERROR] {e}"


def glob_search(pattern: str, path: str = ".") -> str:
    """Find files matching a glob pattern."""
    try:
        search_path = Path(path)
        matches = sorted(str(p) for p in search_path.glob(pattern) if p.is_file())
        if not matches:
            return "[NO MATCHES]"
        return "\n".join(matches)
    except Exception as e:
        return f"[ERROR] {e}"


# ---------- tool registry ----------

TOOL_FUNCTIONS = {
    "file_read": file_read,
    "file_write": file_write,
    "file_patch": file_patch,
    "bash": bash,
    "grep": grep,
    "glob": glob_search,
}

TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "file_read",
            "description": "Read a file and return its contents with line numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "offset": {
                        "type": "integer",
                        "description": "Line offset to start reading from (0-based)",
                        "default": 0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of lines to read",
                        "default": 2000,
                    },
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_write",
            "description": "Write content to a file, creating parent directories if needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "content": {
                        "type": "string",
                        "description": "Content to write",
                    },
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "file_patch",
            "description": "Replace old_string with new_string in a file. The old_string must appear exactly once.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Path to the file"},
                    "old_string": {
                        "type": "string",
                        "description": "The exact string to find",
                    },
                    "new_string": {
                        "type": "string",
                        "description": "The replacement string",
                    },
                },
                "required": ["path", "old_string", "new_string"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a shell command and return stdout+stderr. Dangerous commands are blocked.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell command to execute",
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Timeout in seconds",
                        "default": 30,
                    },
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "grep",
            "description": "Search file contents using a regex pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Regex pattern to search for",
                    },
                    "path": {
                        "type": "string",
                        "description": "File or directory to search in",
                        "default": ".",
                    },
                    "include": {
                        "type": "string",
                        "description": "Glob pattern to filter files (e.g. '**/*.py')",
                        "default": "",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "glob",
            "description": "Find files matching a glob pattern.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {
                        "type": "string",
                        "description": "Glob pattern (e.g. '**/*.py')",
                    },
                    "path": {
                        "type": "string",
                        "description": "Base directory to search from",
                        "default": ".",
                    },
                },
                "required": ["pattern"],
            },
        },
    },
]


def get_tool_schemas(allowed_tools: list[str]) -> list[dict]:
    """Return OpenAI function calling schemas for allowed tools."""
    return [s for s in TOOL_SCHEMAS if s["function"]["name"] in allowed_tools]


def execute_tool(name: str, arguments: str) -> str:
    """Execute a tool by name with JSON arguments string."""
    func = TOOL_FUNCTIONS.get(name)
    if not func:
        return f"[ERROR] Unknown tool: {name}"
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError as e:
        return f"[ERROR] Invalid JSON arguments: {e}"
    try:
        return func(**args)
    except TypeError as e:
        return f"[ERROR] Invalid arguments for {name}: {e}"
