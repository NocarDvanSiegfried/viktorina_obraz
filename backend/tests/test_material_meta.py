"""Day 2: generate endpoint, MaterialUpload metadata, validation."""

from unittest.mock import patch

import pytest

from app.db.models import MaterialUpload, Question, Quiz

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


def test_generate_requires_owner_id(client):
    response = client.post(
        "/quiz/generate-from-materials",
        data={
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "3",
            "difficulty": "easy",
            "source_text": "Текст урока про клетку.",
            "question_types": "single_choice",
        },
    )
    assert response.status_code == 422


def test_generate_requires_source_text(client):
    response = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": "owner-day2",
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "3",
            "difficulty": "easy",
            "question_types": "single_choice",
        },
    )
    assert response.status_code == 400


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_generate_saves_quiz_questions_and_material_meta(
    _mock_chat,
    client,
    db_engine,
):
    from sqlalchemy.orm import sessionmaker

    owner_id = "owner-day2-meta"

    response = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "source_text": "Клетка — основная единица организмов. Мембрана отделяет клетку от среды.",
            "question_types": "single_choice",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["quiz_id"]
    assert body["title"] == "Тест мета"
    assert len(body["questions"]) == 1

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        quiz = session.get(Quiz, body["quiz_id"])
        assert quiz is not None
        assert quiz.owner_id == owner_id
        assert quiz.subject == "Биология"
        assert quiz.difficulty == "easy"

        questions = session.query(Question).filter(Question.quiz_id == quiz.id).all()
        assert len(questions) == 1
        assert questions[0].question_type == "single_choice"
        assert questions[0].source_fragment == "manual_1"

        uploads = (
            session.query(MaterialUpload)
            .filter(MaterialUpload.quiz_id == quiz.id)
            .all()
        )
        assert len(uploads) == 1
        assert uploads[0].owner_id == owner_id
        assert uploads[0].source_type == "manual_text"
        assert uploads[0].size_bytes == len(
            "Клетка — основная единица организмов. Мембрана отделяет клетку от среды.".encode(
                "utf-8"
            )
        )
    finally:
        session.close()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_generate_list_shows_new_quiz(_mock_chat, client):
    owner_id = "owner-day2-list"

    client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "История",
            "grade": "9",
            "topic": "Древний мир",
            "question_count": "1",
            "difficulty": "medium",
            "source_text": "Древний Египет располагался в долине Нила.",
            "question_types": "single_choice",
        },
    )

    listed = client.get("/quiz/list", params={"owner_id": owner_id})
    assert listed.status_code == 200
    assert len(listed.json()["quizzes"]) >= 1
