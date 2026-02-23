"""Agent loop — the core of skill-runner.

Calls Chat Completion API, parses tool_calls, executes tools, feeds results
back, and repeats until a text-only response or max_turns is reached.
"""

from __future__ import annotations

import sys

from .api import Config, chat_completion
from .skill import Skill
from .tools import execute_tool, get_tool_schemas


def run(
    skill: Skill,
    user_input: str,
    config: Config,
) -> str:
    """Execute the agent loop and return the final text response."""
    tools = get_tool_schemas(skill.allowed_tools)
    messages: list[dict] = [
        {"role": "system", "content": skill.system_prompt},
        {"role": "user", "content": user_input},
    ]

    for turn in range(skill.max_turns):
        resp = chat_completion(
            config, messages, tools=tools if tools else None
        )
        message = resp["choices"][0]["message"]

        # Text-only response — done
        tool_calls = message.get("tool_calls")
        if not tool_calls:
            return message.get("content", "")

        # Tool calls — execute and continue
        messages.append(message)

        for call in tool_calls:
            fn = call["function"]
            args_str = fn["arguments"]
            print(
                f"  [turn {turn + 1}] {fn['name']}({args_str[:80]}...)"
                if len(args_str) > 80
                else f"  [turn {turn + 1}] {fn['name']}({args_str})",
                file=sys.stderr,
            )
            result = execute_tool(fn["name"], args_str)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call["id"],
                    "content": result,
                }
            )

    return "[max_turns reached]"
