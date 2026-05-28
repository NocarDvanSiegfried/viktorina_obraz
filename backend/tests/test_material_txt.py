"""Day 3: TXT parsing and generate from .txt file."""

from io import BytesIO
from unittest.mock import patch

from app.services.material_service import material_service

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Викторина из TXT",
  "subject": "История",
  "grade": "9",
  "topic": "Древний мир",
  "questions": [
    {
      "type": "single_choice",
      "text": "Где располагался Древний Египет?",
      "options": ["В долине Нила", "В Гималаях", "В Сибири", "В Альпах"],
      "correct_answers": ["В долине Нила"],
      "explanation": "Египет развивался вдоль Нила.",
      "difficulty": "easy",
      "source_fragment_id": "txt_1"
    }
  ]
}
[JSON_END]
"""

TXT_CONTENT = (
    "Древний Египет располагался в долине реки Нил. "
    "Фараоны управляли страной. Пирамиды строили как гробницы."
).encode("utf-8")


def test_extract_text_from_txt():
    text = material_service.extract_text_from_txt(TXT_CONTENT)
    assert "Древний Египет" in text
    assert "Нил" in text


def test_extract_fragments_from_txt_file():
    file_type, fragments = material_service.extract_fragments(
        "lesson.txt",
        TXT_CONTENT,
    )
    assert file_type == "txt"
    assert len(fragments) == 1
    assert fragments[0].fragment_id == "txt_1"
    assert fragments[0].source_type == "txt"


def test_merge_fragments_manual_and_txt():
    file_type, file_fragments = material_service.extract_fragments(
        "notes.txt",
        TXT_CONTENT,
    )
    merged = material_service.merge_fragments(
        "Краткий конспект урока.",
        file_fragments,
    )
    assert len(merged) == 2
    assert merged[0].source_type == "manual_text"
    assert merged[1].source_type == "txt"


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_generate_from_txt_file(_mock_chat, client, db_engine):
    from sqlalchemy.orm import sessionmaker

    from app.db.models import MaterialUpload, Quiz

    owner_id = "owner-day3-txt"

    response = client.post(
        "/quiz/generate-from-materials",
        files={"file": ("lesson.txt", BytesIO(TXT_CONTENT), "text/plain")},
        data={
            "owner_id": owner_id,
            "subject": "История",
            "grade": "9",
            "topic": "Древний мир",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["quiz_id"]
    assert body["title"] == "Викторина из TXT"

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        quiz = session.get(Quiz, body["quiz_id"])
        assert quiz is not None

        uploads = (
            session.query(MaterialUpload)
            .filter(MaterialUpload.quiz_id == quiz.id)
            .all()
        )
        assert len(uploads) == 1
        assert uploads[0].source_type == "txt"
        assert uploads[0].original_filename == "lesson.txt"
    finally:
        session.close()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_generate_requires_text_or_file(_mock_chat, client):
    response = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": "owner-day3",
            "subject": "История",
            "grade": "9",
            "topic": "Тема",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
        },
    )
    assert response.status_code == 400


def test_generate_rejects_unsupported_file(client):
    response = client.post(
        "/quiz/generate-from-materials",
        files={
            "file": (
                "data.xlsx",
                BytesIO(b"PK"),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        data={
            "owner_id": "owner-day3",
            "subject": "История",
            "grade": "9",
            "topic": "Тема",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
        },
    )
    assert response.status_code == 400
