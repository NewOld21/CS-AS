"""Local staging catalog. Immutable object files, transactional revision metadata."""
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .parsing import CHUNK_VERSION, PARSER_VERSION, chunks, digest


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Store:
    def __init__(self, root: Path):
        self.root = root
        (root / "objects").mkdir(parents=True, exist_ok=True)
        (root / "raw").mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(root / "catalog.sqlite3")
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS revisions (
                source_id TEXT NOT NULL, document_id TEXT NOT NULL, revision TEXT NOT NULL,
                content_hash TEXT NOT NULL, object_path TEXT NOT NULL,
                PRIMARY KEY(document_id, revision));
            CREATE TABLE IF NOT EXISTS failures (
                source_id TEXT NOT NULL, item_key TEXT NOT NULL, item TEXT NOT NULL,
                reason TEXT NOT NULL, PRIMARY KEY(source_id, item_key));
            CREATE TABLE IF NOT EXISTS checkpoints (
                source_id TEXT PRIMARY KEY, revision TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS discovery_states (
                source_id TEXT PRIMARY KEY, state TEXT NOT NULL, updated_at TEXT NOT NULL);
        """)

    def close(self):
        self.db.close()

    def stage_raw(self, raw: str) -> str:
        path = Path("raw") / (digest(raw) + ".txt")
        if not (self.root / path).exists():
            tmp = (self.root / path).with_suffix(".tmp")
            # Bytes preserve original newlines on Windows as well as POSIX.
            tmp.write_bytes(raw.encode("utf-8"))
            tmp.replace(self.root / path)
        return path.as_posix()

    def known(self, source: dict, item: dict) -> bool:
        if not item.get("revision"):
            return False
        document_id = "doc:" + digest(source["id"] + ":" + item["key"])
        row = self.db.execute("SELECT object_path FROM revisions WHERE document_id=? AND revision=?",
                              (document_id, str(item["revision"]))).fetchone()
        if row:
            old = json.loads((self.root / row[0]).read_text(encoding="utf-8"))["document"]
            expected = digest(str(sorted(source.get("concept_mappings", {}).items())))
            if old.get("concept_mapping_version") != expected or old.get("parser_version") != PARSER_VERSION:
                raise ValueError("Parser or concept mapping changed; use a new staging output")
        return row is not None

    def save(self, doc: dict, raw: str) -> str:
        old = self.db.execute("SELECT content_hash, object_path FROM revisions WHERE document_id=? AND revision=?",
                              (doc["document_id"], doc["revision"])).fetchone()
        if old:
            saved = json.loads((self.root / old[1]).read_text(encoding="utf-8"))
            if (saved["document"].get("concept_mapping_version") != doc["concept_mapping_version"]
                    or saved["document"].get("parser_version") != PARSER_VERSION):
                raise ValueError("Parser or concept mapping changed; use a new staging output")
            if saved["document"]["raw_hash"] != doc["raw_hash"]:
                raise ValueError("Immutable revision content changed")
            return "duplicate"
        existing = self.db.execute("SELECT 1 FROM revisions WHERE document_id=?", (doc["document_id"],)).fetchone()
        same = self.db.execute("SELECT 1 FROM revisions WHERE content_hash=?", (doc["content_hash"],)).fetchone()
        doc["fetched_at"] = utc_now()
        doc["raw_uri"] = self.stage_raw(raw)
        doc["exact_duplicate_content"] = bool(same)
        # Separate documents keep attribution even when their text is identical.
        payload = {"document": doc, "chunks": chunks(doc)}
        key = digest(doc["document_id"] + ":" + doc["revision"])
        path = Path("objects") / (key + ".json")
        temporary = self.root / (str(path) + ".tmp")
        temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        temporary.replace(self.root / path)
        with self.db:
            self.db.execute("INSERT INTO revisions VALUES (?, ?, ?, ?, ?)",
                            (doc["source_id"], doc["document_id"], doc["revision"], doc["content_hash"], path.as_posix()))
        return "changed" if existing else "success"

    def fail(self, source_id: str, item: dict, reason: str):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO failures VALUES (?, ?, ?, ?)",
                            (source_id, item.get("key", "__discovery__"), json.dumps(item), reason))

    def failed(self, source_id: str) -> list[dict]:
        return [json.loads(x[0]) for x in self.db.execute("SELECT item FROM failures WHERE source_id=? ORDER BY item_key", (source_id,))]

    def clear_failure(self, source_id: str, key: str):
        with self.db:
            self.db.execute("DELETE FROM failures WHERE source_id=? AND item_key=?", (source_id, key))

    def checkpoint(self, source_id: str, revision: str):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO checkpoints VALUES (?, ?)", (source_id, revision))

    def last_revision(self, source_id: str):
        row = self.db.execute("SELECT revision FROM checkpoints WHERE source_id=?", (source_id,)).fetchone()
        return row[0] if row else None

    def discovery_state(self, source_id: str):
        row = self.db.execute("SELECT state FROM discovery_states WHERE source_id=?", (source_id,)).fetchone()
        return json.loads(row[0]) if row else None

    def save_discovery_state(self, source_id: str, state: dict):
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO discovery_states VALUES (?, ?, ?)",
                            (source_id, json.dumps(state, ensure_ascii=False), utc_now()))

    def manifest(self, registry_hash: str) -> dict:
        entries = [{"source_id": s, "document_id": d, "revision": r, "content_hash": h, "object_path": p}
                   for s, d, r, h, p in self.db.execute("SELECT * FROM revisions ORDER BY source_id, document_id, revision")]
        manifest = {"schema_version": 1, "parser_version": PARSER_VERSION,
                    "chunk_config_version": CHUNK_VERSION, "registry_hash": registry_hash,
                    "embedding_index": None, "documents": entries}
        manifest["corpus_digest"] = digest(json.dumps(manifest, sort_keys=True))
        manifest["created_at"] = utc_now()
        path = self.root / "manifest.json"
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        tmp.replace(path)
        self.export_jsonl(entries)
        return manifest

    def export_jsonl(self, entries: list[dict]) -> None:
        """Export committed objects only; never expose an uncommitted raw/parser result."""
        documents = self.root / "normalized.jsonl"
        chunk_file = self.root / "chunks.jsonl"
        document_tmp = documents.with_suffix(".tmp")
        chunk_tmp = chunk_file.with_suffix(".tmp")
        with document_tmp.open("w", encoding="utf-8", newline="\n") as doc_out, chunk_tmp.open(
            "w", encoding="utf-8", newline="\n"
        ) as chunk_out:
            for entry in entries:
                payload = json.loads((self.root / entry["object_path"]).read_text(encoding="utf-8"))
                document = payload["document"]
                normalized = {
                    "source_id": document["source_id"],
                    "document_id": document["document_id"],
                    "revision": document["revision"],
                    "title": document["title"],
                    "content": document["text"],
                    "source_url": document["url"],
                    "locator": document["locator"],
                    "category": document["category"],
                    "concept_ids": document["concept_ids"],
                    "language": document["language"],
                    "license": document["license"],
                    "attribution": document["attribution"],
                    "content_hash": document["content_hash"],
                    "collected_at": document["fetched_at"],
                    "metadata": {
                        **document["metadata"],
                        "version": document["version"],
                        "headings": document["headings"],
                        "raw_uri": document["raw_uri"],
                    },
                }
                doc_out.write(json.dumps(normalized, ensure_ascii=False, sort_keys=True) + "\n")
                for chunk in payload["chunks"]:
                    chunk_out.write(json.dumps(chunk, ensure_ascii=False, sort_keys=True) + "\n")
        document_tmp.replace(documents)
        chunk_tmp.replace(chunk_file)
