"""Stage 4: retry on parse failure."""

import pytest

from app.schemas.material import SourceFragment
from app.services.quiz_model_observability import QuizModelResponseError
from app.services.quiz_service import QuizService

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "E2E Викторина",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Что является основной единицей жизни?",
      "options": ["Атом", "Клетка", "Орган", "Ткань"],
      "correct_answers": ["Клетка"],
      "explanation": "Клетка — основная структурная единица.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""

BROKEN_JSON = '[JSON_START]\n{"quiz_title": "T", "questions": [\n'


@pytest.fixture
def fragments() -> list[SourceFragment]:
    return [
        SourceFragment(
            fragment_id="manual_1",
            source_type="manual_text",
            source_name="teacher_input",
            text="Клетка — основная единица.",
        )
    ]


def test_retries_and_succeeds_on_second_attempt(monkeypatch, fragments):
    service = QuizService()
    calls: list[dict] = []

    def fake_chat(messages, temperature=0.2, max_tokens=None):
        calls.append(
            {
                "max_tokens": max_tokens,
                "compact": "режим компактный" in messages[1]["content"].lower(),
            }
        )
        if len(calls) == 1:
            return BROKEN_JSON
        return SAMPLE_MODEL_JSON

    monkeypatch.setattr(
        "app.services.quiz_service.gigachat_service.chat",
        fake_chat,
    )

    result = service.generate_quiz_from_fragments(
        subject="Биология",
        grade="8",
        topic="Клетка",
        question_count=5,
        question_types=["single_choice"],
        difficulty="easy",
        fragments=fragments,
    )

    assert len(calls) == 2
    assert calls[1]["compact"] is True
    assert len(result.questions) == 1


def test_raises_after_all_retries_exhausted(monkeypatch, fragments):
    service = QuizService()

    def fake_chat(messages, temperature=0.2, max_tokens=None):
        return BROKEN_JSON

    monkeypatch.setattr(
        "app.services.quiz_service.gigachat_service.chat",
        fake_chat,
    )

    with pytest.raises(QuizModelResponseError):
        service.generate_quiz_from_fragments(
            subject="Биология",
            grade="8",
            topic="Клетка",
            question_count=5,
            question_types=["single_choice"],
            difficulty="easy",
            fragments=fragments,
        )
