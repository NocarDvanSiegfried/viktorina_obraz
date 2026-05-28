from unittest.mock import patch


SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Тест копирования",
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
def test_duplicate_quiz_creates_draft_copy(_mock_chat, client):
    owner_id = "owner-duplicate-1"

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
    source_id = created.json()["quiz_id"]

    duplicated = client.post(
        f"/quiz/{source_id}/duplicate",
        data={"owner_id": owner_id},
    )
    assert duplicated.status_code == 200
    body = duplicated.json()
    assert body["quiz_id"] != source_id
    assert body["title"].endswith(" (копия)")
    assert body["status"] == "draft"
    assert len(body["questions"]) == 2

    listed = client.get("/quiz/list", params={"owner_id": owner_id})
    assert listed.status_code == 200
    titles = [item["title"] for item in listed.json()["quizzes"]]
    assert "Тест копирования (копия)" in titles
