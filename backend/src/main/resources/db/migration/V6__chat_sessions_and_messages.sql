CREATE TABLE csas.chat_sessions (
  id uuid PRIMARY KEY,
  user_id uuid NOT NULL REFERENCES csas.users(id),
  context_attempt_id uuid REFERENCES csas.quiz_attempts(id),
  created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX chat_sessions_user_created_idx
  ON csas.chat_sessions(user_id, created_at DESC, id DESC);

CREATE TABLE csas.chat_messages (
  id uuid PRIMARY KEY,
  session_id uuid NOT NULL REFERENCES csas.chat_sessions(id),
  role varchar(16) NOT NULL CHECK (role IN ('USER', 'ASSISTANT')),
  content text,
  status varchar(32) CHECK (status IN ('answered', 'insufficient_evidence')),
  concept_ids text NOT NULL DEFAULT '[]',
  request_id varchar(128),
  model_version varchar(128),
  index_version varchar(128),
  prompt_version varchar(128),
  created_at timestamptz NOT NULL DEFAULT now(),
  CHECK ((role = 'USER' AND content IS NOT NULL AND status IS NULL)
      OR (role = 'ASSISTANT' AND status IS NOT NULL))
);

CREATE INDEX chat_messages_session_created_idx
  ON csas.chat_messages(session_id, created_at, id);

CREATE TABLE csas.message_citations (
  message_id uuid NOT NULL REFERENCES csas.chat_messages(id) ON DELETE CASCADE,
  ordinal smallint NOT NULL CHECK (ordinal >= 0),
  source_id varchar(128) NOT NULL,
  document_id varchar(256) NOT NULL,
  revision varchar(256) NOT NULL,
  chunk_id varchar(256) NOT NULL,
  index_version varchar(128) NOT NULL,
  title text NOT NULL,
  url text NOT NULL,
  locator text NOT NULL,
  PRIMARY KEY (message_id, ordinal),
  UNIQUE (message_id, chunk_id)
);
