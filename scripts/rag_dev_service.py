#!/usr/bin/env python3
"""Run the Docker-only local RAG service with a small, explicit demo corpus."""
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/ai/src"))

from csas_rag.api.server import serve
from csas_rag.generation.answering import AnswerService, RagUnavailable
from csas_rag.generation.quiz import QuizService
from csas_rag.generation.quiz.validation import validate_candidate
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import DeterministicTestEmbedding, OpenAIEmbedding
from csas_rag.providers.llm import OpenAIAnswerGenerator
from csas_rag.retrieval.vector import VectorRetriever
from csas_rag.retrieval.planning import QueryPlanner


class LocalGroundedGenerator:
    """Deterministic local adapter that keeps Docker development offline."""

    model = "local-grounded-demo-v1"

    def generate(self, _system: str, prompt: str) -> dict:
        match = re.search(
            r"<evidence chunk_id=([^>]+)>\n(.*?)\n</evidence>", prompt, re.DOTALL
        )
        if not match:
            return {"status": "insufficient_evidence"}
        chunk_id, content = match.groups()
        return {
            "status": "answered",
            "answer": "로컬 개발용 근거 문서에 따르면 " + content.strip(),
            "cited_chunk_ids": [chunk_id],
        }


def load_documents(path: Path) -> list[dict]:
    documents = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(documents, list) or not documents:
        raise ValueError("Local RAG fixture must contain at least one document")
    return documents


def seed(store: ChromaVectorStore, embedding, documents: list[dict], index_version: str) -> None:
    chunks = []
    for position, document in enumerate(documents):
        chunks.append({
            "source_id": "local-demo",
            "document_id": document["document_id"],
            "revision": "local-v2",
            "chunk_id": document["document_id"] + ":local-v2:chunk:0",
            "title": document["title"],
            "source_url": document["source_url"],
            "locator": "local-fixture.json#" + str(position),
            "category": document["category"],
            "language": "ko",
            "concept_ids": [document["concept_id"]],
            "chunk_index": 0,
            "chunk_config_version": "local-v1",
            "content": document["content"],
        })
    chunk_ids = [chunk["chunk_id"] for chunk in chunks]
    if store.has_chunks(chunk_ids):
        return
    vectors = embedding.embed([chunk["content"] for chunk in chunks])
    for chunk, vector in zip(chunks, vectors):
        store.replace_document([chunk], [vector], index_version)


def main() -> None:
    token = os.environ.get("RAG_SERVICE_TOKEN", "")
    if len(token) < 32:
        raise SystemExit("RAG_SERVICE_TOKEN must contain at least 32 characters")
    provider = os.environ.get("RAG_DEV_PROVIDER", "deterministic-test")
    index_version = os.environ.get("RAG_ACTIVE_INDEX", "local-dev-v1")
    fixture = Path(os.environ.get(
        "RAG_LOCAL_FIXTURE", ROOT / "backend/ai/fixtures/local_documents.json"
    ))
    manifest_path = Path(os.environ.get(
        "RAG_INDEX_MANIFEST", ROOT / "data/processed/indexes" / (index_version + ".json")
    ))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else None
    if provider == "gms" and (not (os.environ.get("GMS_KEY") or os.environ.get("OPENAI_API_KEY")) or not manifest):
        code = "GMS_KEY_MISSING" if not (os.environ.get("GMS_KEY") or os.environ.get("OPENAI_API_KEY")) else "INDEX_MISSING"
        class Unavailable:
            runtime_status = {"mode": "gms", "model": os.environ.get("GMS_CHAT_MODEL", "unknown"),
                              "live": False, "configured": False, "error_code": code, "corpus_kind": "unavailable"}
            def answer(self, request):
                raise RagUnavailable(code)
        serve(Unavailable(), token, index_version, host="0.0.0.0", port=8090)
        return
    if manifest and (manifest.get("status") != "ACTIVE"
                     or manifest.get("index_version") != index_version):
        raise SystemExit("RAG_INDEX_MANIFEST must describe the configured ACTIVE index")
    if provider == "gms":
        embedding = OpenAIEmbedding(
            model=manifest.get("model") if manifest else None,
            dimensions=manifest.get("dimensions") if manifest else None,
        )
        generator = OpenAIAnswerGenerator()
    elif provider == "deterministic-test":
        embedding = DeterministicTestEmbedding()
        generator = LocalGroundedGenerator()
    else:
        raise SystemExit("RAG_DEV_PROVIDER must be gms or deterministic-test")
    store = ChromaVectorStore(index_version)
    if manifest:
        if not store.count():
            raise SystemExit("The configured ACTIVE index is empty")
    else:
        seed(store, embedding, load_documents(fixture), index_version)
        manifest = {"model": embedding.model, "dimensions": embedding.dimensions}
    retriever = VectorRetriever(store, embedding, manifest)
    service = AnswerService(retriever, generator, min_score=-1.0 if provider == "deterministic-test" else 0.2,
                            max_chunks=int(os.environ.get("RAG_TOP_K", "5")),
                            planner=QueryPlanner() if provider == "gms" else None)
    service.runtime_status = {"mode": provider, "model": generator.model,
                              "live": provider == "gms", "configured": True,
                              "corpus_kind": "active" if manifest_path.exists() else "demo"}
    serve(
        service,
        token,
        index_version,
        host="0.0.0.0",
        port=8090,
        quiz_service=QuizService(retriever, generator, validate_candidate, min_score=-1.0),
    )


if __name__ == "__main__":
    main()
