-- Provenance and option explanations for sourced public quizzes. No answer fields
-- are added to the pre-submission catalog response.
ALTER TABLE csas.quizzes ADD COLUMN source_metadata JSONB;
