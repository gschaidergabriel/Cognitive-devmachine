from __future__ import annotations

import asyncio
import html
import json
import os
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

from .adapters import AuthenticationError, ClerkTokenVerifier
from .identity import CANONICAL_TERMINAL_NAMES, IdentityRouter
from .store import UnifiedDB
from .terminal_sessions import TerminalSessionManager


def _write_pty_all(fd: int, payload: bytes) -> None:
    """Write one terminal-input frame completely or fail closed."""
    remaining = memoryview(payload)
    while remaining:
        written = os.write(fd, remaining)
        if written <= 0:
            raise OSError("PTY write made no progress")
        remaining = remaining[written:]


def _runtime_ready(db: UnifiedDB) -> bool:
    """Read-only readiness check for the canonical UnifiedDB spine."""
    try:
        schema = db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        generation = db.db.execute("SELECT value FROM meta WHERE key='entity_generation'").fetchone()
        users = db.db.execute(
            "SELECT COUNT(*) FROM users WHERE user_id IN ('gabriel','andreas')"
        ).fetchone()
        session_rows = db.db.execute(
            "SELECT user_id,terminal_name,generation FROM sessions ORDER BY user_id"
        ).fetchall()
        sessions = {row["user_id"]: row for row in session_rows}
        entity_generation = int(generation[0]) if generation else -1
        return bool(
            schema and schema[0] == "5"
            and entity_generation >= 1
            and users and int(users[0]) == 2
            and set(sessions) == {"gabriel", "andreas"}
            and all(
                sessions[user_id]["terminal_name"] == terminal_name
                and int(sessions[user_id]["generation"]) == entity_generation
                for user_id, terminal_name in CANONICAL_TERMINAL_NAMES.items()
            )
        )
    except Exception:
        return False


def create_terminal_app(*, db: UnifiedDB, clerk_map: dict[str, str], verifier: ClerkTokenVerifier,
                        state_root: str | Path, publishable_key: str, frontend_api_url: str):
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    identity = IdentityRouter(db, clerk_map)
    terminals = TerminalSessionManager(state_root, os.environ.get("CLAYVERSE_WORKSPACE", "/workspace"))
    app = FastAPI(title="ClayVerse", docs_url=None, redoc_url=None)
    app.mount("/vendor/xterm", StaticFiles(directory="/opt/clayverse/vendor/xterm", check_dir=False), name="xterm")
    frontend_api_url = frontend_api_url.rstrip("/")

    @app.get("/healthz")
    async def healthz():
        return JSONResponse({
            "status": "ok",
            "scope": "liveness",
            "surface": "permanent-claude-code-terminal",
            "users": ["gabriel", "andreas"],
            "consciousness_daemon": False,
        })

    @app.get("/readyz")
    async def readyz():
        ready = _runtime_ready(db)
        return JSONResponse({
            "status": "ready" if ready else "not_ready",
            "scope": "runtime",
            "canonical_state": "unifieddb",
            "surface": "permanent-claude-code-terminal",
        }, status_code=200 if ready else 503)

    @app.get("/", response_class=HTMLResponse)
    async def index():
        key = html.escape(publishable_key, quote=True)
        api = html.escape(frontend_api_url, quote=True)
        if not key or not api:
            return HTMLResponse("Clerk web configuration is incomplete", status_code=503)
        return HTMLResponse(f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>ClayVerse</title>
<link rel="stylesheet" href="/vendor/xterm/css/xterm.css">
<style>html,body,#terminal{{width:100%;height:100%;margin:0;background:#000;overflow:hidden}}#auth{{height:100%;display:grid;place-items:center}}</style>
<script defer crossorigin="anonymous" src="{api}/npm/@clerk/ui@1/dist/ui.browser.js"></script>
<script defer crossorigin="anonymous" data-clerk-publishable-key="{key}" src="{api}/npm/@clerk/clerk-js@6/dist/clerk.browser.js"></script>
<script src="/vendor/xterm/lib/xterm.js"></script></head>
<body><div id="auth"></div><div id="terminal" style="display:none"></div><script>
window.addEventListener('load', async () => {{
  await Clerk.load({{ui:{{ClerkUI:window.__internal_ClerkUICtor}}}});
  const auth=document.getElementById('auth'); const node=document.getElementById('terminal');
  if (!Clerk.isSignedIn) {{ Clerk.mountSignIn(auth); return; }}
  auth.style.display='none'; node.style.display='block';
  const term=new Terminal({{cursorBlink:true,scrollback:10000,convertEol:false}}); term.open(node);
  const proto=location.protocol==='https:'?'wss':'ws'; const ws=new WebSocket(`${{proto}}://${{location.host}}/ws/terminal`); ws.binaryType='arraybuffer';
  ws.onopen=async()=>{{ const token=await Clerk.session.getToken(); ws.send(JSON.stringify({{type:'auth',token,rows:term.rows,cols:term.cols}})); }};
  ws.onmessage=(ev)=>{{ if(typeof ev.data==='string'){{try{{const m=JSON.parse(ev.data);if(m.type==='error')term.writeln('\\r\\n[ClayVerse] '+m.message);}}catch{{term.write(ev.data);}}}}else term.write(new Uint8Array(ev.data)); }};
  term.onData(data=>{{ if(ws.readyState===1) ws.send(new TextEncoder().encode(data)); }});
  const resize=()=>{{ if(ws.readyState===1) ws.send(JSON.stringify({{type:'resize',rows:term.rows,cols:term.cols}})); }};
  window.addEventListener('resize',resize);
}});
</script></body></html>''')

    @app.websocket("/ws/terminal")
    async def terminal_ws(ws: WebSocket):
        await ws.accept()
        attach_pid = attach_fd = None
        try:
            first = await asyncio.wait_for(ws.receive_text(), timeout=10)
            hello = json.loads(first)
            if hello.get("type") != "auth":
                raise AuthenticationError("authentication must be first message")
            claims = verifier.verify(str(hello.get("token", "")))
            user_id, session_id = identity.resolve(str(claims["sub"]))
            attach_pid, attach_fd, binding = await asyncio.to_thread(terminals.attach_pty, user_id)
            if binding.session_id != session_id:
                raise PermissionError("terminal/session identity mismatch")
            terminals.resize(attach_fd, int(hello.get("rows", 24)), int(hello.get("cols", 80)))
            await ws.send_text(json.dumps({"type": "ready", "user_id": user_id, "session_id": session_id}))

            async def pump_out():
                while True:
                    data = await asyncio.to_thread(os.read, attach_fd, 65536)
                    if not data:
                        return
                    await ws.send_bytes(data)

            async def pump_in():
                while True:
                    message = await ws.receive()
                    if message.get("bytes") is not None:
                        await asyncio.to_thread(_write_pty_all, attach_fd, message["bytes"])
                    elif message.get("text"):
                        control = json.loads(message["text"])
                        if control.get("type") == "resize":
                            terminals.resize(attach_fd, int(control.get("rows", 24)), int(control.get("cols", 80)))

            tasks = [asyncio.create_task(pump_out()), asyncio.create_task(pump_in())]
            done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
            for task in pending:
                task.cancel()
            for task in done:
                task.result()
        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception as exc:
            try:
                await ws.send_text(json.dumps({"type": "error", "message": str(exc)))
            except Exception:
                pass
        finally:
            if attach_pid is not None and attach_fd is not None:
                await asyncio.to_thread(terminals.close_attach, attach_pid, attach_fd)

    return app
