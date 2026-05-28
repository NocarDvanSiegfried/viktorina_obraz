"""Diagnostics and user-safe errors for GigaChat quiz JSON responses (stage 1)."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from app.core.logger import logger

JSON_START_MARKERS = ("[JSON_START]", "JSON_START")
JSON_END_MARKERS = ("[JSON_END]", "JSON_END")

TRUNCATION_FINISH_REASONS = frozenset({"length", "max_tokens", "token_limit"})

USER_MESSAGES: dict[str, str] = {
    "JSON_TRUNCATED": (
        "ИИ не завершил ответ. Попробуйте уменьшить число вопросов (например, до 5–7) "
        "или сократить объём материала."
    ),
    "JSON_PARSE_ERROR": (
        "ИИ вернул ответ в неверном формате. Попробуйте ещё раз или уменьшите "
        "число вопросов."
    ),
    "JSON_REPAIR_FAILED": (
        "ИИ начал викторину, но ответ оборвался и не удалось его восстановить. "
        "Уменьшите число вопросов или сократите материал и повторите генерацию."
    ),
}


@dataclass(frozen=True)
class ModelResponseDiagnostics:
    raw_chars: int
    has_json_start: bool
    has_json_end: bool
    finish_reason: str | None
    question_count: int | None
    likely_truncated: bool

    def to_log_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class JsonExtractionReport:
    has_json_start: bool
    has_json_end: bool
    repair_applied: bool
    repair_steps: tuple[str, ...]


class QuizModelResponseError(Exception):
    """Raised when model output cannot be parsed; safe to show `user_message` in API."""

    def __init__(
        self,
        *,
        code: str,
        user_message: str,
        technical_detail: str,
        diagnostics: ModelResponseDiagnostics | None = None,
        extraction: JsonExtractionReport | None = None,
    ) -> None:
        super().__init__(technical_detail)
        self.code = code
        self.user_message = user_message
        self.technical_detail = technical_detail
        self.diagnostics = diagnostics
        self.extraction = extraction


def user_message_for_code(code: str) -> str:
    return USER_MESSAGES.get(code, USER_MESSAGES["JSON_PARSE_ERROR"])


def _has_marker(raw: str, markers: tuple[str, ...]) -> bool:
    return any(marker in raw for marker in markers)


def analyze_model_response(
    raw: str,
    *,
    finish_reason: str | None = None,
    question_count: int | None = None,
    completion_tokens: int | None = None,
) -> ModelResponseDiagnostics:
    text = raw or ""
    has_start = _has_marker(text, JSON_START_MARKERS)
    has_end = _has_marker(text, JSON_END_MARKERS)
    normalized_finish = (finish_reason or "").strip().lower() or None

    likely_truncated = False
    if normalized_finish in TRUNCATION_FINISH_REASONS:
        likely_truncated = True
    if has_start and not has_end:
        likely_truncated = True
    if question_count is not None and question_count >= 10 and not has_end:
        likely_truncated = True

    return ModelResponseDiagnostics(
        raw_chars=len(text),
        has_json_start=has_start,
        has_json_end=has_end,
        finish_reason=normalized_finish,
        question_count=question_count,
        likely_truncated=likely_truncated,
    )


def classify_parse_failure(
    *,
    diagnostics: ModelResponseDiagnostics,
    repair_applied: bool,
    parse_error: BaseException,
) -> str:
    if diagnostics.likely_truncated:
        return "JSON_TRUNCATED"
    if repair_applied:
        return "JSON_REPAIR_FAILED"
    if isinstance(parse_error, json.JSONDecodeError):
        return "JSON_PARSE_ERROR"
    return "JSON_PARSE_ERROR"


def log_model_response_received(
    *,
    diagnostics: ModelResponseDiagnostics,
    completion_tokens: int | None = None,
    prompt_tokens: int | None = None,
) -> None:
    logger.info(
        "GIGACHAT_RESPONSE_META | chars=%s finish_reason=%s completion_tokens=%s "
        "prompt_tokens=%s has_json_start=%s has_json_end=%s likely_truncated=%s "
        "question_count=%s",
        diagnostics.raw_chars,
        diagnostics.finish_reason,
        completion_tokens,
        prompt_tokens,
        diagnostics.has_json_start,
        diagnostics.has_json_end,
        diagnostics.likely_truncated,
        diagnostics.question_count,
    )


def log_json_parse_failure(
    *,
    code: str,
    diagnostics: ModelResponseDiagnostics,
    extraction: JsonExtractionReport,
    technical_detail: str,
    raw_preview: str,
) -> None:
    logger.error(
        "%s | technical=%s | diagnostics=%s | extraction=%s | raw_preview=%s",
        code,
        technical_detail,
        diagnostics.to_log_dict(),
        asdict(extraction),
        raw_preview[:2000],
    )


def build_parse_error(
    *,
    diagnostics: ModelResponseDiagnostics,
    extraction: JsonExtractionReport,
    parse_error: BaseException,
) -> QuizModelResponseError:
    code = classify_parse_failure(
        diagnostics=diagnostics,
        repair_applied=extraction.repair_applied,
        parse_error=parse_error,
    )
    return QuizModelResponseError(
        code=code,
        user_message=user_message_for_code(code),
        technical_detail=f"{type(parse_error).__name__}: {parse_error}",
        diagnostics=diagnostics,
        extraction=extraction,
    )
