"""Integration of quiz_service with stage-1 observability."""

import pytest

from app.schemas.material import SourceFragment
from app.services.quiz_model_observability import QuizModelResponseError
from app.services.gigachat_chat_meta import GigaChatChatMeta
from app.services.quiz_service import QuizService
from app.services import quiz_service as quiz_service_module


def test_generate_raises_quiz_model_response_error_on_broken_json(monkeypatch):
    service = QuizService()

    def fake_chat(messages, temperature=0.2, max_tokens=None):
        return '[JSON_START]\n{"quiz_title": "T", "questions": [\n'

    monkeypatch.setattr(
        "app.services.quiz_service.gigachat_service.chat",
        fake_chat,
    )
    quiz_service_module.gigachat_service.last_chat_meta = GigaChatChatMeta(
        finish_reason="length",
        completion_tokens=9999,
        prompt_tokens=100,
        total_tokens=10099,
    )

    fragments = [
        SourceFragment(
            fragment_id="manual_1",
            source_type="manual_text",
            source_name="teacher_input",
            text="Клетка — основная единица.",
        )
    ]

    with pytest.raises(QuizModelResponseError) as exc_info:
        service.generate_quiz_from_fragments(
            subject="Биология",
            grade="8",
            topic="Клетка",
            question_count=10,
            question_types=["single_choice"],
            difficulty="easy",
            fragments=fragments,
        )

    assert exc_info.value.code == "JSON_TRUNCATED"
    assert "вопрос" in exc_info.value.user_message.lower()
