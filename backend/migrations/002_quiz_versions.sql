-- Day 16: full quiz version history (snapshot + restore).

CREATE TABLE IF NOT EXISTS quiz_versions (
    id VARCHAR NOT NULL PRIMARY KEY,
    quiz_id VARCHAR NOT NULL REFERENCES quizzes(id) ON DELETE CASCADE,
    version_number INTEGER NOT NULL,
    snapshot_json TEXT NOT NULL,
    label VARCHAR NOT NULL,
    created_by VARCHAR NOT NULL,
    created_at DATETIME,
    UNIQUE (quiz_id, version_number)
);

CREATE INDEX IF NOT EXISTS ix_quiz_versions_quiz_id ON quiz_versions (quiz_id);
