"""Day 19: deploy_readiness.py orchestration (mocked)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "deploy_readiness.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("deploy_readiness_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["deploy_readiness_script"] = module
    spec.loader.exec_module(module)
    return module


def test_main_success_when_all_checks_pass(tmp_path):
    mod = _load_module()
    env_file = tmp_path / ".env"
    env_file.write_text("GIGACHAT_AUTH_KEY=key\n", encoding="utf-8")

    with (
        patch.object(mod, "run_secrets_check", return_value=[]),
        patch.object(mod, "run_env_validation", return_value=[]),
        patch.object(mod, "run_health_check", return_value=[]),
    ):
        code = mod.main(
            [
                "--env-file",
                str(env_file),
                "--api-url",
                "http://api.test",
                "--frontend-url",
                "http://ui.test",
            ]
        )

    assert code == 0


def test_main_fails_when_secrets_found():
    mod = _load_module()

    with patch.object(
        mod,
        "run_secrets_check",
        return_value=["backend/.env is tracked or contains secrets"],
    ):
        code = mod.main([])

    assert code == 1
