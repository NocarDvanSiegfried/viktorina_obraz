"""Day 5: in-memory rate limit for quiz generation."""

from unittest.mock import patch

import pytest

from app.core.rate_limiter import rate_limiter

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Тест мета",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Вопрос 1?",
      "options": ["A", "B", "C", "D"],
      "correct_answers": ["A"],
      "explanation": "Пояснение",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""


@pytest.fixture(autouse=True)
def _reset_rate_limiter():
    rate_limiter.clear()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_rate_limit_blocks_after_max_requests(_mock_chat, client, monkeypatch):
    owner_id = "owner-day5-rate"

    # Default settings are typically 3 requests per 60 seconds.
    times = [1000.0, 1001.0, 1002.0, 1003.0, 1004.0]
    idx = {"i": 0}

    def fake_monotonic() -> float:
        i = idx["i"]
        idx["i"] = i + 1
        if i >= len(times):
            return times[-1]
        return times[i]

    monkeypatch.setattr("app.core.rate_limiter.time.monotonic", fake_monotonic)

    for _ in range(3):
        resp = client.post(
            "/quiz/generate-from-materials",
            data={
                "owner_id": owner_id,
                "subject": "Биология",
                "grade": "8",
                "topic": "Клетка",
                "question_count": "1",
                "difficulty": "easy",
                "question_types": "single_choice",
                "source_text": "Текст про клетку.",
            },
        )
        assert resp.status_code == 200

    blocked = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "Текст про клетку.",
        },
    )
    assert blocked.status_code == 429
    detail = blocked.json()["detail"].lower()
    assert "лимит" in detail or "част" in detail

