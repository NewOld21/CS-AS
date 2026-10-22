"""Synthetic responses only: no source approval overrides or network requests."""
import json
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from csas_rag.ingestion.collectors import create_collector

FIXTURES = json.loads((Path(__file__).parent / "fixtures/ingestion.json").read_text(encoding="utf-8"))
COMMIT = "a" * 40


def fixture_source(kind="official-docs", language="en"):
    source = {"id": "fixture-" + ("wiki-" + language if kind == "mediawiki" else kind),
              "kind": kind, "enabled": True, "usage_review": "approved", "storage_policy": "full-text",
              "license": "CC0-1.0 (synthetic fixture)", "attribution": "CSAS synthetic test authors",
              "language": language, "priority": 0, "max_documents": 10, "crawl_depth": 0,
              "request_delay_ms": 0, "version": "fixture-v1", "category": "operating-system",
              "base_url": "https://example.org/docs/",
              "review": {"license_url": "https://example.org/license", "terms_url": "https://example.org/terms",
                         "robots_url": "https://example.org/robots.txt", "reviewed_at": "2026-10-21",
                         "body_storage_allowed": True}, "include_patterns": [], "exclude_patterns": [],
              "allowed_urls": ["https://example.org/docs/"], "request_urls": ["https://example.org/"],
              "adapter": "html", "seed_urls": ["https://example.org/docs/memory.html"],
              "concept_mappings": {"https://example.org/docs/memory.html": ["concept:virtual-memory"]}}
    if kind == "github":
        source.update(repository="fixture/cs", revision=COMMIT, include_globs=["CS/*.md"],
                      allowed_urls=["https://github.com/fixture/cs/blob/"],
                      concept_mappings={"CS/deadlock.md": ["concept:deadlock"]})
    if kind == "mediawiki":
        source.update(endpoint="https://example.org/w/api.php", seed_titles=["Deadlock"], seed_categories=[],
                      allowed_urls=["https://example.org/wiki/"], concept_mappings={"42": ["concept:deadlock"]})
    return source


class FixtureClient:
    def __init__(self, source):
        self.source = source
        self.calls = []

    def json(self, url):
        import base64
        self.calls.append(url)
        path = urlsplit(url).path
        if "/commits/" in path:
            return {"sha": COMMIT}
        if "/git/trees/" in path:
            return {"truncated": False, "tree": [{"type": "blob", "path": p, "sha": "b" * 40}
                                                 for p in ("README.md", "CS/README.md", "CS/deadlock.md", "notes.txt")]}
        if "/git/blobs/" in path:
            return {"encoding": "base64", "content": base64.b64encode(FIXTURES["github_markdown"].encode()).decode()}
        params = parse_qs(urlsplit(url).query)
        if params.get("action") == ["parse"]:
            return {"parse": {"text": FIXTURES["wikipedia_" + self.source["language"]],
                              "categories": [{"category": "Operating systems"}],
                              "links": [{"title": "Process"}], "langlinks": [{"lang": "ko", "title": "교착 상태"}]}}
        return {"query": {"pages": [{"pageid": 42, "ns": 0, "title": "Deadlock",
                                      "revisions": [{"revid": 101, "timestamp": "2026-10-21T00:00:00Z"}],
                                      "pageprops": {"wikibase_item": "Q000-fixture"}}]}}

    def check_robots(self, url):
        self.calls.append("robots:" + url)

    def get(self, url):
        self.calls.append(url)
        return FIXTURES["official_html"].encode("utf-8")


def fixture_factory(source):
    return create_collector(source, FixtureClient(source))
