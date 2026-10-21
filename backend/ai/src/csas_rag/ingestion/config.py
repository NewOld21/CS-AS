"""Registry validation and fail-closed usage policy."""
import fnmatch
import json
import re
from pathlib import Path
from urllib.parse import unquote, urlsplit


class PolicyError(ValueError):
    pass


def load_registry(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data["version"] not in (1, 2):
        raise ValueError("Unsupported registry version")
    sources = data["sources"]
    seen = set()
    for s in sources:
        if not re.fullmatch(r"[a-z0-9-]+", s["id"]) or s["id"] in seen:
            raise ValueError("Invalid or duplicate source id")
        seen.add(s["id"])
        if s["kind"] not in ("github", "mediawiki", "official-docs"):
            raise ValueError("Unsupported source kind")
        if type(s["enabled"]) is not bool:
            raise ValueError("enabled must be boolean")
        for field, low, high in (("max_documents", 1, 10000), ("crawl_depth", 0, 5),
                                 ("request_delay_ms", 0, 60000), ("priority", 0, 3)):
            if type(s.get(field)) is not int or not low <= s[field] <= high:
                raise ValueError(f"Invalid {field}: {s['id']}")
        if s["enabled"]:
            require_approved(s)
    return sources


def require_approved(s: dict) -> None:
    review = s.get("review", {})
    if not (s.get("enabled") is True and s.get("usage_review") == "approved"
            and s.get("storage_policy") == "full-text"
            and s.get("license") and s.get("attribution")
            and all(review.get(k) for k in ("license_url", "terms_url", "robots_url", "reviewed_at"))
            and review.get("body_storage_allowed") is True):
        raise PolicyError("Source requires enabled, approved full-text usage and review evidence")
    if s.get("kind") == "official-docs" and not s.get("version"):
        raise PolicyError("Official documentation requires a reviewed version or snapshot label")


def allowed_url(url: str, scopes: list[str]) -> bool:
    p = urlsplit(url)
    decoded = unquote(p.path)
    if (p.scheme != "https" or p.username or p.password or p.port not in (None, 443)
            or "\\" in decoded or any(x in ("..", ".") for x in decoded.split("/"))):
        return False
    for scope in scopes:
        q = urlsplit(scope)
        base = unquote(q.path).rstrip("/")
        if p.hostname == q.hostname and (decoded == base or decoded.startswith(base + "/")):
            return True
    return False


def document_allowed(s: dict, url: str) -> bool:
    path = unquote(urlsplit(url).path)
    return (allowed_url(url, s.get("allowed_urls", []))
            and (not s.get("include_patterns") or any(fnmatch.fnmatch(path, x) for x in s["include_patterns"]))
            and not any(fnmatch.fnmatch(path, x) for x in s.get("exclude_patterns", [])))
