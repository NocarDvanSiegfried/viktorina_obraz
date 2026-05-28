"""Day 13: GigaChat vision OCR for images and empty PDF fallback."""

from io import BytesIO
from unittest.mock import patch

from pypdf import PdfWriter

from app.services.material_service import material_service

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Викторина из изображения",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Что является основной единицей жизни?",
      "options": ["Атом", "Клетка", "Орган", "Ткань"],
      "correct_answers": ["Клетка"],
      "explanation": "Клетка — основная структурная единица.",
      "difficulty": "easy",
      "source_fragment_id": "image_ocr_1"
    }
  ]
}
[JSON_END]
"""

OCR_TEXT = (
    "Клетка — основная структурная и функциональная единица живых организмов. "
    "Клеточная мембрана отделяет внутреннее содержимое от внешней среды."
)

MINIMAL_PNG = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01"
    b"\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82"
)


def _make_empty_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@patch(
    "app.services.gigachat_service.gigachat_service.extract_text_from_visual",
    return_value=OCR_TEXT,
)
def test_extract_fragments_from_image_via_vision(_mock_vision):
    file_type, fragments = material_service.extract_fragments("slide.png", MINIMAL_PNG)
    assert file_type == "image"
    assert len(fragments) >= 1
    assert fragments[0].source_type == "image"
    assert fragments[0].fragment_id == "image_ocr_1"
    assert "клетка" in fragments[0].text.lower()


@patch(
    "app.services.gigachat_service.gigachat_service.extract_text_from_visual",
    return_value=OCR_TEXT,
)
def test_extract_fragments_from_empty_pdf_via_vision(_mock_vision):
    file_type, fragments = material_service.extract_fragments("scan.pdf", _make_empty_pdf())
    assert file_type == "pdf"
    assert len(fragments) >= 1
    assert fragments[0].fragment_id.startswith("pdf_ocr_")
    assert fragments[0].source_type == "pdf"


@patch(
    "app.services.gigachat_service.gigachat_service.extract_text_from_visual",
    return_value="   ",
)
def test_extract_image_returns_empty_when_vision_empty(_mock_vision):
    file_type, fragments = material_service.extract_fragments("photo.jpg", MINIMAL_PNG)
    assert file_type == "image"
    assert fragments == []


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
@patch(
    "app.services.gigachat_service.gigachat_service.extract_text_from_visual",
    return_value=OCR_TEXT,
)
def test_generate_from_image_file(_mock_vision, _mock_chat, client, db_engine):
    from sqlalchemy.orm import sessionmaker

    from app.db.models import MaterialUpload

    owner_id = "owner-day13-image"
    response = client.post(
        "/quiz/generate-from-materials",
        files={"file": ("lesson.png", BytesIO(MINIMAL_PNG), "image/png")},
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["quiz_id"]
    assert body["title"] == "Викторина из изображения"

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        uploads = (
            session.query(MaterialUpload)
            .filter(MaterialUpload.quiz_id == body["quiz_id"])
            .all()
        )
        assert len(uploads) == 1
        assert uploads[0].source_type == "image"
        assert uploads[0].original_filename == "lesson.png"
    finally:
        session.close()


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
@patch(
    "app.services.gigachat_service.gigachat_service.extract_text_from_visual",
    return_value=OCR_TEXT,
)
def test_generate_from_empty_pdf_via_vision(_mock_vision, _mock_chat, client):
    response = client.post(
        "/quiz/generate-from-materials",
        files={"file": ("scan.pdf", BytesIO(_make_empty_pdf()), "application/pdf")},
        data={
            "owner_id": "owner-day13-pdf-ocr",
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
        },
    )
    assert response.status_code == 200
    assert response.json()["quiz_id"]


@patch(
    "app.services.gigachat_service.gigachat_service.extract_text_from_visual",
    return_value="",
)
def test_generate_rejects_image_when_ocr_empty(_mock_vision, client):
    response = client.post(
        "/quiz/generate-from-materials",
        files={"file": ("blank.png", BytesIO(MINIMAL_PNG), "image/png")},
        data={
            "owner_id": "owner-day13-empty-image",
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
        },
    )
    assert response.status_code == 400
    detail = response.json()["detail"].lower()
    assert "изображен" in detail or "текст" in detail
