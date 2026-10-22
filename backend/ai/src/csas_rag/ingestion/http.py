"""Bounded HTTP transport. Redirects are rejected before following them."""
import json
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
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
        retries = self.source.get("max_retries", 3)
        for attempt in range(retries + 1):
            request_wait = max(0, self.source["request_delay_ms"] / 1000 - (time.monotonic() - self.last_request))
            if request_wait:
                time.sleep(request_wait)
            self.last_request = time.monotonic()
            try:
                req = Request(url, headers={
                    "User-Agent": "CSAS-Ingestion/1.0 (+https://github.com/NewOld21/CS-AS)",
                    "Accept": "application/json, text/html;q=0.9, text/plain;q=0.8",
                })
                with self.opener.open(req, timeout=self.source.get("timeout_seconds", 15)) as response:
                    body = response.read(4 * 1024 * 1024 + 1)
                    if len(body) > 4 * 1024 * 1024:
                        raise ValueError("Response exceeds 4 MiB")
                    return body
            except (HTTPError, URLError, TimeoutError) as error:
                if isinstance(error, HTTPError) and error.code not in (429, 500, 502, 503, 504):
                    raise
                if attempt == retries:
                    raise
                retry_after = self._retry_after(error) if isinstance(error, HTTPError) else None
                backoff = min(60.0, 2 ** attempt + random.uniform(0, 0.5))
                time.sleep(max(backoff, retry_after or 0))
        raise RuntimeError("Unreachable")

    @staticmethod
    def _retry_after(error: HTTPError):
        value = error.headers.get("Retry-After") if error.headers else None
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            try:
                when = parsedate_to_datetime(value)
                if when.tzinfo is None:
                    when = when.replace(tzinfo=timezone.utc)
                return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
            except (TypeError, ValueError, OverflowError):
                return None

    def json(self, url: str) -> dict:
        return json.loads(self.get(url))

    def check_robots(self, url: str) -> None:
        if self.robots is None:
            robots_url = self.source["review"]["robots_url"]
            self.robots = RobotFileParser()
            self.robots.parse(self.get(robots_url).decode("utf-8").splitlines())
        if not self.robots.can_fetch("CSAS-Ingestion", url):
            raise PolicyError("robots.txt disallows document")
