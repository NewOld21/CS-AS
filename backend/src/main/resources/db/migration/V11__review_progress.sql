ALTER TABLE csas.quiz_attempts
  ADD CONSTRAINT quiz_attempts_owner_quiz_id_key UNIQUE(user_id,quiz_id,id);

CREATE TABLE csas.review_states (
  user_id uuid NOT NULL REFERENCES csas.users(id),
  quiz_id uuid NOT NULL REFERENCES csas.quizzes(id),
  status varchar(16) NOT NULL CHECK (status IN ('NEEDS_REVIEW','RESOLVED')),
  latest_attempt_id uuid NOT NULL,
  first_wrong_at timestamptz NOT NULL,
  last_wrong_at timestamptz NOT NULL,
  last_reviewed_at timestamptz,
  PRIMARY KEY(user_id,quiz_id),
  FOREIGN KEY(user_id,quiz_id,latest_attempt_id) REFERENCES csas.quiz_attempts(user_id,quiz_id,id)
);
CREATE INDEX review_states_user_wrong_idx ON csas.review_states(user_id,last_wrong_at DESC,quiz_id DESC);

INSERT INTO csas.review_states(user_id,quiz_id,status,latest_attempt_id,first_wrong_at,last_wrong_at,last_reviewed_at)
SELECT wrong.user_id,wrong.quiz_id,CASE WHEN latest.is_correct THEN 'RESOLVED' ELSE 'NEEDS_REVIEW' END,
  latest.id,wrong.first_wrong_at,wrong.last_wrong_at,
  CASE WHEN latest.submitted_at>wrong.first_wrong_at THEN latest.submitted_at ELSE NULL END
FROM (SELECT user_id,quiz_id,min(submitted_at) first_wrong_at,max(submitted_at) last_wrong_at
  FROM csas.quiz_attempts WHERE NOT is_correct GROUP BY user_id,quiz_id) wrong
JOIN LATERAL (SELECT id,is_correct,submitted_at FROM csas.quiz_attempts a
  WHERE a.user_id=wrong.user_id AND a.quiz_id=wrong.quiz_id ORDER BY submitted_at DESC,id DESC LIMIT 1) latest ON true;
