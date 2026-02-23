"""Chat Completion API client using only stdlib (urllib)."""

from __future__ import annotations

import json
import os
import urllib.request
from dataclasses import dataclass

DEFAULT_BASE_URL = "https://api.openai.com/v1"


@dataclass
class Config:
    base_url: str = DEFAULT_BASE_URL
    api_key: str = ""
    model: str = "gpt-4o"

    @classmethod
    def from_env(cls) -> Config:
        return cls(
            base_url=os.environ.get(
                "SKILL_RUNNER_BASE_URL", DEFAULT_BASE_URL
            ),
            api_key=os.environ.get(
                "SKILL_RUNNER_API_KEY",
                os.environ.get("OPENAI_API_KEY", ""),
            ),
            model=os.environ.get("SKILL_RUNNER_MODEL", "gpt-4o"),
        )


def chat_completion(
    config: Config,
    messages: list[dict],
    tools: list[dict] | None = None,
) -> dict:
    """Call Chat Completion API and return the parsed JSON response."""
    url = f"{config.base_url.rstrip('/')}/chat/completions"

    body: dict = {"model": config.model, "messages": messages}
    if tools:
        body["tools"] = tools

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
    )

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
