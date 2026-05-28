"""Day 20: smoke_api_check.py CLI and report (mocked HTTP)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "smoke_api_check.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("smoke_api_check_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["smoke_api_check_script"] = module
    spec.loader.exec_module(module)
    return module


def test_parse_args_default_base_url():
    mod = _load_module()
    args = mod.parse_args([])
    assert args.base_url == "http://127.0.0.1:8000"


def test_parse_args_custom_base_url():
    mod = _load_module()
    args = mod.parse_args(["--base-url", "https://api.example.com/"])
    assert args.base_url == "https://api.example.com"


def test_export_headers_valid():
    mod = _load_module()
    response = MagicMock()
    response.headers = {
        "content-type": "application/pdf",
        "content-disposition": "attachment; filename*=UTF-8''quiz.pdf",
    }
    assert mod.check_export_headers(response, "pdf") is True


def test_export_headers_invalid_docx():
    mod = _load_module()
    response = MagicMock()
    response.headers = {"content-type": "text/plain"}
    assert mod.check_export_headers(response, "docx") is False


def test_write_report_creates_markdown(tmp_path):
    mod = _load_module()
    report_path = tmp_path / "PROD_SMOKE_REPORT.md"
    mod.write_report(
        report_path,
        base_url="https://api.test",
        passed=20,
        total=22,
        lines=["[OK] GET /health", "[FAIL] POST /student/finish"],
    )
    text = report_path.read_text(encoding="utf-8")
    assert "https://api.test" in text
    assert "20/22" in text
