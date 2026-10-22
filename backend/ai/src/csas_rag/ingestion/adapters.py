"""Reusable extraction adapters for reviewed official documentation sources."""
import re
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urljoin
from xml.etree import ElementTree

from .parsing import HTMLText


@dataclass(frozen=True)
class ExtractedContent:
    raw: str
    format: str
    links: list[str]
    metadata: dict


class ContentAdapter(Protocol):
    def extract(self, raw: str, url: str) -> ExtractedContent: ...


class HTMLAdapter:
    def extract(self, raw: str, url: str) -> ExtractedContent:
        parser = HTMLText()
        parser.feed(raw)
        links = parser.main_links if parser.main else parser.links
        headings = parser.main_headings if parser.main else parser.headings
        return ExtractedContent(raw, "html", [urljoin(url, link) for link in links],
                                {"adapter": "html", "extracted_title": "".join(parser.title).strip(),
                                 "extracted_headings": headings})


class MarkdownAdapter:
    def extract(self, raw: str, url: str) -> ExtractedContent:
        headings = re.findall(r"^#{1,6}\s+(.+)$", raw, re.M)
        frontmatter = re.search(r"\A---\s*\n.*?^title:\s*[\"']?([^\n\"']+)", raw, re.M | re.S)
        title = frontmatter.group(1).strip() if frontmatter else (headings[0] if headings else "")
        links = [urljoin(url, link) for link in re.findall(
            r"(?<!!)\[[^\]]*\]\(([^\s)]+)(?:[^)]*)\)", raw
        )]
        return ExtractedContent(raw, "markdown", links,
                                {"adapter": "markdown", "extracted_title": title,
                                 "extracted_headings": headings})


class RFCAdapter(MarkdownAdapter):
    def extract(self, raw: str, url: str) -> ExtractedContent:
        extracted = super().extract(raw, url)
        title = re.search(r"\n\s*([^\n]+?)\s*\n\s*\nAbstract\s*\n", raw)
        metadata = {**extracted.metadata,
                    "adapter": "rfc",
                    "extracted_title": title.group(1).strip() if title else extracted.metadata["extracted_title"],
                    "rfc_number": re.findall(r"rfc(\d+)", url, re.I),
                    "status": re.findall(r"(?:Category|Status):\s*([^\n<]+)", raw),
                    "obsoletes": re.findall(r"Obsoletes:\s*([^\n<]+)", raw),
                    "updates": re.findall(r"Updates:\s*([^\n<]+)", raw),
                    "current_status_verified": False}
        return ExtractedContent(extracted.raw, extracted.format, extracted.links, metadata)


class SitemapAdapter:
    """Parse one reviewed urlset; sitemap indexes stay fail-closed."""

    def urls(self, raw: bytes) -> list[str]:
        root = ElementTree.fromstring(raw)
        if root.tag.rsplit("}", 1)[-1] != "urlset":
            raise ValueError("Only explicit urlset sitemaps supported")
        return [node.text.strip() for node in root.findall("{*}url/{*}loc") if node.text]


def content_adapter(name: str) -> ContentAdapter:
    adapters = {
        "html": HTMLAdapter,
        "markdown": MarkdownAdapter,
        "sitemap": HTMLAdapter,
        "rfc": RFCAdapter,
    }
    if name not in adapters:
        raise ValueError("Unregistered official adapter")
    return adapters[name]()
