"""Day 5: privacy checks (403) for quiz owner access."""

from unittest.mock import patch

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
      "options": ["A", "B"],
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
def test_get_quiz_other_owner_403(_mock_chat, client):
    owner_a = "owner-day5-privacy-a"
    owner_b = "owner-day5-privacy-b"

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

    resp = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_b})
    assert resp.status_code == 403
    detail = resp.json()["detail"].lower()
    assert "запрещ" in detail or "доступ" in detail

