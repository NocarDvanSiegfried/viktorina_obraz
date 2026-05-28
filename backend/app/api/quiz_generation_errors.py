"""Map quiz generation failures to teacher-friendly HTTP errors."""

from fastapi import HTTPException

from app.services.quiz_model_observability import QuizModelResponseError


def raise_quiz_ai_http_error(exc: Exception, *, action_label: str) -> None:
    """
    Raise HTTPException for quiz AI failures.

    action_label: short Russian verb phrase, e.g. "сгенерировать викторину".
    """
    if isinstance(exc, QuizModelResponseError):
        raise HTTPException(status_code=502, detail=exc.user_message) from exc

    raise HTTPException(
        status_code=502,
        detail=f"Не удалось {action_label}: {exc}",
    ) from exc
