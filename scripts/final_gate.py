#!/usr/bin/env python3
"""Day 22: developer final gate — tests, secrets, optional API demo (no presentation assets)."""

from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND = _REPO_ROOT / "backend"
_FRONTEND = _REPO_ROOT / "frontend"
_SCRIPTS = _REPO_ROOT / "scripts"


def _run(command: list[str], *, cwd: Path, label: str) -> bool:
    print(f"\n==> {label}")
    print("    " + " ".join(command))
    result = subprocess.run(command, cwd=cwd, check=False)
    if result.returncode != 0:
        print(f"FAIL {label} (exit {result.returncode})")
        return False
    print(f"OK   {label}")
    return True


def _load_script(name: str, filename: str):
    path = _SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Final development gate before defense.")
    parser.add_argument(
        "--skip-pytest",
        action="store_true",
        help="Skip backend pytest",
    )
    parser.add_argument(
        "--skip-frontend-build",
        action="store_true",
        help="Skip npm run build",
    )
    parser.add_argument(
        "--skip-secrets",
        action="store_true",
        help="Skip secrets scan",
    )
    parser.add_argument(
        "--run-demo-api",
        action="store_true",
        help="Run demo_jury_flow.py (requires running backend)",
    )
    parser.add_argument(
        "--api-url",
        default=os.getenv("API_URL", os.getenv("SMOKE_API_URL", "http://127.0.0.1:8000")),
        help="API base for demo_jury_flow",
    )
    parser.add_argument(
        "--frontend-url",
        default=os.getenv("FRONTEND_URL", os.getenv("PUBLIC_FRONTEND_URL", "")),
    )
    args = parser.parse_args(argv)

    ok = True

    if not args.skip_pytest:
        ok &= _run(
            [sys.executable, "-m", "pytest", "-q", "-m", "not integration"],
            cwd=_BACKEND,
            label="backend pytest",
        )

    if not args.skip_frontend_build:
        npm = "npm.cmd" if sys.platform == "win32" else "npm"
        ok &= _run([npm, "run", "build"], cwd=_FRONTEND, label="frontend build")

    if not args.skip_secrets:
        secrets = _load_script("check_secrets_gate", "check_secrets.py")
        findings = secrets.scan_repository(_REPO_ROOT)
        if findings:
            print("\nFAIL secrets scan:")
            for item in findings:
                print(f"  - {item}")
            ok = False
        else:
            print("\nOK   secrets scan")

    if args.run_demo_api and args.api_url.strip():
        demo = _load_script("demo_jury_gate", "demo_jury_flow.py")
        demo_argv = [
            "--api-url",
            args.api_url.rstrip("/"),
            "--skip-report",
        ]
        if args.frontend_url.strip():
            demo_argv.extend(["--frontend-url", args.frontend_url.rstrip("/")])
        code = demo.main(demo_argv)
        if code != 0:
            print("\nFAIL demo_jury_flow API")
            ok = False
        else:
            print("\nOK   demo_jury_flow API")

    if ok:
        print("\nFinal gate passed.")
        return 0
    print("\nFinal gate failed.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
