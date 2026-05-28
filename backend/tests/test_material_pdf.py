"""Day 4: PDF parsing and generate from .pdf file."""

from io import BytesIO
from unittest.mock import patch

from pypdf import PdfWriter

from app.services.material_service import material_service

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "Викторина из PDF",
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
      "source_fragment_id": "pdf_page_1_chunk_1"
    }
  ]
}
[JSON_END]
"""

PDF_TEXT = (
    "The cell is the basic structural and functional unit of living organisms. "
    "The cell membrane separates the internal contents from the external environment."
)


def _make_pdf_with_text(text: str) -> bytes:
    from fpdf import FPDF

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 8, text)
    return pdf.output()


def _make_empty_pdf() -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def test_extract_text_from_pdf():
    pdf_bytes = _make_pdf_with_text(PDF_TEXT)
    fragments = material_service.extract_text_from_pdf(pdf_bytes)
    assert len(fragments) >= 1
    combined = " ".join(fragment.text for fragment in fragments)
    assert "cell" in combined.lower()


def test_extract_fragments_from_pdf_file():
    pdf_bytes = _make_pdf_with_text(PDF_TEXT)
    file_type, fragments = material_service.extract_fragments("lesson.pdf", pdf_bytes)
    assert file_type == "pdf"
    assert len(fragments) >= 1
    assert fragments[0].source_type == "pdf"
    assert fragments[0].fragment_id.startswith("pdf_page_")


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_generate_from_pdf_file(_mock_chat, client, db_engine):
    from sqlalchemy.orm import sessionmaker

    from app.db.models import MaterialUpload, Quiz

    owner_id = "owner-day4-pdf"
    pdf_bytes = _make_pdf_with_text(PDF_TEXT)

    response = client.post(
        "/quiz/generate-from-materials",
        files={"file": ("lesson.pdf", BytesIO(pdf_bytes), "application/pdf")},
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
    assert body["title"] == "Викторина из PDF"

    SessionLocal = sessionmaker(bind=db_engine)
    session = SessionLocal()
    try:
        uploads = (
            session.query(MaterialUpload)
            .filter(MaterialUpload.quiz_id == body["quiz_id"])
            .all()
        )
        assert len(uploads) == 1
        assert uploads[0].source_type == "pdf"
        assert uploads[0].original_filename == "lesson.pdf"
    finally:
        session.close()


@patch(
    "app.services.gigachat_service.gigachat_service.extract_text_from_visual",
    return_value="",
)
def test_generate_rejects_empty_pdf_when_vision_empty(_mock_vision, client):
    response = client.post(
        "/quiz/generate-from-materials",
        files={"file": ("empty.pdf", BytesIO(_make_empty_pdf()), "application/pdf")},
        data={
            "owner_id": "owner-day4",
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
    assert "txt" in detail or "текст" in detail


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_get_quiz_by_id(_mock_chat, client):
    owner_id = "owner-day4-get"
    pdf_bytes = _make_pdf_with_text(PDF_TEXT)

    created = client.post(
        "/quiz/generate-from-materials",
        files={"file": ("lesson.pdf", BytesIO(pdf_bytes), "application/pdf")},
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
    quiz_id = created.json()["quiz_id"]

    response = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id})
    assert response.status_code == 200
    body = response.json()
    assert body["quiz_id"] == quiz_id
    assert len(body["questions"]) == 1
    assert body["questions"][0]["question_text"]
