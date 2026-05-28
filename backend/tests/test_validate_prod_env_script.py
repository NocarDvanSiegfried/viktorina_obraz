"""Day 19: validate_prod_env.py (no network)."""

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "validate_prod_env.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("validate_prod_env_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["validate_prod_env_script"] = module
    spec.loader.exec_module(module)
    return module


def test_validate_env_file_ok(tmp_path):
    mod = _load_module()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GIGACHAT_AUTH_KEY=secret-key",
                "GIGACHAT_SCOPE=GIGACHAT_API_PERS",
                "GIGACHAT_MODEL=GigaChat-2-Pro",
                "GIGACHAT_VISION_MODEL=GigaChat-2-Pro",
                "GIGACHAT_CA_BUNDLE_FILE=./certs/russian_trusted_root_ca_pem.crt",
                "FRONTEND_ORIGIN=https://app.example.com",
                "DATABASE_URL=sqlite:///./data/app.db",
            ]
        ),
        encoding="utf-8",
    )

    errors = mod.validate_env_file(env_file, production=True)
    assert errors == []


def test_validate_env_file_rejects_mock_in_production(tmp_path):
    mod = _load_module()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "GIGACHAT_AUTH_KEY=key\nE2E_MOCK_GIGACHAT=1\n",
        encoding="utf-8",
    )

    errors = mod.validate_env_file(env_file, production=True)
    assert any("E2E_MOCK_GIGACHAT" in item for item in errors)


def test_validate_env_file_requires_gigachat_key(tmp_path):
    mod = _load_module()
    env_file = tmp_path / ".env"
    env_file.write_text("FRONTEND_ORIGIN=https://app.example.com\n", encoding="utf-8")

    errors = mod.validate_env_file(env_file, production=True)
    assert any("GIGACHAT_AUTH_KEY" in item for item in errors)


def test_main_returns_zero_on_valid_env(tmp_path):
    mod = _load_module()
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "GIGACHAT_AUTH_KEY=secret-key",
                "GIGACHAT_SCOPE=GIGACHAT_API_PERS",
                "GIGACHAT_MODEL=GigaChat-2-Pro",
                "GIGACHAT_VISION_MODEL=GigaChat-2-Pro",
                "FRONTEND_ORIGIN=https://app.example.com",
                "DATABASE_URL=sqlite:///./data/app.db",
            ]
        ),
        encoding="utf-8",
    )

    code = mod.main(["--env-file", str(env_file), "--production"])
    assert code == 0
