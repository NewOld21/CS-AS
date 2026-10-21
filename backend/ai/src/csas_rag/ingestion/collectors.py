"""Source-specific discovery/fetch adapters. All traversal is bounded."""
import base64
import fnmatch
import re
from collections import deque
from typing import Protocol
from urllib.parse import quote, urlencode, urljoin, urlsplit
from xml.etree import ElementTree

from .config import PolicyError, document_allowed, require_approved
from .http import Client
from .parsing import HTMLText, digest


class Collector(Protocol):
    def discover(self, limit: int): ...
    def fetch(self, item: dict) -> tuple[dict, str]: ...


class GitHubCollector:
    def __init__(self, source: dict, client: Client):
        self.s, self.client = source, client
        self.api = "https://api.github.com/repos/" + source["repository"]

    def discover(self, limit: int):
        require_approved(self.s)
        ref = self.s.get("revision") or "HEAD"
        commit = self.client.json(self.api + "/commits/" + quote(ref, safe=""))
        sha = commit["sha"]
        if not re.fullmatch(r"[a-f0-9]{40}", sha):
            raise ValueError("Invalid commit SHA")
        tree = self.client.json(self.api + f"/git/trees/{sha}?recursive=1")
        if tree.get("truncated"):
            raise ValueError("Truncated GitHub tree; narrow source before collecting")
        count = 0
        for entry in tree["tree"]:
            path = entry["path"]
            name = path.rsplit("/", 1)[-1].lower()
            if (entry["type"] != "blob" or not path.lower().endswith(".md")
                    or name in ("readme.md", "contributing.md", "license.md", "index.md")
                    or not any(fnmatch.fnmatch(path, p) for p in self.s["include_globs"])
                    or any(fnmatch.fnmatch(path, p) for p in self.s.get("exclude_globs", []))):
                continue
            url = f"https://github.com/{self.s['repository']}/blob/{sha}/{quote(path)}"
            if not document_allowed(self.s, url):
                continue
            yield {"key": path, "url": url, "revision": sha, "blob_sha": entry["sha"],
                   "format": "markdown", "metadata": {"commit_sha": sha, "file_path": path,
                                                         "topic_path": path.split("/")[:-1]}}
            count += 1
            if count >= limit:
                break

    def fetch(self, item: dict):
        data = self.client.json(self.api + "/git/blobs/" + quote(item["blob_sha"], safe=""))
        if data.get("encoding") != "base64":
            raise ValueError("Unsupported GitHub blob encoding")
        return item, base64.b64decode(data["content"]).decode("utf-8")


class WikipediaCollector:
    def __init__(self, source: dict, client: Client):
        self.s, self.client = source, client

    def query(self, **params):
        data = self.client.json(self.s["endpoint"] + "?" + urlencode({"format": "json", "formatversion": 2, **params}))
        if "error" in data:
            raise ValueError("MediaWiki API error: " + data["error"]["code"])
        return data

    def discover(self, limit: int):
        require_approved(self.s)
        titles = list(self.s.get("seed_titles", []))[:limit]
        # Category expansion has a separate bound; no related-page traversal.
        queue = deque((x, 0) for x in self.s.get("seed_categories", [])[:limit])
        seen = set()
        while queue and len(titles) < limit and len(seen) < limit:
            category, depth = queue.popleft()
            if category in seen:
                continue
            seen.add(category)
            data = self.query(action="query", list="categorymembers", cmtitle=category,
                              cmlimit=min(500, limit - len(titles)), cmtype="page|subcat")
            for member in data["query"]["categorymembers"]:
                if member["ns"] == 0:
                    titles.append(member["title"])
                elif member["ns"] == 14 and depth < self.s["crawl_depth"]:
                    queue.append((member["title"], depth + 1))
        origin = "https://" + urlsplit(self.s["endpoint"]).hostname
        for title in list(dict.fromkeys(titles))[:limit]:
            url = origin + "/wiki/" + quote(title.replace(" ", "_"))
            if document_allowed(self.s, url):
                yield {"key": title, "title": title, "url": url, "format": "html"}

    def fetch(self, item: dict):
        data = self.query(action="query", titles=item["title"], prop="revisions|pageprops",
                          rvprop="ids|timestamp", rvlimit=1, ppprop="wikibase_item")
        page = data["query"]["pages"][0]
        if "missing" in page or page.get("ns", 0) != 0:
            raise ValueError("Missing or non-article Wikipedia page")
        rev = page["revisions"][0]
        parsed = self.query(action="parse", oldid=rev["revid"], prop="text|categories|links|langlinks", disableeditsection=1)["parse"]
        body = parsed["text"]
        if not isinstance(body, str):
            body = body["*"]
        return {**item, "key": str(page["pageid"]), "revision": str(rev["revid"]),
                "metadata": {"page_id": page["pageid"], "updated_at": rev["timestamp"],
                             "seed_title": item["title"], "wikidata_id": page.get("pageprops", {}).get("wikibase_item"),
                             "categories": parsed.get("categories", []), "related_documents": parsed.get("links", []),
                             "langlinks": parsed.get("langlinks", []),
                             "history_url": item["url"] + "?action=history"}}, body


class OfficialCollector:
    """Explicit HTML/Markdown seeds or a bounded sitemap, with per-site parser adapters."""

    def __init__(self, source: dict, client: Client):
        self.s, self.client = source, client

    def discover(self, limit: int):
        require_approved(self.s)
        queue = deque((url, 0) for url in self.s.get("seed_urls", [])[:limit])
        if self.s.get("adapter") == "sitemap":
            sitemap = self.s["sitemap_url"]
            self.client.check_robots(sitemap)
            root = ElementTree.fromstring(self.client.get(sitemap))
            # Sitemap indexes are deliberately not recursively followed.
            if root.tag.rsplit("}", 1)[-1] != "urlset":
                raise ValueError("Only explicit urlset sitemaps supported")
            for node in root.findall("{*}url/{*}loc"):
                if node.text and document_allowed(self.s, node.text):
                    queue.append((node.text, 0))
                if len(queue) >= limit:
                    break
        seen = set()
        while queue and len(seen) < limit:
            url, depth = queue.popleft()
            if url in seen or not document_allowed(self.s, url):
                continue
            seen.add(url)
            item = {"key": url, "url": url, "format": self.s.get("format", "html"), "depth": depth}
            yield item
            # fetch is performed by the runner before resuming this generator.
            for link in item.get("discovered_links", []):
                if depth < self.s["crawl_depth"] and len(queue) < limit:
                    queue.append((link, depth + 1))

    def fetch(self, item: dict):
        self.client.check_robots(item["url"])
        raw = self.client.get(item["url"]).decode("utf-8")
        parser = HTMLText()
        if item["format"] == "html":
            parser.feed(raw)
        item["discovered_links"] = [urljoin(item["url"], x).split("#")[0] for x in parser.links
                                    if document_allowed(self.s, urljoin(item["url"], x))]
        adapter = self.s.get("adapter", "html")
        if adapter not in ("html", "markdown", "sitemap", "rfc"):
            raise ValueError("Unregistered official adapter")
        metadata = {}
        if adapter == "rfc":
            # Preserve evidence without guessing present-day standard status.
            metadata = {"rfc_number": re.findall(r"rfc(\d+)", item["url"], re.I),
                        "status": re.findall(r"(?:Category|Status):\s*([^\n<]+)", raw),
                        "obsoletes": re.findall(r"Obsoletes:\s*([^\n<]+)", raw),
                        "updates": re.findall(r"Updates:\s*([^\n<]+)", raw),
                        "current_status_verified": False}
        return {**item, "revision": digest(raw), "metadata": metadata}, raw


def create_collector(source: dict, client=None) -> Collector:
    require_approved(source)
    adapters = {"github": GitHubCollector, "mediawiki": WikipediaCollector, "official-docs": OfficialCollector}
    if source["kind"] == "official-docs" and source.get("adapter") == "github":
        return GitHubCollector(source, client or Client(source))
    return adapters[source["kind"]](source, client or Client(source))
