CREATE TABLE csas.users (
    id UUID PRIMARY KEY,
    email_normalized VARCHAR(254) NOT NULL,
    password_hash VARCHAR(60) NOT NULL,
    nickname VARCHAR(40),
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT users_email_normalized_key UNIQUE (email_normalized),
    CONSTRAINT users_email_normalized_check CHECK (email_normalized = lower(btrim(email_normalized))),
    CONSTRAINT users_password_hash_check CHECK (password_hash ~ '^\$2[aby]\$12\$[./A-Za-z0-9]{53}$')
);
