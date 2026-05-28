"""Lightweight schema upgrades for SQLite (no Alembic)."""

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def apply_migrations(engine: Engine) -> None:
    inspector = inspect(engine)
    if not inspector.has_table("quizzes"):
        return

    columns = {column["name"] for column in inspector.get_columns("quizzes")}
    if "updated_at" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE quizzes ADD COLUMN updated_at DATETIME")
            )
            connection.execute(
                text(
                    "UPDATE quizzes SET updated_at = created_at "
                    "WHERE updated_at IS NULL"
                )
            )

    if not inspector.has_table("quiz_versions"):
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE TABLE quiz_versions (
                        id VARCHAR NOT NULL PRIMARY KEY,
                        quiz_id VARCHAR NOT NULL
                            REFERENCES quizzes(id) ON DELETE CASCADE,
                        version_number INTEGER NOT NULL,
                        snapshot_json TEXT NOT NULL,
                        label VARCHAR NOT NULL,
                        created_by VARCHAR NOT NULL,
                        created_at DATETIME,
                        UNIQUE (quiz_id, version_number)
                    )
                    """
                )
            )
            connection.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_quiz_versions_quiz_id "
                    "ON quiz_versions (quiz_id)"
                )
            )

    columns = {column["name"] for column in inspector.get_columns("quizzes")}
    if "source_fragments_json" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE quizzes ADD COLUMN source_fragments_json TEXT")
            )

    columns = {column["name"] for column in inspector.get_columns("quizzes")}
    if "deleted_at" not in columns:
        with engine.begin() as connection:
            connection.execute(text("ALTER TABLE quizzes ADD COLUMN deleted_at DATETIME"))
