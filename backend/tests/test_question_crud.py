"""Day 11: CRUD for quiz questions (owner-protected)."""

from unittest.mock import patch

from sqlalchemy.orm import sessionmaker

from app.db.models import Question, Quiz

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Тест CRUD вопросов",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Вопрос 1?",
      "options": ["A", "B", "C", "D"],
      "correct_answers": ["A"],
      "explanation": "A",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""


def _create_quiz(client, owner_id: str = "owner-day11") -> str:
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
    return response.json()["quiz_id"]


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_create_question(_mock_chat, client, db_engine):
    owner_id = "owner-day11-create"
    quiz_id = _create_quiz(client, owner_id)

    resp = client.post(
        f"/quiz/{quiz_id}/questions",
        data={
            "owner_id": owner_id,
            "question_text": "Новый вопрос?",
            "question_type": "true_false",
            "answers": ["Верно", "Неверно"],
            "correct_answers": ["Неверно"],
            "explanation": "Потому что нет",
            "source_fragment": "manual_1",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["questions"]) == 2
    created = body["questions"][-1]
    assert created["question_text"] == "Новый вопрос?"
    assert created["question_type"] == "true_false"
    assert created["correct_answers"] == ["Неверно"]

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        count = session.query(Question).filter(Question.quiz_id == quiz_id).count()
        assert count == 2
    finally:
        session.close()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_update_question(_mock_chat, client, db_engine):
    owner_id = "owner-day11-update"
    quiz_id = _create_quiz(client, owner_id)

    quiz = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id}).json()
    question_id = quiz["questions"][0]["id"]

    resp = client.put(
        f"/quiz/{quiz_id}/questions/{question_id}",
        data={
            "owner_id": owner_id,
            "question_text": "Изменённый текст?",
            "question_type": "single_choice",
            "answers": ["X", "Y", "Z"],
            "correct_answers": ["Y"],
            "explanation": "Y верно",
        },
    )
    assert resp.status_code == 200
    updated = next(q for q in resp.json()["questions"] if q["id"] == question_id)
    assert updated["question_text"] == "Изменённый текст?"
    assert updated["answers"] == ["X", "Y", "Z"]
    assert updated["correct_answers"] == ["Y"]


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_delete_question(_mock_chat, client, db_engine):
    owner_id = "owner-day11-delete"
    quiz_id = _create_quiz(client, owner_id)

    created = client.post(
        f"/quiz/{quiz_id}/questions",
        data={
            "owner_id": owner_id,
            "question_text": "Удалить меня",
            "question_type": "single_choice",
            "answers": ["1", "2"],
            "correct_answers": ["1"],
        },
    )
    assert created.status_code == 200
    to_delete = created.json()["questions"][-1]["id"]

    resp = client.delete(
        f"/quiz/{quiz_id}/questions/{to_delete}",
        params={"owner_id": owner_id},
    )
    assert resp.status_code == 200
    assert len(resp.json()["questions"]) == 1

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        assert (
            session.query(Question).filter(Question.id == to_delete).first() is None
        )
    finally:
        session.close()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_reorder_question(_mock_chat, client):
    owner_id = "owner-day11-reorder"
    quiz_id = _create_quiz(client, owner_id)

    client.post(
        f"/quiz/{quiz_id}/questions",
        data={
            "owner_id": owner_id,
            "question_text": "Второй",
            "question_type": "single_choice",
            "answers": ["1", "2"],
            "correct_answers": ["2"],
        },
    )
    quiz = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id}).json()
    first_id = quiz["questions"][0]["id"]

    moved = client.post(
        f"/quiz/{quiz_id}/questions/{first_id}/reorder",
        data={"owner_id": owner_id, "direction": "down"},
    )
    assert moved.status_code == 200
    questions = moved.json()["questions"]
    assert questions[0]["question_text"] == "Второй"
    assert questions[1]["question_text"] == "Вопрос 1?"


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_question_crud_other_owner_403(_mock_chat, client):
    owner_a = "owner-day11-a"
    owner_b = "owner-day11-b"
    quiz_id = _create_quiz(client, owner_a)
    quiz = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_a}).json()
    qid = quiz["questions"][0]["id"]

    resp = client.put(
        f"/quiz/{quiz_id}/questions/{qid}",
        data={
            "owner_id": owner_b,
            "question_text": "hack",
            "question_type": "single_choice",
            "answers": ["1", "2"],
            "correct_answers": ["1"],
        },
    )
    assert resp.status_code == 403


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_create_question_validation_error(_mock_chat, client):
    owner_id = "owner-day11-validation"
    quiz_id = _create_quiz(client, owner_id)

    resp = client.post(
        f"/quiz/{quiz_id}/questions",
        data={
            "owner_id": owner_id,
            "question_text": "Плохой",
            "question_type": "single_choice",
            "answers": ["1", "2"],
            "correct_answers": ["1", "2"],
        },
    )
    assert resp.status_code == 400


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_max_questions_limit(_mock_chat, client):
    owner_id = "owner-day11-limit"
    quiz_id = _create_quiz(client, owner_id)

    for i in range(14):
        resp = client.post(
            f"/quiz/{quiz_id}/questions",
            data={
                "owner_id": owner_id,
                "question_text": f"Q{i}",
                "question_type": "single_choice",
                "answers": ["1", "2"],
                "correct_answers": ["1"],
            },
        )
        assert resp.status_code == 200

    overflow = client.post(
        f"/quiz/{quiz_id}/questions",
        data={
            "owner_id": owner_id,
            "question_text": "Лишний",
            "question_type": "single_choice",
            "answers": ["1", "2"],
            "correct_answers": ["1"],
        },
    )
    assert overflow.status_code == 400
