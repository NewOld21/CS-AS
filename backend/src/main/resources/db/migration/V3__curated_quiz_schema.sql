CREATE TABLE csas.concepts (
    id VARCHAR(100) PRIMARY KEY,
    slug VARCHAR(100) NOT NULL UNIQUE,
    name_ko VARCHAR(100) NOT NULL,
    name_en VARCHAR(100) NOT NULL,
    category VARCHAR(32) NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT concepts_id_check CHECK (id = 'concept:' || slug),
    CONSTRAINT concepts_slug_check CHECK (slug ~ '^[a-z0-9]+(?:-[a-z0-9]+)*$'),
    CONSTRAINT concepts_category_check CHECK (
        category IN ('OPERATING_SYSTEM', 'NETWORK', 'DATABASE', 'DATA_STRUCTURE', 'ALGORITHM', 'COMPUTER_ARCHITECTURE')
    ),
    CONSTRAINT concepts_names_check CHECK (
        btrim(name_ko) <> '' AND btrim(name_en) <> '' AND btrim(description) <> ''
    )
);

CREATE TABLE csas.quizzes (
    id UUID PRIMARY KEY,
    family_id UUID NOT NULL,
    version INTEGER NOT NULL,
    stem TEXT NOT NULL,
    category VARCHAR(32) NOT NULL,
    difficulty VARCHAR(16) NOT NULL,
    origin VARCHAR(16) NOT NULL,
    status VARCHAR(16) NOT NULL,
    owner_user_id UUID REFERENCES csas.users(id) ON DELETE RESTRICT,
    explanation TEXT NOT NULL,
    source_url TEXT,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT quizzes_family_version_key UNIQUE (family_id, version),
    CONSTRAINT quizzes_stem_check CHECK (btrim(stem) <> ''),
    CONSTRAINT quizzes_version_check CHECK (version > 0),
    CONSTRAINT quizzes_category_check CHECK (
        category IN ('OPERATING_SYSTEM', 'NETWORK', 'DATABASE', 'DATA_STRUCTURE', 'ALGORITHM', 'COMPUTER_ARCHITECTURE')
    ),
    CONSTRAINT quizzes_difficulty_check CHECK (difficulty IN ('EASY', 'MEDIUM', 'HARD')),
    CONSTRAINT quizzes_origin_check CHECK (origin IN ('CURATED', 'AI_GENERATED')),
    CONSTRAINT quizzes_status_check CHECK (status IN ('DRAFT', 'READY', 'RETIRED')),
    CONSTRAINT quizzes_owner_check CHECK (
        (origin = 'CURATED' AND owner_user_id IS NULL)
        OR (origin = 'AI_GENERATED' AND owner_user_id IS NOT NULL)
    ),
    CONSTRAINT quizzes_ready_metadata_check CHECK (
        status <> 'READY'
        OR (btrim(explanation) <> '' AND source_url IS NOT NULL AND btrim(source_url) <> '' AND reviewed_at IS NOT NULL)
    )
);

CREATE TABLE csas.quiz_options (
    id UUID PRIMARY KEY,
    quiz_id UUID NOT NULL REFERENCES csas.quizzes(id) ON DELETE RESTRICT,
    position SMALLINT NOT NULL,
    text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT quiz_options_quiz_id_id_key UNIQUE (quiz_id, id),
    CONSTRAINT quiz_options_quiz_position_key UNIQUE (quiz_id, position),
    CONSTRAINT quiz_options_position_check CHECK (position BETWEEN 1 AND 4),
    CONSTRAINT quiz_options_text_check CHECK (btrim(text) <> '')
);

CREATE UNIQUE INDEX quiz_options_one_correct_idx
    ON csas.quiz_options (quiz_id)
    WHERE is_correct;

CREATE TABLE csas.quiz_concepts (
    quiz_id UUID NOT NULL REFERENCES csas.quizzes(id) ON DELETE RESTRICT,
    concept_id VARCHAR(100) NOT NULL REFERENCES csas.concepts(id) ON DELETE RESTRICT,
    is_primary BOOLEAN NOT NULL DEFAULT false,
    PRIMARY KEY (quiz_id, concept_id)
);

CREATE UNIQUE INDEX quiz_concepts_one_primary_idx
    ON csas.quiz_concepts (quiz_id)
    WHERE is_primary;

CREATE INDEX quizzes_catalog_idx ON csas.quizzes (status, category, difficulty, id);
CREATE INDEX quiz_concepts_concept_idx ON csas.quiz_concepts (concept_id, quiz_id);

CREATE FUNCTION csas.validate_ready_quiz(target_quiz_id UUID)
RETURNS void
LANGUAGE plpgsql
AS $$
DECLARE
    current_status VARCHAR(16);
    option_count INTEGER;
    correct_count INTEGER;
    concept_count INTEGER;
    primary_count INTEGER;
BEGIN
    SELECT status INTO current_status FROM csas.quizzes WHERE id = target_quiz_id;
    IF current_status IS DISTINCT FROM 'READY' THEN
        RETURN;
    END IF;

    SELECT count(*), count(*) FILTER (WHERE is_correct)
      INTO option_count, correct_count
      FROM csas.quiz_options
     WHERE quiz_id = target_quiz_id;
    SELECT count(*), count(*) FILTER (WHERE is_primary)
      INTO concept_count, primary_count
      FROM csas.quiz_concepts
     WHERE quiz_id = target_quiz_id;

    IF option_count <> 4 OR correct_count <> 1 OR concept_count < 1 OR primary_count <> 1 THEN
        RAISE EXCEPTION 'READY quiz % violates publication invariants', target_quiz_id
            USING ERRCODE = '23514';
    END IF;
END;
$$;

CREATE FUNCTION csas.validate_ready_quiz_trigger()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    target_quiz_id UUID;
BEGIN
    IF TG_TABLE_NAME = 'quizzes' THEN
        target_quiz_id := COALESCE(NEW.id, OLD.id);
    ELSE
        target_quiz_id := COALESCE(NEW.quiz_id, OLD.quiz_id);
    END IF;
    PERFORM csas.validate_ready_quiz(target_quiz_id);
    RETURN NULL;
END;
$$;

CREATE CONSTRAINT TRIGGER quizzes_ready_invariants
AFTER INSERT OR UPDATE ON csas.quizzes
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION csas.validate_ready_quiz_trigger();

CREATE CONSTRAINT TRIGGER quiz_options_ready_invariants
AFTER INSERT OR UPDATE OR DELETE ON csas.quiz_options
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION csas.validate_ready_quiz_trigger();

CREATE CONSTRAINT TRIGGER quiz_concepts_ready_invariants
AFTER INSERT OR UPDATE OR DELETE ON csas.quiz_concepts
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW EXECUTE FUNCTION csas.validate_ready_quiz_trigger();
