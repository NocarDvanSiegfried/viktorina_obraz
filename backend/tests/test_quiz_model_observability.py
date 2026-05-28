"""Stage 1: model response diagnostics and user-safe error mapping."""

import json

import pytest

from app.services.quiz_model_observability import (
    QuizModelResponseError,
    analyze_model_response,
    classify_parse_failure,
    user_message_for_code,
)


def test_analyze_detects_missing_json_end():
    raw = '[JSON_START]\n{"quiz_title": "T", "questions": [\n'
    diag = analyze_model_response(
        raw,
        finish_reason="stop",
        question_count=10,
    )
    assert diag.has_json_start is True
    assert diag.has_json_end is False
    assert diag.likely_truncated is True


def test_analyze_finish_reason_length_marks_truncated():
    raw = "[JSON_START]{}\n[JSON_END]"
    diag = analyze_model_response(
        raw,
        finish_reason="length",
        question_count=5,
    )
    assert diag.likely_truncated is True
    assert diag.finish_reason == "length"


def test_classify_parse_failure_prefers_truncated_when_no_end_tag():
    diag = analyze_model_response(
        '[JSON_START]\n{"questions": [',
        finish_reason="stop",
        question_count=8,
    )
    code = classify_parse_failure(
        diagnostics=diag,
        repair_applied=True,
        parse_error=json.JSONDecodeError("Expecting", "", 0),
    )
    assert code == "JSON_TRUNCATED"


def test_classify_parse_failure_repair_failed():
    diag = analyze_model_response(
        "[JSON_START]{bad}\n[JSON_END]",
        finish_reason="stop",
        question_count=3,
    )
    code = classify_parse_failure(
        diagnostics=diag,
        repair_applied=True,
        parse_error=json.JSONDecodeError("Expecting", "", 0),
    )
    assert code == "JSON_REPAIR_FAILED"


def test_classify_parse_failure_plain_parse_error():
    diag = analyze_model_response(
        "not json at all",
        finish_reason="stop",
        question_count=3,
    )
    code = classify_parse_failure(
        diagnostics=diag,
        repair_applied=False,
        parse_error=ValueError("bad"),
    )
    assert code == "JSON_PARSE_ERROR"


def test_user_messages_are_teacher_friendly():
    assert "вопрос" in user_message_for_code("JSON_TRUNCATED").lower()
    assert user_message_for_code("JSON_PARSE_ERROR")
    assert user_message_for_code("JSON_REPAIR_FAILED")


def test_quiz_model_response_error_exposes_user_message():
    err = QuizModelResponseError(
        code="JSON_TRUNCATED",
        user_message=user_message_for_code("JSON_TRUNCATED"),
        technical_detail="JSONDecodeError: ...",
    )
    assert err.code == "JSON_TRUNCATED"
    assert "вопрос" in err.user_message.lower()
