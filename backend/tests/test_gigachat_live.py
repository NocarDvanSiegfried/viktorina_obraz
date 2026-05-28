"""Optional live GigaChat tests — run only when GIGACHAT_AUTH_KEY is set."""

import os
from io import BytesIO

import pytest
from dotenv import load_dotenv

from app.schemas.material import SourceFragment
from app.services.gigachat_service import gigachat_service
from app.services.material_service import material_service
from app.services.quiz_service import quiz_service

load_dotenv()

pytestmark = pytest.mark.skipif(
    not os.getenv("GIGACHAT_AUTH_KEY"),
    reason="GIGACHAT_AUTH_KEY not configured",
)


def _make_text_png(text: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont

    image = Image.new("RGB", (640, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except OSError:
        font = ImageFont.load_default()
    draw.text((24, 72), text, fill=(0, 0, 0), font=font)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


LIVE_OCR_TEXT = (
    "Клетка — основная структурная и функциональная единица живых организмов."
)


def _make_empty_pdf() -> bytes:
    from io import BytesIO

    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


@pytest.mark.integration
@pytest.mark.live
def test_live_gigachat_generate_minimal():
    fragments = [
        SourceFragment(
            fragment_id="manual_1",
            source_type="manual_text",
            source_name="teacher_input",
            text=(
                "Клетка — основная структурная и функциональная единица живых организмов. "
                "Клеточная мембрана отделяет внутреннее содержимое клетки от внешней среды."
            ),
        )
    ]

    result = quiz_service.generate_quiz_from_fragments(
        subject="Биология",
        grade="8",
        topic="Клетка",
        question_count=2,
        question_types=["single_choice", "true_false"],
        difficulty="easy",
        fragments=fragments,
    )

    assert result.quiz_title
    assert len(result.questions) >= 1
    assert result.questions[0].options


@pytest.mark.integration
@pytest.mark.live
def test_live_gigachat_vision_ocr_from_image():
    png_bytes = _make_text_png(LIVE_OCR_TEXT)
    extracted = gigachat_service.extract_text_from_visual("live_ocr.png", png_bytes)

    assert extracted.strip()
    normalized = extracted.lower()
    assert "клет" in normalized or "cell" in normalized


@pytest.mark.integration
@pytest.mark.live
def test_live_material_image_to_fragments():
    png_bytes = _make_text_png(LIVE_OCR_TEXT)
    file_type, fragments = material_service.extract_fragments("live_lesson.png", png_bytes)

    assert file_type == "image"
    assert len(fragments) >= 1
    assert fragments[0].fragment_id.startswith("image_ocr_")
    assert fragments[0].text.strip()


@pytest.mark.integration
@pytest.mark.live
def test_live_generate_quiz_from_image_material():
    png_bytes = _make_text_png(LIVE_OCR_TEXT)
    file_type, fragments = material_service.extract_fragments("live_lesson.png", png_bytes)
    assert file_type == "image"
    assert fragments

    result = quiz_service.generate_quiz_from_fragments(
        subject="Биология",
        grade="8",
        topic="Клетка",
        question_count=1,
        question_types=["single_choice"],
        difficulty="easy",
        fragments=fragments,
    )

    assert result.quiz_title
    assert len(result.questions) == 1
    assert result.questions[0].source_fragment_id
    assert result.questions[0].source_fragment_id.startswith("image_ocr_")


@pytest.mark.integration
@pytest.mark.live
def test_live_empty_pdf_ocr_fragments():
    pdf_bytes = _make_empty_pdf()
    file_type, fragments = material_service.extract_fragments(
        "live_empty_scan.pdf", pdf_bytes
    )

    assert file_type == "pdf"
    assert len(fragments) >= 1
    assert fragments[0].fragment_id.startswith("pdf_ocr_")
    assert fragments[0].text.strip()
