"""Day 19: check_secrets.py (filesystem scan, no git required)."""

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRIPT_PATH = _REPO_ROOT / "scripts" / "check_secrets.py"


def _load_module():
    spec = importlib.util.spec_from_file_location("check_secrets_script", _SCRIPT_PATH)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["check_secrets_script"] = module
    spec.loader.exec_module(module)
    return module


def test_scan_text_finds_inline_secret():
    mod = _load_module()
    leaked_line = "GIGACHAT_AUTH_KEY" + ' = "super-secret-token-12345"\n'
    findings = mod.scan_text(
        "config.py",
        leaked_line,
    )
    assert findings


def test_scan_text_ignores_empty_example_values():
    mod = _load_module()
    findings = mod.scan_text(
        "backend/.env.example",
        "GIGACHAT_AUTH_KEY" + "=\nGIGACHAT_MODEL=GigaChat\n",
    )
    assert findings == []


def test_git_tracked_forbidden_env():
    mod = _load_module()
    tracked = ["README.md", "backend/.env", "backend/app/main.py"]
    findings = mod.git_tracked_forbidden_env(tracked)
    assert any("backend/.env" in item for item in findings)


def test_scan_tracked_files_finds_secret_in_committed_file(tmp_path):
    mod = _load_module()
    secret_file = tmp_path / "backend" / "config_leak.py"
    secret_file.parent.mkdir(parents=True)
    secret_file.write_text(
        "GIGACHAT_AUTH_KEY" + ' = "leaked-token-abc"\n',
        encoding="utf-8",
    )

    findings = mod.scan_tracked_files(
        tmp_path,
        ["backend/config_leak.py"],
    )
    assert findings
