"""Day 6: student flow (start/questions/answer/finish) with timers and attempts."""

from datetime import datetime, timezone
from unittest.mock import patch

import pytest


SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Тест попыток",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Какой вариант правильный?",
      "options": ["A", "B", "C", "D"],
      "correct_answers": ["A"],
      "explanation": "Верный ответ: A",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    },
    {
      "type": "true_false",
      "text": "Клетка имеет ядро.",
      "options": ["Верно", "Неверно"],
      "correct_answers": ["Верно"],
      "explanation": "У большинства клеток есть ядро",
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
def test_student_start_enforces_max_attempts(_mock_chat, client):
    owner_id = "owner-day6-attempts"

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

    # max_attempts = 1
    put_resp = client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Тест попыток",
            "difficulty": "easy",
            "full_time_seconds": "120",
            "question_time_seconds": "10",
            "max_attempts": "1",
            "status": "draft",
        },
    )
    assert put_resp.status_code == 200

    student_name = "student-a"
    start1 = client.post(
        "/student/start",
        data={"quiz_id": quiz_id, "student_name": student_name},
    )
    assert start1.status_code == 200

    start2 = client.post(
        "/student/start",
        data={"quiz_id": quiz_id, "student_name": student_name},
    )
    assert start2.status_code == 403
    assert "попыт" in start2.json()["detail"].lower()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_student_answer_validates_question_timer_and_finish_scoring(_mock_chat, client):
    owner_id = "owner-day6-flow"

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

    put_resp = client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Тест попыток",
            "difficulty": "easy",
            "full_time_seconds": "60",
            "question_time_seconds": "10",
            "max_attempts": "3",
            "status": "draft",
        },
    )
    assert put_resp.status_code == 200

    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    started_at = _iso(base)

    start = client.post(
        "/student/start",
        data={
            "quiz_id": quiz_id,
            "student_name": "student-b",
            "started_at": started_at,
        },
    )
    assert start.status_code == 200
    result_id = start.json()["result_id"]

    questions_resp = client.get(f"/student/questions?result_id={result_id}")
    assert questions_resp.status_code == 200
    questions_body = questions_resp.json()
    assert questions_body["completed"] is False
    next_question = questions_body["next_question"]
    assert next_question["question_type"] in ["single_choice", "true_false"]
    question_id_1 = next_question["id"]

    # Answer #1 correctly within time (5s)
    q1_started = base
    q1_answered = base.replace(second=5)
    ans1 = client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": question_id_1,
            "selected_options": ["A"],
            "question_started_at": _iso(q1_started),
            "answered_at": _iso(q1_answered),
        },
    )
    assert ans1.status_code == 200

    questions_resp2 = client.get(f"/student/questions?result_id={result_id}")
    assert questions_resp2.status_code == 200
    next2 = questions_resp2.json()["next_question"]
    question_id_2 = next2["id"]

    # Answer #2 correctly within time (4s)
    q2_started = base.replace(second=6)
    q2_answered = base.replace(second=10)
    ans2 = client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": question_id_2,
            "selected_options": ["Верно"],
            "question_started_at": _iso(q2_started),
            "answered_at": _iso(q2_answered),
        },
    )
    assert ans2.status_code == 200

    finish = client.post(
        "/student/finish",
        data={"result_id": result_id, "finished_at": _iso(base.replace(second=20))},
    )
    assert finish.status_code == 200
    body = finish.json()
    assert body["score"] == 2
    assert body["max_score"] == 2
    assert body["percent"] == 100
    assert body["duration_seconds"] == 20


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_student_answer_rejects_question_time_overflow(_mock_chat, client):
    owner_id = "owner-day6-timeout"
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

    put_resp = client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Тест попыток",
            "difficulty": "easy",
            "full_time_seconds": "60",
            "question_time_seconds": "10",
            "max_attempts": "3",
            "status": "draft",
        },
    )
    assert put_resp.status_code == 200

    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    start = client.post(
        "/student/start",
        data={
            "quiz_id": quiz_id,
            "student_name": "student-c",
            "started_at": _iso(base),
        },
    )
    assert start.status_code == 200
    result_id = start.json()["result_id"]

    questions_resp = client.get(f"/student/questions?result_id={result_id}")
    assert questions_resp.status_code == 200
    next_question = questions_resp.json()["next_question"]

    # Spend 11s on a question (limit=10)
    ans = client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": next_question["id"],
            "selected_options": ["A"],
            "question_started_at": _iso(base),
            "answered_at": _iso(base.replace(second=11)),
        },
    )
    assert ans.status_code == 400
    assert "сек" in ans.json()["detail"].lower() or "время" in ans.json()["detail"].lower()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_student_finish_rejects_overall_time_overflow(_mock_chat, client):
    owner_id = "owner-day6-overall"
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

    put_resp = client.put(
        f"/quiz/{quiz_id}",
        data={
            "owner_id": owner_id,
            "title": "Тест попыток",
            "difficulty": "easy",
            "full_time_seconds": "10",
            "question_time_seconds": "10",
            "max_attempts": "3",
            "status": "draft",
        },
    )
    assert put_resp.status_code == 200

    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    start = client.post(
        "/student/start",
        data={
            "quiz_id": quiz_id,
            "student_name": "student-d",
            "started_at": _iso(base),
        },
    )
    assert start.status_code == 200
    result_id = start.json()["result_id"]

    q1 = client.get(f"/student/questions?result_id={result_id}").json()["next_question"]
    ans1 = client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": q1["id"],
            "selected_options": ["A"],
            "question_started_at": _iso(base),
            "answered_at": _iso(base.replace(second=3)),
        },
    )
    assert ans1.status_code == 200

    q2 = client.get(f"/student/questions?result_id={result_id}").json()["next_question"]
    ans2 = client.post(
        "/student/answer",
        data={
            "result_id": result_id,
            "question_id": q2["id"],
            "selected_options": ["Верно"],
            "question_started_at": _iso(base.replace(second=4)),
            "answered_at": _iso(base.replace(second=8)),
        },
    )
    assert ans2.status_code == 200

    # Finish after 11 seconds (limit=10)
    finish = client.post(
        "/student/finish",
        data={"result_id": result_id, "finished_at": _iso(base.replace(second=11))},
    )
    assert finish.status_code == 400
    assert "время" in finish.json()["detail"].lower() or "сек" in finish.json()["detail"].lower()

