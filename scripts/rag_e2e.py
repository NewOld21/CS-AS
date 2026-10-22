#!/usr/bin/env python3
"""Exercise Vue proxy -> Spring -> GMS RAG using a dedicated local test account."""
import argparse
import http.cookiejar
import json
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import HTTPCookieProcessor, Request, build_opener
from uuid import uuid4


class Browser:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def request(self, method: str, path: str, body=None, headers=None):
        data = None if body is None else json.dumps(body).encode("utf-8")
        request = Request(self.base_url + path, data=data, method=method, headers={
            **({"Content-Type": "application/json"} if data else {}), **(headers or {})
        })
        try:
            with self.opener.open(request, timeout=90) as response:
                return response.status, None if response.status == 204 else json.load(response)
        except HTTPError as error:
            try:
                payload = json.load(error)
            except (ValueError, json.JSONDecodeError):
                payload = {"code": "INVALID_ERROR_RESPONSE"}
            return error.code, payload

    def csrf(self) -> str:
        status, body = self.request("GET", "/auth/csrf")
        if status != 200:
            raise RuntimeError("CSRF bootstrap failed")
        return body["token"]

    def post(self, path: str, body: dict, extra_headers=None):
        return self.request("POST", path, body, {
            "X-CSRF-Token": self.csrf(), **(extra_headers or {})
        })


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://frontend:5173/api/v1")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args(argv)
    browser = Browser(args.base_url)
    email = "rag-live-e2e@local.invalid"
    password = "Docker-RAG-E2E-Password-2026"
    signup_status, signup = browser.post("/auth/signup", {
        "email": email, "password": password, "nickname": "RAG E2E"
    })
    if signup_status not in (201, 409):
        raise RuntimeError("Signup failed")
    login_status, _ = browser.post("/auth/login", {"email": email, "password": password})
    if login_status != 200:
        raise RuntimeError("Login failed")
    quiz_id = "10000000-0000-0000-0000-000000000001"
    quiz_status, quiz = browser.request("GET", "/quizzes/" + quiz_id)
    if quiz_status != 200 or len(quiz["options"]) != 4:
        raise RuntimeError("Quiz lookup failed")
    selected = quiz["options"][1]["id"]
    attempt_status, attempt = browser.post(
        "/quizzes/" + quiz_id + "/attempts",
        {"selected_option_id": selected},
        {"Idempotency-Key": str(uuid4())},
    )
    if attempt_status != 200 or attempt["is_correct"] is not False:
        raise RuntimeError("Wrong-answer attempt was not recorded")
    session_status, session = browser.post("/chat/sessions", {
        "quiz_id": quiz_id, "attempt_id": attempt["id"]
    })
    if session_status != 201:
        raise RuntimeError("Context chat creation failed")
    answer_status, answer = browser.post(
        "/chat/sessions/" + session["id"] + "/messages",
        {"question": "왜 틀렸어?"},
        {"Idempotency-Key": str(uuid4())},
    )
    sources = answer.get("sources", []) if isinstance(answer, dict) else []
    passed = (answer_status == 200 and answer.get("status") == "answered" and answer.get("answer")
              and sources and all(source.get("url", "").startswith("https://") for source in sources))
    result = {
        "status": "PASS" if passed else "FAIL",
        "path": "Vue proxy -> Spring Boot -> Python RAG -> ChromaDB/GMS",
        "signup": "created" if signup_status == 201 else "reused",
        "quiz_id": quiz_id,
        "attempt_is_correct": attempt["is_correct"],
        "answer_http_status": answer_status,
        "error_code": answer.get("code") if isinstance(answer, dict) else None,
        "answer_status": answer.get("status") if isinstance(answer, dict) else None,
        "answer": answer.get("answer") if isinstance(answer, dict) else None,
        "sources": sources,
    }
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
