ALTER TABLE csas.chat_sessions
  ADD COLUMN title varchar(200) NOT NULL DEFAULT '새 CS 질문',
  ADD COLUMN updated_at timestamptz NOT NULL DEFAULT now();

UPDATE csas.chat_sessions SET updated_at = created_at;

DROP INDEX csas.chat_sessions_user_created_idx;
CREATE INDEX chat_sessions_user_updated_idx
  ON csas.chat_sessions(user_id, updated_at DESC, id DESC);

ALTER TABLE csas.chat_messages
  DROP CONSTRAINT chat_messages_status_check,
  DROP CONSTRAINT chat_messages_check,
  ADD COLUMN request_key uuid,
  ADD COLUMN user_message_id uuid REFERENCES csas.chat_messages(id),
  ADD COLUMN failure_code varchar(64),
  ADD CONSTRAINT chat_messages_status_check
    CHECK (status IN ('pending', 'answered', 'insufficient_evidence', 'failed')),
  ADD CONSTRAINT chat_messages_role_state_check
    CHECK ((role = 'USER' AND content IS NOT NULL AND status IS NULL AND request_key IS NULL)
        OR (role = 'ASSISTANT' AND status IS NOT NULL));

CREATE UNIQUE INDEX chat_messages_session_request_key_uq
  ON csas.chat_messages(session_id, request_key)
  WHERE request_key IS NOT NULL;
