"""Day 22: demo_jury_flow.py (mocked)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "demo_jury_flow.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("demo_jury_flow_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["demo_jury_flow_script"] = module
    spec.loader.exec_module(module)
    return module


def test_main_success_when_smoke_and_extras_pass(tmp_path):
    mod = _load_module()
    smoke_mod = MagicMock()
    smoke_mod.run_smoke.return_value = (10, 10, ["[OK] smoke"], {"quiz_id": "q1", "owner_id": "o1"})
    smoke_mod.ok = lambda name, cond, detail="": (cond, f"  [{'OK ' if cond else 'FAIL'}] {name}")

    with patch.object(mod, "_load_smoke", return_value=smoke_mod):
        with patch.object(
            mod,
            "_extra_jury_checks",
            return_value=(1, 1, ["[OK] versions"]),
        ):
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
    assert (tmp_path / "report.md").exists()


def test_main_fails_when_smoke_incomplete(tmp_path):
    mod = _load_module()
    smoke_mod = MagicMock()
    smoke_mod.run_smoke.return_value = (5, 10, ["[FAIL] x"], None)

    with patch.object(mod, "_load_smoke", return_value=smoke_mod):
        code = mod.main(
            [
                "--api-url",
                "http://api.test",
                "--skip-report",
            ]
        )

    assert code == 1
