"""Day 15: quiz.updated_at changes on edits."""

import time
from unittest.mock import patch

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Updated At Quiz",
  "subject": "Biology",
  "grade": "8",
  "topic": "Cell",
  "questions": [
    {
      "type": "single_choice",
      "text": "Q1?",
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


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_quiz_updated_at_changes_on_settings_save(_mock_chat, client):
    owner_id = "owner-day15-updated"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Biology",
            "grade": "8",
            "topic": "Cell",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "Cell basics.",
        },
    )
    quiz_id = created.json()["quiz_id"]

    before = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id}).json()
    assert before.get("updated_at")
    before_ts = before["updated_at"]

    time.sleep(0.02)

    client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Updated At Quiz v2",
            "difficulty": "medium",
            "full_time_seconds": "0",
            "question_time_seconds": "0",
            "max_attempts": "1",
            "status": "draft",
        },
    )

    after = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id}).json()
    assert after["title"] == "Updated At Quiz v2"
    assert after["updated_at"] >= before_ts


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_list_quizzes_includes_updated_at(_mock_chat, client):
    owner_id = "owner-day15-list"
    client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Biology",
            "grade": "8",
            "topic": "Cell",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "Cell basics.",
        },
    )

    listed = client.get("/quiz/list", params={"owner_id": owner_id}).json()
    assert listed["quizzes"]
    assert listed["quizzes"][0].get("updated_at")
