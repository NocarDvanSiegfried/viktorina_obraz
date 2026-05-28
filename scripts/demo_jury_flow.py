#!/usr/bin/env python3
"""Day 22: full jury demo flow over HTTP API (material → edit → versions → student → exports)."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
_DEFAULT_REPORT = _REPO_ROOT / "docs" / "DEMO_JURY_REPORT.md"
_TIMEOUT = 120.0


def _load_smoke():
    path = _SCRIPTS / "smoke_api_check.py"
    spec = importlib.util.spec_from_file_location("smoke_embed_demo", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _extra_jury_checks(
    base_url: str,
    *,
    quiz_id: str,
    owner_id: str,
    frontend_url: str,
) -> tuple[int, int, list[str]]:
    smoke = _load_smoke()
    base = base_url.rstrip("/")
    results: list[bool] = []
    lines: list[str] = []

    with httpx.Client(base_url=base, timeout=_TIMEOUT) as client:
        versions = client.get(f"/quiz/{quiz_id}/versions", params={"owner_id": owner_id})
        version_items = (
            versions.json().get("versions", []) if versions.status_code == 200 else []
        )
        passed, line = smoke.ok(
            "versions count >= 2 (create + edit)",
            len(version_items) >= 2,
            f"count={len(version_items)}",
        )
        results.append(passed)
        lines.append(line)

    ui_base = (frontend_url or "http://127.0.0.1:8080").rstrip("/")
    ui_lines = [
        "",
        "## UI URLs for live demo",
        "",
        f"- Create: `{ui_base}/create`",
        f"- Edit: `{ui_base}/edit/{quiz_id}`",
        f"- Student: `{ui_base}/student/{quiz_id}`",
        f"- Results: `{ui_base}/results/{quiz_id}`",
        f"- Teacher: `{ui_base}/teacher/{quiz_id}`",
        "",
        f"- **owner_id** (localStorage): `{owner_id}`",
    ]
    for item in ui_lines:
        print(item)
        lines.append(item)

    return sum(results), len(results), lines


def write_demo_report(
    path: Path,
    *,
    base_url: str,
    frontend_url: str,
    passed: int,
    total: int,
    lines: list[str],
    quiz_id: str = "",
) -> None:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    status = "PASSED" if passed == total else "FAILED"
    body = [
        "# Jury demo flow report (API)",
        "",
        f"- **Date:** {now}",
        f"- **API:** `{base_url}`",
        f"- **Frontend:** `{frontend_url or '(set --frontend-url)'}`",
        f"- **Quiz ID:** `{quiz_id or '(n/a)'}`",
        f"- **Result:** **{status}** ({passed}/{total} checks)",
        "",
        "## Matrix (hackathon)",
        "",
        "| Step | API smoke |",
        "|------|-----------|",
        "| Material → generation | POST /quiz/generate-from-materials |",
        "| Edit + versions | PUT /quiz/{id}, GET /versions |",
        "| Source fragments | GET /quiz/{id} → fragments[] |",
        "| Student + score | /student/start → answer → finish |",
        "| Results | GET /quiz/{id}/results |",
        "| PDF + DOCX | export-pdf, export-docx |",
        "| Teacher (UI) | open /teacher/{id} manually |",
        "",
        "## Log",
        "",
        "```text",
        *lines,
        "```",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run full jury demo API flow and optional report."
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("SMOKE_API_URL", os.getenv("API_URL", "http://127.0.0.1:8000")),
    )
    parser.add_argument(
        "--frontend-url",
        default=os.getenv("FRONTEND_URL", os.getenv("PUBLIC_FRONTEND_URL", "http://127.0.0.1:8080")),
    )
    parser.add_argument("--report", default=str(_DEFAULT_REPORT))
    parser.add_argument("--skip-report", action="store_true")
    args = parser.parse_args(argv)

    smoke = _load_smoke()
    api_url = args.api_url.rstrip("/")
    print(f"Jury demo API flow -> {api_url}\n")

    passed, total, lines, meta = smoke.run_smoke(api_url)
    all_lines = list(lines)

    if meta:
        extra_passed, extra_total, extra_lines = _extra_jury_checks(
            api_url,
            quiz_id=meta["quiz_id"],
            owner_id=meta["owner_id"],
            frontend_url=args.frontend_url,
        )
        passed += extra_passed
        total += extra_total
        all_lines.extend(extra_lines)
        quiz_id = meta["quiz_id"]
    else:
        quiz_id = ""

    if not args.skip_report:
        write_demo_report(
            Path(args.report),
            base_url=api_url,
            frontend_url=args.frontend_url,
            passed=passed,
            total=total,
            lines=all_lines,
            quiz_id=quiz_id,
        )
        print(f"\nReport: {args.report}")

    if passed != total:
        return 1
    print("\nJury demo API flow passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
