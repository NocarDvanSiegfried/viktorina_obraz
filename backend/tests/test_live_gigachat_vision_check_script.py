"""Day 18: live_gigachat_vision_check.py (mocked, no network)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "live_gigachat_vision_check.py"


def _load_vision_check_module():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(
        "live_gigachat_vision_check_script", _SCRIPT_PATH
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["live_gigachat_vision_check_script"] = module
    spec.loader.exec_module(module)
    return module


def test_run_image_ocr_case_validates_fragment_prefix():
    vision_check = _load_vision_check_module()

    fragment = type(
        "Fragment",
        (),
        {
            "fragment_id": "image_ocr_1",
            "text": "Клетка — основная единица",
            "source_type": "image",
        },
    )()

    with patch.object(
        vision_check.material_service,
        "extract_fragments",
        return_value=("image", [fragment]),
    ):
        result = vision_check.run_image_ocr_case()

    assert result["fragment_id"] == "image_ocr_1"
    assert result["case"] == "image_png"


def test_run_empty_pdf_ocr_case_validates_pdf_ocr_prefix():
    vision_check = _load_vision_check_module()

    fragment = type(
        "Fragment",
        (),
        {
            "fragment_id": "pdf_ocr_1",
            "text": "Клетка — основная единица",
            "source_type": "pdf",
        },
    )()

    with patch.object(
        vision_check.material_service,
        "extract_fragments",
        return_value=("pdf", [fragment]),
    ):
        result = vision_check.run_empty_pdf_ocr_case()

    assert result["fragment_id"].startswith("pdf_ocr_")


def test_main_success_with_mocked_cases():
    vision_check = _load_vision_check_module()

    with (
        patch.object(vision_check, "validate_live_environment", return_value=[]),
        patch.object(vision_check, "print_environment_header"),
        patch.object(
            vision_check,
            "run_image_ocr_case",
            return_value={"case": "image_png", "fragment_id": "image_ocr_1", "text_preview": "x"},
        ),
        patch.object(
            vision_check,
            "run_empty_pdf_ocr_case",
            return_value={"case": "empty_pdf", "fragment_id": "pdf_ocr_1", "text_preview": "y"},
        ),
        patch.object(
            vision_check,
            "run_quiz_from_image_ocr",
            return_value={
                "case": "quiz_from_image",
                "quiz_title": "Q",
                "source_fragment_id": "image_ocr_1",
                "question_preview": "text",
            },
        ),
    ):
        code = vision_check.main(["--skip-quiz"])

    assert code == 0


def test_main_fails_when_environment_invalid():
    vision_check = _load_vision_check_module()

    with patch.object(
        vision_check,
        "validate_live_environment",
        return_value=["GIGACHAT_VISION_MODEL is not set"],
    ):
        code = vision_check.main([])

    assert code == 1
