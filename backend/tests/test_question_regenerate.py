"""Day 15: regenerate single question via LLM."""

from unittest.mock import patch

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Regen Quiz",
  "subject": "Biology",
  "grade": "8",
  "topic": "Cell",
  "questions": [
    {
      "type": "single_choice",
      "text": "Original question?",
      "options": ["A", "B", "C", "D"],
      "correct_answers": ["A"],
      "explanation": "A is correct.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""

REGENERATED_JSON = """
[JSON_START]
{
  "type": "single_choice",
  "text": "Regenerated: what is the cell membrane?",
  "options": ["Wall", "Barrier", "Nucleus", "Ribosome"],
  "correct_answers": ["Barrier"],
  "explanation": "Membrane separates inside from outside.",
  "difficulty": "easy",
  "source_fragment_id": "manual_1"
}
[JSON_END]
"""


@patch(
    "app.services.gigachat_service.gigachat_service.chat",
    side_effect=[SAMPLE_MODEL_JSON, REGENERATED_JSON],
)
def test_regenerate_question_updates_text(_mock_chat, client):
    owner_id = "owner-day15-regen"
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
            "source_text": "Cell membrane protects the cell.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    detail = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id})
    question_id = detail.json()["questions"][0]["id"]

    resp = client.post(
        f"/quiz/{quiz_id}/questions/{question_id}/regenerate",
        data={"owner_id": owner_id},
    )
    assert resp.status_code == 200
    body = resp.json()
    updated = body["questions"][0]
    assert "Regenerated" in updated["question_text"]
    assert updated["correct_answers"] == ["Barrier"]
    assert _mock_chat.call_count == 2


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_regenerate_question_other_owner_403(_mock_chat, client):
    owner_id = "owner-day15-regen-a"
    other = "owner-day15-regen-b"
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
            "source_text": "Cell text.",
        },
    )
    quiz_id = created.json()["quiz_id"]
    question_id = (
        client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id})
        .json()["questions"][0]["id"]
    )

    resp = client.post(
        f"/quiz/{quiz_id}/questions/{question_id}/regenerate",
        data={"owner_id": other},
    )
    assert resp.status_code == 403
