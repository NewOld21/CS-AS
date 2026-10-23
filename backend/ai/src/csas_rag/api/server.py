"""Authenticated internal RAG HTTP server."""
import json
import secrets
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from csas_rag.generation.answering import GenerationError, RagUnavailable, validate_request
from csas_rag.generation.quiz import validate_quiz_request


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def parse_deadline(value: str) -> datetime:
    try:
        deadline = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise ValueError("Invalid deadline") from error
    if deadline.tzinfo is None:
        raise ValueError("Deadline must include timezone")
    return deadline.astimezone(timezone.utc)


def handler(service, token: str, active_index: str, quiz_service=None):
    class Handler(BaseHTTPRequestHandler):
        server_version = "CSAS-RAG/1"

        def log_message(self, format, *args):
            return

        def send_json(self, status: int, payload: dict):
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def error(self, status: int, request_id: str, code: str, message: str):
            self.send_json(status, {"request_id": request_id, "code": code, "message": message,
                                    "timestamp": utc_now()})

        def do_GET(self):
            if self.path == "/health":
                self.send_json(200, {"status": "UP", "index_version": active_index,
                                    **getattr(service, "runtime_status", {})})
                return
            self.error(404, self.headers.get("X-Request-Id", "unknown"),
                       "NOT_FOUND", "Internal endpoint not found")

        def do_POST(self):
            request_id = self.headers.get("X-Request-Id", "unknown")
            if self.path not in ("/internal/v1/answers", "/internal/v1/quiz-candidates"):
                self.error(404, request_id, "NOT_FOUND", "Internal endpoint not found")
                return
            supplied = self.headers.get("Authorization", "")
            if not secrets.compare_digest(supplied, "Bearer " + token):
                self.error(401, request_id, "SERVICE_UNAUTHORIZED", "Service authentication failed")
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 1 <= length <= 65536:
                    raise ValueError("Invalid content length")
                quiz_request = self.path == "/internal/v1/quiz-candidates"
                validate = validate_quiz_request if quiz_request else validate_request
                data = validate(json.loads(self.rfile.read(length)))
                if data["request_id"] != request_id:
                    raise ValueError("Request id mismatch")
                if data["index_version"] != active_index:
                    self.error(409, request_id, "INDEX_VERSION_UNAVAILABLE", "Requested index is not active")
                    return
                if parse_deadline(data["deadline_at"]) <= datetime.now(timezone.utc):
                    self.error(504, request_id, "DEADLINE_EXCEEDED", "Request deadline exceeded")
                    return
                if quiz_request:
                    if quiz_service is None:
                        raise GenerationError("Quiz service is unavailable")
                    self.send_json(200, quiz_service.generate(data))
                else:
                    self.send_json(200, service.answer(data))
            except (ValueError, json.JSONDecodeError):
                self.error(400, request_id, "INVALID_INPUT", "Invalid answer request")
            except RagUnavailable as error:
                self.error(503, request_id, error.code, "RAG configuration is incomplete")
            except GenerationError:
                self.error(502, request_id, "PROVIDER_FAILED", "RAG provider failed")
            except TimeoutError:
                self.error(504, request_id, "DEADLINE_EXCEEDED", "Request deadline exceeded")
            except Exception:
                self.error(502, request_id, "PROVIDER_FAILED", "RAG service failed")

    return Handler


def serve(service, token: str, active_index: str, host="127.0.0.1", port=8090, quiz_service=None):
    server = ThreadingHTTPServer((host, port), handler(service, token, active_index, quiz_service))
    server.serve_forever()
