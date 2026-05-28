"""Day 12: completed flag after last answer + finish returns score."""

from datetime import datetime, timezone
from unittest.mock import patch

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "День 12",
  "subject": "Биология",
  "grade": "8",
  "topic": "Тест",
  "questions": [
    {
      "type": "single_choice",
      "text": "Q1?",
      "options": ["A", "B"],
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


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_completed_after_last_answer_then_finish(_mock_chat, client):
    owner_id = "owner-day12"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Тест",
            "question_count": "2",
            "difficulty": "easy",
            "question_types": ["single_choice", "true_false"],
            "source_text": "Текст.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    base = datetime(2026, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    start = client.post(
        "/student/start",
        data={
            "quiz_id": quiz_id,
            "student_name": "Ученик-12",
            "started_at": _iso(base),
        },
    )
    result_id = start.json()["result_id"]

    q1 = client.get("/student/questions", params={"result_id": result_id}).json()
    assert q1["completed"] is False
    client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": q1["next_question"]["id"],
            "selected_options": ["A"],
            "question_started_at": _iso(base),
            "answered_at": _iso(base.replace(second=2)),
        },
    )

    q2 = client.get("/student/questions", params={"result_id": result_id}).json()
    assert q2["completed"] is False
    client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": q2["next_question"]["id"],
            "selected_options": ["Верно"],
            "question_started_at": _iso(base.replace(second=3)),
            "answered_at": _iso(base.replace(second=5)),
        },
    )

    after_last = client.get("/student/questions", params={"result_id": result_id}).json()
    assert after_last["completed"] is True
    assert after_last["next_question"] is None

    finished = client.post(
        "/student/finish",
        data={"result_id": result_id, "finished_at": _iso(base.replace(second=8))},
    )
    assert finished.status_code == 200
    body = finished.json()
    assert body["max_score"] == 2
    assert body["score"] == 1
    assert body["percent"] == 50
