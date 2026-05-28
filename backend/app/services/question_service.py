"""Validation and helpers for quiz question CRUD."""

from __future__ import annotations

MAX_QUESTIONS_PER_QUIZ = 15

TRUE_FALSE_OPTIONS = ("Верно", "Неверно")

QuestionType = str


class QuestionValidationError(ValueError):
    pass


def validate_question_payload(
    question_type: QuestionType,
    answers: list[str],
    correct_answers: list[str],
) -> None:
    cleaned_answers = [a.strip() for a in answers if a.strip()]
    cleaned_correct = [c.strip() for c in correct_answers if c.strip()]

    if not cleaned_answers:
        raise QuestionValidationError("Нужен хотя бы один вариант ответа")

    if not cleaned_correct:
        raise QuestionValidationError("Укажите правильный ответ")

    unknown_correct = [c for c in cleaned_correct if c not in cleaned_answers]
    if unknown_correct:
        raise QuestionValidationError("Правильные ответы должны быть среди вариантов")

    if question_type == "single_choice":
        if len(cleaned_answers) < 2:
            raise QuestionValidationError("Для одиночного выбора нужно минимум 2 варианта")
        if len(cleaned_correct) != 1:
            raise QuestionValidationError("Для одиночного выбора укажите один правильный ответ")

    elif question_type == "multiple_choice":
        if len(cleaned_answers) < 3:
            raise QuestionValidationError(
                "Для множественного выбора нужно минимум 3 варианта"
            )
        if len(cleaned_correct) < 2:
            raise QuestionValidationError(
                "Для множественного выбора укажите минимум 2 правильных ответа"
            )

    elif question_type == "true_false":
        if cleaned_answers != list(TRUE_FALSE_OPTIONS):
            raise QuestionValidationError(
                'Для «Верно/Неверно» варианты должны быть: «Верно», «Неверно»'
            )
        if len(cleaned_correct) != 1:
            raise QuestionValidationError("Укажите один правильный ответ")

    else:
        raise QuestionValidationError(f"Неизвестный тип вопроса: {question_type}")


def normalize_answers(answers: list[str]) -> list[str]:
    return [a.strip() for a in answers if a.strip()]


def default_answers_for_type(question_type: QuestionType) -> list[str]:
    if question_type == "true_false":
        return list(TRUE_FALSE_OPTIONS)
    return ["", ""]
