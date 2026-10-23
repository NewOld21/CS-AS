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
    generic = [json.loads(line) for line in prior.read_text(encoding='utf-8').splitlines() if line.strip()] if prior.exists() else []
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
    rows = [r for category in TARGETS for r in json.loads((BANK/(category+'.json')).read_text(encoding='utf-8'))]
    report = ['# gyoogle CS 문제은행 v1', '', f'고정 원문 commit: `{SHA}`.', '',
              '지식 근거는 gyoogle 원문 Markdown뿐입니다. 초안과 별도 블라인드 정답 풀이·근거 검토에 GMS를 사용했습니다. 사람 의미 검수는 수행하지 않았습니다.', '',
              '기존 15문항과 사용자 기록을 유지하고 신규 240문항을 CURATED로 추가합니다. reviewed_at은 자동 검토 일시이며 사람 검수 표시가 아닙니다.', '',
              '| 분야 | 신규 | EASY | MEDIUM | HARD |', '|---|---:|---:|---:|---:|']
    for category,total in TARGETS.items():
        report.append(f'| {category} | {total} | {total*3//10} | {total//2} | {total//5} |')
    report += ['', '## 출처와 재현', '',
               f'문항에 사용한 원문 파일 수: {len({r["sourcePath"] for r in rows})}. 수집한 고정 원문은 73개이며 MIT 원문과 SHA256 manifest를 data/quiz-bank/gyoogle-v1/에 보존합니다.', '',
               '각 JSON 문항은 sourceRepository/sourceCommit/sourcePath/sourceUrl/sourceEvidence, topic, keywords, learningObjective, 네 선택지 해설과 독립 검토 결과를 포함합니다. 원문 내부 링크의 자료는 근거로 사용하지 않습니다.', '',
               '```sh', 'python scripts/gyoogle_quiz_bank.py validate', 'python scripts/build_gyoogle_seed.py', '```', '',
               '컴파일러는 수량·난이도·실제 인용·출처 hash·독립 검토 중 하나라도 실패하면 V13을 만들지 않습니다. seed는 고정 UUID와 ON CONFLICT DO NOTHING으로 재실행할 수 있습니다.', '',
               '## 서비스 연결', '',
               '기존 퀴즈 조회·채점·quiz_attempts·오답 복습·통계 경로를 재사용합니다. source_metadata는 서버 전용이며 제출 전 API에 정답이나 해설을 노출하지 않습니다. 제출 후에는 기존 해설에 네 선택지별 해설을 함께 제공합니다.', '',
               '분야별 최대 100문항 조회 및 난이도 선택, 무작위 배열로 한 바퀴 내 중복을 방지합니다. 기존 문제 URL과 ID는 유지합니다.', '',
               '서버가 확인한 concept:gyoogle-* 문제의 AS와 관련 AI 생성은 planner의 제안과 무관하게 source_id=gyoogle을 강제합니다. 일반 독립 챗봇은 기존 다른 승인 출처도 사용합니다. 존댓말 규칙은 공통 시스템 프롬프트에 적용합니다.', '',
               '## 사용한 원문 파일', '']
    for path in sorted({r['sourcePath'] for r in rows}):
        report.append(f'- [{path}]({docs[path]["source_url"]})')
    report += ['', '## 분야별 예시 2개', '']
    for category in TARGETS:
        report += [f'### {category}', '']
        for row in [r for r in rows if r['category']==category][:2]:
            report += [f'**{row["question"]}** ({row["difficulty"]})', '']
            report += [f'{n}. {text}' for n,text in enumerate(row['options'],1)]
            report += ['', f'정답: {row["correctAnswer"]}. {row["explanation"]}', '', f'출처: [{row["sourcePath"]}]({row["sourceUrl"]})', '']
    (ROOT/'docs/gyoogle-question-bank.md').write_text('\n'.join(report)+'\n',encoding='utf-8')
    (BANK/'validation.json').write_text((ROOT/'reports/gyoogle-bank/validation.json').read_text(encoding='utf-8'),encoding='utf-8')
    print(json.dumps({'seed':str(target),'questions':240,'documents':len(combined)}))


if __name__ == '__main__':
    main()
