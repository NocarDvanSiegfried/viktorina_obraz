"""Day 7: end-to-end flow (teacher -> student -> results)."""

from datetime import datetime, timezone
from unittest.mock import patch


SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Тест результаты",
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


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_results_endpoint_returns_percent_and_wrong_questions(_mock_chat, client):
    owner_id = "owner-day7"
    student_name = "student-day7"

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

    client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Тест результаты",
            "difficulty": "easy",
            "full_time_seconds": "60",
            "question_time_seconds": "30",
            "max_attempts": "3",
            "status": "draft",
        },
    )

    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    start = client.post(
        "/student/start",
        data={
            "quiz_id": quiz_id,
            "student_name": student_name,
            "started_at": _iso(base),
        },
    )
    assert start.status_code == 200
    result_id = start.json()["result_id"]

    q1 = client.get("/student/questions", params={"result_id": result_id}).json()[
        "next_question"
    ]
    # correct
    a1 = client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": q1["id"],
            "selected_options": ["A"],
            "question_started_at": _iso(base),
            "answered_at": _iso(base.replace(second=2)),
        },
    )
    assert a1.status_code == 200

    q2 = client.get("/student/questions", params={"result_id": result_id}).json()[
        "next_question"
    ]
    # wrong: correct is "Неверно"
    a2 = client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": q2["id"],
            "selected_options": ["Верно"],
            "question_started_at": _iso(base.replace(second=3)),
            "answered_at": _iso(base.replace(second=5)),
        },
    )
    assert a2.status_code == 200

    finished = client.post(
        "/student/finish",
        data={"result_id": result_id, "finished_at": _iso(base.replace(second=10))},
    )
    assert finished.status_code == 200
    assert finished.json()["percent"] == 50

    results = client.get(f"/quiz/{quiz_id}/results", params={"owner_id": owner_id})
    assert results.status_code == 200
    body = results.json()
    assert body["quiz_id"] == quiz_id
    assert body["results"][0]["student_name"] == student_name
    assert body["results"][0]["score"] == 1
    assert body["results"][0]["max_score"] == 2
    assert body["results"][0]["percent"] == 50
    assert len(body["results"][0]["wrong_questions"]) == 1
    assert body["results"][0]["wrong_questions"][0]["question_id"] == q2["id"]


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_results_other_owner_403(_mock_chat, client):
    owner_id = "owner-day7-a"
    other_owner = "owner-day7-b"

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

    resp = client.get(f"/quiz/{quiz_id}/results", params={"owner_id": other_owner})
    assert resp.status_code == 403
    detail = resp.json()["detail"].lower()
    assert "запрещ" in detail or "доступ" in detail

