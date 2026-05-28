"""Deterministic GigaChat responses for E2E / CI (no network)."""

E2E_MOCK_CHAT_RESPONSE = """
[JSON_START]
{
  "quiz_title": "E2E Викторина",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Что является основной единицей жизни?",
      "options": ["Атом", "Клетка", "Орган", "Ткань"],
      "correct_answers": ["Клетка"],
      "explanation": "Клетка — основная структурная единица.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    },
    {
      "type": "true_false",
      "text": "Клетка не имеет мембраны.",
      "options": ["Верно", "Неверно"],
      "correct_answers": ["Неверно"],
      "explanation": "У клетки есть мембрана.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""

E2E_MOCK_OCR_TEXT = (
    "Клетка — основная структурная и функциональная единица живых организмов. "
    "Клеточная мембрана отделяет внутреннее содержимое от внешней среды."
)
