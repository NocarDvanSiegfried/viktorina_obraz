"""Shared env validation for live GigaChat scripts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BACKEND_ROOT = _REPO_ROOT / "backend"

if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

os.chdir(_BACKEND_ROOT)

from dotenv import load_dotenv

load_dotenv(_BACKEND_ROOT / ".env")

from app.core.config import settings  # noqa: E402

BACKEND_ROOT = _BACKEND_ROOT


def mask_key(value: str) -> str:
    if len(value) <= 8:
        return "***"
    return f"{value[:4]}...{value[-4:]}"


def validate_live_environment() -> list[str]:
    errors: list[str] = []
    if not settings.GIGACHAT_AUTH_KEY.strip():
        errors.append("GIGACHAT_AUTH_KEY is not set")
    if settings.E2E_MOCK_GIGACHAT:
        errors.append(
            "E2E_MOCK_GIGACHAT is enabled — disable it for a live check"
        )
    if not settings.GIGACHAT_VISION_MODEL.strip():
        errors.append("GIGACHAT_VISION_MODEL is not set")
    return errors


def print_environment_header() -> None:
    print("OK  Environment")
    print(f"    model={settings.GIGACHAT_MODEL}")
    print(f"    vision_model={settings.GIGACHAT_VISION_MODEL}")
    print(f"    scope={settings.GIGACHAT_SCOPE}")
    print(f"    auth_key={mask_key(settings.GIGACHAT_AUTH_KEY)}")
