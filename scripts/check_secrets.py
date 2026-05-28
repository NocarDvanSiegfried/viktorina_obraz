#!/usr/bin/env python3
"""Scan repository for leaked secrets and forbidden tracked .env files."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_RELATIVE_PATHS = (
    "backend/.env",
    "backend/.env.production",
    "frontend/.env",
    "frontend/.env.production",
    ".env",
    ".env.production",
)

SECRET_LINE_PATTERNS = (
    re.compile(r"GIGACHAT_AUTH_KEY\s*=\s*(\S+)"),
    re.compile(r"GIGACHAT_AUTH_KEY\s*:\s*['\"]([^'\"]+)['\"]"),
)

SKIP_SCAN_SUFFIXES = (
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".pdf",
    ".pptx",
    ".db",
    ".crt",
    ".woff",
    ".woff2",
    ".pyc",
)

ALLOWED_SECRET_FILENAMES = (
    ".env.example",
    ".env.production.example",
)


def scan_text(relative_path: str, content: str) -> list[str]:
    normalized = relative_path.replace("\\", "/")
    if normalized.endswith(ALLOWED_SECRET_FILENAMES) or any(
        part.endswith(".example") for part in normalized.split("/")
    ):
        return []

    if any(normalized.endswith(suffix) for suffix in SKIP_SCAN_SUFFIXES):
        return []

    findings: list[str] = []
    for pattern in SECRET_LINE_PATTERNS:
        for match in pattern.finditer(content):
            value = match.group(1).strip()
            if not value or value.lower() in {"changeme", "your_key", "xxx"}:
                continue
            findings.append(
                f"{relative_path}: possible GIGACHAT_AUTH_KEY value committed"
            )
    return findings


def git_tracked_files(repo_root: Path) -> list[str] | None:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None

    return [
        line.strip().replace("\\", "/")
        for line in result.stdout.splitlines()
        if line.strip()
    ]


def git_tracked_forbidden_env(tracked_files: list[str]) -> list[str]:
    tracked_set = set(tracked_files)
    findings: list[str] = []
    for rel in FORBIDDEN_RELATIVE_PATHS:
        if rel in tracked_set:
            findings.append(f"git tracks forbidden file: {rel}")
    return findings


def scan_tracked_files(repo_root: Path, tracked_files: list[str]) -> list[str]:
    findings: list[str] = []
    for relative in tracked_files:
        file_path = repo_root / relative
        if not file_path.is_file():
            continue
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        findings.extend(scan_text(relative, content))
    return findings


def scan_repository(repo_root: Path) -> list[str]:
    tracked = git_tracked_files(repo_root)
    if tracked is None:
        return ["git repository not found — run from project root with git init"]

    findings: list[str] = []
    findings.extend(git_tracked_forbidden_env(tracked))
    findings.extend(scan_tracked_files(repo_root, tracked))
    return sorted(set(findings))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan repo for leaked secrets.")
    parser.add_argument(
        "--repo-root",
        default=str(_REPO_ROOT),
        help="Repository root directory",
    )
    args = parser.parse_args(argv)

    repo_root = Path(args.repo_root)
    findings = scan_repository(repo_root)

    if findings:
        print("FAIL Secrets audit", file=sys.stderr)
        for item in findings:
            print(f"  - {item}", file=sys.stderr)
        print(
            "\nRemove secrets from git and keep only *.env.example in the repository.",
            file=sys.stderr,
        )
        return 1

    print("OK  Secrets audit — no leaked keys in git-tracked files")
    print("OK  git — runtime .env files are not tracked")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
