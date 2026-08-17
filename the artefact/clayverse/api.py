from __future__ import annotations

import html
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock
from typing import Any

from .adapters import AuthenticationError, ClerkTokenVerifier


class ClayVerseAPI:
    def __init__(self, engine: Any, verifier: ClerkTokenVerifier, *, publishable_key: str = "", frontend_api_url: str = "", max_body: int = 1_000_000):
        self.engine = engine
        self.verifier = verifier
        self.publishable_key = publishable_key
        self.frontend_api_url = frontend_api_url.rstrip("/")
        self.max_body = max_body
        # UnifiedDB currently owns one SQLite connection. Keep the canonical state
        # mutation lane strictly ordered without starving health/read requests while
        # a long cognition turn is in flight.
        self._mutation_lock = Lock()

    def homepage(self) -> str:
        key = html.escape(self.publishable_key, quote=True)
        api = html.escape(self.frontend_api_url, quote=True)
        if not key or not api:
            return "<!doctype html><meta charset=utf-8><title>ClayVerse</title><h1>ClayVerse</h1><p>Clerk web configuration is incomplete.</p>"
        return f"""<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>ClayVerse</title><style>body{{font:16px system-ui;max-width:900px;margin:40px auto;padding:0 20px}}textarea{{width:100%;min-height:120px}}#out{{white-space:pre-wrap;border:1px solid #ccc;padding:16px;margin-top:16px}}header{{display:flex;justify-content:space-between;align-items:center}}</style></head><body><header><h1>ClayVerse</h1><div id=\"user-button\"></div></header><main id=\"app\"><p>Loading authentication…</p></main><script defer crossorigin=\"anonymous\" src=\"{api}/npm/@clerk/ui@1/dist/ui.browser.js\"></script><script defer crossorigin=\"anonymous\" data-clerk-publishable-key=\"{key}\" src=\"{api}/npm/@clerk/clerk-js@6/dist/clerk.browser.js\"></script><script>window.addEventListener('load',async()=>{{await Clerk.load({{ui:{{ClerkUI:window.__internal_ClerkUICtor}}}});const app=document.getElementById('app');if(!Clerk.isSignedIn){{app.innerHTML='<div id=\"sign-in\"></div>';Clerk.mountSignIn(document.getElementById('sign-in'));return;}}Clerk.mountUserButton(document.getElementById('user-button'));app.innerHTML='<textarea id=\"msg\" placeholder=\"Talk to ClayVerse\"></textarea><button id=\"send\">Send</button><div id=\"out\"></div>';document.getElementById('send').onclick=async()=>{{const token=await Clerk.session.getToken();const content=document.getElementById('msg').value;const r=await fetch('/api/chat',{{method:'POST',headers:{{'content-type':'application/json','authorization':'Bearer '+token}},body:JSON.stringify({{content}})}});const data=await r.json();document.getElementById('out').textContent=r.ok?(data.decision?.text??JSON.stringify(data,null,2)):(data.error??'request failed');}};}});</script></body></html>"""

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
                    return self._send(HTTPStatus.OK, runtime.homepage(), "text/html; charset=utf-8")
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
                    with runtime._mutation_lock:
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

    def server(self, host: str = "0.0.0.0", port: int = 3000):
        # Read/health traffic may run concurrently, but every canonical state mutation
        # stays behind _mutation_lock until UnifiedDB has a proven multi-connection model.
        return ThreadingHTTPServer((host, port), self.handler())

    def serve(self, host: str = "0.0.0.0", port: int = 3000):
        self.server(host, port).serve_forever()
