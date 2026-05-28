"""Tunable limits for GigaChat quiz generation (stages 2–4)."""

from __future__ import annotations

EXPLANATION_MAX_CHARS_DEFAULT = 160
EXPLANATION_MAX_CHARS_COMPACT = 80

QUIZ_GENERATION_MAX_ATTEMPTS = 3
QUESTION_REGENERATE_MAX_ATTEMPTS = 2

CHAT_MAX_TOKENS_BASE = 1500
CHAT_MAX_TOKENS_PER_QUESTION = 450
CHAT_MAX_TOKENS_CAP = 10000


def explanation_max_chars(*, compact: bool) -> int:
    if compact:
        return EXPLANATION_MAX_CHARS_COMPACT
    return EXPLANATION_MAX_CHARS_DEFAULT


def compute_chat_max_tokens(question_count: int) -> int:
    count = max(1, question_count)
    budget = CHAT_MAX_TOKENS_BASE + count * CHAT_MAX_TOKENS_PER_QUESTION
    return min(CHAT_MAX_TOKENS_CAP, budget)


def truncate_explanation(text: str, *, max_chars: int) -> str:
    cleaned = (text or "").strip()
    if len(cleaned) <= max_chars:
        return cleaned
    trimmed = cleaned[: max_chars - 1].rstrip()
    return f"{trimmed}…"
