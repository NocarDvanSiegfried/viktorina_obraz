"""Metadata from the latest GigaChat completion (for observability)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GigaChatChatMeta:
    finish_reason: str | None
    completion_tokens: int | None
    prompt_tokens: int | None
    total_tokens: int | None
