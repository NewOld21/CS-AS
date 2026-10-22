"""Deterministic text extraction, explicit concept mapping and index preparation."""
import hashlib
import re
import unicodedata
from html.parser import HTMLParser
from urllib.parse import urljoin

CHUNK_VERSION = "chars-1200-v1"
PARSER_VERSION = "html-markdown-v2"


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


class HTMLText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.main = []
        self.in_main = 0
        self.skip = 0
        self.links = []
        self.main_links = []
        self.images = []
        self.main_images = []
        self.title = []
        self.in_title = False
        self.heading = None
        self.headings = []
        self.main_headings = []
        self.code_depth = 0
        self.code = []
        self.code_blocks = []
        self.main_code_blocks = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("script", "style", "nav", "footer", "header"):
            self.skip += 1
        if tag in ("main", "article"):
            self.in_main += 1
        if tag == "title":
            self.in_title = True
        if self.skip:
            return
        if re.fullmatch(r"h[1-6]", tag):
            self.heading = []
        if tag in ("pre", "code"):
            if self.code_depth == 0:
                self.code = []
            self.code_depth += 1
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
            if self.in_main:
                self.main_links.append(a["href"])
        if tag == "img" and a.get("src"):
            self.images.append({"url": a["src"], "alt": a.get("alt", "")})
            if self.in_main:
                self.main_images.append({"url": a["src"], "alt": a.get("alt", "")})
        if tag in ("p", "br", "div", "li", "pre", "tr") or re.fullmatch(r"h[1-6]", tag):
            self.handle_data("\n")

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag in ("script", "style", "nav", "footer", "header"):
            self.skip = max(0, self.skip - 1)
        if tag in ("main", "article"):
            self.in_main = max(0, self.in_main - 1)
        if tag == "title":
            self.in_title = False
        if re.fullmatch(r"h[1-6]", tag) and self.heading is not None:
            heading = "".join(self.heading).strip()
            if heading:
                self.headings.append(heading)
                if self.in_main:
                    self.main_headings.append(heading)
            self.heading = None
        if tag in ("pre", "code") and self.code_depth:
            self.code_depth -= 1
            if self.code_depth == 0:
                code = "".join(self.code).strip()
                if code:
                    self.code_blocks.append(code)
                    if self.in_main:
                        self.main_code_blocks.append(code)
        if tag in ("p", "div", "li", "pre") or re.fullmatch(r"h[1-6]", tag):
            self.handle_data("\n")

    def handle_data(self, data):
        if self.in_title:
            self.title.append(data)
        if self.heading is not None:
            self.heading.append(data)
        if self.code_depth:
            self.code.append(data)
        if not self.skip and not self.in_title:
            self.parts.append(data)
            if self.in_main:
                self.main.append(data)


def parse(raw: str, fmt: str, url: str) -> dict:
    if fmt == "html":
        parser = HTMLText()
        parser.feed(raw)
        text = "".join(parser.main or parser.parts)
        links = parser.main_links if parser.main else parser.links
        images = parser.main_images if parser.main else parser.images
        title = "".join(parser.title).strip()
        headings = parser.main_headings if parser.main else parser.headings
        code = parser.main_code_blocks if parser.main else parser.code_blocks
    else:
        text = raw
        headings = re.findall(r"^#{1,6}\s+(.+)$", raw, re.M)
        title = headings[0] if headings else ""
        code = re.findall(r"```[^\n]*\n(.*?)```", raw, re.S)
        links = re.findall(r"(?<!!)\[[^\]]*\]\(([^\s)]+)(?:[^)]*)\)", raw)
        images = [{"alt": a, "url": b} for a, b in re.findall(r"!\[([^\]]*)\]\(([^)]+)\)", raw)]
        text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = unicodedata.normalize("NFC", text.replace("\r\n", "\n").replace("\r", "\n"))
    text = "\n".join(line.rstrip() for line in text.splitlines()).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    if not text:
        raise ValueError("Empty document")
    return {"text": text, "title": title, "headings": headings, "code_blocks": code,
            "links": [urljoin(url, x) for x in links],
            "images": [{**x, "url": urljoin(url, x["url"])} for x in images]}


def normalize(source: dict, item: dict, raw: str) -> dict:
    parsed = parse(raw, item.get("format", "html"), item["url"])
    document_id = "doc:" + digest(source["id"] + ":" + item["key"])
    # Mappings are reviewed by native page/path identity, never inferred from document ids.
    concepts = source.get("concept_mappings", {}).get(item["key"], [])
    if not all(re.fullmatch(r"concept:[a-z0-9-]+", x) for x in concepts):
        raise ValueError("Invalid reviewed concept id")
    revision = str(item["revision"])
    if not revision:
        raise ValueError("Missing revision")
    return {**parsed, "title": item.get("title") or parsed["title"] or item["key"],
            "source_id": source["id"], "document_id": document_id, "revision": revision,
            "url": item["url"], "locator": item["key"], "language": source.get("language", "en"),
            "license": source["license"], "attribution": source["attribution"],
            "version": source.get("version"), "category": source.get("category"),
            "concept_ids": concepts, "content_hash": digest(parsed["text"]),
            "raw_hash": digest(raw), "parser_version": PARSER_VERSION,
            "concept_mapping_version": digest(str(sorted(source.get("concept_mappings", {}).items()))),
            "metadata": item.get("metadata", {})}


def chunks(doc: dict) -> list[dict]:
    result = []
    for ordinal, start in enumerate(range(0, len(doc["text"]), 1200)):
        end = min(start + 1200, len(doc["text"]))
        result.append({"chunk_id": "chunk:" + digest(f"{doc['document_id']}:{doc['revision']}:{PARSER_VERSION}:{CHUNK_VERSION}:{ordinal}"),
                       "source_id": doc["source_id"], "document_id": doc["document_id"],
                       "revision": doc["revision"], "ordinal": ordinal, "text": doc["text"][start:end],
                       "locator": {"path": doc["locator"], "start_char": start, "end_char": end},
                       "chunk_config_version": CHUNK_VERSION, "concept_ids": []})
    return result
