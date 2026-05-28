"""Day 20: nginx must not proxy React /student/:id routes to the API."""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_NGINX_CONF = _REPO_ROOT / "frontend" / "nginx.conf"


def test_nginx_does_not_proxy_broad_student_prefix():
    text = _NGINX_CONF.read_text(encoding="utf-8")
    assert "location /student/ {" not in text
    assert "location = /student/start" in text
    assert "location /student/questions" in text
