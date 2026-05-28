"""Extract and safely repair quiz JSON from GigaChat text (stage 3)."""

from __future__ import annotations

import json
import re

from app.services.quiz_model_observability import JsonExtractionReport

JSON_START_MARKERS = ("[JSON_START]", "JSON_START")
JSON_END_MARKERS = ("[JSON_END]", "JSON_END")


class JsonExtractionFailed(Exception):
    """JSON repair/parse failed; carries extraction report for logging."""

    def __init__(self, report: JsonExtractionReport, cause: BaseException) -> None:
        super().__init__(str(cause))
        self.report = report
        self.cause = cause


def _has_marker(raw: str, markers: tuple[str, ...]) -> bool:
    return any(marker in raw for marker in markers)


def _strip_tags(raw_text: str, repair_steps: list[str]) -> tuple[str, bool, bool]:
    has_json_start = _has_marker(raw_text, JSON_START_MARKERS)
    has_json_end = _has_marker(raw_text, JSON_END_MARKERS)

    for start_tag, end_tag in zip(JSON_START_MARKERS, JSON_END_MARKERS):
        start = raw_text.find(start_tag)
        end = raw_text.find(end_tag)
        if start != -1 and end != -1 and end > start:
            return raw_text[start + len(start_tag) : end].strip(), has_json_start, has_json_end
        if start != -1:
            repair_steps.append("missing_end_tag")
            return raw_text[start + len(start_tag) :].strip(), has_json_start, has_json_end

    return raw_text, has_json_start, has_json_end


def _has_unclosed_string(value: str) -> bool:
    in_string = False
    escape = False
    for char in value:
        if escape:
            escape = False
            continue
        if char == "\\":
            escape = True
            continue
        if char == '"':
            in_string = not in_string
    return in_string


def _try_parse_json(candidate: str) -> dict:
    parsed = json.loads(candidate)
    if not isinstance(parsed, dict):
        raise ValueError("Ожидался JSON-объект")
    return parsed


def extract_quiz_json(raw_text: str) -> tuple[dict, JsonExtractionReport]:
    original = raw_text.strip()
    repair_steps: list[str] = []

    payload, has_json_start, has_json_end = _strip_tags(original, repair_steps)

    if payload.startswith("```"):
        payload = payload.replace("```json", "").replace("```", "").strip()
        repair_steps.append("strip_markdown_fence")

    candidates: list[str] = [payload]

    if not _has_unclosed_string(payload):
        last_brace = payload.rfind("}")
        if last_brace > 0:
            trimmed = payload[: last_brace + 1]
            if trimmed != payload:
                repair_steps.append("trim_after_last_brace")
                candidates.append(trimmed)

        open_braces = payload.count("{") - payload.count("}")
        open_brackets = payload.count("[") - payload.count("]")
        if open_braces > 0 or open_brackets > 0:
            padded = payload + ("}" * max(0, open_braces)) + ("]" * max(0, open_brackets))
            repair_steps.append("pad_braces_brackets")
            candidates.append(padded)

    escaped = re.sub(r"(?<!\\)\\([a-zA-Z]+)", r"\\\\\1", payload)
    if escaped != payload:
        candidates.append(escaped)
        repair_steps.append("fix_backslash_escapes")

    report = JsonExtractionReport(
        has_json_start=has_json_start,
        has_json_end=has_json_end,
        repair_applied=bool(repair_steps),
        repair_steps=tuple(dict.fromkeys(repair_steps)),
    )

    if not payload:
        raise JsonExtractionFailed(
            report,
            ValueError("Пустой JSON после обработки"),
        )

    if _has_unclosed_string(payload):
        raise JsonExtractionFailed(
            report,
            json.JSONDecodeError("Незакрытая строка в JSON", payload, 0),
        )

    last_error: BaseException | None = None
    for candidate in candidates:
        try:
            return _try_parse_json(candidate), report
        except (json.JSONDecodeError, ValueError) as exc:
            last_error = exc
            compact = candidate.replace("\n", " ").replace("\r", "").strip()
            if compact != candidate:
                repair_steps.append("flatten_newlines")
                try:
                    return _try_parse_json(compact), JsonExtractionReport(
                        has_json_start=has_json_start,
                        has_json_end=has_json_end,
                        repair_applied=True,
                        repair_steps=tuple(dict.fromkeys(repair_steps)),
                    )
                except (json.JSONDecodeError, ValueError) as compact_exc:
                    last_error = compact_exc

    raise JsonExtractionFailed(report, last_error or ValueError("Не удалось разобрать JSON"))
