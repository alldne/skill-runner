"""CLI entry point: python -m skill_runner"""

from __future__ import annotations

import argparse
import sys

from .api import Config
from .loop import run
from .skill import load_skill


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="skill-runner",
        description="Headless agent that executes skill.md files via Chat Completion API",
    )
    parser.add_argument(
        "--skill", required=True, help="Path to a skill.md file"
    )
    parser.add_argument(
        "--input",
        default=None,
        help="Path to input file (reads stdin if omitted)",
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Path to output file (prints to stdout if omitted)",
    )
    parser.add_argument(
        "--api-base",
        default=None,
        help="API base URL (overrides SKILL_RUNNER_BASE_URL)",
    )
    parser.add_argument(
        "--model",
        default=None,
        help="Model name (overrides SKILL_RUNNER_MODEL)",
    )
    parser.add_argument(
        "--max-turns",
        type=int,
        default=None,
        help="Max agent loop turns (overrides skill front matter)",
    )

    args = parser.parse_args()

    # Load skill
    skill = load_skill(args.skill)
    if args.max_turns is not None:
        skill.max_turns = args.max_turns

    # Build config from env, then override with CLI args
    config = Config.from_env()
    if args.api_base:
        config.base_url = args.api_base
    if args.model:
        config.model = args.model

    # Read user input
    if args.input:
        with open(args.input) as f:
            user_input = f.read()
    elif not sys.stdin.isatty():
        user_input = sys.stdin.read()
    else:
        print("Error: No input provided. Use --input FILE or pipe via stdin.", file=sys.stderr)
        sys.exit(1)

    # Run agent loop
    result = run(skill=skill, user_input=user_input, config=config)

    # Output result
    if args.output:
        with open(args.output, "w") as f:
            f.write(result)
        print(f"Result written to {args.output}", file=sys.stderr)
    else:
        print(result)


if __name__ == "__main__":
    main()
