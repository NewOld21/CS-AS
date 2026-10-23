#!/usr/bin/env python3
"""Compile audited gyoogle questions into a deterministic, additive Flyway seed."""
import hashlib
import json
import sys
import uuid
from difflib import SequenceMatcher
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT / 'backend/ai/src'))
from gyoogle_quiz_bank import BANK, SOURCES, SHA, TARGETS, validate
from csas_rag.indexing.pipeline import ChunkConfig, chunk_document

INDEX = 'csas-gyoogle-bank-v1'


def literal(value):
    return "'" + str(value).replace("'", "''") + "'"


def concept(path):
    return 'concept:gyoogle-' + hashlib.sha256(path.encode()).hexdigest()[:16]


def documents():
    manifest = json.loads((SOURCES / 'sources.json').read_text(encoding='utf-8'))
    result = {}
    for item in manifest['documents']:
        path = item['path']
        result[path] = dict(document_id='doc:gyoogle:' + hashlib.sha256(path.encode()).hexdigest(),
                            source_id='gyoogle', revision=SHA, source_url=item['url'],
                            title=Path(path).stem, locator=path, language='ko',
                            category=item['category'].lower().replace('_', '-'),
                            concept_ids=[concept(path)], content=(SOURCES/'sources'/path).read_text(encoding='utf-8'))
    return result


def main():
    docs = documents()
    corpus = ROOT/'data/processed/gyoogle-bank/normalized.jsonl'
    corpus.parent.mkdir(parents=True, exist_ok=True)
    prior = ROOT/'data/processed/checklist-ingestion/normalized.jsonl'
    generic = [json.loads(line) for line in prior.read_text(encoding='utf-8').splitlines() if line.strip()]
    combined = [d for d in generic if d['source_id'] != 'gyoogle'] + list(docs.values())
    corpus.write_text(''.join(json.dumps(d, ensure_ascii=False)+'\n' for d in combined), encoding='utf-8')
    if '--corpus-only' in sys.argv:
        print(json.dumps({'documents':len(combined), 'path':str(corpus)})); return
    if validate():
        raise SystemExit('Refusing to publish an incomplete or invalid dataset')
    sql = ['-- gyoogle-v1: automated blind solution + source audit; human review NOT_PERFORMED.',
           '-- Additive and idempotent: preserves every existing quiz, attempt and review.']
    for category in TARGETS:
        for row in json.loads((BANK/(category+'.json')).read_text(encoding='utf-8')):
            doc = docs[row['sourcePath']]
            cid = concept(row['sourcePath'])
            title = doc['title'][:100]
            sql.append('INSERT INTO csas.concepts(id,slug,name_ko,name_en,category,description) VALUES (' +
                       ','.join(map(literal,[cid,cid.removeprefix('concept:'),title,title,category,'gyoogle: '+title])) + ') ON CONFLICT DO NOTHING;')
            explanation = row['explanation'] + '\n\n' + '\n'.join(f'{n}. {text}' for n,text in enumerate(row['optionExplanations'],1))
            metadata = {**row, 'dataset':'gyoogle-v1','sourceDocumentId':doc['document_id']}
            qid = row['id']
            sql.append('INSERT INTO csas.quizzes(id,family_id,version,stem,category,difficulty,origin,status,explanation,source_url,reviewed_at,source_metadata) VALUES (' +
                       ','.join([literal(qid),literal(qid),'1',literal(row['question']),literal(category),literal(row['difficulty']),"'CURATED'","'READY'",literal(explanation),literal(row['sourceUrl']),'now()',literal(json.dumps(metadata,ensure_ascii=False))+'::jsonb']) + ') ON CONFLICT DO NOTHING;')
            for n,text in enumerate(row['options'],1):
                oid = str(uuid.uuid5(uuid.UUID(qid),str(n)))
                sql.append('INSERT INTO csas.quiz_options(id,quiz_id,position,text,is_correct) VALUES (' + ','.join([literal(oid),literal(qid),str(n),literal(text),str(n==row['correctAnswer']).lower()]) + ') ON CONFLICT DO NOTHING;')
            sql.append(f'INSERT INTO csas.quiz_concepts(quiz_id,concept_id,is_primary) VALUES ({literal(qid)},{literal(cid)},true) ON CONFLICT DO NOTHING;')
            chunks = chunk_document(doc,ChunkConfig())
            quote = row['sourceEvidence']['quote']
            # A source passage can cross chunk boundaries. Keep its full text in metadata;
            # attach the actual chunk with the largest matching span, never invent a chunk ID.
            evidence = max(chunks,key=lambda c:SequenceMatcher(None,quote,c['content']).find_longest_match().size)
            if evidence:
                values=[qid,1,'gyoogle',doc['document_id'],SHA,evidence['chunk_id'],INDEX,doc['title'],doc['source_url'],evidence['locator'],evidence['content'],doc['category'],'']
                sql.append('INSERT INTO csas.quiz_evidence(quiz_id,ordinal,source_id,document_id,revision,chunk_id,index_version,title,url,locator,evidence_text,category,technology_version) VALUES (' + ','.join(map(literal,values)) + ') ON CONFLICT DO NOTHING;')
    target = ROOT/'backend/src/main/resources/db/migration/V13__gyoogle_question_bank.sql'
    target.write_text('\n'.join(sql)+'\n',encoding='utf-8')
    print(json.dumps({'seed':str(target),'questions':240,'documents':len(combined)}))


if __name__ == '__main__':
    main()
