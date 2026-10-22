import contextlib
import io
import json
import tempfile
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlsplit

from support import COMMIT, FIXTURES, FixtureClient, fixture_factory, fixture_source
from csas_rag.ingestion.cli import main
from csas_rag.ingestion.collectors import create_collector
from csas_rag.ingestion.config import PolicyError, allowed_url, load_registry
from csas_rag.ingestion.http import Client, NoRedirect
from csas_rag.ingestion.parsing import chunks, digest, normalize, parse
from csas_rag.ingestion.pipeline import collect
from csas_rag.ingestion.storage import Store


class IngestionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / "store")

    def tearDown(self):
        self.store.close()
        self.temp.cleanup()

    def test_four_collectors_normalize_and_preserve_metadata(self):
        for source in (fixture_source("github"), fixture_source("mediawiki", "ko"),
                       fixture_source("mediawiki", "en"), fixture_source()):
            result = collect(source, self.store, factory=fixture_factory)
            self.assertEqual((result["success"], result["failed"]), (1, 0))
        manifest = self.store.manifest("fixture-registry")
        self.assertEqual(len(manifest["documents"]), 4)
        for row in manifest["documents"]:
            obj = json.loads((self.store.root / row["object_path"]).read_text(encoding="utf-8"))
            doc = obj["document"]
            self.assertTrue(doc["license"] and doc["url"] and doc["fetched_at"])
            self.assertTrue((self.store.root / doc["raw_uri"]).is_file())
            self.assertEqual(len(obj["chunks"]), 1)
            self.assertTrue(doc["concept_ids"])
            self.assertEqual(obj["chunks"][0]["concept_ids"], [])
            if doc["source_id"] == "fixture-github":
                self.assertEqual(doc["revision"], COMMIT)
                self.assertEqual(doc["code_blocks"], ["lock.acquire()\n"])
                self.assertTrue(doc["images"] and doc["links"])
            if "wiki" in doc["source_id"]:
                self.assertEqual(doc["revision"], "101")
                self.assertEqual(doc["metadata"]["wikidata_id"], "Q000-fixture")

    def test_repeat_is_idempotent_and_github_skips_blob(self):
        source = fixture_source("github")
        client = FixtureClient(source)
        factory = lambda s: create_collector(s, client)
        collect(source, self.store, factory=factory)
        first = self.store.manifest("x")["corpus_digest"]
        client.calls.clear()
        result = collect(source, self.store, factory=factory)
        self.assertEqual(result["duplicate"], 1)
        self.assertFalse(any("/git/blobs/" in c for c in client.calls))
        self.assertEqual(first, self.store.manifest("x")["corpus_digest"])

    def test_changed_revision_preserves_history(self):
        source = fixture_source()
        item = {"key": "key", "url": source["seed_urls"][0], "revision": "1", "format": "markdown"}
        first = normalize(source, item, "# Topic\nfirst")
        self.assertEqual(self.store.save(first, "# Topic\nfirst"), "success")
        second = normalize(source, {**item, "revision": "2"}, "# Topic\nsecond")
        self.assertEqual(self.store.save(second, "# Topic\nsecond"), "changed")
        self.assertEqual(first["document_id"], second["document_id"])
        self.assertNotEqual(chunks(first)[0]["chunk_id"], chunks(second)[0]["chunk_id"])
        self.assertEqual(len(self.store.manifest("x")["documents"]), 2)

    def test_immutable_revision_conflict(self):
        source = fixture_source()
        item = {"key": "k", "url": source["seed_urls"][0], "revision": "1", "format": "markdown"}
        self.store.save(normalize(source, item, "first"), "first")
        with self.assertRaisesRegex(ValueError, "Immutable"):
            self.store.save(normalize(source, item, "second"), "second")

    def test_equal_content_keeps_separate_provenance(self):
        source = fixture_source()
        for key in ("one", "two"):
            item = {"key": key, "url": source["seed_urls"][0], "revision": "1", "format": "markdown"}
            self.store.save(normalize(source, item, "Same explanation"), "Same explanation")
        self.assertEqual(len(self.store.manifest("x")["documents"]), 2)

    def test_approval_gate_never_constructs_collector(self):
        source = fixture_source()
        for updates in ({"enabled": False}, {"usage_review": "pending"}, {"storage_policy": "metadata-only"},
                        {"license": None}, {"review": {}}):
            with patch("csas_rag.ingestion.http.Client.get", side_effect=AssertionError("network")):
                result = collect({**source, **updates}, self.store, factory=lambda s: self.fail("collector created"))
            self.assertEqual(result["excluded_sources"], 1)
            self.assertEqual(result["documents"], 0)

    def test_dry_run_no_fetch_or_writes(self):
        result = collect(fixture_source(), None, dry_run=True, factory=lambda s: self.fail("network"))
        self.assertEqual(result["max_documents"], 10)

    def test_url_scope_and_encoded_traversal(self):
        scopes = ["https://example.org/docs/"]
        for url in ("http://example.org/docs/a", "https://example.org.evil/docs/a", "https://example.org/docs-evil/a",
                    "https://example.org/docs/%2e%2e/private", "https://example.org/docs/%5cprivate",
                    "https://user@example.org/docs/a", "https://example.org:8443/docs/a"):
            self.assertFalse(allowed_url(url, scopes), url)
        self.assertTrue(allowed_url("https://example.org/docs/a?x=1", scopes))

    def test_redirect_rejected_before_following(self):
        with self.assertRaises(PolicyError):
            NoRedirect().redirect_request(None, None, 302, "", {}, "https://elsewhere.org/")

    def test_max_documents_and_crawl_depth(self):
        source = fixture_source()
        source["crawl_depth"] = 2
        source["max_documents"] = 1
        source["seed_urls"] += ["https://example.org/docs/extra.html"]
        result = collect(source, self.store, limit=100, factory=fixture_factory)
        self.assertEqual(result["documents"], 1)

    def test_bounded_official_link_discovery(self):
        source = fixture_source()
        source["crawl_depth"] = 1
        result = collect(source, self.store, limit=2, factory=fixture_factory)
        self.assertEqual((result["documents"], result["success"]), (2, 2))

    def test_html_removes_navigation_preserves_code_and_korean(self):
        doc = parse(FIXTURES["official_html"], "html", "https://example.org/docs/memory.html")
        self.assertNotIn("Navigation noise", doc["text"])
        self.assertNotIn("Footer noise", doc["text"])
        self.assertIn("allocate(page)", doc["text"])
        self.assertIn("교착", parse(FIXTURES["wikipedia_ko"], "html", "https://example.org/")["text"])

    def test_failure_is_persistent_retry_succeeds(self):
        source = fixture_source()
        class Broken(FixtureClient):
            def get(self, url):
                raise URLError("unavailable")
        result = collect(source, self.store, factory=lambda s: create_collector(s, Broken(s)))
        self.assertEqual(result["failed"], 1)
        self.assertIsNone(result["last_revision"])
        self.assertEqual(len(self.store.failed(source["id"])), 1)
        result = collect(source, self.store, retry_failed=True, factory=fixture_factory)
        self.assertEqual(result["success"], 1)
        self.assertEqual(self.store.failed(source["id"]), [])

    def test_discovery_failure_retry(self):
        source = fixture_source("github")
        class Broken(FixtureClient):
            def json(self, url):
                raise URLError("unavailable")
        self.assertEqual(collect(source, self.store, factory=lambda s: create_collector(s, Broken(s)))["failed"], 1)
        self.assertEqual(collect(source, self.store, retry_failed=True, factory=fixture_factory)["success"], 1)

    def test_failure_does_not_block_next_source(self):
        first = fixture_source()
        second = fixture_source("github")
        class Broken(FixtureClient):
            def get(self, url):
                raise ValueError("invalid response")
        reports = [collect(first, self.store, factory=lambda s: create_collector(s, Broken(s))),
                   collect(second, self.store, factory=fixture_factory)]
        self.assertEqual((reports[0]["failed"], reports[1]["success"]), (1, 1))

    def test_robots_disallow_is_policy_exclusion(self):
        source = fixture_source()
        class Blocked(FixtureClient):
            def check_robots(self, url):
                raise PolicyError("robots")
        result = collect(source, self.store, factory=lambda s: create_collector(s, Blocked(s)))
        self.assertEqual((result["excluded_policy"], result["success"]), (1, 0))

    def test_http_retries_are_bounded(self):
        source = fixture_source()
        source["max_retries"] = 2
        client = Client(source)
        with patch.object(client.opener, "open", side_effect=URLError("down")) as request, patch("time.sleep"):
            with self.assertRaises(URLError):
                client.get("https://example.org/docs/a")
        self.assertEqual(request.call_count, 3)

    def test_http_429_honors_retry_after_and_timeout(self):
        source = fixture_source()
        source.update(max_retries=1, timeout_seconds=9)
        client = Client(source)
        headers = Message()
        headers["Retry-After"] = "7"
        error = HTTPError("https://example.org/docs/a", 429, "limited", headers, None)

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def read(self, _):
                return b"ok"

        with patch.object(client.opener, "open", side_effect=[error, Response()]) as request, \
                patch("csas_rag.ingestion.http.random.uniform", return_value=0.25), \
                patch("csas_rag.ingestion.http.time.sleep") as sleep:
            self.assertEqual(client.get("https://example.org/docs/a"), b"ok")
        self.assertEqual(request.call_count, 2)
        self.assertTrue(all(call.kwargs["timeout"] == 9 for call in request.call_args_list))
        sleep.assert_any_call(7.0)

    def test_http_non_retryable_4xx_is_not_retried(self):
        client = Client(fixture_source())
        error = HTTPError("https://example.org/docs/a", 403, "forbidden", Message(), None)
        with patch.object(client.opener, "open", side_effect=error) as request:
            with self.assertRaises(HTTPError):
                client.get("https://example.org/docs/a")
        self.assertEqual(request.call_count, 1)

    def test_http_timeout_is_retried_with_a_bound(self):
        source = fixture_source()
        source["max_retries"] = 1
        client = Client(source)
        with patch.object(client.opener, "open", side_effect=TimeoutError("timed out")) as request, \
                patch("csas_rag.ingestion.http.time.sleep"):
            with self.assertRaises(TimeoutError):
                client.get("https://example.org/docs/a")
        self.assertEqual(request.call_count, 2)

    def test_http_checks_scope_before_request(self):
        client = Client(fixture_source())
        with patch.object(client.opener, "open") as request:
            with self.assertRaises(PolicyError):
                client.get("https://outside.example/docs/a")
        request.assert_not_called()

    def test_github_truncated_tree_rejected(self):
        source = fixture_source("github")
        client = FixtureClient(source)
        original = client.json
        client.json = lambda url: {"truncated": True} if "/trees/" in url else original(url)
        self.assertEqual(collect(source, self.store, factory=lambda s: create_collector(s, client))["failed"], 1)

    def test_registry_keeps_all_sources_pending_and_ossu_absent(self):
        path = Path(__file__).resolve().parents[3] / "docs/data-sources.json"
        sources = load_registry(path)
        self.assertGreaterEqual(len(sources), 80)
        self.assertFalse(any(s["enabled"] or s["usage_review"] != "pending" for s in sources))
        self.assertFalse(any("ossu" in json.dumps(s).lower() for s in sources))
        self.assertTrue(all((s["max_retries"], s["timeout_seconds"]) == (3, 15) for s in sources))
        self.assertEqual({s["kind"] for s in sources}, {"github", "mediawiki", "official-docs"})

    def test_registry_rejects_ossu_source(self):
        path = self.root / "ossu.json"
        source = fixture_source("github")
        source["id"] = "ossu-courses"
        path.write_text(json.dumps({"version": 2, "defaults": {"max_retries": 3,
                                                                 "timeout_seconds": 15},
                                    "sources": [source]}), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "outside"):
            load_registry(path)

    def test_cli_pending_and_dry_run_do_not_create_catalog(self):
        path = Path(__file__).resolve().parents[3] / "docs/data-sources.json"
        output = self.root / "not-created"
        with contextlib.redirect_stdout(io.StringIO()) as stdout:
            self.assertEqual(main(["collect", "--registry", str(path), "--output", str(output), "--sample"]), 0)
        self.assertFalse(output.exists())
        self.assertTrue(all(r["excluded_sources"] == 1 for r in json.loads(stdout.getvalue())["sources"]))

    def test_registry_rejects_enabled_pending(self):
        path = self.root / "bad.json"
        source = fixture_source()
        source["usage_review"] = "pending"
        path.write_text(json.dumps({"version": 2, "sources": [source]}), encoding="utf-8")
        with self.assertRaises(PolicyError):
            load_registry(path)

    def test_wikipedia_uses_revision_pinned_parse(self):
        source = fixture_source("mediawiki")
        client = FixtureClient(source)
        collect(source, self.store, factory=lambda s: create_collector(s, client))
        self.assertTrue(any("oldid=101" in url for url in client.calls))

    def test_wikipedia_category_expansion_has_depth_and_document_cap(self):
        source = fixture_source("mediawiki")
        source.update(seed_titles=[], seed_categories=["Category:CS"], crawl_depth=0)
        class CategoryClient(FixtureClient):
            def json(self, url):
                if "categorymembers" in url:
                    self.calls.append(url)
                    return {"query": {"categorymembers": [{"ns": 0, "title": "Deadlock"},
                                                             {"ns": 14, "title": "Category:child"}]}}
                return super().json(url)
        client = CategoryClient(source)
        result = collect(source, self.store, limit=1, factory=lambda s: create_collector(s, client))
        self.assertEqual(result["success"], 1)
        self.assertEqual(sum("categorymembers" in url for url in client.calls), 1)

    def test_wikipedia_category_pagination_bfs_deduplicates_and_excludes(self):
        source = fixture_source("mediawiki")
        source.update(seed_titles=[], seed_categories=["Category:CS"], crawl_depth=1,
                      excluded_categories=["Category:Blocked*"])

        class CategoryClient(FixtureClient):
            def json(self, url):
                params = parse_qs(urlsplit(url).query)
                if params.get("list") != ["categorymembers"]:
                    return super().json(url)
                self.calls.append(url)
                category = params["cmtitle"][0]
                if category == "Category:CS" and "cmcontinue" not in params:
                    return {"continue": {"continue": "-||", "cmcontinue": "next"}, "query": {
                        "categorymembers": [{"pageid": 1, "ns": 0, "title": "One"},
                                            {"pageid": 10, "ns": 14, "title": "Category:Child"},
                                            {"pageid": 11, "ns": 14, "title": "Category:Blocked people"}]}}
                if category == "Category:CS":
                    return {"query": {"categorymembers": [{"pageid": 1, "ns": 0, "title": "One"},
                                                               {"pageid": 2, "ns": 0, "title": "Two"}]}}
                return {"query": {"categorymembers": [{"pageid": 3, "ns": 0, "title": "Three"},
                                                           {"pageid": 12, "ns": 14, "title": "Category:Too deep"}]}}

        saved = []
        collector = create_collector(source, CategoryClient(source))
        found = []
        for item in collector.discover(10, save_state=lambda state: saved.append(state)):
            found.append(item["title"])
            collector.ack(item)
        self.assertEqual(found, ["One", "Two", "Three"])
        self.assertTrue(saved[-1]["complete"])
        self.assertEqual(saved[-1]["processed_document_ids"], ["1", "2", "3"])
        calls = collector.client.calls
        self.assertTrue(any("cmcontinue=next" in url for url in calls))
        self.assertTrue(any("Category%3AChild" in url for url in calls))
        self.assertFalse(any("Blocked" in url or "Too+deep" in url for url in calls))

    def test_wikipedia_discovery_resumes_from_persisted_continuation(self):
        source = fixture_source("mediawiki")
        source.update(seed_titles=[], seed_categories=["Category:CS"], crawl_depth=0,
                      excluded_categories=[])

        class Interrupted(FixtureClient):
            def json(self, url):
                params = parse_qs(urlsplit(url).query)
                if params.get("list") != ["categorymembers"]:
                    return super().json(url)
                self.calls.append(url)
                if "cmcontinue" in params:
                    raise URLError("interrupted")
                return {"continue": {"continue": "-||", "cmcontinue": "resume-token"},
                        "query": {"categorymembers": [{"pageid": 1, "ns": 0, "title": "One"}]}}

        first = create_collector(source, Interrupted(source))
        with self.assertRaises(URLError):
            for item in first.discover(10, save_state=lambda state: self.store.save_discovery_state(
                    source["id"], state)):
                first.ack(item)
        saved = self.store.discovery_state(source["id"])
        run_id = saved["run_id"]
        self.assertEqual(saved["continuation"]["cmcontinue"], "resume-token")

        class Resumed(FixtureClient):
            def json(self, url):
                params = parse_qs(urlsplit(url).query)
                if params.get("list") == ["categorymembers"]:
                    self.calls.append(url)
                    self.assert_resume = params.get("cmcontinue") == ["resume-token"]
                    return {"query": {"categorymembers": [{"pageid": 2, "ns": 0, "title": "Two"}]}}
                return super().json(url)

        client = Resumed(source)
        resumed = create_collector(source, client)
        titles = []
        for item in resumed.discover(10, resume_state=saved,
                                     save_state=lambda state: self.store.save_discovery_state(source["id"], state)):
            titles.append(item["title"])
            resumed.ack(item)
        self.assertEqual(titles, ["Two"])
        self.assertTrue(client.assert_resume)
        final = self.store.discovery_state(source["id"])
        self.assertEqual(final["run_id"], run_id)
        self.assertTrue(final["complete"])

    def test_sitemap_does_not_follow_unregistered_urls(self):
        source = fixture_source()
        source.update(adapter="sitemap", sitemap_url="https://example.org/sitemap.xml", seed_urls=[])
        class SitemapClient(FixtureClient):
            def get(self, url):
                if url.endswith(".xml"):
                    return b'<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://evil.org/a</loc></url><url><loc>https://example.org/docs/a</loc></url></urlset>'
                return super().get(url)
        result = collect(source, self.store, factory=lambda s: create_collector(s, SitemapClient(s)))
        self.assertEqual((result["documents"], result["success"]), (1, 1))

    def test_rfc_preserves_status_without_claiming_current(self):
        source = fixture_source()
        source.update(adapter="rfc", format="markdown", seed_urls=["https://example.org/docs/rfc123.txt"])
        class RFCClient(FixtureClient):
            def get(self, url):
                return b'RFC 123\nCategory: Experimental\nObsoletes: 100\nUpdates: 101\nProtocol text.'
        collect(source, self.store, factory=lambda s: create_collector(s, RFCClient(s)))
        row = self.store.manifest("x")["documents"][0]
        doc = json.loads((self.store.root / row["object_path"]).read_text())["document"]
        self.assertEqual(doc["metadata"]["status"], ["Experimental"])
        self.assertFalse(doc["metadata"]["current_status_verified"])

    def test_changed_mapping_requires_new_staging_catalog(self):
        source = fixture_source("github")
        collect(source, self.store, factory=fixture_factory)
        source["concept_mappings"] = {"CS/deadlock.md": ["concept:resource-lock"]}
        result = collect(source, self.store, factory=fixture_factory)
        self.assertEqual((result["failed"], result["duplicate"]), (1, 0))

    def test_raw_is_preserved_before_parser_failure(self):
        source = fixture_source()
        class Empty(FixtureClient):
            def get(self, url):
                return b'<main></main>'
        result = collect(source, self.store, factory=lambda s: create_collector(s, Empty(s)))
        self.assertEqual(result["failed"], 1)
        self.assertEqual(len(list((self.store.root / "raw").glob("*.txt"))), 1)
        self.assertEqual(self.store.manifest("x")["documents"], [])

    def test_manifest_exports_committed_normalized_and_chunk_jsonl(self):
        source = fixture_source("github")
        collect(source, self.store, factory=fixture_factory)
        self.store.manifest("registry-hash")
        normalized = [json.loads(line) for line in (self.store.root / "normalized.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()]
        exported_chunks = [json.loads(line) for line in (self.store.root / "chunks.jsonl").read_text(
            encoding="utf-8"
        ).splitlines()]
        self.assertEqual(len(normalized), 1)
        self.assertEqual(normalized[0]["source_id"], source["id"])
        self.assertTrue(normalized[0]["source_url"].endswith("/CS/deadlock.md"))
        self.assertEqual(normalized[0]["content_hash"], digest(normalized[0]["content"]))
        self.assertEqual(exported_chunks[0]["document_id"], normalized[0]["document_id"])


if __name__ == "__main__":
    unittest.main()
