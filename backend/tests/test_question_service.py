"""Unit tests for question validation."""

import pytest

from app.services.question_service import (
    QuestionValidationError,
    validate_question_payload,
)


def test_single_choice_requires_one_correct():
    validate_question_payload(
        "single_choice",
        ["A", "B", "C"],
        ["B"],
    )


def test_single_choice_rejects_two_correct():
    with pytest.raises(QuestionValidationError):
        validate_question_payload(
            "single_choice",
            ["A", "B"],
            ["A", "B"],
        )


def test_multiple_choice_requires_two_correct():
    validate_question_payload(
        "multiple_choice",
        ["A", "B", "C", "D"],
        ["A", "C"],
    )


def test_true_false_options_fixed():
    validate_question_payload(
        "true_false",
        ["Верно", "Неверно"],
        ["Неверно"],
    )
