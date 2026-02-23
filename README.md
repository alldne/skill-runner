# skill-runner

Minimal headless agent (~500 LOC) that executes `skill.md` files via any OpenAI-compatible Chat Completion API.

## Features

- **skill.md as system prompt** — write instructions in Markdown with optional YAML front matter
- **6 built-in tools** — `file_read`, `file_write`, `file_patch`, `bash`, `grep`, `glob`
- **Agentic loop** — calls API → parses tool_calls → executes → feeds back → repeats
- **Zero dependencies** — stdlib only (no pip install needed beyond the package itself)
- **Any OpenAI-compatible API** — OpenAI, Azure, local LLMs, etc.

## Install

```bash
pip install skill-runner
```

## Quick Start

1. Create a skill file (`hello.md`):

```markdown
---
tools: [bash]
max_turns: 3
---
# Hello Skill

You are a friendly assistant. Greet the user and run `echo "Hello!"` to demonstrate tools.
```

2. Run it:

```bash
echo "Hi there" | skill-runner --skill hello.md
```

## Usage

```bash
# Pipe input via stdin
echo "Review this code" | skill-runner --skill review.md

# Read input from file
skill-runner --skill review.md --input diff.txt

# Write output to file
skill-runner --skill review.md --input diff.txt --output result.json

# Custom API endpoint and model
skill-runner --skill review.md --input diff.txt \
  --api-base https://api.example.com/v1 \
  --model gpt-4o-mini

# Limit agent loop turns
skill-runner --skill review.md --input diff.txt --max-turns 10
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SKILL_RUNNER_BASE_URL` | API base URL | OpenAI default |
| `SKILL_RUNNER_API_KEY` | API key | `OPENAI_API_KEY` fallback |
| `SKILL_RUNNER_MODEL` | Model name | `gpt-4o` |

CLI flags (`--api-base`, `--model`) override environment variables.

## skill.md Format

A skill file is Markdown with an optional YAML front matter block:

```markdown
---
tools: [file_read, bash, grep]
max_turns: 20
---
# Your Skill Name

System prompt instructions go here...
```

**Front matter fields:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `tools` | list | all 6 tools | Which tools to enable |
| `max_turns` | int | 50 | Max agent loop iterations |

**Available tools:** `file_read`, `file_write`, `file_patch`, `bash`, `grep`, `glob`

## GitHub Actions Example

Use skill-runner for automated code review in CI:

```yaml
- name: Install skill-runner
  run: pip install skill-runner

- name: Run AI review
  run: |
    git diff origin/main...HEAD | skill-runner \
      --skill skills/code-review.md \
      --output /tmp/review.txt
  env:
    SKILL_RUNNER_API_KEY: ${{ secrets.LLM_API_KEY }}
    SKILL_RUNNER_MODEL: gpt-4o-mini
```

See [`examples/ai-review.yml`](examples/ai-review.yml) for a complete workflow.

## License

MIT
