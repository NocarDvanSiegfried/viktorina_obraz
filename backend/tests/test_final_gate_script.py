"""Day 22: final_gate.py (mocked subprocess)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "final_gate.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("final_gate_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["final_gate_script"] = module
    spec.loader.exec_module(module)
    return module


def test_main_passes_when_all_steps_ok():
    mod = _load_module()
    secrets_mod = MagicMock()
    secrets_mod.scan_repository.return_value = []

    with patch.object(mod, "_run", return_value=True):
        with patch.object(mod, "_load_script", return_value=secrets_mod):
            code = mod.main([])

    assert code == 0


def test_main_fails_on_secrets():
    mod = _load_module()
    secrets_mod = MagicMock()
    secrets_mod.scan_repository.return_value = ["leak in file"]

    with patch.object(mod, "_run", return_value=True):
        with patch.object(mod, "_load_script", return_value=secrets_mod):
            code = mod.main(["--skip-pytest", "--skip-frontend-build"])

    assert code == 1
