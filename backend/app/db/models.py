import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    event,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import relationship

from app.db.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    return str(uuid.uuid4())


@event.listens_for(Engine, "connect")
def _fk_pragma_on_connect(dbapi_connection, _) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


class Quiz(Base):
    __tablename__ = "quizzes"

    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, nullable=False, index=True)

    title = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    grade = Column(String, nullable=True)
    difficulty = Column(String, nullable=True)
    full_time_seconds = Column(Integer, nullable=True)
    question_time_seconds = Column(Integer, nullable=True)
    max_attempts = Column(Integer, default=1)
    status = Column(String, default="draft")
    source_fragments_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    deleted_at = Column(DateTime, nullable=True)

    questions = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    results = relationship(
        "Result",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    material_uploads = relationship(
        "MaterialUpload",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    versions = relationship(
        "QuizVersion",
        back_populates="quiz",
        cascade="all, delete-orphan",
        order_by="QuizVersion.version_number.desc()",
    )


class QuizVersion(Base):
    __tablename__ = "quiz_versions"

    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(
        String,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_number = Column(Integer, nullable=False)
    snapshot_json = Column(Text, nullable=False)
    label = Column(String, nullable=False)
    created_by = Column(String, nullable=False)
    created_at = Column(DateTime, default=utcnow)

    quiz = relationship("Quiz", back_populates="versions")


class Question(Base):
    __tablename__ = "questions"

    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(
        String,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )

    question_text = Column(Text, nullable=False)
    question_type = Column(String, nullable=False)
    answers = Column(JSON, nullable=True)
    correct_answers = Column(JSON, nullable=True)
    explanation = Column(Text, nullable=True)
    source_fragment = Column(Text, nullable=True)
    points = Column(Integer, default=1)
    order_idx = Column(Integer, default=0)

    quiz = relationship("Quiz", back_populates="questions")


class Result(Base):
    __tablename__ = "results"

    id = Column(String, primary_key=True, default=generate_uuid)
    quiz_id = Column(
        String,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=False,
    )

    student_name = Column(String, nullable=False)
    score = Column(Integer, default=0)
    max_score = Column(Integer, nullable=True)
    attempt_number = Column(Integer, default=1)
    duration_seconds = Column(Integer, nullable=True)
    answers_json = Column(Text, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    quiz = relationship("Quiz", back_populates="results")


class MaterialUpload(Base):
    """Metadata for uploaded sources (file bytes are not stored publicly)."""

    __tablename__ = "material_uploads"

    id = Column(String, primary_key=True, default=generate_uuid)
    owner_id = Column(String, nullable=False, index=True)
    quiz_id = Column(
        String,
        ForeignKey("quizzes.id", ondelete="CASCADE"),
        nullable=True,
    )

    source_type = Column(String, nullable=False)
    original_filename = Column(String, nullable=True)
    mime_type = Column(String, nullable=True)
    size_bytes = Column(Integer, nullable=True)
    uploaded_at = Column(DateTime, default=utcnow)

    quiz = relationship("Quiz", back_populates="material_uploads")
