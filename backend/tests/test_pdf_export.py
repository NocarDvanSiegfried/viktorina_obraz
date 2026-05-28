"""Day 8: quiz export to PDF."""

from io import BytesIO
from unittest.mock import patch

from pypdf import PdfReader

SAMPLE_MODEL_JSON = """
[JSON_START]
{
  "quiz_title": "PDF Export Quiz",
  "subject": "History",
  "grade": "9",
  "topic": "World War",
  "questions": [
    {
      "type": "single_choice",
      "text": "When did WW2 end?",
      "options": ["1943", "1945", "1947", "1950"],
      "correct_answers": ["1945"],
      "explanation": "War ended in 1945.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""

SAMPLE_MODEL_JSON_RU = """
[JSON_START]
{
  "quiz_title": "Викторина по истории",
  "subject": "История",
  "grade": "9",
  "topic": "Вторая мировая война",
  "questions": [
    {
      "type": "single_choice",
      "text": "В каком году закончилась Вторая мировая война?",
      "options": ["1943", "1945", "1947", "1950"],
      "correct_answers": ["1945"],
      "explanation": "Война завершилась в 1945 году.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""

SAMPLE_MODEL_JSON_MIXED = """
[JSON_START]
{
  "quiz_title": "Викторина: Mixed Language Check",
  "subject": "История",
  "grade": "9",
  "topic": "WW2 Timeline",
  "questions": [
    {
      "type": "single_choice",
      "text": "Выберите correct year of the war end",
      "options": ["1943", "1945", "1947", "1950"],
      "correct_answers": ["1945"],
      "explanation": "Факт: correct answer is 1945.",
      "difficulty": "easy",
      "source_fragment_id": "manual_1"
    }
  ]
}
[JSON_END]
"""


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_export_pdf_returns_binary(_mock_chat, client):
    owner_id = "owner-day8-pdf"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "History",
            "grade": "9",
            "topic": "World War",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "WW2 ended in 1945.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    resp = client.get(f"/quiz/{quiz_id}/export-pdf", params={"owner_id": owner_id})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content.startswith(b"%PDF")


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON)
def test_export_pdf_other_owner_403(_mock_chat, client):
    owner_id = "owner-day8-pdf-a"
    other_owner = "owner-day8-pdf-b"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "History",
            "grade": "9",
            "topic": "World War",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "WW2 ended in 1945.",
        },
    )
    quiz_id = created.json()["quiz_id"]

    resp = client.get(f"/quiz/{quiz_id}/export-pdf", params={"owner_id": other_owner})
    assert resp.status_code == 403


@patch("app.services.gigachat_service.gigachat_service.chat", return_value=SAMPLE_MODEL_JSON_RU)
def test_export_pdf_keeps_cyrillic_text(_mock_chat, client):
    owner_id = "owner-day8-pdf-ru"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "История",
            "grade": "9",
            "topic": "Вторая мировая война",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "Вторая мировая война закончилась в 1945 году.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    resp = client.get(f"/quiz/{quiz_id}/export-pdf", params={"owner_id": owner_id})
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")

    extracted = PdfReader(BytesIO(resp.content)).pages[0].extract_text() or ""
    assert "Викторина по истории" in extracted
    assert "В каком году закончилась Вторая мировая война?" in extracted


@patch(
    "app.services.gigachat_service.gigachat_service.chat",
    return_value=SAMPLE_MODEL_JSON_MIXED,
)
def test_export_pdf_keeps_mixed_language_text_and_symbols(_mock_chat, client):
    owner_id = "owner-day8-pdf-mixed"
    created = client.post(
        "/quiz/generate-from-materials",
        data={
            "owner_id": owner_id,
            "subject": "История",
            "grade": "9",
            "topic": "WW2 Timeline",
            "question_count": "1",
            "difficulty": "easy",
            "question_types": "single_choice",
            "source_text": "WW2 закончилась в 1945 году. This is a mixed language source.",
        },
    )
    assert created.status_code == 200
    quiz_id = created.json()["quiz_id"]

    resp = client.get(f"/quiz/{quiz_id}/export-pdf", params={"owner_id": owner_id})
    assert resp.status_code == 200
    assert resp.content.startswith(b"%PDF")

    extracted = PdfReader(BytesIO(resp.content)).pages[0].extract_text() or ""
    assert "Викторина: Mixed Language Check" in extracted
    assert "Выберите correct year of the war end" in extracted
    assert "Факт: correct answer is 1945." in extracted
    assert "✓ 1945" in extracted
