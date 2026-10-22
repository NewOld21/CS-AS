import io
import json
import sys
import unittest
from email.message import Message
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from csas_rag.providers.http import ProviderError, post_json


class Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return io.BytesIO(json.dumps(self.payload).encode("utf-8"))

    def __exit__(self, *_args):
        return False


def http_error(status, retry_after=None):
    headers = Message()
    if retry_after is not None:
        headers["Retry-After"] = retry_after
    return HTTPError("https://provider.test", status, "failed", headers, None)


class ProviderHttpTests(unittest.TestCase):
    @patch("csas_rag.providers.http.time.sleep")
    @patch("csas_rag.providers.http.urlopen")
    def test_429_is_retried_and_retry_after_is_honored(self, urlopen, sleep):
        urlopen.side_effect = [http_error(429, "0"), Response({"ok": True})]
        self.assertEqual(post_json("https://provider.test", "secret", {}, max_retries=1), {"ok": True})
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(0.0)

    @patch("csas_rag.providers.http.urlopen")
    def test_auth_failure_is_not_retried(self, urlopen):
        urlopen.side_effect = http_error(401)
        with self.assertRaisesRegex(ProviderError, "status 401"):
            post_json("https://provider.test", "invalid", {}, max_retries=2)
        self.assertEqual(urlopen.call_count, 1)

    @patch("csas_rag.providers.http.time.sleep")
    @patch("csas_rag.providers.http.urlopen")
    def test_server_error_and_timeout_use_bounded_retries(self, urlopen, sleep):
        urlopen.side_effect = [http_error(503), TimeoutError("slow"), http_error(503)]
        with self.assertRaises(ProviderError):
            post_json("https://provider.test", "secret", {}, max_retries=2)
        self.assertEqual(urlopen.call_count, 3)
        self.assertEqual(sleep.call_count, 2)


if __name__ == "__main__":
    unittest.main()
