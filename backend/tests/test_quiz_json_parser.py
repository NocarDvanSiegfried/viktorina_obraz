"""Stage 3: quiz JSON extraction."""

import json

import pytest

from app.services.quiz_json_parser import JsonExtractionFailed, extract_quiz_json

VALID_TAGGED = """
[JSON_START]
{"quiz_title": "T", "subject": "S", "grade": "8", "topic": "T", "questions": []}
[JSON_END]
"""


def test_extract_valid_tagged_json():
    data, report = extract_quiz_json(VALID_TAGGED)
    assert data["quiz_title"] == "T"
    assert report.has_json_end is True
    assert report.repair_applied is False


def test_extract_fails_on_truncated_string_inside_value():
    raw = '[JSON_START]\n{"questions": [{"text": "обрыв без кавычки'
    with pytest.raises(JsonExtractionFailed) as exc_info:
        extract_quiz_json(raw)
    assert "missing_end_tag" in exc_info.value.report.repair_steps or exc_info.value.report.repair_applied


def test_extract_repairs_missing_end_tag_when_json_complete():
    raw = (
        '[JSON_START]\n{"quiz_title": "T", "subject": "S", "grade": "8", '
        '"topic": "T", "questions": []}'
    )
    data, report = extract_quiz_json(raw)
    assert data["quiz_title"] == "T"
    assert "missing_end_tag" in report.repair_steps
