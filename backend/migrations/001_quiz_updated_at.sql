-- Day 15: simplified version history via updated_at on quizzes.
ALTER TABLE quizzes ADD COLUMN updated_at DATETIME;
UPDATE quizzes SET updated_at = created_at WHERE updated_at IS NULL;
