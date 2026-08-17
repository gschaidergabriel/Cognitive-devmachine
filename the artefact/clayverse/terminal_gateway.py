from __future__ import annotations

import asyncio
import html
import json
import math
import os
import time
from pathlib import Path

from fastapi import WebSocket, WebSocketDisconnect

from .clerk_auth import AuthenticationError, ClerkTokenVerifier
from .identity import CANONICAL_TERMINAL_NAMES, IdentityRouter
from .store import UnifiedDB
from .terminal_sessions import TerminalSessionManager

_AUTH_MESSAGE_MAX_CHARS = 32_768
_AUTH_TOKEN_MAX_CHARS = 16_384
_CONTROL_MESSAGE_MAX_CHARS = 4_096
_PTY_INPUT_FRAME_MAX_BYTES = 65_536
_PTY_OUTPUT_CHUNK_MAX_BYTES = 65_536
_AUTH_REFRESH_HEADROOM_SECONDS = 10


def _decode_json_object(payload: str, *, name: str, max_chars: int) -> dict:
    """Decode one bounded WebSocket control message or fail closed."""
    if not isinstance(payload, str) or not payload:
        raise ValueError(f"{name} message must be non-empty text")
    if len(payload) > max_chars:
        raise ValueError(f"{name} message exceeds bound")
    try:
        value = json.loads(payload)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{name} message must be valid JSON") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{name} message must be an object")
    return value


def _decode_terminal_control(payload: str) -> dict:
    """Allow a bounded auth refresh envelope without widening ordinary controls."""
    control = _decode_json_object(payload, name="control", max_chars=_AUTH_MESSAGE_MAX_CHARS)
    if control.get("type") != "reauth" and len(payload) > _CONTROL_MESSAGE_MAX_CHARS:
        raise ValueError("control message exceeds bound")
    return control


def _auth_token(hello: dict) -> str:
    token = hello.get("token")
    if not isinstance(token, str) or not token or len(token) > _AUTH_TOKEN_MAX_CHARS:
        raise AuthenticationError("invalid Clerk session token shape")
    return token


def _require_auth_lease_live(deadline: float, *, now: float | None = None) -> None:
    """Require the verified Clerk lease to still be live at an effect/output boundary."""
    current = time.time() if now is None else float(now)
    if not math.isfinite(deadline) or not math.isfinite(current):
        raise AuthenticationError("Clerk session token expiration is invalid")
    if deadline <= current:
        raise AuthenticationError("Clerk session token expired")


def _auth_expiry_deadline(claims: dict, *, now: float | None = None) -> float:
    """Return a finite future Clerk JWT expiry or fail closed."""
    exp = claims.get("exp")
    if isinstance(exp, bool) or not isinstance(exp, (int, float)):
        raise AuthenticationError("Clerk session token missing valid expiration")
    deadline = float(exp)
    _require_auth_lease_live(deadline, now=now)
    return deadline


def _reauthenticated_expiry(
    claims: dict,
    *,
    expected_subject: str,
    expected_clerk_session_id: str,
    now: float | None = None,
) -> float:
    """Fence a refreshed token to the already-authenticated Clerk identity/session."""
    if str(claims.get("sub", "")) != expected_subject:
        raise AuthenticationError("Clerk refresh changed subject")
    if str(claims.get("sid", "")) != expected_clerk_session_id:
        raise AuthenticationError("Clerk refresh changed session")
    return _auth_expiry_deadline(claims, now=now)


def _terminal_dimensions(message: dict) -> tuple[int, int]:
    rows = message.get("rows", 24)
    cols = message.get("cols", 80)
    if isinstance(rows, bool) or not isinstance(rows, int):
        raise ValueError("terminal rows must be an integer")
    if isinstance(cols, bool) or not isinstance(cols, int):
        raise ValueError("terminal cols must be an integer")
    return rows, cols


def _bounded_pty_input(payload: bytes) -> bytes:
    if not isinstance(payload, bytes):
        raise TypeError("PTY input frame must be bytes")
    if len(payload) > _PTY_INPUT_FRAME_MAX_BYTES:
        raise ValueError("PTY input frame exceeds bound")
    return payload


def _write_pty_all(fd: int, payload: bytes, auth_deadline: float) -> None:
    """Write one terminal-input frame while its authenticated lease remains live.

    PTY writes may complete partially or block in the worker thread. Re-check the
    immutable deadline immediately before and after every kernel write so an expired
    frame can never continue through a later partial-write iteration or be reported as
    successfully written after a blocking syscall crossed the lease boundary.
    """
    remaining = memoryview(payload)
    while remaining:
        _require_auth_lease_live(auth_deadline)
        written = os.write(fd, remaining)
        _require_auth_lease_live(auth_deadline)
        if written <= 0:
            raise OSError("PTY write made no progress")
        remaining = remaining[written:]


def _terminal_sessions_ready(terminals: TerminalSessionManager) -> bool:
    """Read-only readiness through the canonical manager-owned tmux control path."""
    for user_id in CANONICAL_TERMINAL_NAMES:
        binding = terminals.binding(user_id)
        if not terminals._has_session(binding):
            return False
        terminals._assert_tmux_server_policy(binding)
    return True


def _runtime_ready(db: UnifiedDB, terminals: TerminalSessionManager) -> bool:
    """Read-only readiness check for canonical state plus both admitted product terminals."""
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
        state_ready = bool(
            schema and schema[0] == "6"
            and entity_generation >= 1
            and users and int(users[0]) == 2
            and set(sessions) == {"gabriel", "andreas"}
            and all(
                sessions[user_id]["terminal_name"] == terminal_name
                and int(sessions[user_id]["generation"]) == entity_generation
                for user_id, terminal_name in CANONICAL_TERMINAL_NAMES.items()
            )
        )
        return state_ready and _terminal_sessions_ready(terminals)
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
        ready = await asyncio.to_thread(_runtime_ready, db, terminals)
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
  const maxInputFrameBytes={_PTY_INPUT_FRAME_MAX_BYTES};
  let terminalReady=false; let authRefreshTimer=null;
  const scheduleAuthRefresh=(expiresAt)=>{{
    if(authRefreshTimer) clearTimeout(authRefreshTimer);
    const delay=Math.max(1000,Number(expiresAt)*1000-Date.now()-{_AUTH_REFRESH_HEADROOM_SECONDS * 1000});
    authRefreshTimer=setTimeout(async()=>{{
      try{{
        const token=await Clerk.session.getToken({{skipCache:true}});
        if(terminalReady&&ws.readyState===1) ws.send(JSON.stringify({{type:'reauth',token}}));
      }}catch{{ws.close();}}
    }},delay);
  }};
  ws.onopen=async()=>{{ const token=await Clerk.session.getToken({{skipCache:true}}); ws.send(JSON.stringify({{type:'auth',token,rows:term.rows,cols:term.cols}})); }};
  ws.onmessage=(ev)=>{{
    if(typeof ev.data==='string'){{
      try{{
        const m=JSON.parse(ev.data);
        if(m.type==='ready'){{scheduleAuthRefresh(m.auth_expires_at);}}
        if(m.type==='ready'){{terminalReady=true;term.focus();return;}}
        if(m.type==='reauthenticated'){{scheduleAuthRefresh(m.auth_expires_at);return;}}
        if(m.type==='error'){{terminalReady=false;term.writeln('\\r\\n[ClayVerse] '+m.message);return;}}
      }}catch{{if(terminalReady)term.write(ev.data);}}
    }}else if(terminalReady) term.write(new Uint8Array(ev.data));
  }};
  term.onData(data=>{{
    if(!terminalReady||ws.readyState!==1)return;
    const encoded=new TextEncoder().encode(data);
    for(let offset=0;offset<encoded.length;offset+=maxInputFrameBytes){{
      ws.send(encoded.slice(offset,offset+maxInputFrameBytes));
    }}
  }});
  const resize=()=>{{ if(terminalReady&&ws.readyState===1) ws.send(JSON.stringify({{type:'resize',rows:term.rows,cols:term.cols}})); }};
  ws.onclose=()=>{{terminalReady=false;}};
  ws.addEventListener('close',()=>{{if(authRefreshTimer)clearTimeout(authRefreshTimer);}});
  window.addEventListener('resize',resize);
}});
</script></body></html>''')

    @app.websocket("/ws/terminal")
    async def terminal_ws(ws: WebSocket):
        await ws.accept()
        attach_pid = attach_fd = None
        send_lock = asyncio.Lock()

        async def send_json(payload: dict) -> None:
            async with send_lock:
                await ws.send_text(json.dumps(payload))

        try:
            first = await asyncio.wait_for(ws.receive_text(), timeout=10)
            hello = _decode_json_object(first, name="auth", max_chars=_AUTH_MESSAGE_MAX_CHARS)
            if hello.get("type") != "auth":
                raise AuthenticationError("authentication must be first message")
            token = _auth_token(hello)
            rows, cols = _terminal_dimensions(hello)
            claims = await asyncio.to_thread(verifier.verify, token)
            auth_expires_at = _auth_expiry_deadline(claims)
            clerk_subject = str(claims["sub"])
            clerk_session_id = str(claims["sid"])
            user_id, session_id = identity.resolve(clerk_subject)
            attach_pid, attach_fd, binding = await asyncio.to_thread(terminals.attach_pty, user_id)
            if binding.session_id != session_id:
                raise PermissionError("terminal/session identity mismatch")
            # PTY/tmux attachment is a blocking trust-boundary transition. If the
            # verified Clerk lease expired while it blocked, do not mutate terminal
            # state (including its initial size) under an expired authorization.
            _require_auth_lease_live(auth_expires_at)
            terminals.resize(attach_fd, rows, cols)
            # Resize may itself cross a scheduling/blocking boundary. Never publish
            # readiness after the lease has expired in that interval.
            _require_auth_lease_live(auth_expires_at)
            await send_json({
                "type": "ready",
                "user_id": user_id,
                "session_id": session_id,
                "auth_expires_at": int(auth_expires_at),
            })

            async def pump_out():
                while True:
                    data = await asyncio.to_thread(os.read, attach_fd, _PTY_OUTPUT_CHUNK_MAX_BYTES)
                    if not data:
                        return
                    async with send_lock:
                        # Output is an authenticated capability too. Re-check after
                        # the blocking PTY read and after waiting for the send lock.
                        _require_auth_lease_live(auth_expires_at)
                        await ws.send_bytes(data)

            async def pump_in():
                nonlocal auth_expires_at
                while True:
                    remaining = auth_expires_at - time.time()
                    if remaining <= 0:
                        raise AuthenticationError("Clerk session token expired")
                    try:
                        message = await asyncio.wait_for(ws.receive(), timeout=remaining)
                    except asyncio.TimeoutError as exc:
                        raise AuthenticationError("Clerk session token expired") from exc
                    # wait_for() and websocket receive completion race at the deadline.
                    # Re-check the lease before any received frame can affect PTY/control state.
                    if auth_expires_at <= time.time():
                        raise AuthenticationError("Clerk session token expired")
                    if message.get("type") == "websocket.disconnect":
                        return
                    if message.get("bytes") is not None:
                        _bounded_pty_input(message["bytes"])
                        # Freeze the lease that admitted this frame. A concurrent reauth may
                        # extend future frames but must not retroactively authorize a write
                        # that already crossed its original admission deadline.
                        frame_auth_deadline = auth_expires_at
                        await asyncio.to_thread(
                            _write_pty_all,
                            attach_fd,
                            message["bytes"],
                            frame_auth_deadline,
                        )
                    elif message.get("text") is not None:
                        control = _decode_terminal_control(message["text"])
                        if control.get("type") == "reauth":
                            refreshed = await asyncio.to_thread(verifier.verify, _auth_token(control))
                            auth_expires_at = _reauthenticated_expiry(
                                refreshed,
                                expected_subject=clerk_subject,
                                expected_clerk_session_id=clerk_session_id,
                            )
                            await send_json({
                                "type": "reauthenticated",
                                "auth_expires_at": int(auth_expires_at),
                            })
                            continue
                        if control.get("type") != "resize":
                            raise ValueError("unsupported terminal control message")
                        rows, cols = _terminal_dimensions(control)
                        terminals.resize(attach_fd, rows, cols)
                    else:
                        raise ValueError("unsupported WebSocket terminal frame")

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
                await send_json({"type": "error", "message": str(exc)})
            except Exception:
                pass
        finally:
            if attach_pid is not None and attach_fd is not None:
                await asyncio.to_thread(terminals.close_attach, attach_pid, attach_fd)

    return app