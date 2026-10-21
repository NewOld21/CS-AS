#!/usr/bin/env python3
"""Dedicated disposable smoke objects. Never resets databases or collections."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
import uuid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['write', 'read', 'cleanup'])
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--docker-config', type=Path)
    args = parser.parse_args()
    # SDK import creates default Settings and otherwise auto-loads cwd/.env.
    # Import in an empty directory; then explicitly disable its dotenv source.
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory(prefix='csas-chroma-import-') as directory:
        try:
            os.chdir(directory)
            import chromadb
        finally:
            os.chdir(original_cwd)

    command = ['docker']
    if args.docker_config:
        command += ['--config', str(args.docker_config)]
    command += ['compose', 'exec', '-T', 'postgres', 'sh', '-c',
                'export PGPASSWORD="$POSTGRES_PASSWORD"; '
                'exec psql -h 127.0.0.1 -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At']

    def sql(statement):
        result = subprocess.run(command, input=statement, text=True, encoding='utf-8',
                                capture_output=True, timeout=30)
        if result.returncode:
            raise RuntimeError('PostgreSQL SQL failed (inspect local container state)')
        return result.stdout.strip()

    # Compose loads .env itself; host client reads only these public settings.
    public = {}
    env_file = Path('.env')
    if env_file.exists():
        for line in env_file.read_text(encoding='utf-8').splitlines():
            key, sep, value = line.partition('=')
            if sep and key in {'CHROMA_HOST', 'CHROMA_PORT'}:
                public[key] = value.strip()
    client = chromadb.HttpClient(
        host=os.environ.get('CHROMA_HOST', public.get('CHROMA_HOST', 'localhost')),
        port=int(os.environ.get('CHROMA_PORT', public.get('CHROMA_PORT', '8000'))),
        settings=chromadb.Settings(_env_file=None))
    assert client.heartbeat() > 0, 'Chroma heartbeat failed'
    assert sql('SHOW server_encoding;') == 'UTF8', 'PostgreSQL encoding is not UTF8'

    if args.action == 'write':
        if args.state.exists():
            raise RuntimeError('State already exists; use read or cleanup')
        token = uuid.uuid4().hex
        args.state.parent.mkdir(parents=True, exist_ok=True)
        args.state.write_text(json.dumps({'token': token})+'\n', encoding='utf-8')
    else:
        token = json.loads(args.state.read_text(encoding='utf-8'))['token']
    if not re.fullmatch(r'[a-f0-9]{32}', token):
        raise ValueError('Invalid smoke state token')
    table = 'smoke_' + token
    collection_name = 'csas-smoke-' + token
    if args.action == 'cleanup':
        sql(f'DROP TABLE IF EXISTS "{table}";')
        client.delete_collection(collection_name)
        print('PASS: removed only this run\'s SQL table and Chroma collection')
        return
    if args.action == 'write':
        # Identifiers and values contain only the validated generated hex token.
        sql(f'CREATE TABLE "{table}" (id text PRIMARY KEY, note text NOT NULL); '
            f'INSERT INTO "{table}" VALUES (\'{token}\', \'한글 CS 테스트\');')
        collection = client.create_collection(collection_name, embedding_function=None)
        collection.add(ids=[token], embeddings=[[1.0, 0.0, 0.0]],
                       documents=['CS smoke document'],
                       metadatas=[{'source_id': 'smoke', 'document_id': token,
                                   'revision': 'test-v1', 'chunk_id': token}])
    collection = client.get_collection(collection_name, embedding_function=None)
    assert sql(f'SELECT note FROM "{table}" WHERE id=\'{token}\';') == '한글 CS 테스트'
    result = collection.get(ids=[token], include=['documents', 'metadatas'])
    assert result['ids'] == [token]
    assert result['documents'] == ['CS smoke document']
    assert result['metadatas'][0]['chunk_id'] == token
    result = collection.query(query_embeddings=[[1.0, 0.0, 0.0]], n_results=1)
    assert result['ids'] == [[token]], 'Vector query did not return saved document'
    print('PASS: SQL UTF8 read/write, Chroma heartbeat/get/vector query; state=' + str(args.state))


if __name__ == '__main__':
    main()
