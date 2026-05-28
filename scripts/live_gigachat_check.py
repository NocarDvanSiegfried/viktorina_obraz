#!/usr/bin/env python3
"""Verify real GigaChat text generation (not E2E mock)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from live_gigachat_env import print_environment_header, validate_live_environment

from app.core.config import settings  # noqa: E402
from app.schemas.material import SourceFragment  # noqa: E402
from app.services.quiz_service import quiz_service  # noqa: E402


def run_live_generation() -> dict:
    fragments = [
        SourceFragment(
            fragment_id="manual_1",
            source_type="manual_text",
            source_name="live_check",
            text=(
                "Клетка — основная структурная и функциональная единица живых организмов. "
                "Клеточная мембрана отделяет внутреннее содержимое клетки от внешней среды."
            ),
        )
    ]
    result = quiz_service.generate_quiz_from_fragments(
        subject="Биология",
        grade="8",
        topic="Клетка",
        question_count=2,
        question_types=["single_choice", "true_false"],
        difficulty="easy",
        fragments=fragments,
    )
    return {
        "quiz_title": result.quiz_title,
        "question_count": len(result.questions),
        "first_question": result.questions[0].text if result.questions else "",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Live GigaChat check: real quiz generation without mock."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable summary on success",
    )
    args = parser.parse_args(argv)

    env_errors = validate_live_environment()
    if env_errors:
        for message in env_errors:
            print(f"FAIL {message}", file=sys.stderr)
        return 1

    print_environment_header()

    try:
        summary = run_live_generation()
    except Exception as exc:
        print(f"FAIL GigaChat generation: {exc}", file=sys.stderr)
        return 1

    print("OK  GigaChat generation")
    print(f"    title={summary['quiz_title']!r}")
    print(f"    questions={summary['question_count']}")
    if summary["first_question"]:
        preview = summary["first_question"][:120]
        print(f"    first_question={preview!r}")

    if args.json:
        print(
            json.dumps(
                {
                    "status": "ok",
                    "model": settings.GIGACHAT_MODEL,
                    **summary,
                },
                ensure_ascii=False,
            )
        )

    print("\nLive GigaChat check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
