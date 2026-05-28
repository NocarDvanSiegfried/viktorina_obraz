"""Mirrors frontend quizResultsAnalytics formulas (UI-8, client-side only)."""


def _average_percent(results: list[dict]) -> int:
    if not results:
        return 0
    return round(sum(item["percent"] for item in results) / len(results))


def _unique_student_count(results: list[dict]) -> int:
    return len({item["student_name"].strip().lower() for item in results})


def _top_hardest_questions(results: list[dict], top_n: int = 3) -> list[dict]:
    counts: dict[str, dict] = {}
    for attempt in results:
        for wrong in attempt.get("wrong_questions", []):
            key = wrong.get("question_id") or wrong["question_text"]
            row = counts.setdefault(
                key,
                {
                    "question_id": wrong.get("question_id", ""),
                    "question_text": wrong["question_text"],
                    "wrong_count": 0,
                },
            )
            row["wrong_count"] += 1
    ranked = sorted(counts.values(), key=lambda item: item["wrong_count"], reverse=True)
    return ranked[:top_n]


def test_average_percent_rounds_mean():
    results = [{"percent": 60}, {"percent": 70}]
    assert _average_percent(results) == 65


def test_unique_student_count_ignores_case():
    results = [
        {"student_name": "Ivan"},
        {"student_name": "ivan"},
        {"student_name": "Maria"},
    ]
    assert _unique_student_count(results) == 2


def test_top_hardest_questions_groups_by_question_id():
    results = [
        {
            "wrong_questions": [
                {"question_id": "q1", "question_text": "A"},
                {"question_id": "q1", "question_text": "A"},
            ]
        },
        {"wrong_questions": [{"question_id": "q2", "question_text": "B"}]},
    ]
    top = _top_hardest_questions(results)
    assert top[0]["question_id"] == "q1"
    assert top[0]["wrong_count"] == 2
    assert top[1]["wrong_count"] == 1
