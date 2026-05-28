"""Day 17: live_gigachat_check.py (mocked, no network)."""

import importlib.util
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "live_gigachat_check.py"
_ENV_PATH = _REPO_ROOT / "scripts" / "live_gigachat_env.py"


def _load_live_check_module():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("live_gigachat_check_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["live_gigachat_check_script"] = module
    spec.loader.exec_module(module)
    return module


def _load_env_module():
    scripts_dir = str(_REPO_ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location("live_gigachat_env_script", _ENV_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["live_gigachat_env_script"] = module
    spec.loader.exec_module(module)
    return module


def test_validate_environment_requires_auth_key():
    env_module = _load_env_module()

    with patch.object(env_module, "settings") as mock_settings:
        setattr(mock_settings, "GIGACHAT_AUTH_KEY", "")
        mock_settings.E2E_MOCK_GIGACHAT = False
        mock_settings.GIGACHAT_VISION_MODEL = "GigaChat-Pro"
        errors = env_module.validate_live_environment()

    assert any("GIGACHAT_AUTH_KEY" in item for item in errors)


def test_validate_environment_rejects_mock_mode():
    env_module = _load_env_module()

    with patch.object(env_module, "settings") as mock_settings:
        setattr(mock_settings, "GIGACHAT_AUTH_KEY", "".join(["test", "-key-value"]))
        mock_settings.E2E_MOCK_GIGACHAT = True
        mock_settings.GIGACHAT_VISION_MODEL = "GigaChat-Pro"
        errors = env_module.validate_live_environment()

    assert any("E2E_MOCK_GIGACHAT" in item for item in errors)


def test_main_success_when_generation_works():
    live_check = _load_live_check_module()

    with (
        patch.object(live_check, "validate_live_environment", return_value=[]),
        patch.object(live_check, "print_environment_header"),
        patch.object(
            live_check,
            "run_live_generation",
            return_value={
                "quiz_title": "Live Quiz",
                "question_count": 1,
                "first_question": "Question one?",
            },
        ),
    ):
        code = live_check.main([])

    assert code == 0


def test_main_fails_when_environment_invalid():
    live_check = _load_live_check_module()

    with patch.object(
        live_check,
        "validate_live_environment",
        return_value=["GIGACHAT_AUTH_KEY is not set"],
    ):
        code = live_check.main([])

    assert code == 1
