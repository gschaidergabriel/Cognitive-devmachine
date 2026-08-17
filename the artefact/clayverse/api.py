from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .adapters import AuthenticationError, ClerkTokenVerifier


class ClayVerseAPI:
    def __init__(self, engine: Any, verifier: ClerkTokenVerifier, *, max_body: int = 1_000_000):
        self.engine = engine
        self.verifier = verifier
        self.max_body = max_body

    def handler(self):
        runtime = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "ClayVerse/0.1"

            def log_message(self, format, *args):
                return

            def _send(self, status: int, payload: Any, content_type: str = "application/json; charset=utf-8"):
                body = payload.encode() if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False).encode()
                self.send_response(status)
                self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _claims(self):
                token = runtime.verifier.bearer(self.headers.get("Authorization"))
                return runtime.verifier.verify(token)

            def _json_body(self):
                size = int(self.headers.get("Content-Length", "0") or "0")
                if size <= 0 or size > runtime.max_body:
                    raise ValueError("invalid request body size")
                return json.loads(self.rfile.read(size))

            def do_GET(self):
                if self.path == "/healthz":
                    return self._send(HTTPStatus.OK, {"ok": True, "service": "clayverse"})
                if self.path == "/":
                    return self._send(HTTPStatus.OK, "ClayVerse web boundary is running. Clerk-authenticated API: POST /api/chat\n", "text/plain; charset=utf-8")
                if self.path == "/api/status":
                    try:
                        claims = self._claims()
                        return self._send(HTTPStatus.OK, {"ok": True, "clerk_subject": claims["sub"]})
                    except AuthenticationError:
                        return self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                return self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def do_POST(self):
                if self.path != "/api/chat":
                    return self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})
                try:
                    claims = self._claims()
                    body = self._json_body()
                    content = str(body.get("content", "")).strip()
                    if not content or len(content) > 100_000:
                        return self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid_content"})
                    resources = body.get("resources") or []
                    if not isinstance(resources, list) or not all(isinstance(x, str) for x in resources):
                        return self._send(HTTPStatus.BAD_REQUEST, {"error": "invalid_resources"})
                    result = runtime.engine.ingest(claims["sub"], content, resources=resources)
                    return self._send(HTTPStatus.OK, result)
                except AuthenticationError:
                    return self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                except PermissionError:
                    return self._send(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
                except (ValueError, json.JSONDecodeError):
                    return self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request"})
                except Exception:
                    return self._send(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": "internal_error"})

        return Handler

    def serve(self, host: str = "0.0.0.0", port: int = 3000):
        server = ThreadingHTTPServer((host, port), self.handler())
        server.serve_forever()
