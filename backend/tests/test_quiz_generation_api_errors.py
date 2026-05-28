"""API returns teacher-friendly detail for QuizModelResponseError."""

from unittest.mock import patch

from app.services.quiz_model_observability import QuizModelResponseError, user_message_for_code


@patch("app.api.quizzes.quiz_service.generate_quiz_from_fragments")
def test_generate_from_materials_returns_friendly_detail(mock_generate, client):
    mock_generate.side_effect = QuizModelResponseError(
        code="JSON_TRUNCATED",
        user_message=user_message_for_code("JSON_TRUNCATED"),
        technical_detail="JSONDecodeError: ...",
    )

    response = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": "owner-api-error-test",
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "5",
            "question_types": ["single_choice"],
            "difficulty": "easy",
            "source_text": "Клетка — основная единица жизни.",
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == user_message_for_code("JSON_TRUNCATED")
