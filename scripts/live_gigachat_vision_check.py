#!/usr/bin/env python3
"""Verify live GigaChat Vision OCR (image + empty PDF fallback)."""

from __future__ import annotations

import argparse
import json
import sys
from io import BytesIO
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from live_gigachat_env import print_environment_header, validate_live_environment

from app.services.material_service import material_service  # noqa: E402
from app.services.quiz_service import quiz_service  # noqa: E402

LIVE_OCR_TEXT = (
    "Клетка — основная структурная и функциональная единица живых организмов. "
    "Клеточная мембрана отделяет внутреннее содержимое клетки от внешней среды."
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


def _make_empty_pdf() -> bytes:
    from pypdf import PdfWriter

    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buffer = BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


def run_image_ocr_case() -> dict:
    png_bytes = _make_text_png(LIVE_OCR_TEXT)
    file_type, fragments = material_service.extract_fragments(
        "live_vision_check.png", png_bytes
    )
    if file_type != "image":
        raise RuntimeError(f"Expected image type, got {file_type}")
    if not fragments:
        raise RuntimeError("No fragments from image OCR")
    fragment_id = fragments[0].fragment_id
    if not fragment_id.startswith("image_ocr_"):
        raise RuntimeError(f"Unexpected fragment_id: {fragment_id}")
    text = fragments[0].text.strip()
    if not text:
        raise RuntimeError("OCR returned empty text for image")
    return {
        "case": "image_png",
        "fragment_id": fragment_id,
        "text_preview": text[:120],
    }


def run_empty_pdf_ocr_case() -> dict:
    pdf_bytes = _make_empty_pdf()
    file_type, fragments = material_service.extract_fragments(
        "live_vision_empty.pdf", pdf_bytes
    )
    if file_type != "pdf":
        raise RuntimeError(f"Expected pdf type, got {file_type}")
    if not fragments:
        raise RuntimeError("No fragments from empty PDF vision fallback")
    fragment_id = fragments[0].fragment_id
    if not fragment_id.startswith("pdf_ocr_"):
        raise RuntimeError(f"Expected pdf_ocr_* fragment_id, got {fragment_id}")
    text = fragments[0].text.strip()
    if not text:
        raise RuntimeError("OCR returned empty text for PDF")
    return {
        "case": "empty_pdf",
        "fragment_id": fragment_id,
        "text_preview": text[:120],
    }


def run_quiz_from_image_ocr() -> dict:
    png_bytes = _make_text_png(LIVE_OCR_TEXT)
    _file_type, fragments = material_service.extract_fragments(
        "live_vision_quiz.png", png_bytes
    )
    result = quiz_service.generate_quiz_from_fragments(
        subject="Биология",
        grade="8",
        topic="Клетка",
        question_count=1,
        question_types=["single_choice"],
        difficulty="easy",
        fragments=fragments,
    )
    if not result.questions:
        raise RuntimeError("Quiz generation returned no questions")
    source_id = result.questions[0].source_fragment_id or ""
    if not source_id.startswith("image_ocr_"):
        raise RuntimeError(f"Question source_fragment_id expected image_ocr_*, got {source_id!r}")
    return {
        "case": "quiz_from_image",
        "quiz_title": result.quiz_title,
        "source_fragment_id": source_id,
        "question_preview": result.questions[0].text[:120],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Live GigaChat Vision: OCR from PNG and empty PDF."
    )
    parser.add_argument("--json", action="store_true", help="Print JSON summary")
    parser.add_argument(
        "--skip-quiz",
        action="store_true",
        help="Only OCR cases, skip quiz generation (faster)",
    )
    args = parser.parse_args(argv)

    env_errors = validate_live_environment()
    if env_errors:
        for message in env_errors:
            print(f"FAIL {message}", file=sys.stderr)
        return 1

    print_environment_header()

    results: list[dict] = []
    try:
        image_result = run_image_ocr_case()
        results.append(image_result)
        print("OK  Image OCR (PNG)")
        print(f"    fragment_id={image_result['fragment_id']}")
        print(f"    text_preview={image_result['text_preview']!r}")

        pdf_result = run_empty_pdf_ocr_case()
        results.append(pdf_result)
        print("OK  Empty PDF OCR (vision fallback)")
        print(f"    fragment_id={pdf_result['fragment_id']}")
        print(f"    text_preview={pdf_result['text_preview']!r}")

        if not args.skip_quiz:
            quiz_result = run_quiz_from_image_ocr()
            results.append(quiz_result)
            print("OK  Quiz from image OCR")
            print(f"    source_fragment_id={quiz_result['source_fragment_id']}")
            print(f"    title={quiz_result['quiz_title']!r}")
    except Exception as exc:
        print(f"FAIL Vision check: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps({"status": "ok", "results": results}, ensure_ascii=False))

    print("\nLive GigaChat Vision check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
