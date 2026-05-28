"""Seed demo quiz into data/app.db for local UI testing."""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from unittest.mock import patch

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _ROOT)
os.chdir(_ROOT)

os.environ.setdefault("DATABASE_URL", "sqlite:///./data/app.db")
os.environ.setdefault("FRONTEND_ORIGIN", "http://localhost:5173")

from fastapi.testclient import TestClient  # noqa: E402

from app.db.database import Base, engine  # noqa: E402
from app.main import app  # noqa: E402

SAMPLE = """
[JSON_START]
{
  "quiz_title": "Демо викторина",
  "subject": "Обществознание",
  "grade": "8",
  "topic": "Промышленная революция",
  "questions": [
    {
      "type": "single_choice",
      "text": "Что стало результатом промышленной революции?",
      "options": ["Переход от мануфактуры к фабрике", "Фондовые биржи", "Новые виды животных", "Сельское хозяйство"],
      "correct_answers": ["Переход от мануфактуры к фабрике"],
      "explanation": "Машины и фабрики.",
      "difficulty": "easy",
      "source_fragment_id": "m1"
    },
    {
      "type": "true_false",
      "text": "Фондовые биржи появились до промышленной революции.",
      "options": ["Верно", "Неверно"],
      "correct_answers": ["Неверно"],
      "explanation": "Биржи развивались вместе с промышленностью.",
      "difficulty": "easy",
      "source_fragment_id": "m1"
    }
  ]
}
[JSON_END]
"""

OWNER = "bd6862e8-6837-479f-8a52-1c743b1116eb"


def main() -> int:
    Base.metadata.create_all(bind=engine)
    with patch(
        "app.services.gigachat_service.gigachat_service.chat",
        return_value=SAMPLE,
    ):
        client = TestClient(app)
        created = client.post(
            "/quiz/generate-from-materials",
            data={
                "owner_id": OWNER,
                "subject": "Обществознание",
                "grade": "8",
                "topic": "Промышленная революция",
                "question_count": "2",
                "difficulty": "easy",
                "question_types": ["single_choice", "true_false"],
                "source_text": "Текст о промышленной революции.",
            },
        )
        if created.status_code != 200:
            print(created.status_code, created.text)
            return 1
        quiz_id = created.json()["quiz_id"]

        base = datetime.now(timezone.utc)
        start = client.post(
            "/student/start",
            data={"quiz_id": quiz_id, "student_name": "Демо-ученик"},
        )
        result_id = start.json()["result_id"]
        q1 = client.get("/student/questions", params={"result_id": result_id}).json()[
            "next_question"
        ]
        client.post(
            "/student/answer",
            data={
                "result_id": result_id,
                "question_id": q1["id"],
                "selected_options": ["Переход от мануфактуры к фабрике"],
                "question_started_at": base.isoformat(),
                "answered_at": base.isoformat(),
            },
        )
        q2 = client.get("/student/questions", params={"result_id": result_id}).json()[
            "next_question"
        ]
        client.post(
            "/student/answer",
            data={
                "result_id": result_id,
                "question_id": q2["id"],
                "selected_options": ["Верно"],
                "question_started_at": base.isoformat(),
                "answered_at": base.isoformat(),
            },
        )
        client.post(
            "/student/finish",
            data={"result_id": result_id, "finished_at": base.isoformat()},
        )

    print(f"owner_id={OWNER}")
    print(f"quiz_id={quiz_id}")
    print(f"edit=http://localhost:5173/edit/{quiz_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
