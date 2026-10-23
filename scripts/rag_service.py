#!/usr/bin/env python3
"""Run the internal RAG answer API on a loopback/private interface."""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend/ai/src"))

from csas_rag.api.server import serve
from csas_rag.generation.answering import AnswerService
from csas_rag.generation.quiz import QuizService
from csas_rag.generation.quiz.validation import validate_candidate
from csas_rag.providers.chroma import ChromaVectorStore
from csas_rag.providers.embeddings import OpenAIEmbedding
from csas_rag.providers.llm import OpenAIAnswerGenerator
from csas_rag.retrieval.vector import VectorRetriever


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8090)
    args = parser.parse_args(argv)
    token = os.environ.get("RAG_SERVICE_TOKEN")
    if not token or len(token) < 32:
        raise SystemExit("RAG_SERVICE_TOKEN must contain at least 32 characters")
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    if manifest.get("status") != "ACTIVE":
        raise SystemExit("Only an ACTIVE index manifest can serve answers")
    embedding = OpenAIEmbedding(model=manifest["model"], dimensions=manifest["dimensions"])
    retriever = VectorRetriever(ChromaVectorStore(manifest["index_version"]), embedding, manifest)
    generator = OpenAIAnswerGenerator()
    serve(AnswerService(retriever, generator), token, manifest["index_version"], args.host, args.port,
          quiz_service=QuizService(retriever, generator, validate_candidate))


if __name__ == "__main__":
    raise SystemExit(main())
