#!/usr/bin/env python3
"""Deployment readiness: verify API and frontend URLs respond."""

from __future__ import annotations

import argparse
import os
import sys

import httpx

DEFAULT_API_URL = os.getenv("API_URL", os.getenv("PUBLIC_API_URL", "http://localhost:8000"))
DEFAULT_FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    os.getenv("PUBLIC_FRONTEND_URL", "http://localhost:5173"),
)


def check_url(name: str, url: str, *, expect_json: bool = False) -> None:
    try:
        response = httpx.get(url, timeout=15.0, follow_redirects=True)
    except httpx.HTTPError as exc:
        raise RuntimeError(f"{name} unreachable at {url}: {exc}") from exc

    if response.status_code >= 400:
        raise RuntimeError(f"{name} returned HTTP {response.status_code} for {url}")

    if expect_json:
        payload = response.json()
        if payload.get("status") != "ok":
            raise RuntimeError(f"{name} health payload unexpected: {payload!r}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check API and frontend availability.")
    parser.add_argument("--api-url", default=DEFAULT_API_URL, help="Backend base URL")
    parser.add_argument(
        "--frontend-url",
        default=DEFAULT_FRONTEND_URL,
        help="Frontend base URL (dev server or static host)",
    )
    parser.add_argument(
        "--skip-frontend",
        action="store_true",
        help="Only check API (useful behind reverse proxy with API-only health)",
    )
    args = parser.parse_args(argv)

    api_base = args.api_url.rstrip("/")
    frontend_base = args.frontend_url.rstrip("/")

    errors: list[str] = []

    try:
        check_url("API /health", f"{api_base}/health", expect_json=True)
        print(f"OK  API health  {api_base}/health")
    except RuntimeError as exc:
        errors.append(str(exc))
        print(f"FAIL API health  {exc}", file=sys.stderr)

    if not args.skip_frontend:
        try:
            check_url("Frontend", frontend_base)
            print(f"OK  Frontend     {frontend_base}")
        except RuntimeError as exc:
            errors.append(str(exc))
            print(f"FAIL Frontend     {exc}", file=sys.stderr)

    if errors:
        print(
            "\nHealth-check failed. Verify DNS, SSL, reverse proxy, and env URLs.",
            file=sys.stderr,
        )
        return 1

    print("\nHealth-check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
