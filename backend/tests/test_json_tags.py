from app.services.quiz_service import QuizService

RAW_WITHOUT_BRACKETS = """
JSON_START
{"quiz_title": "T", "subject": "S", "grade": "1", "topic": "T", "questions": []}
JSON_END
"""


def test_extract_json_without_square_brackets():
    data = QuizService()._extract_json(RAW_WITHOUT_BRACKETS)
    assert data["quiz_title"] == "T"
