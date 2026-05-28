"""Day 1: health, DB bootstrap, quiz list by owner_id."""

import os

from sqlalchemy import inspect

from app.db.database import Base, engine


def test_health_returns_ok(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "service" in data


def test_root_returns_ok(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_database_tables_created():
    inspector = inspect(engine)
    tables = set(inspector.get_table_names())
    assert tables >= {"quizzes", "questions", "results", "material_uploads"}


def test_quiz_list_requires_owner_id(client):
    response = client.get("/quiz/list")
    assert response.status_code == 422


def test_quiz_list_empty_for_new_owner(client):
    response = client.get("/quiz/list", params={"owner_id": "owner-day1-test"})
    assert response.status_code == 200
    assert response.json() == {"quizzes": []}


def test_quiz_list_returns_only_owner_quizzes(client, db_session):
    from app.db.models import Quiz

    owner_a = "owner-a-day1"
    owner_b = "owner-b-day1"

    db_session.add(
        Quiz(
            owner_id=owner_a,
            title="Викторина A",
            subject="Биология",
            grade="8",
        )
    )
    db_session.add(
        Quiz(
            owner_id=owner_b,
            title="Викторина B",
            subject="История",
            grade="9",
        )
    )
    db_session.commit()

    response = client.get("/quiz/list", params={"owner_id": owner_a})
    assert response.status_code == 200
    quizzes = response.json()["quizzes"]
    assert len(quizzes) == 1
    assert quizzes[0]["title"] == "Викторина A"
    assert quizzes[0]["subject"] == "Биология"
    assert quizzes[0]["questions_count"] == 0


def test_material_upload_model_fields(db_session):
    from app.db.models import MaterialUpload, Quiz

    quiz = Quiz(owner_id="owner-meta", title="Тест мета")
    db_session.add(quiz)
    db_session.flush()

    upload = MaterialUpload(
        owner_id="owner-meta",
        quiz_id=quiz.id,
        source_type="manual_text",
        original_filename=None,
        mime_type="text/plain",
        size_bytes=128,
    )
    db_session.add(upload)
    db_session.commit()

    saved = db_session.get(MaterialUpload, upload.id)
    assert saved is not None
    assert saved.quiz_id == quiz.id
    assert saved.source_type == "manual_text"
