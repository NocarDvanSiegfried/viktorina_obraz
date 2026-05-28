"""Day 15: quiz export to DOCX."""

from unittest.mock import patch

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "DOCX Export Quiz",
  "subject": "History",
  "grade": "9",
  "topic": "World War",
  "questions": [
    {
      "type": "single_choice",
      "text": "When did WW2 end?",
      "options": ["1943", "1945", "1947", "1950"],
      "correct_answers": ["1945"],
      "explanation": "War ended in 1945.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_export_docx_returns_binary(_mock_chat, client):
    owner_id = "owner-day15-docx"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "History",
            "grade": "9",
            "topic": "World War",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "WW2 ended in 1945.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    resp = client.get(f"/quiz/{quiz_id}/export-docx", params={"owner_id": owner_id})
    assert resp.status_code == 200
    assert (
        resp.headers["content-type"]
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
    assert resp.content.startswith(b"PK")


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_export_docx_other_owner_403(_mock_chat, client):
    owner_id = "owner-day15-docx-a"
    other_owner = "owner-day15-docx-b"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "History",
            "grade": "9",
            "topic": "World War",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "WW2 ended in 1945.",
        },
    )
    quiz_id = created.json()["quiz_id"]

    resp = client.get(f"/quiz/{quiz_id}/export-docx", params={"owner_id": other_owner})
    assert resp.status_code == 403
