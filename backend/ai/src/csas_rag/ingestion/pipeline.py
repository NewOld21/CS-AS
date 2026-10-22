"""Policy gate, failure isolation and bounded source runs."""
import time
import sqlite3
from urllib.error import HTTPError, URLError

from .collectors import create_collector
from .config import PolicyError, document_allowed, require_approved
from .parsing import normalize

RECOVERABLE = (ValueError, KeyError, TypeError, OSError, HTTPError, URLError, sqlite3.Error)


def collect(source: dict, store, limit=None, dry_run=False, retry_failed=False, factory=create_collector) -> dict:
    started = time.monotonic()
    result = {"source_id": source["id"], "documents": 0, "success": 0, "duplicate": 0,
              "changed": 0, "failed": 0, "excluded_policy": 0, "excluded_sources": 0, "last_revision": None}
    try:
        require_approved(source)
    except PolicyError:
        result.update(excluded_sources=1, reason="source_not_approved_for_body_storage", elapsed_seconds=0)
        return result
    cap = min(limit if limit is not None else source["max_documents"], source["max_documents"])
    if cap < 1:
        raise ValueError("limit must be positive")
    if dry_run:
        result.update(reason="dry_run_no_network_or_writes", max_documents=cap, elapsed_seconds=0)
        return result
    try:
        collector = factory(source)
        pending = store.failed(source["id"]) if retry_failed else []
        discovery_retry = any(not x for x in pending)
        if not retry_failed or discovery_retry:
            if hasattr(collector, "ack"):
                state = store.discovery_state(source["id"])
                items = collector.discover(
                    cap, resume_state=state,
                    save_state=lambda value: store.save_discovery_state(source["id"], value),
                )
            else:
                items = collector.discover(cap)
        else:
            items = iter(pending)
        for item in items:
            if result["documents"] >= cap:
                break
            result["documents"] += 1
            acknowledged = item
            try:
                if not document_allowed(source, item["url"]):
                    raise PolicyError("Document outside registered scope")
                if store.known(source, item):
                    result["duplicate"] += 1
                    result["last_revision"] = str(item["revision"])
                    store.clear_failure(source["id"], item["key"])
                    continue
                fetched, raw = collector.fetch(item)
                acknowledged = fetched
                if not document_allowed(source, fetched["url"]):
                    raise PolicyError("Fetched document outside registered scope")
                store.stage_raw(raw)
                doc = normalize(source, fetched, raw)
                status = store.save(doc, raw)
                result[status] += 1
                result["last_revision"] = doc["revision"]
                store.clear_failure(source["id"], item["key"])
            except PolicyError:
                result["excluded_policy"] += 1
                store.fail(source["id"], item, "policy")
            except RECOVERABLE as error:
                result["failed"] += 1
                store.fail(source["id"], item, type(error).__name__)
            finally:
                if hasattr(collector, "ack"):
                    collector.ack(acknowledged)
        store.clear_failure(source["id"], "__discovery__")
        # A partial run never advances the source checkpoint past failed documents.
        if not store.failed(source["id"]) and result["last_revision"]:
            store.checkpoint(source["id"], result["last_revision"])
    except RECOVERABLE as error:
        result["failed"] += 1
        result["reason"] = type(error).__name__
        store.fail(source["id"], {}, type(error).__name__)
    result["last_revision"] = store.last_revision(source["id"])
    state = store.discovery_state(source["id"]) if store else None
    if state:
        result["discovery_run_id"] = state["run_id"]
        result["discovery_complete"] = state["complete"]
    result["elapsed_seconds"] = round(time.monotonic() - started, 3)
    return result
