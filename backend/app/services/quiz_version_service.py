"""Quiz version snapshots: save, list, restore."""

from __future__ import annotations

import json

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Question, Quiz, QuizVersion, generate_uuid, utcnow


class QuizVersionNotFoundError(Exception):
    pass


def build_snapshot(quiz: Quiz, questions: list[Question]) -> dict:
    return {
        "quiz": {
            "title": quiz.title,
            "subject": quiz.subject,
            "grade": quiz.grade,
            "difficulty": quiz.difficulty,
            "full_time_seconds": quiz.full_time_seconds,
            "question_time_seconds": quiz.question_time_seconds,
            "max_attempts": quiz.max_attempts,
            "status": quiz.status,
        },
        "questions": [
            {
                "id": question.id,
                "question_text": question.question_text,
                "question_type": question.question_type,
                "answers": question.answers,
                "correct_answers": question.correct_answers,
                "explanation": question.explanation,
                "source_fragment": question.source_fragment,
                "points": question.points,
                "order_idx": question.order_idx,
            }
            for question in questions
        ],
    }


def _next_version_number(db: Session, quiz_id: str) -> int:
    current = (
        db.query(func.max(QuizVersion.version_number))
        .filter(QuizVersion.quiz_id == quiz_id)
        .scalar()
    )
    return int(current or 0) + 1


def save_version(
    db: Session,
    quiz: Quiz,
    questions: list[Question],
    *,
    label: str,
    created_by: str,
) -> QuizVersion:
    snapshot = build_snapshot(quiz, questions)
    version = QuizVersion(
        id=generate_uuid(),
        quiz_id=quiz.id,
        version_number=_next_version_number(db, quiz.id),
        snapshot_json=json.dumps(snapshot, ensure_ascii=False),
        label=label.strip() or "Изменение",
        created_by=created_by,
        created_at=utcnow(),
    )
    db.add(version)
    db.flush()
    return version


def list_versions(db: Session, quiz_id: str) -> list[QuizVersion]:
    return (
        db.query(QuizVersion)
        .filter(QuizVersion.quiz_id == quiz_id)
        .order_by(QuizVersion.version_number.desc())
        .all()
    )


def get_version(db: Session, quiz_id: str, version_id: str) -> QuizVersion:
    version = (
        db.query(QuizVersion)
        .filter(QuizVersion.id == version_id, QuizVersion.quiz_id == quiz_id)
        .first()
    )
    if version is None:
        raise QuizVersionNotFoundError("Версия не найдена")
    return version


def parse_snapshot(version: QuizVersion) -> dict:
    try:
        payload = json.loads(version.snapshot_json)
    except json.JSONDecodeError as exc:
        raise ValueError("Некорректный snapshot версии") from exc
    if not isinstance(payload, dict):
        raise ValueError("Некорректный snapshot версии")
    return payload


def restore_version(
    db: Session,
    quiz: Quiz,
    version: QuizVersion,
) -> list[Question]:
    snapshot = parse_snapshot(version)
    quiz_data = snapshot.get("quiz") or {}
    quiz.title = quiz_data.get("title", quiz.title)
    quiz.subject = quiz_data.get("subject", quiz.subject)
    quiz.grade = quiz_data.get("grade", quiz.grade)
    quiz.difficulty = quiz_data.get("difficulty", quiz.difficulty)
    quiz.full_time_seconds = quiz_data.get("full_time_seconds", quiz.full_time_seconds)
    quiz.question_time_seconds = quiz_data.get(
        "question_time_seconds", quiz.question_time_seconds
    )
    quiz.max_attempts = quiz_data.get("max_attempts", quiz.max_attempts)
    quiz.status = quiz_data.get("status", quiz.status)
    quiz.updated_at = utcnow()

    existing = {
        question.id: question
        for question in db.query(Question).filter(Question.quiz_id == quiz.id).all()
    }
    snapshot_questions = snapshot.get("questions") or []
    kept_ids: set[str] = set()

    for idx, item in enumerate(snapshot_questions):
        question_id = item.get("id") or generate_uuid()
        kept_ids.add(question_id)
        question = existing.get(question_id)
        if question is None:
            question = Question(id=question_id, quiz_id=quiz.id)
            db.add(question)
            existing[question_id] = question

        question.question_text = item.get("question_text", "")
        question.question_type = item.get("question_type", "single_choice")
        question.answers = item.get("answers")
        question.correct_answers = item.get("correct_answers")
        question.explanation = item.get("explanation")
        question.source_fragment = item.get("source_fragment")
        question.points = int(item.get("points") or 1)
        question.order_idx = int(item.get("order_idx", idx))

    for question_id, question in list(existing.items()):
        if question_id not in kept_ids:
            db.delete(question)

    db.flush()
    return (
        db.query(Question)
        .filter(Question.quiz_id == quiz.id)
        .order_by(Question.order_idx)
        .all()
    )
