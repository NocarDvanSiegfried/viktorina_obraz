from unittest.mock import patch


SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Тест soft delete",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Q1?",
      "options": ["A", "B", "C", "D"],
      "correct_answers": ["A"],
      "explanation": "A",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    },
    {
      "type": "true_false",
      "text": "Q2?",
      "options": ["Верно", "Неверно"],
      "correct_answers": ["Неверно"],
      "explanation": "Неверно",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_soft_delete_hides_quiz_from_list_and_get(_mock_chat, client):
    owner_id = "owner-soft-delete-1"

    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "2",
            "difficulty": "easy",
            "question_types": ["single_choice", "true_false"],
            "source_text": "Текст про клетку.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    deleted = client.delete(f"/quiz/{quiz_id}", params={"owner_id": owner_id})
    assert deleted.status_code == 200
    assert deleted.json()["quiz_id"] == quiz_id
    assert deleted.json()["deleted"] is True

    listed = client.get("/quiz/list", params={"owner_id": owner_id})
    assert listed.status_code == 200
    listed_ids = [item["id"] for item in listed.json()["quizzes"]]
    assert quiz_id not in listed_ids

    detail = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id})
    assert detail.status_code == 404


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_soft_deleted_quiz_unavailable_for_student_start(_mock_chat, client):
    owner_id = "owner-soft-delete-2"

    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "2",
            "difficulty": "easy",
            "question_types": ["single_choice", "true_false"],
            "source_text": "Текст про клетку.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    deleted = client.delete(f"/quiz/{quiz_id}", params={"owner_id": owner_id})
    assert deleted.status_code == 200

    start = client.post(
        "/student/start",
        data={"quiz_id": quiz_id, "student_name": "Тестовый ученик"},
    )
    assert start.status_code == 404
