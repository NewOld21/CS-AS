"""Structure-aware chunking and versioned index construction."""
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ChunkConfig:
    max_chars: int = 1200
    overlap_chars: int = 180
    min_chars: int = 160
    version: str = "markdown-structure-1200-180-v1"

    def validate(self) -> None:
        if self.max_chars < 256 or self.min_chars < 1 or not 0 <= self.overlap_chars < self.max_chars:
            raise ValueError("Invalid chunk configuration")


def _sections(content: str) -> list[tuple[str, str]]:
    heading = ""
    buffer = []
    result = []
    in_code = False
    for line in content.splitlines(keepends=True):
        if line.lstrip().startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,6}\s+", line):
            if buffer:
                result.append((heading, "".join(buffer).strip()))
            heading, buffer = line.strip(), [line]
        else:
            buffer.append(line)
    if buffer:
        result.append((heading, "".join(buffer).strip()))
    return [(heading, text) for heading, text in result if text]


def chunk_document(document: dict, config: ChunkConfig) -> list[dict]:
    config.validate()
    pieces = []
    for heading, section in _sections(document["content"]):
        start = 0
        while start < len(section):
            hard_end = min(start + config.max_chars, len(section))
            end = hard_end
            if hard_end < len(section):
                candidates = [section.rfind(marker, start + config.min_chars, hard_end) for marker in ("\n\n", "\n", ". ")]
                boundary = max(candidates)
                if boundary > start:
                    end = boundary + (2 if section[boundary:boundary + 2] == "\n\n" else 1)
            text = section[start:end].strip()
            if text:
                pieces.append((heading, text))
            if end >= len(section):
                break
            start = max(start + 1, end - config.overlap_chars)
    if len(pieces) > 1 and len(pieces[-1][1]) < config.min_chars:
        previous_heading, previous = pieces[-2]
        last_heading, last = pieces.pop()
        pieces[-1] = (previous_heading or last_heading, previous + "\n\n" + last)
    chunks = []
    for index, (heading, content) in enumerate(pieces):
        key = f"{document['document_id']}:{document['revision']}:{config.version}:{index}"
        chunks.append({
            "chunk_id": "chunk:" + digest(key), "document_id": document["document_id"],
            "source_id": document["source_id"], "revision": document["revision"],
            "source_url": document["source_url"], "title": document["title"],
            "category": document.get("category"), "concept_ids": document.get("concept_ids", []),
            "version": document.get("version", ""),
            "language": document["language"], "chunk_index": index, "content": content,
            "locator": document["locator"] + ("#" + heading.lstrip("# ") if heading else ""),
            "chunk_config_version": config.version,
        })
    return chunks


def load_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def build_index(documents: list[dict], store, embedding, index_version: str, corpus_digest: str,
                config: ChunkConfig = ChunkConfig(), batch_size: int = 32) -> dict:
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,62}", index_version):
        raise ValueError("Invalid index version")
    if batch_size < 1 or embedding.dimensions < 1:
        raise ValueError("Invalid index settings")
    count = 0
    for document in documents:
        chunks = chunk_document(document, config)
        vectors = []
        for offset in range(0, len(chunks), batch_size):
            vectors.extend(embedding.embed([chunk["content"] for chunk in chunks[offset:offset + batch_size]]))
        if chunks:
            store.replace_document(chunks, vectors, index_version)
            count += len(chunks)
    return {
        "schema_version": 1, "status": "BUILDING", "index_version": index_version,
        "collection": "csas-" + index_version.replace("_", "-"), "model": embedding.model,
        "dimensions": embedding.dimensions, "chunk_config": asdict(config),
        "corpus_digest": corpus_digest, "document_count": len(documents), "chunk_count": count,
        "built_at": utc_now(),
    }


def _content_hash(document: dict) -> str:
    return document.get("content_hash") or digest(document["content"])


def _chunk_record(chunk: dict, embedding, config: ChunkConfig, index_version: str) -> dict:
    content_hash = digest(chunk["content"])
    identity = ":".join((content_hash, config.version, embedding.model,
                         str(embedding.dimensions), index_version))
    return {"chunk_id": chunk["chunk_id"], "content_hash": content_hash,
            "embedding_key": digest(identity)}


def _document_record(document: dict, chunks: list[dict], embedding, config: ChunkConfig,
                     index_version: str, now: str, indexed_at: str | None = None) -> dict:
    return {
        "source_id": document["source_id"], "document_id": document["document_id"],
        "source_revision": document["revision"], "content_hash": _content_hash(document),
        "chunk_ids": [chunk["chunk_id"] for chunk in chunks],
        "chunks": [_chunk_record(chunk, embedding, config, index_version) for chunk in chunks],
        "embedding_model": embedding.model, "embedding_dimension": embedding.dimensions,
        "chunking_version": config.version, "index_version": index_version,
        "indexed_at": indexed_at or now, "last_seen_at": now, "indexing_status": "indexed",
    }


def incremental_index(documents: list[dict], store, embedding, index_version: str,
                      corpus_digest: str, previous_manifest: dict | None = None,
                      config: ChunkConfig = ChunkConfig(), batch_size: int = 32,
                      complete_source_ids: set[str] | None = None,
                      dry_run: bool = False) -> tuple[dict, dict]:
    """Synchronize one collection without re-embedding unchanged document/chunk content.

    Deletion is intentionally source-scoped and opt-in. A caller may only pass source IDs whose
    discovery completed successfully without a document cap. Failed documents retain their prior
    chunks and manifest entry so a later run can retry safely.
    """
    if not re.fullmatch(r"[a-z0-9][a-z0-9._-]{2,62}", index_version):
        raise ValueError("Invalid index version")
    config.validate()
    if batch_size < 1 or embedding.dimensions < 1:
        raise ValueError("Invalid index settings")
    complete_source_ids = set(complete_source_ids or set())
    by_id = {document["document_id"]: document for document in documents}
    if len(by_id) != len(documents):
        raise ValueError("Duplicate document_id in indexing input")
    previous_manifest = previous_manifest or {}
    previous_records = {row["document_id"]: row for row in previous_manifest.get("documents", [])
                        if isinstance(row, dict) and row.get("document_id")}
    now = utc_now()
    planned = {}
    prepared = {}
    settings = (embedding.model, embedding.dimensions, config.version, index_version)
    for document_id, document in by_id.items():
        chunks = chunk_document(document, config)
        prepared[document_id] = chunks
        previous = previous_records.get(document_id)
        previous_settings = None if not previous else (
            previous.get("embedding_model"), previous.get("embedding_dimension"),
            previous.get("chunking_version"), previous.get("index_version"))
        expected_ids = [chunk["chunk_id"] for chunk in chunks]
        stored_ids = set(store.document_chunk_ids(document_id))
        complete = set(expected_ids) == stored_ids
        if (previous and previous.get("content_hash") == _content_hash(document)
                and previous_settings == settings and complete
                and previous.get("indexing_status") == "indexed"):
            planned[document_id] = "unchanged"
        elif not previous and complete and expected_ids:
            # Adopt an existing pre-C21 collection without paying for the same embeddings again.
            planned[document_id] = "unchanged"
        elif previous:
            planned[document_id] = "modified"
        else:
            planned[document_id] = "new"
    deleted_ids = sorted(document_id for document_id, row in previous_records.items()
                         if document_id not in by_id and row.get("source_id") in complete_source_ids)
    stats = {
        "total_documents": len(documents),
        "new": sum(value == "new" for value in planned.values()),
        "modified": sum(value == "modified" for value in planned.values()),
        "unchanged": sum(value == "unchanged" for value in planned.values()),
        "deleted": len(deleted_ids), "embedded_documents": 0, "embedded_chunks": 0,
        "reused_chunks": 0, "skipped_documents": sum(value == "unchanged" for value in planned.values()),
        "removed_documents": 0, "failed_documents": 0, "failures": [],
        "dry_run": dry_run,
    }
    if dry_run:
        return previous_manifest, {**stats, "changes": planned, "deleted_document_ids": deleted_ids}

    records = dict(previous_records)
    for document_id, action in planned.items():
        document, chunks = by_id[document_id], prepared[document_id]
        previous = previous_records.get(document_id)
        if action == "unchanged":
            records[document_id] = _document_record(
                document, chunks, embedding, config, index_version, now,
                previous.get("indexed_at") if previous else now)
            continue
        try:
            previous_chunks = {row.get("embedding_key"): row.get("chunk_id")
                               for row in (previous or {}).get("chunks", [])
                               if row.get("embedding_key") and row.get("chunk_id")}
            reusable = {}
            if previous and (previous.get("embedding_model"), previous.get("embedding_dimension"),
                             previous.get("chunking_version"), previous.get("index_version")) == settings:
                reusable = store.get_embeddings(list(previous_chunks.values()))
            vectors = [None] * len(chunks)
            pending_positions = []
            for position, chunk in enumerate(chunks):
                key = _chunk_record(chunk, embedding, config, index_version)["embedding_key"]
                old_id = previous_chunks.get(key)
                if old_id in reusable:
                    vectors[position] = reusable[old_id]
                    stats["reused_chunks"] += 1
                else:
                    pending_positions.append(position)
            for offset in range(0, len(pending_positions), batch_size):
                positions = pending_positions[offset:offset + batch_size]
                embedded = embedding.embed([chunks[position]["content"] for position in positions])
                for position, vector in zip(positions, embedded):
                    vectors[position] = vector
                stats["embedded_chunks"] += len(positions)
            if chunks:
                store.replace_document(chunks, vectors, index_version)
            elif previous:
                store.remove_document(document_id)
            records[document_id] = _document_record(document, chunks, embedding, config,
                                                     index_version, now)
            stats["embedded_documents"] += 1
        except Exception as error:  # Provider/store adapters normalize their own public errors.
            stats["failed_documents"] += 1
            stats["failures"].append({"document_id": document_id,
                                      "error_type": type(error).__name__})
            if previous:
                records[document_id] = {**previous, "indexing_status": "failed",
                                        "last_error": type(error).__name__, "last_seen_at": now,
                                        "pending_content_hash": _content_hash(document)}
    for document_id in deleted_ids:
        try:
            store.remove_document(document_id)
            records.pop(document_id, None)
            stats["removed_documents"] += 1
        except Exception as error:
            stats["failed_documents"] += 1
            stats["failures"].append({"document_id": document_id,
                                      "error_type": type(error).__name__})
            records[document_id] = {**records[document_id], "indexing_status": "delete_failed",
                                    "last_error": type(error).__name__}
    chunk_count = sum(len(row.get("chunk_ids", [])) for row in records.values())
    manifest = {
        "schema_version": 2,
        "status": previous_manifest.get("status", "BUILDING"),
        "index_version": index_version,
        "collection": "csas-" + index_version.replace("_", "-"),
        "model": embedding.model, "dimensions": embedding.dimensions,
        "chunk_config": asdict(config), "corpus_digest": corpus_digest,
        "document_count": len(records), "chunk_count": chunk_count,
        "documents": sorted(records.values(), key=lambda row: (row["source_id"], row["document_id"])),
        "built_at": previous_manifest.get("built_at", now), "updated_at": now,
        "last_run": stats,
    }
    if previous_manifest.get("evaluation"):
        manifest["evaluation"] = previous_manifest["evaluation"]
    if previous_manifest.get("activated_at"):
        manifest["activated_at"] = previous_manifest["activated_at"]
    return manifest, stats


def write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def activate_manifest(manifest: dict, evaluation: dict) -> dict:
    """Promote only an evaluated BUILDING index; never overwrite another active collection."""
    if manifest.get("status") != "BUILDING":
        raise ValueError("Only a BUILDING index can be activated")
    if evaluation.get("passed") is not True or evaluation.get("query_count", 0) < 5:
        raise ValueError("Index evaluation did not satisfy the activation gate")
    return {**manifest, "status": "ACTIVE", "evaluation": evaluation,
            "activated_at": utc_now()}
