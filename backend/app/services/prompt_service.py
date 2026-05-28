from app.schemas.material import SourceFragment
from app.services.quiz_generation_config import explanation_max_chars


def build_quiz_prompt(
    subject: str,
    grade: str,
    topic: str,
    question_count: int,
    question_types: list[str],
    difficulty: str,
    combined_context: str,
    fragments: list[SourceFragment],
    *,
    compact: bool = False,
) -> str:
    fragments_info = "\n".join(
        [
            f"- {fragment.fragment_id}: {fragment.source_name} ({fragment.source_type})"
            for fragment in fragments
        ]
    )
    valid_fragment_ids = ", ".join(fragment.fragment_id for fragment in fragments)
    max_explanation = explanation_max_chars(compact=compact)

    compact_block = ""
    if compact:
        compact_block = (
            "\nРежим компактный: сократи формулировки. "
            "Обязательно закрой ответ тегом [JSON_END].\n"
        )

    return f"""
Ты — методист и автор школьных викторин.
Верни только валидный JSON, без markdown, без комментариев и пояснений.
{compact_block}
Параметры:
- Предмет: {subject}
- Класс: {grade}
- Тема: {topic}
- Количество вопросов: {question_count}
- Типы вопросов: {", ".join(question_types)}
- Уровень сложности всех вопросов: {difficulty}

Доступные фрагменты источника:
{fragments_info}

Допустимые source_fragment_id:
{valid_fragment_ids}

Объединенный контекст:
{combined_context}

Нужно вернуть JSON строго такого вида:
{{
  "quiz_title": "string",
  "subject": "{subject}",
  "grade": "{grade}",
  "topic": "{topic}",
  "questions": [
    {{
      "type": "single_choice|multiple_choice|true_false",
      "text": "string",
      "options": ["string", "string"],
      "correct_answers": ["string"],
      "explanation": "string",
      "difficulty": "easy|medium|hard",
      "source_fragment_id": "string"
    }}
  ]
}}

Строгие требования:
- Используй только информацию из переданных материалов.
- Каждый вопрос должен опираться на один фрагмент и иметь source_fragment_id строго из списка допустимых (без выдуманных id).
- source_fragment_id должен соответствовать фрагменту, из которого взят факт для вопроса.
- Дистракторы должны быть правдоподобными типичными ошибками учеников.
- Все вопросы одного уровня сложности: {difficulty}.
- Для single_choice: 4 варианта, 1 правильный.
- Для multiple_choice: 5 вариантов, 2 правильных.
- Для true_false: варианты ровно ["Верно", "Неверно"].
- Поле explanation: не более {max_explanation} символов, одно короткое предложение.
- Ключи: correct_answers, source_fragment_id (snake_case).
- В начале ответа [JSON_START], в конце [JSON_END].
- Между тегами только валидный JSON.
"""


def build_regenerate_question_prompt(
    subject: str,
    grade: str,
    topic: str,
    difficulty: str,
    question_type: str,
    current_question_text: str,
    source_fragment_id: str | None,
    *,
    compact: bool = False,
) -> str:
    fragment_hint = source_fragment_id or "manual_1"
    max_explanation = explanation_max_chars(compact=compact)
    compact_block = ""
    if compact:
        compact_block = "\nРежим компактный: обязательно закрой ответ тегом [JSON_END].\n"

    return f"""
Ты — методист. Пересоздай один вопрос викторины по тем же параметрам.
Верни только валидный JSON одного вопроса, без markdown.
{compact_block}
Параметры викторины:
- Предмет: {subject}
- Класс: {grade}
- Тема: {topic}
- Сложность: {difficulty}
- Тип вопроса (сохрани): {question_type}
- source_fragment_id (сохрани если возможно): {fragment_hint}

Текущий вопрос (замени на новый по той же теме, другая формулировка):
{current_question_text}

JSON строго такого вида:
{{
  "type": "{question_type}",
  "text": "string",
  "options": ["string"],
  "correct_answers": ["string"],
  "explanation": "string",
  "difficulty": "{difficulty}",
  "source_fragment_id": "{fragment_hint}"
}}

Требования:
- Тип вопроса не менять.
- single_choice: 4 варианта, 1 правильный.
- multiple_choice: 5 вариантов, 2 правильных.
- true_false: варианты ровно ["Верно", "Неверно"].
- explanation: не более {max_explanation} символов.
- В начале [JSON_START], в конце [JSON_END].
"""
