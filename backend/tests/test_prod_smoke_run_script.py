"""Day 20: prod_smoke_run.py (mocked)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "prod_smoke_run.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("prod_smoke_run_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["prod_smoke_run_script"] = module
    spec.loader.exec_module(module)
    return module


def test_main_success_when_smoke_and_health_pass(tmp_path):
    mod = _load_module()
    smoke_mod = MagicMock()
    smoke_mod.run_smoke.return_value = (5, 5, ["[OK] health"], {"quiz_id": "q", "owner_id": "o"})
    smoke_mod.write_report = MagicMock()
    health_mod = MagicMock()

    with patch.object(mod, "_load", side_effect=[smoke_mod, health_mod]):
        code = mod.main(
            [
                "--api-url",
                "http://api.test",
                "--frontend-url",
                "http://ui.test",
                "--report",
                str(tmp_path / "report.md"),
            ]
        )

    assert code == 0
    smoke_mod.write_report.assert_called_once()


def test_main_fails_when_smoke_incomplete(tmp_path):
    mod = _load_module()
    smoke_mod = MagicMock()
    smoke_mod.run_smoke.return_value = (3, 5, ["[OK] a", "[FAIL] b"], None)
    smoke_mod.write_report = MagicMock()
    health_mod = MagicMock()

    with patch.object(mod, "_load", side_effect=[smoke_mod, health_mod]):
        code = mod.main(
            [
                "--api-url",
                "http://api.test",
                "--report",
                str(tmp_path / "report.md"),
                "--skip-health",
            ]
        )

    assert code == 1
