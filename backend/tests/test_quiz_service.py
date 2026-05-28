"""Unit tests for quiz JSON parsing and normalization (no GigaChat network)."""

import json

import pytest

from app.schemas.material import SourceFragment
from app.schemas.quiz import DifficultyLevel, GenerateQuizResponse
from app.services.quiz_service import QuizService


SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Викторина: Клетка",
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
    },
    {
      "type": "true_false",
      "text": "Все клетки имеют ядро.",
      "options": ["Верно", "Неверно"],
      "correct answers": ["Неверно"],
      "explanation": "У прокариот нет ядра.",
      "difficulty": "DifficultyLevel.easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""


@pytest.fixture
def quiz_service() -> QuizService:
    return QuizService()


def test_extract_json_from_tagged_response(quiz_service: QuizService):
    data = quiz_service._extract_json(SAMPLE_MODEL_JSON)
    assert data["quiz_title"] == "Викторина: Клетка"
    assert len(data["questions"]) == 2


def test_normalize_question_aliases(quiz_service: QuizService):
    raw = {
        "type": "true_false",
        "text": "Вопрос?",
        "options": ["Верно", "Неверно"],
        "correct answers": ["Верно"],
        "difficulty": "DifficultyLevel.medium",
    }
    normalized = quiz_service._normalize_question_dict(raw, "easy")
    assert normalized["correct_answers"] == ["Верно"]
    assert normalized["difficulty"] == "medium"


def test_normalize_quiz_response_applies_difficulty(quiz_service: QuizService):
    data = quiz_service._extract_json(SAMPLE_MODEL_JSON)
    normalized = quiz_service._normalize_quiz_response_data(data, "hard")
    result = GenerateQuizResponse(**normalized)
    result = quiz_service._apply_difficulty_to_all_questions(result, "hard")
    assert all(q.difficulty == DifficultyLevel.hard for q in result.questions)


def test_generate_quiz_from_fragments_with_mock_gigachat(monkeypatch, quiz_service: QuizService):
    def fake_chat(messages, temperature=0.2, max_tokens=None):
        assert messages[0]["role"] == "system"
        return SAMPLE_MODEL_JSON

    monkeypatch.setattr(
        "app.services.quiz_service.gigachat_service.chat",
        fake_chat,
    )

    fragments = [
        SourceFragment(
            fragment_id="manual_1",
            source_type="manual_text",
            source_name="teacher_input",
            text="Клетка — основная единица строения организмов.",
        )
    ]

    result = quiz_service.generate_quiz_from_fragments(
        subject="Биология",
        grade="8",
        topic="Клетка",
        question_count=2,
        question_types=["single_choice", "true_false"],
        difficulty="easy",
        fragments=fragments,
    )

    assert result.quiz_title
    assert len(result.questions) == 2
    assert result.questions[0].type == "single_choice"
    assert result.questions[1].type == "true_false"
