#!/usr/bin/env python3
"""Day 20: run API smoke + optional health check; write PROD_SMOKE_REPORT.md."""

from __future__ import annotations

import argparse
import importlib.util
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
_DEFAULT_REPORT = _REPO_ROOT / "docs" / "PROD_SMOKE_REPORT.md"


def _load(name: str, filename: str):
    path = _SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Production smoke: API + health + report.")
    parser.add_argument(
        "--api-url",
        default=os.getenv("SMOKE_API_URL", os.getenv("API_URL", "http://127.0.0.1:8000")),
    )
    parser.add_argument(
        "--frontend-url",
        default=os.getenv("FRONTEND_URL", os.getenv("PUBLIC_FRONTEND_URL", "http://127.0.0.1:8080")),
    )
    parser.add_argument(
        "--report",
        default=str(_DEFAULT_REPORT),
        help="Markdown report output path",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip frontend/API health_check.py",
    )
    args = parser.parse_args(argv)

    smoke = _load("smoke_embed", "smoke_api_check.py")
    passed, total, lines, _meta = smoke.run_smoke(args.api_url.rstrip("/"))

    health_errors: list[str] = []
    if not args.skip_health:
        health = _load("health_embed", "health_check.py")
        api_base = args.api_url.rstrip("/")
        frontend_base = args.frontend_url.rstrip("/")
        try:
            health.check_url(f"{api_base}/health", f"{api_base}/health", expect_json=True)
            print(f"OK  Health API  {api_base}/health")
        except RuntimeError as exc:
            health_errors.append(str(exc))
            print(f"FAIL Health API  {exc}", file=sys.stderr)

        if frontend_base:
            try:
                health.check_url("Frontend", frontend_base)
                print(f"OK  Health UI   {frontend_base}")
            except RuntimeError as exc:
                health_errors.append(str(exc))
                print(f"FAIL Health UI   {exc}", file=sys.stderr)

    if health_errors:
        for item in health_errors:
            lines.append(f"  [FAIL] Health — {item}")

    smoke.write_report(
        Path(args.report),
        base_url=args.api_url.rstrip("/"),
        passed=passed,
        total=total,
        lines=lines,
        frontend_url=args.frontend_url,
    )
    print(f"\nReport: {args.report}")

    if passed != total or health_errors:
        return 1
    print("\nProduction smoke run passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
