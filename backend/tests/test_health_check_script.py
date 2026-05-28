"""Health-check deployment script (mocked HTTP)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "health_check.py"


def _load_health_check_module():
    spec = importlib.util.spec_from_file_location("health_check_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["health_check_script"] = module
    spec.loader.exec_module(module)
    return module


def test_check_url_api_health():
    health_check = _load_health_check_module()

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"status": "ok", "service": "test"}

    with patch.object(health_check.httpx, "get", return_value=mock_response) as mock_get:
        health_check.check_url("API", "http://example.test/health", expect_json=True)
        mock_get.assert_called_once()


def test_main_reports_success():
    health_check = _load_health_check_module()

    with patch.object(health_check, "check_url") as mock_check:
        mock_check.return_value = None
        code = health_check.main(
            ["--api-url", "http://api.test", "--frontend-url", "http://ui.test"]
        )

    assert code == 0
    assert mock_check.call_count == 2
