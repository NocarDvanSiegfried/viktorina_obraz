from enum import Enum
import json
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.core.logger import logger
from app.core.rate_limiter import rate_limiter
from app.db.database import get_db
from app.db.models import MaterialUpload, Question, Quiz, utcnow
from app.schemas.material import SourceFragment
from app.schemas.quiz import DifficultyLevel, GenerateQuizResponse
from app.services.material_service import (
    EMPTY_IMAGE_MESSAGE,
    EMPTY_PDF_MESSAGE,
    material_service,
)
from app.services.docx_export_service import docx_export_service
from app.services.pdf_export_service import pdf_export_service
from app.services.pptx_export_service import pptx_export_service
from app.services.question_service import (
    MAX_QUESTIONS_PER_QUIZ,
    QuestionValidationError,
    normalize_answers,
    validate_question_payload,
)
from app.api.quiz_generation_errors import raise_quiz_ai_http_error
from app.services.quiz_service import quiz_service
from app.services import fragment_catalog_service, quiz_version_service
from app.services.quiz_version_service import QuizVersionNotFoundError
from app.db.models import QuizVersion

router = APIRouter(prefix="/quiz", tags=["Quiz"])

PLACEHOLDER_TEXTS = {"string", "source_text", "null", "none"}


class QuestionType(str, Enum):
    single_choice = "single_choice"
    multiple_choice = "multiple_choice"
    true_false = "true_false"


def _normalize_source_text(value: str | None) -> str:
    text = (value or "").strip()
    if text.lower() in PLACEHOLDER_TEXTS:
        return ""
    return text


def _load_result_state(answers_json: str | None) -> dict:
    if not answers_json:
        return {"started_at": None, "answers": {}}
    try:
        return json.loads(answers_json)
    except Exception:
        return {"started_at": None, "answers": {}}


def _record_material_uploads(
    db: Session,
    owner_id: str,
    quiz_id: str,
    fragments: list[SourceFragment],
    file_source_type: str | None,
    uploaded_filename: str | None,
    uploaded_mime: str | None,
    uploaded_size: int | None,
) -> None:
    manual_fragment = next((f for f in fragments if f.source_type == "manual_text"), None)

    if manual_fragment:
        db.add(
            MaterialUpload(
                owner_id=owner_id,
                quiz_id=quiz_id,
                source_type="manual_text",
                original_filename=None,
                mime_type="text/plain",
                size_bytes=len(manual_fragment.text.encode("utf-8")),
            )
        )

    if file_source_type == "txt":
        db.add(
            MaterialUpload(
                owner_id=owner_id,
                quiz_id=quiz_id,
                source_type="txt",
                original_filename=uploaded_filename,
                mime_type=uploaded_mime or "text/plain",
                size_bytes=uploaded_size,
            )
        )

    if file_source_type == "pdf":
        db.add(
            MaterialUpload(
                owner_id=owner_id,
                quiz_id=quiz_id,
                source_type="pdf",
                original_filename=uploaded_filename,
                mime_type=uploaded_mime or "application/pdf",
                size_bytes=uploaded_size,
            )
        )

    if file_source_type == "docx":
        db.add(
            MaterialUpload(
                owner_id=owner_id,
                quiz_id=quiz_id,
                source_type="docx",
                original_filename=uploaded_filename,
                mime_type=uploaded_mime
                or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                size_bytes=uploaded_size,
            )
        )

    if file_source_type == "pptx":
        db.add(
            MaterialUpload(
                owner_id=owner_id,
                quiz_id=quiz_id,
                source_type="pptx",
                original_filename=uploaded_filename,
                mime_type=uploaded_mime
                or "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                size_bytes=uploaded_size,
            )
        )

    if file_source_type == "image":
        db.add(
            MaterialUpload(
                owner_id=owner_id,
                quiz_id=quiz_id,
                source_type="image",
                original_filename=uploaded_filename,
                mime_type=uploaded_mime or "image/png",
                size_bytes=uploaded_size,
            )
        )


def _touch_quiz(quiz: Quiz) -> None:
    quiz.updated_at = utcnow()


def _record_version(db: Session, quiz: Quiz, owner_id: str, label: str) -> None:
    questions = _load_ordered_questions(db, quiz.id)
    quiz_version_service.save_version(
        db,
        quiz,
        questions,
        label=label,
        created_by=owner_id,
    )


def _serialize_version_summary(version: QuizVersion) -> dict:
    snapshot = quiz_version_service.parse_snapshot(version)
    return {
        "id": version.id,
        "version_number": version.version_number,
        "label": version.label,
        "created_at": _iso_datetime(version.created_at),
        "created_by": version.created_by,
        "question_count": len(snapshot.get("questions", [])),
        "quiz_title": (snapshot.get("quiz") or {}).get("title"),
    }


def _iso_datetime(value) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def _get_owned_quiz(
    db: Session,
    quiz_id: str,
    owner_id: str,
    *,
    include_deleted: bool = False,
) -> Quiz:
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id).first()
    if quiz is None or (not include_deleted and quiz.deleted_at is not None):
        raise HTTPException(status_code=404, detail="Викторина не найдена")
    if quiz.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Доступ к викторине запрещён")
    return quiz


def _load_ordered_questions(db: Session, quiz_id: str) -> list[Question]:
    return (
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order_idx)
        .all()
    )


def _serialize_question(question: Question) -> dict:
    return {
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


def _serialize_quiz_detail(quiz: Quiz, questions: list[Question]) -> dict:
    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "subject": quiz.subject,
        "grade": quiz.grade,
        "topic": "",
        "difficulty": quiz.difficulty,
        "status": quiz.status,
        "full_time_seconds": quiz.full_time_seconds,
        "question_time_seconds": quiz.question_time_seconds,
        "max_attempts": quiz.max_attempts,
        "created_at": _iso_datetime(quiz.created_at),
        "updated_at": _iso_datetime(quiz.updated_at),
        "fragments": fragment_catalog_service.resolve_catalog(quiz, questions),
        "questions": [_serialize_question(question) for question in questions],
    }


def _renumber_questions(questions: list[Question]) -> None:
    for idx, question in enumerate(questions):
        question.order_idx = idx


def _save_quiz_to_db(
    db: Session,
    owner_id: str,
    subject: str,
    grade: str,
    difficulty: str,
    result: GenerateQuizResponse,
    fragments: list[SourceFragment],
    file_source_type: str | None = None,
    uploaded_filename: str | None = None,
    uploaded_mime: str | None = None,
    uploaded_size: int | None = None,
) -> Quiz:
    quiz = Quiz(
        owner_id=owner_id,
        title=result.quiz_title,
        subject=subject,
        grade=grade,
        difficulty=difficulty,
        status="draft",
    )
    db.add(quiz)
    db.flush()

    quiz.source_fragments_json = fragment_catalog_service.catalog_to_json(
        fragment_catalog_service.build_catalog(fragments)
    )

    _record_material_uploads(
        db,
        owner_id,
        quiz.id,
        fragments,
        file_source_type,
        uploaded_filename,
        uploaded_mime,
        uploaded_size,
    )

    for idx, question in enumerate(result.questions):
        default_fragment = fragments[0].fragment_id if fragments else "manual_1"
        db.add(
            Question(
                quiz_id=quiz.id,
                question_text=question.text,
                question_type=question.type,
                answers=question.options,
                correct_answers=question.correct_answers,
                explanation=question.explanation,
                source_fragment=question.source_fragment_id or default_fragment,
                points=1,
                order_idx=idx,
            )
        )

    db.flush()
    _record_version(db, quiz, owner_id, "Создание викторины")
    return quiz


@router.get("/list")
def list_quizzes(
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    quizzes = (
        db.query(Quiz)
        .filter(Quiz.owner_id == owner_id, Quiz.deleted_at.is_(None))
        .order_by(Quiz.created_at.desc())
        .all()
    )

    return {
        "quizzes": [
            {
                "id": quiz.id,
                "title": quiz.title,
                "subject": quiz.subject,
                "grade": quiz.grade,
                "difficulty": quiz.difficulty,
                "status": quiz.status,
                "questions_count": len(quiz.questions),
                "created_at": _iso_datetime(quiz.created_at),
                "updated_at": _iso_datetime(quiz.updated_at),
            }
            for quiz in quizzes
        ]
    }


@router.get("/{quiz_id}")
def get_quiz(
    quiz_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)
    questions = _load_ordered_questions(db, quiz_id)
    return _serialize_quiz_detail(quiz, questions)


@router.get("/{quiz_id}/results")
def get_quiz_results(
    quiz_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    from app.db.models import Result

    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.deleted_at.is_(None)).first()
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")
    if quiz.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Доступ к викторине запрещён")

    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order_idx)
        .all()
    )
    question_map = {q.id: q for q in questions}

    attempts = (
        db.query(Result)
        .filter(Result.quiz_id == quiz_id)
        .order_by(Result.created_at.desc())
        .all()
    )

    payload_results = []
    for attempt in attempts:
        max_score = int(attempt.max_score or 0)
        score = int(attempt.score or 0)
        percent = int((score * 100) / max_score) if max_score > 0 else 0

        state = _load_result_state(attempt.answers_json)
        answers_map = state.get("answers", {}) or {}

        wrong_questions = []
        for qid, answer_data in answers_map.items():
            q = question_map.get(qid)
            if not q:
                continue
            chosen = answer_data.get("selected_options", []) or []
            correct = q.correct_answers or []
            if sorted(chosen) != sorted(correct):
                wrong_questions.append(
                    {
                        "question_id": q.id,
                        "question_text": q.question_text,
                        "selected_options": chosen,
                        "correct_answers": correct,
                    }
                )

        payload_results.append(
            {
                "result_id": attempt.id,
                "student_name": attempt.student_name,
                "attempt_number": attempt.attempt_number,
                "score": score,
                "max_score": max_score,
                "percent": percent,
                "duration_seconds": attempt.duration_seconds,
                "created_at": attempt.created_at.isoformat() if attempt.created_at else None,
                "wrong_questions": wrong_questions,
            }
        )

    return {
        "quiz_id": quiz.id,
        "title": quiz.title,
        "results": payload_results,
    }


@router.put("/{quiz_id}")
def update_quiz_settings(
    quiz_id: str,
    owner_id: str = Form(..., min_length=1),
    title: str = Form(...),
    difficulty: DifficultyLevel = Form(...),
    full_time_seconds: int = Form(..., ge=0),
    question_time_seconds: int = Form(..., ge=0),
    max_attempts: int = Form(..., ge=1),
    status: str = Form(...),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)

    quiz.title = title
    quiz.difficulty = difficulty.value
    quiz.full_time_seconds = full_time_seconds
    quiz.question_time_seconds = question_time_seconds
    quiz.max_attempts = max_attempts
    quiz.status = status
    _touch_quiz(quiz)

    questions = _load_ordered_questions(db, quiz_id)
    _record_version(db, quiz, owner_id, "Изменение настроек")
    return _serialize_quiz_detail(quiz, questions)


@router.post("/{quiz_id}/questions")
def create_question(
    quiz_id: str,
    owner_id: str = Form(..., min_length=1),
    question_text: str = Form(..., min_length=1),
    question_type: QuestionType = Form(...),
    answers: list[str] = Form(...),
    correct_answers: list[str] = Form(...),
    explanation: str | None = Form(None),
    source_fragment: str | None = Form(None),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)
    existing = _load_ordered_questions(db, quiz_id)
    if len(existing) >= MAX_QUESTIONS_PER_QUIZ:
        raise HTTPException(
            status_code=400,
            detail=f"Максимум {MAX_QUESTIONS_PER_QUIZ} вопросов в викторине",
        )

    cleaned_answers = normalize_answers(answers)
    cleaned_correct = normalize_answers(correct_answers)
    try:
        validate_question_payload(
            question_type.value,
            cleaned_answers,
            cleaned_correct,
        )
    except QuestionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    question = Question(
        quiz_id=quiz.id,
        question_text=question_text.strip(),
        question_type=question_type.value,
        answers=cleaned_answers,
        correct_answers=cleaned_correct,
        explanation=(explanation or "").strip() or None,
        source_fragment=(source_fragment or "").strip() or None,
        points=1,
        order_idx=len(existing),
    )
    db.add(question)
    db.flush()
    _touch_quiz(quiz)

    questions = _load_ordered_questions(db, quiz_id)
    _record_version(db, quiz, owner_id, "Добавление вопроса")
    return _serialize_quiz_detail(quiz, questions)


@router.put("/{quiz_id}/questions/{question_id}")
def update_question(
    quiz_id: str,
    question_id: str,
    owner_id: str = Form(..., min_length=1),
    question_text: str = Form(..., min_length=1),
    question_type: QuestionType = Form(...),
    answers: list[str] = Form(...),
    correct_answers: list[str] = Form(...),
    explanation: str | None = Form(None),
    source_fragment: str | None = Form(None),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)
    question = (
        db.query(Question)
        .filter(Question.id == question_id, Question.quiz_id == quiz_id)
        .first()
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    cleaned_answers = normalize_answers(answers)
    cleaned_correct = normalize_answers(correct_answers)
    try:
        validate_question_payload(
            question_type.value,
            cleaned_answers,
            cleaned_correct,
        )
    except QuestionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    question.question_text = question_text.strip()
    question.question_type = question_type.value
    question.answers = cleaned_answers
    question.correct_answers = cleaned_correct
    question.explanation = (explanation or "").strip() or None
    question.source_fragment = (source_fragment or "").strip() or None
    _touch_quiz(quiz)

    questions = _load_ordered_questions(db, quiz_id)
    _record_version(db, quiz, owner_id, "Изменение вопроса")
    return _serialize_quiz_detail(quiz, questions)


@router.delete("/{quiz_id}/questions/{question_id}")
def delete_question(
    quiz_id: str,
    question_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)
    questions = _load_ordered_questions(db, quiz_id)
    if len(questions) <= 1:
        raise HTTPException(
            status_code=400,
            detail="Нельзя удалить последний вопрос викторины",
        )

    question = next((q for q in questions if q.id == question_id), None)
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    db.delete(question)
    db.flush()

    remaining = _load_ordered_questions(db, quiz_id)
    _renumber_questions(remaining)
    db.flush()
    _touch_quiz(quiz)

    _record_version(db, quiz, owner_id, "Удаление вопроса")
    return _serialize_quiz_detail(quiz, remaining)


class ReorderDirection(str, Enum):
    up = "up"
    down = "down"


@router.post("/{quiz_id}/questions/{question_id}/reorder")
def reorder_question(
    quiz_id: str,
    question_id: str,
    owner_id: str = Form(..., min_length=1),
    direction: ReorderDirection = Form(...),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)
    questions = _load_ordered_questions(db, quiz_id)
    index = next((i for i, q in enumerate(questions) if q.id == question_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    if direction == ReorderDirection.up and index > 0:
        questions[index - 1], questions[index] = questions[index], questions[index - 1]
    elif direction == ReorderDirection.down and index < len(questions) - 1:
        questions[index + 1], questions[index] = questions[index], questions[index + 1]

    _renumber_questions(questions)
    db.flush()
    _touch_quiz(quiz)

    _record_version(db, quiz, owner_id, "Изменение порядка вопросов")
    return _serialize_quiz_detail(quiz, questions)


@router.post("/{quiz_id}/questions/{question_id}/regenerate")
def regenerate_question(
    quiz_id: str,
    question_id: str,
    owner_id: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)
    question = (
        db.query(Question)
        .filter(Question.id == question_id, Question.quiz_id == quiz_id)
        .first()
    )
    if question is None:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    try:
        regenerated = quiz_service.regenerate_question(
            subject=quiz.subject or "",
            grade=quiz.grade or "",
            topic=quiz.title or "",
            difficulty=quiz.difficulty or "easy",
            question_type=question.question_type,
            current_question_text=question.question_text,
            source_fragment_id=question.source_fragment,
        )
    except Exception as exc:
        raise_quiz_ai_http_error(exc, action_label="пересоздать вопрос")

    new_type = regenerated.get("type", question.question_type)
    cleaned_answers = normalize_answers(regenerated.get("options", []))
    cleaned_correct = normalize_answers(regenerated.get("correct_answers", []))
    try:
        validate_question_payload(new_type, cleaned_answers, cleaned_correct)
    except QuestionValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    question.question_text = regenerated.get("text", question.question_text)
    question.question_type = new_type
    question.answers = cleaned_answers
    question.correct_answers = cleaned_correct
    question.explanation = regenerated.get("explanation", question.explanation)
    if regenerated.get("source_fragment_id"):
        question.source_fragment = regenerated["source_fragment_id"]

    _touch_quiz(quiz)
    db.flush()

    questions = _load_ordered_questions(db, quiz_id)
    _record_version(db, quiz, owner_id, "Пересоздание вопроса (ИИ)")
    return _serialize_quiz_detail(quiz, questions)


@router.get("/{quiz_id}/versions")
def list_quiz_versions(
    quiz_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    _get_owned_quiz(db, quiz_id, owner_id)
    versions = quiz_version_service.list_versions(db, quiz_id)
    return {
        "quiz_id": quiz_id,
        "versions": [_serialize_version_summary(version) for version in versions],
    }


@router.get("/{quiz_id}/versions/{version_id}")
def get_quiz_version(
    quiz_id: str,
    version_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    _get_owned_quiz(db, quiz_id, owner_id)
    try:
        version = quiz_version_service.get_version(db, quiz_id, version_id)
    except QuizVersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    snapshot = quiz_version_service.parse_snapshot(version)
    return {
        "id": version.id,
        "quiz_id": quiz_id,
        "version_number": version.version_number,
        "label": version.label,
        "created_at": _iso_datetime(version.created_at),
        "created_by": version.created_by,
        "snapshot": snapshot,
    }


@router.delete("/{quiz_id}")
def soft_delete_quiz(
    quiz_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id, include_deleted=True)
    if quiz.deleted_at is None:
        quiz.deleted_at = utcnow()
        _touch_quiz(quiz)
        db.flush()

    return {"quiz_id": quiz.id, "deleted": True}


@router.post("/{quiz_id}/duplicate")
def duplicate_quiz(
    quiz_id: str,
    owner_id: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    source_quiz = _get_owned_quiz(db, quiz_id, owner_id)
    source_questions = _load_ordered_questions(db, source_quiz.id)

    duplicate = Quiz(
        owner_id=source_quiz.owner_id,
        title=f"{source_quiz.title} (копия)",
        subject=source_quiz.subject,
        grade=source_quiz.grade,
        difficulty=source_quiz.difficulty,
        full_time_seconds=source_quiz.full_time_seconds,
        question_time_seconds=source_quiz.question_time_seconds,
        max_attempts=source_quiz.max_attempts,
        status="draft",
        source_fragments_json=source_quiz.source_fragments_json,
    )
    db.add(duplicate)
    db.flush()

    for idx, source_question in enumerate(source_questions):
        db.add(
            Question(
                quiz_id=duplicate.id,
                question_text=source_question.question_text,
                question_type=source_question.question_type,
                answers=source_question.answers,
                correct_answers=source_question.correct_answers,
                explanation=source_question.explanation,
                source_fragment=source_question.source_fragment,
                points=source_question.points,
                order_idx=idx,
            )
        )
    db.flush()

    duplicate_questions = _load_ordered_questions(db, duplicate.id)
    _record_version(db, duplicate, owner_id, "Создание копии")
    return _serialize_quiz_detail(duplicate, duplicate_questions)


@router.post("/{quiz_id}/versions/{version_id}/restore")
def restore_quiz_version(
    quiz_id: str,
    version_id: str,
    owner_id: str = Form(..., min_length=1),
    db: Session = Depends(get_db),
):
    quiz = _get_owned_quiz(db, quiz_id, owner_id)
    try:
        version = quiz_version_service.get_version(db, quiz_id, version_id)
    except QuizVersionNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    questions = quiz_version_service.restore_version(db, quiz, version)
    _record_version(
        db,
        quiz,
        owner_id,
        f"Восстановление из версии {version.version_number}",
    )
    return _serialize_quiz_detail(quiz, questions)


@router.get("/{quiz_id}/export-pdf")
def export_quiz_pdf(
    quiz_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.deleted_at.is_(None)).first()
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")
    if quiz.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Доступ к викторине запрещён")

    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order_idx)
        .all()
    )

    pdf_bytes = pdf_export_service.build_quiz_pdf(quiz, questions)
    safe_name = quote((quiz.title or f"quiz-{quiz.id}")[:100])
    headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}.pdf"}
    return Response(content=pdf_bytes, media_type="application/pdf", headers=headers)


@router.get("/{quiz_id}/export-docx")
def export_quiz_docx(
    quiz_id: str,
    owner_id: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.deleted_at.is_(None)).first()
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")
    if quiz.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Доступ к викторине запрещён")

    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order_idx)
        .all()
    )

    docx_bytes = docx_export_service.build_quiz_docx(quiz, questions)
    safe_name = quote((quiz.title or f"quiz-{quiz.id}")[:100])
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}.docx"
    }
    return Response(
        content=docx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers=headers,
    )


@router.get("/{quiz_id}/export-pptx")
def export_quiz_pptx(
    quiz_id: str,
    owner_id: str = Query(..., min_length=1),
    include_answers: bool = Query(True),
    db: Session = Depends(get_db),
):
    quiz = db.query(Quiz).filter(Quiz.id == quiz_id, Quiz.deleted_at.is_(None)).first()
    if quiz is None:
        raise HTTPException(status_code=404, detail="Викторина не найдена")
    if quiz.owner_id != owner_id:
        raise HTTPException(status_code=403, detail="Доступ к викторине запрещён")

    questions = (
        db.query(Question)
        .filter(Question.quiz_id == quiz_id)
        .order_by(Question.order_idx)
        .all()
    )

    pptx_bytes = pptx_export_service.build_quiz_pptx(
        quiz,
        questions,
        include_answers=include_answers,
    )
    safe_name = quote((quiz.title or f"quiz-{quiz.id}")[:100])
    headers = {
        "Content-Disposition": f"attachment; filename*=UTF-8''{safe_name}.pptx"
    }
    return Response(
        content=pptx_bytes,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers=headers,
    )


@router.post("/generate-from-materials")
async def generate_quiz_from_materials(
    owner_id: str = Form(..., min_length=1),
    subject: str = Form(...),
    grade: str = Form(...),
    topic: str = Form(...),
    question_count: int = Form(..., ge=1, le=15),
    question_types: list[QuestionType] = Form(...),
    difficulty: DifficultyLevel = Form(...),
    source_text: str | None = Form(None),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
):
    """Generate quiz from manual text, .txt/.pdf/.docx/.pptx file."""
    cleaned_source_text = _normalize_source_text(source_text)
    file_fragments: list[SourceFragment] = []
    file_source_type: str | None = None
    uploaded_filename: str | None = None
    uploaded_mime: str | None = None
    uploaded_size: int | None = None

    if file is not None and file.filename:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Загруженный файл пуст.")

        try:
            file_source_type, file_fragments = material_service.extract_fragments(
                file.filename,
                file_content,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if not file_fragments:
            if file_source_type == "pdf":
                raise HTTPException(status_code=400, detail=EMPTY_PDF_MESSAGE)
            if file_source_type == "image":
                raise HTTPException(status_code=400, detail=EMPTY_IMAGE_MESSAGE)
            if file_source_type == "docx":
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось извлечь текст из DOCX. Вставьте текст вручную или загрузите TXT.",
                )
            if file_source_type == "pptx":
                raise HTTPException(
                    status_code=400,
                    detail="Не удалось извлечь текст из PPTX. Вставьте текст вручную или загрузите TXT.",
                )
            raise HTTPException(
                status_code=400,
                detail="Не удалось извлечь текст из TXT-файла.",
            )

        uploaded_filename = file.filename
        uploaded_mime = file.content_type
        uploaded_size = len(file_content)

    fragments = material_service.merge_fragments(cleaned_source_text, file_fragments)

    if not fragments:
        raise HTTPException(
            status_code=400,
            detail=(
                "Укажите текст (source_text) или загрузите "
                ".txt / .pdf / .docx / .pptx / изображение (.png, .jpg, .webp)."
            ),
        )

    parsed_question_types = [item.value for item in question_types]

    allowed, retry_after_seconds = rate_limiter.allow(owner_id)
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail=f"Слишком много запросов: лимит исчерпан. Попробуйте позже (через {retry_after_seconds} сек.)",
        )

    logger.info(
        "POST /quiz/generate-from-materials | owner=%s subject=%s topic=%s sources=%s",
        owner_id,
        subject,
        topic,
        [f.source_type for f in fragments],
    )

    try:
        result = quiz_service.generate_quiz_from_fragments(
            subject=subject,
            grade=grade,
            topic=topic,
            question_count=question_count,
            question_types=parsed_question_types,
            difficulty=difficulty.value,
            fragments=fragments,
        )
    except Exception as exc:
        raise_quiz_ai_http_error(exc, action_label="сгенерировать викторину")

    quiz = _save_quiz_to_db(
        db,
        owner_id,
        subject,
        grade,
        difficulty.value,
        result,
        fragments,
        file_source_type,
        uploaded_filename,
        uploaded_mime,
        uploaded_size,
    )

    return {
        "quiz_id": quiz.id,
        "title": result.quiz_title,
        "subject": result.subject,
        "grade": result.grade,
        "topic": result.topic,
        "difficulty": difficulty.value,
        "questions": [
            {
                "type": q.type,
                "text": q.text,
                "options": q.options,
                "correct_answers": q.correct_answers,
                "explanation": q.explanation,
                "source_fragment_id": q.source_fragment_id,
            }
            for q in result.questions
        ],
    }
