CREATE TABLE csas.quiz_attempts (
    id UUID PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES csas.users(id) ON DELETE RESTRICT,
    quiz_id UUID NOT NULL REFERENCES csas.quizzes(id) ON DELETE RESTRICT,
    selected_option_id UUID NOT NULL,
    correct_option_id UUID NOT NULL,
    is_correct BOOLEAN NOT NULL,
    explanation_snapshot TEXT NOT NULL,
    source_url_snapshot TEXT NOT NULL,
    submitted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    idempotency_key UUID NOT NULL,
    request_hash CHAR(64) NOT NULL,
    retry_of_attempt_id UUID REFERENCES csas.quiz_attempts(id) ON DELETE RESTRICT,
    CONSTRAINT quiz_attempts_user_key UNIQUE (user_id, idempotency_key),
    CONSTRAINT quiz_attempts_selected_option_fk
        FOREIGN KEY (quiz_id, selected_option_id)
        REFERENCES csas.quiz_options(quiz_id, id) ON DELETE RESTRICT,
    CONSTRAINT quiz_attempts_correct_option_fk
        FOREIGN KEY (quiz_id, correct_option_id)
        REFERENCES csas.quiz_options(quiz_id, id) ON DELETE RESTRICT,
    CONSTRAINT quiz_attempts_hash_check CHECK (request_hash ~ '^[0-9a-f]{64}$'),
    CONSTRAINT quiz_attempts_explanation_check CHECK (btrim(explanation_snapshot) <> ''),
    CONSTRAINT quiz_attempts_source_check CHECK (btrim(source_url_snapshot) <> '')
);

CREATE INDEX quiz_attempts_user_submitted_idx
    ON csas.quiz_attempts (user_id, submitted_at DESC, id DESC);
CREATE INDEX quiz_attempts_user_quiz_idx
    ON csas.quiz_attempts (user_id, quiz_id, submitted_at DESC);
