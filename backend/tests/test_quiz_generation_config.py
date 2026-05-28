"""Stage 2: generation limits and token budget."""

from app.services.quiz_generation_config import (
    compute_chat_max_tokens,
    explanation_max_chars,
)


def test_explanation_max_chars_default():
    assert explanation_max_chars(compact=False) == 160


def test_explanation_max_chars_compact():
    assert explanation_max_chars(compact=True) == 80


def test_compute_chat_max_tokens_scales_with_question_count():
    small = compute_chat_max_tokens(2)
    large = compute_chat_max_tokens(15)
    assert large > small
    assert large <= 10000
