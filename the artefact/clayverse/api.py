from __future__ import annotations

import base64
import binascii
import html
import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any
from urllib.parse import parse_qs, urlsplit

from .adapters import AuthenticationError, ClerkTokenVerifier


class ClayVerseAPI:
    def __init__(
        self,
        engine: Any,
        verifier: ClerkTokenVerifier,
        *,
        publishable_key: str = "",
        frontend_api_url: str = "",
        terminal_supervisor: Any | None = None,
        max_body: int = 1_000_000,
    ):
        self.engine = engine
        self.verifier = verifier
        self.publishable_key = publishable_key
        self.frontend_api_url = frontend_api_url.rstrip("/")
        self.terminal_supervisor = terminal_supervisor
        self.max_body = max_body

    def homepage(self) -> str:
        key = html.escape(self.publishable_key, quote=True)
        api = html.escape(self.frontend_api_url, quote=True)
        if not key or not api:
            return "<!doctype html><meta charset=utf-8><title>ClayVerse</title><h1>ClayVerse</h1><p>Clerk web configuration is incomplete.</p>"
        return f"""<!doctype html><html><head><meta charset=\"utf-8\"><meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>ClayVerse</title><style>body{{font:16px system-ui;max-width:1000px;margin:32px auto;padding:0 20px}}textarea{{width:100%;min-height:100px}}#out{{white-space:pre-wrap;border:1px solid #ccc;padding:16px;margin-top:16px}}header{{display:flex;justify-content:space-between;align-items:center}}#terminal{{margin-top:28px}}#term-out{{background:#111;color:#eee;min-height:260px;max-height:520px;overflow:auto;padding:12px;white-space:pre-wrap;font:14px/1.35 ui-monospace,SFMono-Regular,Menlo,monospace}}#term-in{{width:100%;box-sizing:border-box;font:14px ui-monospace,SFMono-Regular,Menlo,monospace;padding:8px}}</style></head><body><header><h1>ClayVerse</h1><div id=\"user-button\"></div></header><main id=\"app\"><p>Loading authentication…</p></main><script defer crossorigin=\"anonymous\" src=\"{api}/npm/@clerk/ui@1/dist/ui.browser.js\"></script><script defer crossorigin=\"anonymous\" data-clerk-publishable-key=\"{key}\" src=\"{api}/npm/@clerk/clerk-js@6/dist/clerk.browser.js\"></script><script>window.addEventListener('load',async()=>{{await Clerk.load({{ui:{{ClerkUI:window.__internal_ClerkUICtor}}}});const app=document.getElementById('app');if(!Clerk.isSignedIn){{app.innerHTML='<div id=\"sign-in\"></div>';Clerk.mountSignIn(document.getElementById('sign-in'));return;}}Clerk.mountUserButton(document.getElementById('user-button'));app.innerHTML='<textarea id=\"msg\" placeholder=\"Talk to ClayVerse\"></textarea><button id=\"send\">Send</button><div id=\"out\"></div><section id=\"terminal\"><h2>Claude Code terminal</h2><button id=\"term-start\">Start terminal</button><pre id=\"term-out\"></pre><input id=\"term-in\" autocomplete=\"off\" spellcheck=\"false\" placeholder=\"Terminal input — Enter sends a newline\"></section>';const auth=async()=>{{const token=await Clerk.session.getToken();return {{'authorization':'Bearer '+token}};}};document.getElementById('send').onclick=async()=>{{const content=document.getElementById('msg').value;const headers=await auth();headers['content-type']='application/json';const r=await fetch('/api/chat',{{method:'POST',headers,body:JSON.stringify({{content}})}});const data=await r.json();document.getElementById('out').textContent=r.ok?(data.decision?.text??JSON.stringify(data,null,2)):(data.error??'request failed');}};const termOut=document.getElementById('term-out');const decoder=new TextDecoder();let polling=false;const bytesToB64=(bytes)=>{{let s='';for(const b of bytes)s+=String.fromCharCode(b);return btoa(s);}};const poll=async()=>{{if(!polling)return;try{{const r=await fetch('/api/terminal/read?max_bytes=65536',{{headers:await auth()}});if(r.ok){{const data=await r.json();if(data.data_b64){{const raw=atob(data.data_b64);const bytes=Uint8Array.from(raw,c=>c.charCodeAt(0));termOut.textContent+=decoder.decode(bytes,{{stream:true}});termOut.scrollTop=termOut.scrollHeight;}}}}}}finally{{setTimeout(poll,250);}}}};document.getElementById('term-start').onclick=async()=>{{const r=await fetch('/api/terminal/start',{{method:'POST',headers:await auth()}});if(r.ok&&!polling){{polling=true;poll();}}}};document.getElementById('term-in').addEventListener('keydown',async(e)=>{{if(e.key!=='Enter')return;e.preventDefault();const input=e.currentTarget;const bytes=new TextEncoder().encode(input.value+'\\n');input.value='';const headers=await auth();headers['content-type']='application/json';await fetch('/api/terminal/write',{{method:'POST',headers,body:JSON.stringify({{data_b64:bytesToB64(bytes)}})}});}});}});</script></body></html>"""

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

            def _canonical_terminal(self):
                if runtime.terminal_supervisor is None:
                    raise RuntimeError("terminal adapter unavailable")
                claims = self._claims()
                user_id, _session_id = runtime.engine.identity.resolve(claims["sub"])
                return user_id, runtime.terminal_supervisor.for_user(user_id)

            def _json_body(self):
                size = int(self.headers.get("Content-Length", "0") or "0")
                if size <= 0 or size > runtime.max_body:
                    raise ValueError("invalid request body size")
                return json.loads(self.rfile.read(size))

            def do_GET(self):
                parsed = urlsplit(self.path)
                if parsed.path == "/healthz":
                    return self._send(HTTPStatus.OK, {"ok": True, "service": "clayverse"})
                if parsed.path == "/":
                    return self._send(HTTPStatus.OK, runtime.homepage(), "text/html; charset=utf-8")
                if parsed.path == "/api/status":
                    try:
                        claims = self._claims()
                        return self._send(HTTPStatus.OK, {"ok": True, "clerk_subject": claims["sub"]})
                    except AuthenticationError:
                        return self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                if parsed.path == "/api/terminal/read":
                    try:
                        user_id, terminal = self._canonical_terminal()
                        params = parse_qs(parsed.query)
                        max_bytes = int(params.get("max_bytes", ["65536"])[0])
                        data = terminal.read(max_bytes=max_bytes)
                        return self._send(HTTPStatus.OK, {
                            "ok": True,
                            "user_id": user_id,
                            "alive": terminal.alive(),
                            "exit_status": terminal.exit_status,
                            "data_b64": base64.b64encode(data).decode("ascii"),
                        })
                    except AuthenticationError:
                        return self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                    except PermissionError:
                        return self._send(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
                    except (ValueError, OverflowError):
                        return self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request"})
                    except RuntimeError:
                        return self._send(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "terminal_unavailable"})
                return self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

            def do_POST(self):
                parsed = urlsplit(self.path)
                if parsed.path == "/api/chat":
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

                if parsed.path in {"/api/terminal/start", "/api/terminal/write"}:
                    try:
                        user_id, terminal = self._canonical_terminal()
                        if parsed.path == "/api/terminal/start":
                            terminal.start()
                            return self._send(HTTPStatus.OK, {"ok": True, "user_id": user_id, "alive": terminal.alive()})
                        body = self._json_body()
                        encoded = body.get("data_b64")
                        if not isinstance(encoded, str) or not encoded:
                            raise ValueError("data_b64 is required")
                        try:
                            data = base64.b64decode(encoded, validate=True)
                        except (binascii.Error, ValueError) as exc:
                            raise ValueError("invalid base64") from exc
                        written = terminal.write(data)
                        return self._send(HTTPStatus.OK, {"ok": True, "user_id": user_id, "written": written})
                    except AuthenticationError:
                        return self._send(HTTPStatus.UNAUTHORIZED, {"error": "unauthorized"})
                    except PermissionError:
                        return self._send(HTTPStatus.FORBIDDEN, {"error": "forbidden"})
                    except (ValueError, json.JSONDecodeError):
                        return self._send(HTTPStatus.BAD_REQUEST, {"error": "bad_request"})
                    except RuntimeError:
                        return self._send(HTTPStatus.CONFLICT, {"error": "terminal_unavailable"})

                return self._send(HTTPStatus.NOT_FOUND, {"error": "not_found"})

        return Handler

    def server(self, host: str = "0.0.0.0", port: int = 3000):
        # UnifiedDB currently owns one SQLite connection and the central entity is
        # deliberately one ordered mutation lane. Do not admit concurrent request
        # handlers until DB access is refactored to a proven multi-connection model.
        return HTTPServer((host, port), self.handler())

    def serve(self, host: str = "0.0.0.0", port: int = 3000):
        self.server(host, port).serve_forever()
