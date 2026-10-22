"""Structure-aware chunking and versioned index construction."""
import hashlib
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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
        "built_at": datetime.now(timezone.utc).isoformat(),
    }


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
            "activated_at": datetime.now(timezone.utc).isoformat()}
