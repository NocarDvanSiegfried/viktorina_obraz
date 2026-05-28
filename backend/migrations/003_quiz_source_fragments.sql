-- Day 21: persisted source fragment catalog (id, preview, source_type) per quiz
ALTER TABLE quizzes ADD COLUMN source_fragments_json TEXT;
