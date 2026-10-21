-- Flyway owns the csas schema and its versioned history. Domain tables follow in V2+.
CREATE SCHEMA IF NOT EXISTS csas;
COMMENT ON SCHEMA csas IS 'CS/AS service data; managed by Flyway';
