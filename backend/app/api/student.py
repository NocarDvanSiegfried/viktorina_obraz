import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.db.database import get_db
from app.db.models import Question, Result, Quiz
from app.schemas.student import (
    StudentAnswerResponse,
    StudentFinishResponse,
    StudentQuestionsResponse,
    StudentStartResponse,
)

router = APIRouter(prefix="/student", tags=["Student"])


def _parse_iso_datetime(value: str) -> datetime:
    # Support common ISO formats including trailing "Z".
    normalized = value.replace("Z", "+00:00") if value.endswith("Z") else value
    return datetime.fromisoformat(normalized)


def _load_result_state(result: Result) -> dict:
    if not result.answers_json:
        return {"started_at": None, "answers": {}}
    try:
        return json.loads(result.answers_json)
    except Exception:
        return {"started_at": None, "answers": {}}


def _dump_result_state(state: dict) -> str:
    return json.dumps(state, ensure_ascii=False)


def _sort_questions(quiz_questions: list[Question]) -> list[Question]:
    return sorted(quiz_questions, key=lambda q: q.order_idx)


@router.post("/start")
def student_start(
    quiz_id: str = Form(..., min_length=1),
    student_name: str = Form(..., min_length=1),
    started_at: str | None = Form(None),
    db: Session = Depends(get_db),
) -> StudentStartResponse:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.deleted_at.is_(None)).first()
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")

    attempts_count = (
        db.query(Result)
        .filter(Result.quiz_id == quiz_id, Result.student_name == student_name)
        .count()
    )
    attempt_number = attempts_count + 1

    if quiz.max_attempts is not None and attempt_number > quiz.max_attempts:
        raise HTTPException(status_code=403, detail="Превышен лимит попыток")

    effective_started_at = started_at
    if not effective_started_at:
        effective_started_at = datetime.now(timezone.utc).isoformat()

    initial_state = {"started_at": effective_started_at, "answers": {}}

    result = Result(
        quiz_id=quiz_id,
        student_name=student_name,
        score=0,
        max_score=None,
        attempt_number=attempt_number,
        duration_seconds=None,
        answers_json=_dump_result_state(initial_state),
    )
    db.add(result)
    db.flush()

    logger.info(
        "POST /student/start | quiz=%s student=%s attempt=%s",
        quiz_id,
        student_name,
        attempt_number,
    )

    return StudentStartResponse(
        result_id=result.id,
        quiz_id=quiz_id,
        student_name=student_name,
        attempt_number=attempt_number,
        full_time_seconds=quiz.full_time_seconds,
        question_time_seconds=quiz.question_time_seconds,
        max_attempts=quiz.max_attempts or 1,
        questions_count=len(quiz.questions),
        started_at=effective_started_at,
    )


@router.get("/questions")
def student_questions(
    result_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
) -> StudentQuestionsResponse:
    result = db.query(Result).filter(Result.id == result_id).first()
    if result is None:
        raise HTTPException(status_code=404, detail="Сессия ученика не найдена")

    state = _load_result_state(result)
    started_at = state.get("started_at")
    answers_map: dict = state.get("answers", {}) or {}

    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == result.quiz_id, Quiz.deleted_at.is_(None))
        .first()
    )
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")

    quiz_questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz.id)
        .order_by(Question.order_idx)
        .all()
    )
    quiz_questions = _sort_questions(quiz_questions)

    unanswered = [q for q in quiz_questions if q.id not in answers_map]
    answered_questions = [qid for qid in answers_map.keys()]

    next_question = None
    if unanswered:
        q = unanswered[0]
        next_question = {
            "id": q.id,
            "question_text": q.question_text,
            "question_type": q.question_type,
            "options": q.answers or [],
        }

    completed = not unanswered
    return StudentQuestionsResponse(
        result_id=result.id,
        quiz_id=quiz.id,
        student_name=result.student_name,
        attempt_number=result.attempt_number,
        full_time_seconds=quiz.full_time_seconds,
        question_time_seconds=quiz.question_time_seconds,
        max_attempts=quiz.max_attempts or 1,
        questions_count=len(quiz_questions),
        started_at=started_at or result.created_at.isoformat(),
        completed=completed,
        next_question=next_question,
        answered_questions=answered_questions,
    )


@router.post("/answer")
def student_answer(
    result_id: str = Form(..., min_length=1),
    question_id: str = Form(..., min_length=1),
    selected_options: list[str] = Form(...),
    question_started_at: str = Form(...),
    answered_at: str = Form(...),
    db: Session = Depends(get_db),
) -> StudentAnswerResponse:
    result = db.query(Result).filter(Result.id == result_id).first()
    if result is None:
        raise HTTPException(status_code=404, detail="Сессия ученика не найдена")

    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == result.quiz_id, Quiz.deleted_at.is_(None))
        .first()
    )
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")

    state = _load_result_state(result)
    answers_map: dict = state.get("answers", {}) or {}

    quiz_question = (
        db.query(Question)
        .filter(Question.quiz_id == quiz.id, Question.id == question_id)
        .first()
    )
    if quiz_question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    if question_id in answers_map:
        raise HTTPException(status_code=400, detail="Этот вопрос уже отвечен")

    started_dt = _parse_iso_datetime(question_started_at)
    answered_dt = _parse_iso_datetime(answered_at)

    if answered_dt < started_dt:
        raise HTTPException(status_code=400, detail="Некорректные timestamps")

    if quiz.question_time_seconds is not None:
        spent = int((answered_dt - started_dt).total_seconds())
        if spent > quiz.question_time_seconds:
            raise HTTPException(
                status_code=400,
                detail="Превышено время на вопрос",
            )

    overall_started = state.get("started_at")
    if overall_started:
        overall_started_dt = _parse_iso_datetime(overall_started)
        if quiz.full_time_seconds is not None:
            total_spent = int((answered_dt - overall_started_dt).total_seconds())
            if total_spent > quiz.full_time_seconds:
                raise HTTPException(
                    status_code=400,
                    detail="Превышено общее время",
                )

    answers_map[question_id] = {
        "selected_options": selected_options,
        "question_started_at": question_started_at,
        "answered_at": answered_at,
    }
    state["answers"] = answers_map
    result.answers_json = _dump_result_state(state)

    db.add(result)
    db.flush()

    logger.info(
        "POST /student/answer | result=%s question=%s",
        result_id,
        question_id,
    )

    return StudentAnswerResponse(
        result_id=result.id, question_id=question_id, received=True
    )


@router.post("/finish")
def student_finish(
    result_id: str = Form(..., min_length=1),
    finished_at: str = Form(...),
    db: Session = Depends(get_db),
) -> StudentFinishResponse:
    result = db.query(Result).filter(Result.id == result_id).first()
    if result is None:
        raise HTTPException(status_code=404, detail="Сессия ученика не найдена")

    quiz = (
        db.query(Quiz)
        .filter(Quiz.id == result.quiz_id, Quiz.deleted_at.is_(None))
        .first()
    )
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")

    state = _load_result_state(result)
    started_at = state.get("started_at")
    answers_map: dict = state.get("answers", {}) or {}

    finished_dt = _parse_iso_datetime(finished_at)

    if started_at:
        started_dt = _parse_iso_datetime(started_at)
        total_spent = int((finished_dt - started_dt).total_seconds())
    else:
        # Fallback: use DB created_at.
        started_dt = result.created_at
        total_spent = int((finished_dt - started_dt).total_seconds())

    if quiz.full_time_seconds is not None and total_spent > quiz.full_time_seconds:
        raise HTTPException(status_code=400, detail="Превышено общее время на викторину")

    quiz_questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz.id)
        .order_by(Question.order_idx)
        .all()
    )

    if any(q.id not in answers_map for q in quiz_questions):
        raise HTTPException(status_code=400, detail="Не все вопросы отвечены")

    max_score = sum(int(q.points or 1) for q in quiz_questions)
    score = 0

    for q in quiz_questions:
        chosen = answers_map[q.id].get("selected_options", [])
        correct = q.correct_answers or []

        # Order-insensitive comparison for robustness.
        chosen_sorted = sorted(chosen)
        correct_sorted = sorted(correct)

        if chosen_sorted == correct_sorted:
            score += int(q.points or 1)

    percent = int((score * 100) / max_score) if max_score > 0 else 0

    result.score = score
    result.max_score = max_score
    result.duration_seconds = total_spent
    result.answers_json = _dump_result_state(state)

    db.add(result)
    db.flush()

    logger.info(
        "POST /student/finish | result=%s score=%s/%s",
        result_id,
        score,
        max_score,
    )

    return StudentFinishResponse(
        result_id=result.id,
        score=score,
        max_score=max_score,
        percent=percent,
        duration_seconds=total_spent,
    )

