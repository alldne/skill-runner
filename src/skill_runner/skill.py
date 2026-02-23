"""skill.md parser — loads markdown with optional YAML front matter."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

DEFAULT_MAX_TURNS = 50
ALL_TOOLS = ["file_read", "file_write", "file_patch", "bash", "grep", "glob"]


@dataclass
class Skill:
    system_prompt: str
    allowed_tools: list[str] = field(default_factory=lambda: list(ALL_TOOLS))
    max_turns: int = DEFAULT_MAX_TURNS


def _parse_front_matter(text: str) -> tuple[dict, str]:
    """Extract YAML front matter (between --- delimiters) and body.

    Uses simple regex parsing to avoid PyYAML dependency.
    Only supports `tools` (list) and `max_turns` (int).
    """
    m = re.match(r"\A---\s*\n(.*?)\n---\s*\n(.*)", text, re.DOTALL)
    if not m:
        return {}, text

    raw, body = m.group(1), m.group(2)
    meta: dict = {}

    # Parse tools: [file_read, bash]
    tools_match = re.search(r"tools:\s*\[([^\]]*)\]", raw)
    if tools_match:
        meta["tools"] = [t.strip() for t in tools_match.group(1).split(",") if t.strip()]

    # Parse max_turns: 20
    turns_match = re.search(r"max_turns:\s*(\d+)", raw)
    if turns_match:
        meta["max_turns"] = int(turns_match.group(1))

    return meta, body


def load_skill(path: str) -> Skill:
    """Load a skill.md file and return a Skill instance."""
    with open(path) as f:
        text = f.read()

    meta, body = _parse_front_matter(text)

    allowed_tools = meta.get("tools", list(ALL_TOOLS))
    # Validate tool names
    for t in allowed_tools:
        if t not in ALL_TOOLS:
            raise ValueError(f"Unknown tool in front matter: {t}")

    return Skill(
        system_prompt=body.strip(),
        allowed_tools=allowed_tools,
        max_turns=meta.get("max_turns", DEFAULT_MAX_TURNS),
    )
