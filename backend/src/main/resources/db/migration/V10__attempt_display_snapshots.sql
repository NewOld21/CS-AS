ALTER TABLE csas.quiz_attempts
  ADD COLUMN quiz_snapshot jsonb,
  ADD COLUMN evidence_snapshot jsonb NOT NULL DEFAULT '[]'::jsonb;

UPDATE csas.quiz_attempts a SET quiz_snapshot = jsonb_build_object(
  'id',q.id,'version',q.version,'stem',q.stem,'category',q.category,
  'difficulty',q.difficulty,'origin',q.origin,
  'concept_ids',COALESCE((SELECT jsonb_agg(qc.concept_id ORDER BY qc.is_primary DESC,qc.concept_id)
    FROM csas.quiz_concepts qc WHERE qc.quiz_id=q.id),'[]'::jsonb),
  'options',COALESCE((SELECT jsonb_agg(jsonb_build_object('id',o.id,'position',o.position,'text',o.text) ORDER BY o.position)
    FROM csas.quiz_options o WHERE o.quiz_id=q.id),'[]'::jsonb)
), evidence_snapshot = COALESCE((SELECT jsonb_agg(jsonb_build_object(
  'source_id',e.source_id,'document_id',e.document_id,'revision',e.revision,'chunk_id',e.chunk_id,
  'index_version',e.index_version,'title',e.title,'url',e.url,'locator',e.locator,
  'evidence_text',e.evidence_text,'category',e.category,'technology_version',e.technology_version
) ORDER BY e.ordinal) FROM csas.quiz_evidence e WHERE e.quiz_id=q.id),'[]'::jsonb)
FROM csas.quizzes q WHERE q.id=a.quiz_id;

ALTER TABLE csas.quiz_attempts ALTER COLUMN quiz_snapshot SET NOT NULL;
