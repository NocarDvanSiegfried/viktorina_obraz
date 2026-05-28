"""Day 5: quiz settings CRUD (PUT) and teacher ownership checks."""

from unittest.mock import patch

from sqlalchemy.orm import sessionmaker

from app.db.models import Quiz

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


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_put_updates_quiz_settings_for_owner(_mock_chat, client, db_engine):
    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        owner_id = "owner-day5-put-ok"
        response = client.post(
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
        assert response.status_code == 200
        quiz_id = response.json()["quiz_id"]

        put_resp = client.put(
            f"/quiz/{quiz_id}",
            data={
                "owner_id": owner_id,
                "title": "Обновлённый заголовок",
                "difficulty": "medium",
                "full_time_seconds": "3600",
                "question_time_seconds": "30",
                "max_attempts": "2",
                "status": "draft",
            },
        )
        assert put_resp.status_code == 200
        body = put_resp.json()
        assert body["quiz_id"] == quiz_id
        assert body["title"] == "Обновлённый заголовок"
        assert body["difficulty"] == "medium"
        assert body["max_attempts"] == 2

        quiz = session.get(Quiz, quiz_id)
        assert quiz is not None
        assert quiz.title == "Обновлённый заголовок"
        assert quiz.difficulty == "medium"
        assert quiz.full_time_seconds == 3600
        assert quiz.question_time_seconds == 30
        assert quiz.max_attempts == 2
        assert quiz.status == "draft"
    finally:
        session.close()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_put_rejects_other_owner_403(_mock_chat, client):
    owner_a = "owner-day5-put-a"
    owner_b = "owner-day5-put-b"

    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_a,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "Текст про клетку.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    resp = client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_b,
            "title": "Проверка 403",
            "difficulty": "easy",
            "full_time_seconds": "100",
            "question_time_seconds": "10",
            "max_attempts": "1",
            "status": "draft",
        },
    )
    assert resp.status_code == 403
    detail = resp.json()["detail"].lower()
    assert "запрещ" in detail or "доступ" in detail

