"""Day 21: GET /quiz/{id} returns source fragment catalog with previews."""

from unittest.mock import patch

SAMPLE_JSON = """
[JSON_START]
{
  "quiz_title": "Фрагменты тест",
  "subject": "Биология",
  "grade": "8",
  "topic": "Клетка",
  "questions": [
    {
      "type": "single_choice",
      "text": "Вопрос по клетке?",
      "options": ["A", "B"],
      "correct_answers": ["A"],
      "explanation": "Пояснение",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""

SOURCE_TEXT = (
    "Клетка — основная структурная и функциональная единица живых организмов. "
    "Мембрана отделяет цитоплазму от внешней среды."
)


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_JSON)
def test_get_quiz_includes_fragment_catalog(_mock_chat, client):
    owner_id = "owner-day21-fragments"
    gen = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": SOURCE_TEXT,
        },
    )
    assert gen.status_code == 200
    quiz_id = gen.json()["quiz_id"]

    detail = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id})
    assert detail.status_code == 200
    body = detail.json()

    assert "fragments" in body
    fragments = body["fragments"]
    assert len(fragments) >= 1

    manual = next((f for f in fragments if f["id"] == "manual_1"), None)
    assert manual is not None
    assert manual["source_type"] == "manual_text"
    assert manual["preview"]
    assert "Клетка" in manual["preview"]

    question = body["questions"][0]
    assert question["source_fragment"] == "manual_1"


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_JSON)
def test_fragment_lookup_by_id(_mock_chat, client):
    owner_id = "owner-day21-lookup"
    gen = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "Биология",
            "grade": "8",
            "topic": "Клетка",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": SOURCE_TEXT,
        },
    )
    quiz_id = gen.json()["quiz_id"]
    detail = client.get(f"/quiz/{quiz_id}", params={"owner_id": owner_id}).json()

    from app.services.fragment_catalog_service import find_fragment

    found = find_fragment(detail["fragments"], "manual_1")
    assert found is not None
    assert found["preview"]
