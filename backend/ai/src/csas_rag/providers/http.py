"""Small JSON HTTP client for OpenAI-compatible providers."""
import json
import os
import time
from email.utils import parsedate_to_datetime
from urllib.error import HTTPError
from urllib.request import Request, urlopen


class ProviderError(RuntimeError):
    pass


def _retry_after(value: str | None, fallback: float) -> float:
    if not value:
        return fallback
    try:
        return min(10.0, max(0.0, float(value)))
    except ValueError:
        try:
            delay = parsedate_to_datetime(value).timestamp() - time.time()
            return min(10.0, max(0.0, delay))
        except (TypeError, ValueError, OverflowError):
            return fallback


def post_json(endpoint: str, api_key: str, payload: dict, timeout: float | None = None,
              max_retries: int | None = None) -> dict:
    timeout = timeout or float(os.environ.get("GMS_TIMEOUT_SECONDS", "45"))
    max_retries = max_retries if max_retries is not None else int(os.environ.get("GMS_MAX_RETRIES", "2"))
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(endpoint, data=body, headers={
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }, method="POST")
    for attempt in range(max_retries + 1):
        try:
            with urlopen(request, timeout=timeout) as response:
                result = json.load(response)
            if not isinstance(result, dict):
                raise ProviderError("Provider returned a non-object response")
            return result
        except HTTPError as error:
            retryable = error.code == 429 or 500 <= error.code <= 504
            if not retryable or attempt >= max_retries:
                raise ProviderError(f"Provider HTTP request failed with status {error.code}") from error
            time.sleep(_retry_after(error.headers.get("Retry-After"), 0.5 * (2 ** attempt)))
        except (OSError, ValueError, json.JSONDecodeError) as error:
            if attempt >= max_retries:
                raise ProviderError("Provider request failed") from error
            time.sleep(0.5 * (2 ** attempt))
    raise ProviderError("Provider request failed")
