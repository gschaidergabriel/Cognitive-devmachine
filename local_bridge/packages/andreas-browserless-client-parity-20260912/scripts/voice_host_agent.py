#!/usr/bin/env python3
"""Persistent typed host-side ChatGPT/voice client for FranKenstein.

One process stays alive per real FranKenstein installation.  It is not a
second brain, browser, model, database or effect authority.  It owns only
RAM session leases and exposes bounded typed context operations to the
existing ChatGPT/voice bridge.

Lifecycle:
  /v1/session/open         -> identity-neutral RAM lease, NO person DB access
  /v1/session/select       -> exact local person/host bind; starts canonical lifecycle
  /v1/session/turn-context -> one canonical retrieval/GRID uptake + TITAN + state assembly
  /v1/session/close        -> closes only that session; daemon remains alive

Arbitrary shell and effect execution are deliberately absent.  Effects stay
behind existing Frankenstein authority/effect fences.

For Andreas run inside the EntityOS nspawn machine with:
  FRANK_VOICE_MACHINE_ID=andreas-maco
  FRANK_VOICE_OWNER=andreas
  FRANK_VOICE_PERSON=andreas
  FRANK_VOICE_DB_PATH=/var/lib/entityos/unified.db
For Gabriel use exact ai-core-node/gabriel identity and the canonical DB path.
"""
from __future__ import annotations

import dataclasses
import json
import os
import sqlite3
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlsplit

HERE = Path(__file__).resolve().parent
LEGACY = HERE.parent / "DEV_SOURCE_RESEARCH" / "repository" / "scripts"
for p in (HERE, LEGACY):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

import f2wp1207_titan_mc as titan_mc  # noqa: E402
from frankenstein_identity_assembly import canonical_identity_block  # noqa: E402

try:
    import stern  # noqa: E402
except Exception:
    stern = None

MACHINE_ID = (os.environ.get("FRANK_VOICE_MACHINE_ID") or os.environ.get("LOCAL_BRIDGE_MACHINE_ID") or "").strip().lower()
OWNER = (os.environ.get("FRANK_VOICE_OWNER") or os.environ.get("LOCAL_BRIDGE_OWNER") or "").strip().lower()
PERSON = (os.environ.get("FRANK_VOICE_PERSON") or OWNER or "").strip().lower()
TOKEN = (os.environ.get("FRANK_VOICE_BROKER_TOKEN") or "").strip()
HOST = (os.environ.get("FRANK_VOICE_BROKER_BIND") or "127.0.0.1").strip()
PORT = int(os.environ.get("FRANK_VOICE_BROKER_PORT") or "8765")
DB_PATH = (os.environ.get("FRANK_VOICE_DB_PATH") or (getattr(stern, "DB_PATH", "") if stern else "")).strip()
SESSION_TTL_S = max(60, int(os.environ.get("FRANK_CHATGPT_SESSION_TTL_S") or "1800"))
MAX_SESSIONS = max(1, min(int(os.environ.get("FRANK_CHATGPT_MAX_SESSIONS") or "16"), 128))

EXPECTED = {
    "gabriel": ("ai-core-node", "gabriel"),
    "andreas": ("andreas-maco", "andreas"),
}

_CANONICAL_TURN_LOCK = threading.RLock()
_SESSIONS_LOCK = threading.RLock()
_SESSIONS: dict[str, "SessionLease"] = {}


@dataclasses.dataclass
class SessionLease:
    session_id: str
    created_mono: float
    last_seen_mono: float
    selected_person: str | None = None
    lifecycle_started: bool = False
    runtime_epoch_id: str | None = None

    @property
    def identity_state(self) -> str:
        return "BOUND" if self.selected_person == PERSON and self.lifecycle_started else "IDENTITY_REQUIRED"

    def touch(self) -> None:
        self.last_seen_mono = time.monotonic()

    def as_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "identity_state": self.identity_state,
            "selected_person": self.selected_person,
            "lifecycle_started": self.lifecycle_started,
            "runtime_epoch_id": self.runtime_epoch_id,
            "age_s": round(max(0.0, time.monotonic() - self.created_mono), 3),
            "idle_s": round(max(0.0, time.monotonic() - self.last_seen_mono), 3),
        }


def _identity_ok() -> None:
    if PERSON not in EXPECTED:
        raise RuntimeError(f"invalid FRANK_VOICE_PERSON={PERSON!r}")
    expected_machine, expected_owner = EXPECTED[PERSON]
    if MACHINE_ID != expected_machine or OWNER != expected_owner:
        raise RuntimeError(
            f"identity mismatch: person={PERSON} expects {expected_machine}/{expected_owner}, got {MACHINE_ID}/{OWNER}"
        )
    if not TOKEN:
        raise RuntimeError("FRANK_VOICE_BROKER_TOKEN is required")
    if not DB_PATH:
        raise RuntimeError("FRANK_VOICE_DB_PATH/stern.DB_PATH missing")
    if stern is None:
        raise RuntimeError("canonical stern runtime is required for persistent ChatGPT client")


def _db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, timeout=0.12)
    conn.execute("PRAGMA busy_timeout=120")
    return conn


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None


def _state_snapshot() -> dict[str, Any]:
    out: dict[str, Any] = {"person": PERSON, "db_path": DB_PATH}
    with _db() as conn:
        if _table_exists(conn, "f2_grid10_frame"):
            row = conn.execute(
                "SELECT frame_id,runtime_epoch_id,session_id,turn_event_id,broadcast_winner_cell,broadcast_value,status "
                "FROM f2_grid10_frame ORDER BY rowid DESC LIMIT 1"
            ).fetchone()
            out["grid10_latest"] = None if row is None else {
                "frame_id": row[0], "runtime_epoch_id": row[1], "session_id": row[2],
                "turn_event_id": row[3], "winner_cell": row[4], "broadcast_value": row[5], "status": row[6],
            }
        if _table_exists(conn, "entityos_arbeitspaket"):
            rows = conn.execute(
                "SELECT paket_id,auftrag,stand,geaendert FROM entityos_arbeitspaket "
                "ORDER BY geaendert DESC LIMIT 5"
            ).fetchall()
            out["recent_goals_effects"] = [
                {"paket_id": r[0], "auftrag": str(r[1] or "")[:240], "stand": r[2], "geaendert": r[3]} for r in rows
            ]
        if _table_exists(conn, "durable_memory"):
            out["durable_memory_count"] = conn.execute(
                "SELECT count(*) FROM durable_memory WHERE lower(user_id)=?", (PERSON,)
            ).fetchone()[0]
    return out


def _binding_dict() -> dict[str, Any]:
    return {"label": PERSON, "machine_id": MACHINE_ID, "owner": OWNER, "verified_at": time.time()}


def _neutral_identity(session_id: str) -> str:
    return canonical_identity_block(
        selected_person=None,
        binding=None,
        channel="ChatGPT persistent host client",
        model_organ="ChatGPT",
    )


def _bound_identity(*, state: dict[str, Any], titan: str, emergent: str) -> str:
    return canonical_identity_block(
        selected_person=PERSON,
        binding=_binding_dict(),
        channel="ChatGPT persistent host client",
        model_organ="ChatGPT/Realtime",
        inner_state=json.dumps(state, ensure_ascii=False, separators=(",", ":"))[:8000],
        titan_context=titan,
        emergent_context=emergent,
    )


def _session_open(requested_id: str = "") -> SessionLease:
    sid = str(requested_id or "").strip()[:200] or f"chatgpt-{uuid.uuid4().hex}"
    now = time.monotonic()
    with _SESSIONS_LOCK:
        existing = _SESSIONS.get(sid)
        if existing is not None:
            existing.touch()
            return existing
        if len(_SESSIONS) >= MAX_SESSIONS:
            raise RuntimeError("session_capacity_reached")
        lease = SessionLease(session_id=sid, created_mono=now, last_seen_mono=now)
        _SESSIONS[sid] = lease
        return lease


def _session_get(session_id: str) -> SessionLease:
    sid = str(session_id or "").strip()[:200]
    if not sid:
        raise KeyError("session_id_required")
    with _SESSIONS_LOCK:
        lease = _SESSIONS.get(sid)
        if lease is None:
            raise KeyError("unknown_session")
        lease.touch()
        return lease


def _canonical_lifecycle_start(lease: SessionLease) -> None:
    if lease.lifecycle_started:
        return
    # This is deliberately called only after exact person selection. Session
    # open itself remains RAM-only, satisfying the no-prebind-mutation rule.
    opener = getattr(stern, "zyklus_oeffnen", None)
    if not callable(opener):
        raise RuntimeError("canonical zyklus_oeffnen unavailable")
    with _CANONICAL_TURN_LOCK:
        opener(lease.session_id, "chatgpt-bridge")
        runtime_epoch = getattr(stern, "_f2wp1207_runtime_epoch", None)
        if callable(runtime_epoch):
            result = runtime_epoch(lease.session_id)
            if isinstance(result, tuple) and result:
                lease.runtime_epoch_id = str(result[0] or "") or None
            elif isinstance(result, str):
                lease.runtime_epoch_id = result or None
    lease.lifecycle_started = True


def _session_select(lease: SessionLease, person: str) -> None:
    requested = str(person or "").strip().lower()
    if requested != PERSON:
        raise ValueError(f"person_scope_mismatch:{requested}->{PERSON}")
    lease.selected_person = PERSON
    _canonical_lifecycle_start(lease)
    lease.touch()


def _canonical_turn_context(lease: SessionLease, query: str, char_budget: int) -> dict[str, Any]:
    if lease.identity_state != "BOUND":
        raise PermissionError("IDENTITY_REQUIRED")
    text = str(query or "")[:12000]
    with _CANONICAL_TURN_LOCK:
        # One productive emergent retrieval, then exactly the existing GRID
        # hook bridge. Never call run_canonical_turn() separately here.
        emergent = ""
        retrieve = getattr(stern, "automatischer_abruf", None)
        if callable(retrieve):
            emergent = str(retrieve(lease.session_id, text) or "")[:12000]
        grid_auto = getattr(stern, "_f2wp1207_turn_loop_auto", None)
        grid_result = None
        if callable(grid_auto):
            grid_result = grid_auto(lease.session_id, text, emergent or None)

        with _db() as conn:
            titan = titan_mc.injection_text(
                conn, PERSON, text,
                session_id=lease.session_id,
                char_budget=max(512, min(int(char_budget), 8000)),
            )
        state = _state_snapshot()
        if grid_result is not None:
            state["canonical_turn_result"] = grid_result
        if lease.runtime_epoch_id:
            state["runtime_epoch_id"] = lease.runtime_epoch_id
        active = _bound_identity(state=state, titan=titan, emergent=emergent)
    lease.touch()
    return {
        "ok": True,
        "person": PERSON,
        "session": lease.as_dict(),
        "identity_active_assembly": active,
        "titan_context": titan,
        "emergent_context": emergent,
        "state": state,
    }


def _canonical_lifecycle_close(lease: SessionLease, reason: str) -> None:
    if not lease.lifecycle_started:
        return
    closer = getattr(stern, "zyklus_schliessen", None)
    if callable(closer):
        with _CANONICAL_TURN_LOCK:
            closer(lease.session_id)
    lease.lifecycle_started = False


def _session_close(session_id: str, reason: str = "client_close") -> bool:
    sid = str(session_id or "").strip()[:200]
    with _SESSIONS_LOCK:
        lease = _SESSIONS.pop(sid, None)
    if lease is None:
        return False
    _canonical_lifecycle_close(lease, reason)
    return True


def _scavenge_sessions() -> None:
    while True:
        time.sleep(min(30.0, max(5.0, SESSION_TTL_S / 4.0)))
        now = time.monotonic()
        with _SESSIONS_LOCK:
            stale = [sid for sid, lease in _SESSIONS.items() if now - lease.last_seen_mono > SESSION_TTL_S]
        for sid in stale:
            try:
                _session_close(sid, reason="ttl_expired")
            except Exception:
                pass


class Handler(BaseHTTPRequestHandler):
    server_version = "FrankChatGPTClient/2"

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def _authorized(self) -> bool:
        return self.headers.get("Authorization", "") == f"Bearer {TOKEN}"

    def _reply(self, code: int, payload: dict[str, Any]) -> None:
        body = json.dumps({"machine_id": MACHINE_ID, "owner": OWNER, **payload}, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        n = min(int(self.headers.get("Content-Length") or 0), 64 * 1024)
        raw = self.rfile.read(n)
        obj = json.loads(raw.decode("utf-8") or "{}")
        if not isinstance(obj, dict):
            raise ValueError("request body must be an object")
        return obj

    def do_GET(self) -> None:  # noqa: N802
        if not self._authorized():
            self._reply(401, {"ok": False, "error": "unauthorized"})
            return
        split = urlsplit(self.path)
        if split.path == "/health":
            with _SESSIONS_LOCK:
                active = len(_SESSIONS)
            self._reply(200, {
                "ok": True, "person": PERSON, "db_path": DB_PATH,
                "persistent_client": True, "active_sessions": active,
            })
            return
        if split.path == "/v1/session/status":
            sid = (parse_qs(split.query).get("session_id") or [""])[0]
            try:
                lease = _session_get(sid)
                self._reply(200, {"ok": True, "session": lease.as_dict()})
            except KeyError as exc:
                self._reply(404, {"ok": False, "error": str(exc)})
            return
        self._reply(404, {"ok": False, "error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802
        if not self._authorized():
            self._reply(401, {"ok": False, "error": "unauthorized"})
            return
        try:
            req = self._read_json()

            if self.path == "/v1/session/open":
                lease = _session_open(str(req.get("session_id") or ""))
                # Crucial: open is RAM-only and returns no person-specific state.
                self._reply(200, {
                    "ok": True,
                    "session": lease.as_dict(),
                    "identity_active_assembly": _neutral_identity(lease.session_id),
                })
                return

            if self.path == "/v1/session/select":
                lease = _session_get(str(req.get("session_id") or ""))
                _session_select(lease, str(req.get("person") or ""))
                self._reply(200, {
                    "ok": True,
                    "person": PERSON,
                    "session": lease.as_dict(),
                    "identity_active_assembly": canonical_identity_block(
                        selected_person=PERSON,
                        binding=_binding_dict(),
                        channel="ChatGPT persistent host client",
                        model_organ="ChatGPT/Realtime",
                    ),
                })
                return

            if self.path == "/v1/session/turn-context":
                lease = _session_get(str(req.get("session_id") or ""))
                result = _canonical_turn_context(
                    lease,
                    str(req.get("query") or ""),
                    max(512, min(int(req.get("char_budget") or 4200), 8000)),
                )
                self._reply(200, result)
                return

            if self.path == "/v1/session/close":
                sid = str(req.get("session_id") or "")
                closed = _session_close(sid, reason=str(req.get("reason") or "client_close")[:120])
                self._reply(200, {"ok": True, "closed": closed, "session_id": sid[:200]})
                return

            # Backwards-compatible bounded context operations. These are
            # person-scoped but do not themselves create a ChatGPT session.
            req_person = str(req.get("person") or "").strip().lower()
            if req_person != PERSON:
                self._reply(409, {"ok": False, "error": "person_scope_mismatch", "person": PERSON})
                return
            if self.path == "/v1/relationship-context":
                budget = max(512, min(int(req.get("char_budget") or 4200), 8000))
                with _db() as conn:
                    text = titan_mc.injection_text(
                        conn, PERSON, str(req.get("query") or "")[:8000],
                        session_id=str(req.get("session_id") or "")[:200], char_budget=budget,
                    )
                self._reply(200, {
                    "ok": True,
                    "person": PERSON,
                    "context": text,
                    "state": _state_snapshot(),
                })
                return
            if self.path == "/v1/state-snapshot":
                self._reply(200, {"ok": True, **_state_snapshot()})
                return
            self._reply(404, {"ok": False, "error": "not_found"})
        except KeyError as exc:
            self._reply(404, {"ok": False, "error": str(exc)})
        except PermissionError as exc:
            self._reply(409, {"ok": False, "error": str(exc)})
        except ValueError as exc:
            self._reply(409, {"ok": False, "error": str(exc)})
        except Exception as exc:
            self._reply(500, {"ok": False, "error": f"{type(exc).__name__}: {exc}"})


def main() -> int:
    _identity_ok()
    threading.Thread(target=_scavenge_sessions, name="frank-chatgpt-session-scavenger", daemon=True).start()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
