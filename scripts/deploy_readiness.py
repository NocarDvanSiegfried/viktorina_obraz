#!/usr/bin/env python3
"""Production deploy readiness: secrets audit + env validation + optional health URLs."""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"


def _load_script_module(module_name: str, filename: str):
    path = _SCRIPTS / filename
    spec = importlib.util.spec_from_file_location(module_name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_secrets_check(repo_root: Path) -> list[str]:
    module = _load_script_module("check_secrets_embed", "check_secrets.py")
    findings = module.scan_repository(repo_root)
    return findings


def run_env_validation(env_file: Path, *, production: bool) -> list[str]:
    module = _load_script_module("validate_prod_env_embed", "validate_prod_env.py")
    return module.validate_env_file(env_file, production=production)


def run_health_check(api_url: str, frontend_url: str, *, skip_frontend: bool) -> list[str]:
    module = _load_script_module("health_check_embed", "health_check.py")
    errors: list[str] = []
    try:
        module.check_url("API /health", f"{api_url.rstrip('/')}/health", expect_json=True)
    except RuntimeError as exc:
        errors.append(str(exc))

    if not skip_frontend:
        try:
            module.check_url("Frontend", frontend_url.rstrip("/"))
        except RuntimeError as exc:
            errors.append(str(exc))

    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Full production deploy readiness check.")
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help="Repository root",
    )
    parser.add_argument(
        "--env-file",
        default=str(_REPO_ROOT / "backend" / ".env.production"),
        help="Backend .env for validation",
    )
    parser.add_argument("--api-url", default="", help="Public API base URL (optional)")
    parser.add_argument("--frontend-url", default="", help="Public UI URL (optional)")
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip HTTP health checks",
    )
    parser.add_argument(
        "--skip-frontend-health",
        action="store_true",
        help="Only check API /health",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    env_file = Path(args.env_file)
    failed = False

    secret_findings = run_secrets_check(repo_root)
    if secret_findings:
        failed = True
        print("FAIL Secrets audit", file=sys.stderr)
        for item in secret_findings:
            print(f"  - {item}", file=sys.stderr)
    else:
        print("OK  Secrets audit")

    env_errors = run_env_validation(env_file, production=True)
    if env_errors:
        failed = True
        print("FAIL Env validation", file=sys.stderr)
        for item in env_errors:
            print(f"  - {item}", file=sys.stderr)
    else:
        print(f"OK  Env validation ({env_file})")

    if not args.skip_health and args.api_url:
        health_errors = run_health_check(
            args.api_url,
            args.frontend_url or args.api_url,
            skip_frontend=args.skip_frontend_health or not args.frontend_url,
        )
        if health_errors:
            failed = True
            print("FAIL Health check", file=sys.stderr)
            for item in health_errors:
                print(f"  - {item}", file=sys.stderr)
        else:
            print(f"OK  Health check  API={args.api_url.rstrip('/')}/health")
            if args.frontend_url and not args.skip_frontend_health:
                print(f"    Frontend={args.frontend_url}")

    if failed:
        print("\nDeploy readiness check failed.", file=sys.stderr)
        return 1

    print("\nDeploy readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
