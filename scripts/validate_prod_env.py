#!/usr/bin/env python3
"""Validate backend environment file for production deployment."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_ENV = _REPO_ROOT / "backend" / ".env.production"

REQUIRED_KEYS = (
    "GIGACHAT_AUTH_KEY",
    "GIGACHAT_SCOPE",
    "GIGACHAT_MODEL",
    "GIGACHAT_VISION_MODEL",
    "FRONTEND_ORIGIN",
    "DATABASE_URL",
)

RECOMMENDED_KEYS = ("GIGACHAT_CA_BUNDLE_FILE",)

TRUTHY = {"1", "true", "yes", "on"}


def parse_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def validate_env_values(
    values: dict[str, str],
    *,
    production: bool,
) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_KEYS:
        if not values.get(key):
            errors.append(f"Missing or empty: {key}")

    if production and values.get("E2E_MOCK_GIGACHAT", "").lower() in TRUTHY:
        errors.append(
            "E2E_MOCK_GIGACHAT must be disabled in production (remove or set to 0)"
        )

    if production:
        origin = values.get("FRONTEND_ORIGIN", "")
        if origin.startswith("http://localhost") or origin.startswith("http://127.0.0.1"):
            errors.append(
                f"FRONTEND_ORIGIN looks like local dev ({origin}); set public HTTPS URL"
            )

    gigachat_key = values.get("GIGACHAT_AUTH_KEY", "")
    if gigachat_key.lower() in PLACEHOLDER_KEYS:
        errors.append("GIGACHAT_AUTH_KEY must be a real key, not a placeholder")

    return errors


def validate_env_file(path: Path, *, production: bool) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"Env file not found: {path}"]

    values = parse_env_file(path)
    errors.extend(validate_env_values(values, production=production))

    for key in RECOMMENDED_KEYS:
        if not values.get(key):
            print(f"WARN Recommended variable not set: {key}", file=sys.stderr)

    return errors


PLACEHOLDER_KEYS = {"", "changeme", "your_key", "xxx", "test", "string"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate production backend .env")
    parser.add_argument(
        "--env-file",
        default=str(_DEFAULT_ENV),
        help="Path to backend .env file",
    )
    parser.add_argument(
        "--production",
        action="store_true",
        help="Strict production rules (no mock, no localhost CORS)",
    )
    args = parser.parse_args(argv)

    env_path = Path(args.env_file)
    errors = validate_env_file(env_path, production=args.production)

    if errors:
        print(f"FAIL Env validation ({env_path})", file=sys.stderr)
        for message in errors:
            print(f"  - {message}", file=sys.stderr)
        return 1

    print(f"OK  Env validation ({env_path})")
    if args.production:
        print("    mode=production")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
