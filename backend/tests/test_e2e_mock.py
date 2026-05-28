"""E2E mock mode: generate without real GigaChat."""

import pytest


@pytest.fixture
def e2e_mock_env(monkeypatch):
    monkeypatch.setenv("E2E_MOCK_GIGACHAT", "1")

    from app.core.config import settings

    monkeypatch.setattr(settings, "E2E_MOCK_GIGACHAT", True)


def test_e2e_mock_generate_from_text(client, e2e_mock_env):
    response = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": "e2e-mock-owner",
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "2",
            "difficulty": "easy",
            "question_types": ["single_choice", "true_false"],
            "source_text": "Текст про клетку для e2e mock.",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["quiz_id"]
    assert body["title"] == "E2E Викторина"
    assert len(body["questions"]) == 2
