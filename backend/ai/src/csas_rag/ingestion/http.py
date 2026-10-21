"""Bounded HTTP transport. Redirects are rejected before following them."""
import json
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from urllib.robotparser import RobotFileParser

from .config import PolicyError, allowed_url, require_approved


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise PolicyError("Redirect requires explicit registry review")


class Client:
    def __init__(self, source: dict):
        self.source = source
        self.opener = build_opener(NoRedirect())
        self.last_request = 0.0
        self.robots = None

    def get(self, url: str) -> bytes:
        require_approved(self.source)
        if not allowed_url(url, self.source.get("request_urls", [])):
            raise PolicyError("Request outside registered scope")
        for attempt in range(3):
            time.sleep(max(0, self.source["request_delay_ms"] / 1000 - (time.monotonic() - self.last_request)))
            self.last_request = time.monotonic()
            try:
                req = Request(url, headers={"User-Agent": "CSAS-Ingestion/1.0 (bounded research collector)"})
                with self.opener.open(req, timeout=20) as response:
                    body = response.read(4 * 1024 * 1024 + 1)
                    if len(body) > 4 * 1024 * 1024:
                        raise ValueError("Response exceeds 4 MiB")
                    return body
            except (HTTPError, URLError, TimeoutError) as error:
                if isinstance(error, HTTPError) and error.code not in (429, 500, 502, 503, 504):
                    raise
                if attempt == 2:
                    raise
                time.sleep(2 ** attempt)
        raise RuntimeError("Unreachable")

    def json(self, url: str) -> dict:
        return json.loads(self.get(url))

    def check_robots(self, url: str) -> None:
        if self.robots is None:
            robots_url = self.source["review"]["robots_url"]
            self.robots = RobotFileParser()
            self.robots.parse(self.get(robots_url).decode("utf-8").splitlines())
        if not self.robots.can_fetch("CSAS-Ingestion", url):
            raise PolicyError("robots.txt disallows document")
