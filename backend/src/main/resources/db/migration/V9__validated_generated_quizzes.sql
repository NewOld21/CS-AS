CREATE TABLE csas.generation_requests (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES csas.users(id),
  chat_session_id uuid REFERENCES csas.chat_sessions(id),
  idempotency_key uuid NOT NULL,
  request_hash varchar(64) NOT NULL,
  concept_ids text NOT NULL,
  difficulty varchar(16) NOT NULL,
  status varchar(16) NOT NULL CHECK (status IN ('GENERATING','VALIDATING','READY','REJECTED','FAILED')),
  outcome varchar(32),
  failure_code varchar(64),
  quiz_id uuid UNIQUE REFERENCES csas.quizzes(id),
  model_version varchar(128),
  prompt_version varchar(128),
  validator_version varchar(128),
  index_version varchar(128),
  corpus_digest varchar(256),
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(user_id,idempotency_key)
);
CREATE TABLE csas.generation_validations (
  generation_id uuid PRIMARY KEY REFERENCES csas.generation_requests(id),
  report text NOT NULL,
  reason_codes text NOT NULL,
  passed boolean NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE csas.quiz_evidence (
  quiz_id uuid NOT NULL REFERENCES csas.quizzes(id),
  ordinal smallint NOT NULL,
  source_id varchar(128) NOT NULL,
  document_id varchar(256) NOT NULL,
  revision varchar(256) NOT NULL,
  chunk_id varchar(256) NOT NULL,
  index_version varchar(128) NOT NULL,
  title text NOT NULL,
  url text NOT NULL,
  locator text NOT NULL,
  evidence_text text NOT NULL,
  category varchar(128),
  technology_version varchar(128),
  PRIMARY KEY(quiz_id,ordinal),
  UNIQUE(quiz_id,chunk_id)
);
CREATE FUNCTION csas.validate_generated_quiz_trigger() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF NEW.origin='AI_GENERATED' AND NEW.status='READY' AND NOT EXISTS (
    SELECT 1 FROM csas.generation_requests g
      JOIN csas.generation_validations v ON v.generation_id=g.id
     WHERE g.quiz_id=NEW.id AND g.user_id=NEW.owner_user_id AND g.status='READY' AND v.passed
  ) THEN
    RAISE EXCEPTION 'Generated READY quiz requires validated generation' USING ERRCODE='23514';
  END IF;
  RETURN NULL;
END;
$$;
CREATE CONSTRAINT TRIGGER generated_quiz_validation_required
AFTER INSERT OR UPDATE ON csas.quizzes DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION csas.validate_generated_quiz_trigger();
