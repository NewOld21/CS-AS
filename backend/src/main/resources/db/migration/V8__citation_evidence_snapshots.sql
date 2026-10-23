ALTER TABLE csas.message_citations
  ADD COLUMN evidence_text text,
  ADD COLUMN category varchar(128),
  ADD COLUMN technology_version varchar(128);
