"""Tests for the agent loop using mock API responses."""

from __future__ import annotations

from unittest.mock import patch

from skill_runner.api import Config
from skill_runner.loop import run
from skill_runner.skill import Skill


def _make_text_response(content: str) -> dict:
    """Create a mock API response with text content only."""
    return {
        "choices": [
            {"message": {"role": "assistant", "content": content}}
        ]
    }


def _make_tool_response(tool_calls: list[dict]) -> dict:
    """Create a mock API response with tool calls."""
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": tc["id"],
                            "type": "function",
                            "function": {
                                "name": tc["name"],
                                "arguments": tc["arguments"],
                            },
                        }
                        for tc in tool_calls
                    ],
                }
            }
        ]
    }


CONFIG = Config(base_url="http://fake", api_key="fake", model="test-model")


@patch("skill_runner.loop.chat_completion")
def test_text_only_response(mock_api):
    """Loop returns immediately on text-only response."""
    mock_api.return_value = _make_text_response("Hello!")

    skill = Skill(system_prompt="You are helpful.", allowed_tools=[], max_turns=10)
    result = run(skill, "Hi", CONFIG)
    assert result == "Hello!"
    assert mock_api.call_count == 1


@patch("skill_runner.loop.chat_completion")
def test_tool_call_then_text(mock_api, tmp_path):
    """Loop executes tool, feeds result back, then gets text response."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("file content here\n")

    mock_api.side_effect = [
        _make_tool_response(
            [
                {
                    "id": "call_1",
                    "name": "file_read",
                    "arguments": f'{{"path": "{test_file}"}}',
                }
            ]
        ),
        _make_text_response("I read the file. It says: file content here"),
    ]

    skill = Skill(
        system_prompt="Read files when asked.",
        allowed_tools=["file_read"],
        max_turns=10,
    )
    result = run(skill, "Read the test file", CONFIG)
    assert "file content here" in result
    assert mock_api.call_count == 2


@patch("skill_runner.loop.chat_completion")
def test_max_turns_reached(mock_api):
    """Loop stops at max_turns and returns sentinel."""
    mock_api.return_value = _make_tool_response(
        [{"id": "call_1", "name": "bash", "arguments": '{"command": "echo hi"}'}]
    )

    skill = Skill(
        system_prompt="Keep going.",
        allowed_tools=["bash"],
        max_turns=3,
    )
    result = run(skill, "Loop forever", CONFIG)
    assert result == "[max_turns reached]"
    assert mock_api.call_count == 3
