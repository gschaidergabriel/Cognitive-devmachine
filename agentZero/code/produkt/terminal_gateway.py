from __future__ import annotations

import asyncio
import html
import json
import math
import os
import sqlite3
import sys
import time
from pathlib import Path

from fastapi import Request, WebSocket, WebSocketDisconnect

from .clerk_auth import AuthenticationError, ClerkTokenVerifier
from .identity import (
    SITZUNGEN_JE_MENSCH, terminal_von, CANONICAL_TERMINAL_NAMES, CANONICAL_USER_IDS,
    IdentityRouter, ist_kanonische_sitzung,
)
from .postfach import (
    Postfach,
    PostfachFehler,
    PostfachNichtEingerichtet,
    postfach_fuer_menschen,
    registriere_postfach_wege,
)
from .postfach import zugaenge_laden as postfach_zugaenge_laden
from .store import UnifiedDB
from .zustand import zustand as zustand_lesen

try:  # Die Vorstufe ist im Bau. Fehlt sie, soll /ws/chat scheitern -- nicht der Dienst.
    from .mistral_prestage.pipeline import run_chat_turn
except Exception as _prestage_fehlt:  # pragma: no cover
    _PRESTAGE_FEHLER = _prestage_fehlt
    def run_chat_turn(**_kw):
        raise RuntimeError(f"chat pipeline unavailable: {_PRESTAGE_FEHLER}")
from .terminal_sessions import TerminalSessionManager

_AUTH_MESSAGE_MAX_CHARS = 32_768
_AUTH_TOKEN_MAX_CHARS = 16_384
_CONTROL_MESSAGE_MAX_CHARS = 4_096
# Unter der Rohprompt-Grenze der Vorstufe (100_000) und der Caveman-Grenze des
# Uebersetzers (20_000) -- die knappste Grenze gewinnt, sonst faellt eine
# Nachricht erst tief in der Kette durch.
_CHAT_MESSAGE_MAX_CHARS = 8_000
# Das Terminal haelt Platz 1. Der Chat kommt auf Platz 2, damit die beiden
# Oberflaechen nie um dieselbe active_turns-Zeile streiten.
_CHAT_DEFAULT_PLATZ = 2
_PTY_INPUT_FRAME_MAX_BYTES = 65_536
_PTY_OUTPUT_CHUNK_MAX_BYTES = 65_536
_AUTH_REFRESH_HEADROOM_SECONDS = 10
# /api/history Blaettergroesse: genug fuer einen Bildschirm voll Verlauf ohne
# bei jedem Reload Dutzende Zuege auf einmal zu ziehen; der Bogen bleibt bei
# _HISTORY_MAX_LIMIT, damit ein manipulierter ?limit= nicht die ganze Sitzung
# in einer Antwort zieht.
_HISTORY_DEFAULT_LIMIT = 50
_HISTORY_MAX_LIMIT = 200

# Wo die Menschenseiten liegen. Im Bild unter /opt/clayverse/web (per
# `COPY web ./web`). Die Umgebungsvariable gibt es nur, damit die Testsuite
# ohne Container gegen echte Dateien laufen kann -- der Vorgabewert ist
# derselbe feste Pfad wie vorher, der Betrieb aendert sich dadurch nicht.
_WEB_ROOT_DEFAULT = "/opt/clayverse/web"

# Die HTTP-Wege loesen den Menschen auf Platz 1 auf. Sie lesen und schreiben
# Mail; sie sollen keinen zweiten Sitzungsplatz belegen, um den sich der Chat
# und das Terminal dann streiten.
_HTTP_PLATZ = 1


def _web_root() -> Path:
    return Path(os.environ.get("ENTITYOS_WEB_ROOT", "").strip() or _WEB_ROOT_DEFAULT)


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


def _decode_chat_control(payload: str) -> dict:
    """Begrenztes Entschluesseln der Chat-Steuerrahmen: message | reauth | switch_platz."""
    control = _decode_json_object(payload, name="control", max_chars=_AUTH_MESSAGE_MAX_CHARS)
    ctype = control.get("type")
    if ctype == "message":
        text = control.get("text")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("message text must be non-empty")
        if len(text) > _CHAT_MESSAGE_MAX_CHARS:
            raise ValueError("message text exceeds bound")
    elif ctype == "switch_platz":
        platz = control.get("platz")
        # bool ist in Python ein int -- ohne die Abfrage waere True == Platz 1.
        if isinstance(platz, bool) or not isinstance(platz, int) or platz < 1:
            raise ValueError("switch_platz requires a positive integer platz")
    elif ctype != "reauth" and len(payload) > _CONTROL_MESSAGE_MAX_CHARS:
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


def _runtime_ready(db: UnifiedDB, terminals: TerminalSessionManager) -> bool:
    """Read-only readiness for canonical state and policy-attested product terminals."""
    try:
        schema = db.db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        generation = db.db.execute("SELECT value FROM meta WHERE key='entity_generation'").fetchone()
        users = db.db.execute(
            "SELECT COUNT(*) FROM users WHERE user_id IN ('gabriel','andreas')"
        ).fetchone()
        session_rows = db.db.execute(
            "SELECT user_id,terminal_name,generation FROM sessions ORDER BY user_id"
        ).fetchall()
        # Jeder Mensch hat mehrere gleichzeitige Sitzungen. Eine Abbildung
        # {user_id: row} wuerde sie zu einer zusammenfalten und die zuletzt
        # gelesene gewinnen lassen -- deren Terminalname passt dann nicht zum
        # erwarteten und die Bereitschaft steht dauerhaft auf nein, obwohl
        # alles laeuft. Also sammeln statt ueberschreiben.
        je_mensch: dict[str, list] = {}
        for row in session_rows:
            je_mensch.setdefault(row["user_id"], []).append(row)
        entity_generation = int(generation[0]) if generation else -1
        erwartet = {
            uid: {terminal_von(uid, platz) for platz in range(1, SITZUNGEN_JE_MENSCH + 1)}
            for uid in CANONICAL_USER_IDS
        }
        state_ready = bool(
            schema and schema[0] == "6"
            and entity_generation >= 1
            and users and int(users[0]) == 2
            and set(je_mensch) == CANONICAL_USER_IDS
            and all(
                {r["terminal_name"] for r in je_mensch[uid]} == erwartet[uid]
                and all(int(r["generation"]) == entity_generation for r in je_mensch[uid])
                for uid in CANONICAL_USER_IDS
            )
        )
        if not state_ready:
            return False
        for user_id in CANONICAL_TERMINAL_NAMES:
            binding = terminals.binding(user_id)
            if not terminals._has_session(binding):
                return False
            # `attach_pty()` will fail closed on this same attestation. Readiness
            # must never advertise a stale/unmanaged tmux server that cannot be
            # admitted by the real attach path.
            terminals._assert_tmux_server_policy(binding)
        return True
    except Exception as exc:
        # Bereitschaft darf den Dienst nie reissen -- aber ein stilles False hat
        # hier schon zweimal einen eigenen Fehler als "System nicht bereit"
        # getarnt. Fangen ja, verschweigen nein.
        print(f"readiness probe failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return False


def _history_page(db: UnifiedDB, session_id: str, *, before_ordinal: int | None, limit: int) -> tuple[list[dict], bool]:
    """One page of durable turns for an already-authorised session, oldest-first.

    Reads `turns` -- the canonical per-session record -- newest-last within the
    page. `before_ordinal` walks backward (older) from that cursor when set.
    Fetches one row past `limit` to learn whether an older page exists without
    a second round-trip.
    """
    fetch_limit = limit + 1
    if before_ordinal is None:
        rows = db.db.execute(
            "SELECT turn_id,ordinal,ts,role,content FROM turns WHERE session_id=? "
            "ORDER BY ordinal DESC LIMIT ?",
            (session_id, fetch_limit),
        ).fetchall()
    else:
        rows = db.db.execute(
            "SELECT turn_id,ordinal,ts,role,content FROM turns WHERE session_id=? AND ordinal<? "
            "ORDER BY ordinal DESC LIMIT ?",
            (session_id, before_ordinal, fetch_limit),
        ).fetchall()
    has_more = len(rows) > limit
    rows = list(reversed(rows[:limit]))

    # Assistant turns store Zero's caveman voice as their canonical `content`
    # (see turn_lifecycle.complete()/mistral_prestage.pipeline.run_chat_turn) --
    # the human is never shown that directly on the live path either. Join the
    # pre-stage's own translation log (same wiki.db file, separate connection,
    # WAL-safe) to recover the German text shown live; a turn with no matching
    # row (e.g. a terminal/CLI turn, which was never caveman in the first
    # place) falls back to its own content unchanged.
    # ⭐ Achtung Fallstrick auf der Aufnahmeseite: mistral_prestage.pipeline.run_chat_turn
    # loggt die Uebersetzung in mv_translation_log unter der ID des BENUTZER-Zugs
    # (admission["turn_id"]), waehrend turn_lifecycle.complete() den ASSISTENTEN-Zug
    # mit einer ANDEREN turn_id anlegt. Ein Join mv_translation_log.turn_id ==
    # turns.turn_id (Assistent) traf darum NIE -> die History fiel still auf Zeros
    # englischen Caveman-Rohtext (turns.content) zurueck, obwohl der Live-Pfad Deutsch
    # zeigt. Wir stellen die Zuordnung inhaltsbasiert wieder her: m.caveman_original
    # IST identisch mit turns.content des Assistenten (beides = zero["caveman_answer"]).
    # Innerhalb der Sitzung bekommt jede Assistenten-Zeile die inhaltsgleiche
    # Uebersetzung; bei mehrdeutigen Kurzantworten (z.B. zweimal "Ack.") bricht die
    # Naehe des Benutzer-Ordinals zu (Assistent-Ordinal - 1) den Gleichstand, denn
    # der Benutzer-Zug steht bei der Aufnahme direkt vor dem Assistenten-Zug.
    # Ein echter Terminal/CLI-Zug ohne Uebersetzung faellt unveraendert auf seinen
    # content zurueck.
    translations_by_ordinal: dict[int, dict] = {}
    assistant_rows = [r for r in rows if r["role"] == "assistant"]
    if assistant_rows:
        contents = list({r["content"] for r in assistant_rows})
        placeholders = ",".join("?" * len(contents))
        candidates: list[dict] = []
        try:
            for m in db.db.execute(
                f"SELECT m.translation_id, m.caveman_original, m.german_translation, "
                f"t.ordinal AS user_ordinal "
                f"FROM mv_translation_log m JOIN turns t ON t.turn_id = m.turn_id "
                f"WHERE t.session_id=? AND m.caveman_original IN ({placeholders})",
                (session_id, *contents),
            ):
                candidates.append(dict(m))
        except sqlite3.OperationalError:
            pass  # translation log not created yet (no chat turn has ever run) -- not an error
        for a in assistant_rows:
            passend = [c for c in candidates if c["caveman_original"] == a["content"]]
            if not passend:
                continue
            best = min(passend, key=lambda c: abs((c["user_ordinal"] or 0) - (a["ordinal"] - 1)))
            translations_by_ordinal[a["ordinal"]] = best  # Ordinal ist je Sitzung eindeutig

    turns = []
    for r in rows:
        entry = {
            "turn_id": r["turn_id"],
            "ordinal": r["ordinal"],
            "ts": r["ts"],
            "role": r["role"],
            "text": r["content"],
            "caveman": None,
            "translator_receipt": None,
        }
        tr = translations_by_ordinal.get(r["ordinal"]) if r["role"] == "assistant" else None
        if tr is not None:
            entry["text"] = tr["german_translation"]
            entry["caveman"] = tr["caveman_original"]
            entry["translator_receipt"] = tr["translation_id"]
        turns.append(entry)
    return turns, has_more


def create_terminal_app(*, db: UnifiedDB, clerk_map: dict[str, str], verifier: ClerkTokenVerifier,
                        state_root: str | Path, publishable_key: str, frontend_api_url: str,
                        terminals: TerminalSessionManager | None = None):
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles

    identity = IdentityRouter(db, clerk_map)
    # One arbiter, not two. The autonomy pulse attestation requires the browser
            # attach path and the pulse to hold the SAME TerminalSessionManager, so
            # autonomy can never drive a terminal the human side does not see.
            # Creating a second one here silently made that attestation impossible.
    terminals = terminals or TerminalSessionManager(state_root, os.environ.get("CLAYVERSE_WORKSPACE", "/workspace"))
    app = FastAPI(title="EntityOS", docs_url=None, redoc_url=None)

    @app.middleware("http")
    async def _statik_immer_frisch(request, call_next):
        # ⭐ Statische Assets (schale.js/css, zero-avatar.js, emergenz.js,
        # ...) NIE blind aus dem Browser-Cache: "no-cache" heisst NICHT
        # "nicht cachen", sondern "vor Gebrauch revalidieren" -> 304 wenn
        # unveraendert (billig), frisch bei jeder Aenderung. Ohne das zeigte
        # der Browser trotz Deploy altes UI (altes Logo, alte Animation).
        resp = await call_next(request)
        pfad = request.url.path
        if pfad.startswith("/web/") or pfad.startswith("/vendor/"):
            resp.headers["Cache-Control"] = "no-cache"
        return resp

    @app.on_event("startup")
    def _zero_vorwaermen():
        # ⭐ Den dauerhaften Zero-Prozess-Pool schon beim Container-Start
        # anwerfen, damit der ERSTE Zug nach einem Neustart nicht kalt ist.
        try:
            from .mistral_prestage.warm_zero import POOL
            POOL.starten()
        except Exception:
            pass  # Vorwaermen darf den Start nie blockieren

    app.mount("/vendor/xterm", StaticFiles(directory="/opt/clayverse/vendor/xterm", check_dir=False), name="xterm")
    app.mount("/web", StaticFiles(directory="/opt/clayverse/web", check_dir=False), name="web")
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
        ready = _runtime_ready(db, terminals)
        return JSONResponse({
            "status": "ready" if ready else "not_ready",
            "scope": "runtime",
            "canonical_state": "unifieddb",
            "surface": "permanent-claude-code-terminal",
        }, status_code=200 if ready else 503)

    @app.get("/api/history")
    async def history(request: Request):
        # Same authentication as /ws/chat's first frame: a verified Clerk
        # session token, here carried as a normal Authorization bearer header
        # because this is a plain GET, not a socket handshake. Nothing here
        # trusts the query string for identity -- only the verified subject
        # does, exactly as required.
        try:
            token = ClerkTokenVerifier.bearer(request.headers.get("Authorization"))
            claims = await asyncio.to_thread(verifier.verify, token)
        except AuthenticationError:
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        clerk_subject = str(claims.get("sub", ""))
        user_id = identity.clerk_map.get(clerk_subject)
        if user_id not in CANONICAL_USER_IDS:
            return JSONResponse({"error": "unauthorized"}, status_code=401)

        # The session id comes from the query string and is UNTRUSTED. It is
        # never used to look anything up until it has been checked against the
        # canonical session list of the user the verified token names -- this
        # is the exact check that was missing the one time this system leaked
        # one user's memory into the other's session.
        session_id = request.query_params.get("session_id", "")
        if not ist_kanonische_sitzung(session_id, user_id):
            return JSONResponse({"error": "forbidden"}, status_code=403)

        before_raw = request.query_params.get("before")
        before_ordinal: int | None = None
        if before_raw is not None:
            try:
                before_ordinal = int(before_raw)
            except ValueError:
                return JSONResponse({"error": "invalid before parameter"}, status_code=400)
            if before_ordinal < 1:
                return JSONResponse({"error": "invalid before parameter"}, status_code=400)

        limit_raw = request.query_params.get("limit")
        limit = _HISTORY_DEFAULT_LIMIT
        if limit_raw is not None:
            try:
                limit = int(limit_raw)
            except ValueError:
                return JSONResponse({"error": "invalid limit parameter"}, status_code=400)
            if limit < 1 or limit > _HISTORY_MAX_LIMIT:
                return JSONResponse({"error": "invalid limit parameter"}, status_code=400)

        turns, has_more = await asyncio.to_thread(
            _history_page, db, session_id, before_ordinal=before_ordinal, limit=limit)
        return JSONResponse({
            "session_id": session_id,
            "user_id": user_id,
            "turns": turns,
            "has_more": has_more,
        })

    _CHAT_PAGE = Path("/opt/clayverse/web/chat/index.html")

    @app.get("/", response_class=HTMLResponse)
    async def chat_index():
        key = html.escape(publishable_key, quote=True)
        api = html.escape(frontend_api_url, quote=True)
        if not key or not api:
            return HTMLResponse("Clerk web configuration is incomplete", status_code=503)
        if not _CHAT_PAGE.is_file():
            # Kein stiller Rueckfall auf das Terminal: eine fehlende Chatseite ist
            # ein Bauproblem und soll als solches sichtbar sein, nicht als
            # "sieht heute halt anders aus".
            return HTMLResponse("chat surface missing from image", status_code=503)
        page = _CHAT_PAGE.read_text(encoding="utf-8")
        page = page.replace("__CLERK_API__", api).replace("__CLERK_PUBLISHABLE_KEY__", key)
        return HTMLResponse(page)

    # ── Die Mailbox ───────────────────────────────────────────────────────
    # Eignerentscheidung 2026-08-18: es gibt nur den Chat und die Mailbox.
    # Keine Startseite -- "/" bleibt unveraendert der Chat.
    # ── Seitenuebersicht: was wir hosten, wie es laeuft, wie man es aendert ──
    _SEITEN_PAGE = Path("/opt/clayverse/web/seiten/index.html")

    @app.get("/api/seiten")
    async def seiten_api(request: Request):
        # Dieselbe Anmeldepruefung wie /api/history. Die Uebersicht nennt
        # Verzeichnisse und Besucherzahlen -- das gehoert hinter die Anmeldung,
        # auch wenn es keine Geheimnisse sind.
        try:
            token = ClerkTokenVerifier.bearer(request.headers.get("Authorization"))
            claims = await asyncio.to_thread(verifier.verify, token)
        except AuthenticationError:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        if identity.clerk_map.get(str(claims.get("sub", ""))) not in CANONICAL_USER_IDS:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        from . import seiten as _seiten
        return JSONResponse(await asyncio.to_thread(_seiten.uebersicht))

    @app.get("/api/me")
    async def me_api(request: Request):
        # Der Ausweis-Endpunkt: NUR die zwei kanonischen Konten bekommen hier ein
        # 200 mit ihrer user_id. Jedes andere angemeldete Clerk-Konto -- und seit
        # die Instanz offen stand, gibt es solche -- bekommt 401. Das Frontend
        # fragt das direkt nach der Anmeldung ab und zeigt einem Fremdkonto gar
        # keine Oberflaeche. Reine Bestaetigung, keine Geheimnisse.
        try:
            token = ClerkTokenVerifier.bearer(request.headers.get("Authorization"))
            claims = await asyncio.to_thread(verifier.verify, token)
        except AuthenticationError:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        uid = identity.clerk_map.get(str(claims.get("sub", "")))
        if uid not in CANONICAL_USER_IDS:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        return JSONResponse({"user_id": uid})

    @app.get("/api/systeme")
    async def systeme_api(request: Request):
        # Dieselbe Anmeldepruefung wie /api/seiten. Zeigt den Live-Zustand der
        # drei Tailscale-Maschinen (online, CPU/RAM/Disk) -- keine Geheimnisse,
        # aber hinter die Anmeldung. Der Host-Sammler (systemwacht) schreibt die
        # Datei; wir liefern sie nur aus und haengen das Alter in Sekunden an,
        # damit das Frontend "veraltet" erkennen kann.
        try:
            token = ClerkTokenVerifier.bearer(request.headers.get("Authorization"))
            claims = await asyncio.to_thread(verifier.verify, token)
        except AuthenticationError:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        if identity.clerk_map.get(str(claims.get("sub", ""))) not in CANONICAL_USER_IDS:
            return JSONResponse({"error": "unauthorized"}, status_code=401)
        import json as _json, time as _time
        try:
            with open("/var/lib/clay/systeme.json", encoding="utf-8") as f:
                d = _json.load(f)
        except Exception:
            return JSONResponse({"stand": 0, "systeme": [], "alter_s": None})
        d["alter_s"] = max(0, int(_time.time()) - int(d.get("stand", 0)))
        return JSONResponse(d)

    @app.get("/seiten", response_class=HTMLResponse)
    async def seiten_index():
        key = html.escape(publishable_key, quote=True)
        api = html.escape(frontend_api_url, quote=True)
        if not key or not api:
            return HTMLResponse("Clerk web configuration is incomplete", status_code=503)
        if not _SEITEN_PAGE.is_file():
            return HTMLResponse("seiten surface missing from image", status_code=503)
        page = _SEITEN_PAGE.read_text(encoding="utf-8")
        return HTMLResponse(page.replace("__CLERK_API__", api).replace("__CLERK_PUBLISHABLE_KEY__", key))

    @app.get("/postfach", response_class=HTMLResponse)
    async def postfach_index():
        key = html.escape(publishable_key, quote=True)
        api = html.escape(frontend_api_url, quote=True)
        if not key or not api:
            return HTMLResponse("Clerk web configuration is incomplete", status_code=503)
        seite = _web_root() / "postfach" / "index.html"
        if not seite.is_file():
            # Gleiche Begruendung wie beim Chat: kein stiller Rueckfall auf eine
            # andere Seite. Eine fehlende Oberflaeche ist ein Bauproblem und
            # soll als solches sichtbar sein, nicht als "sieht heute halt
            # anders aus".
            return HTMLResponse("postfach surface missing from image", status_code=503)
        page = seite.read_text(encoding="utf-8")
        page = page.replace("__CLERK_API__", api).replace("__CLERK_PUBLISHABLE_KEY__", key)
        return HTMLResponse(page)

    # ── Der HTTP-Zweig fuer Zustand und Mail ──────────────────────────────
    async def _angemeldeter_mensch(request) -> tuple[str, str]:
        """Bearer-Token -> (Mensch, Sitzung).

        Dieselbe Kette wie bei /api/history und beim WebSocket-Handschlag:
        Clerk pruefen, den Ablaufzeitpunkt erzwingen, dann ueber den
        IdentityRouter aufloesen. `verifier.verify` kann ins Netz gehen (JWKS)
        und gehoert deshalb nicht in die Ereignisschleife.
        """
        token = ClerkTokenVerifier.bearer(request.headers.get("Authorization"))
        claims = await asyncio.to_thread(verifier.verify, token)
        _auth_expiry_deadline(claims)
        return identity.resolve(str(claims["sub"]), platz=_HTTP_PLATZ)

    def _antwort_auf_fehler(exc: Exception) -> JSONResponse:
        """Ausnahmen -> Statuscodes, an genau einer Stelle.

        AuthenticationError erbt von PermissionError -- die Reihenfolge ist
        deshalb keine Geschmacksfrage: umgekehrt bekaeme ein abgelaufenes Token
        403 statt 401, und der Browser wuerde nicht erneuern, sondern aufgeben.
        Fremde Fehlertexte gehen nie roh nach aussen; sie koennen eine
        Serverantwort mit Zugangsdaten tragen.
        """
        if isinstance(exc, AuthenticationError):
            return JSONResponse({"ok": False, "error": "unauthorized"}, status_code=401)
        if isinstance(exc, PermissionError):
            return JSONResponse({"ok": False, "error": "forbidden"}, status_code=403)
        if isinstance(exc, PostfachNichtEingerichtet):
            return JSONResponse({"ok": False, "error": "postfach_not_configured"}, status_code=503)
        if isinstance(exc, PostfachFehler):
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=502)
        if isinstance(exc, (ValueError, KeyError, TypeError)):
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=400)
        print(f"api failed: {type(exc).__name__}", file=sys.stderr)
        return JSONResponse({"ok": False, "error": "internal_error"}, status_code=500)

    @app.get("/api/zustand")
    async def api_zustand(request: Request):
        """Nur lesend, Clerk-geschuetzt.

        Schlank gehalten (Eignerentscheidung 2026-08-18): die Oberflaeche liest
        daraus die Zahl am Mailbox-Punkt und die Bereitschaft. Die uebrigen
        Zaehlwerte kommen aus denselben Tabellen wie ueberall sonst und kosten
        nichts.

        ⭐ Was nicht messbar ist, kommt als null zurueck. Eine 0 waere hier eine
        Behauptung ("es gibt keine"), null ist eine Auskunft ("ich weiss es
        nicht") -- und "Postfach nicht erreichbar" ist etwas anderes als "keine
        ungelesene Mail".
        """
        try:
            user_id, _session_id = await _angemeldeter_mensch(request)
        except Exception as exc:
            return _antwort_auf_fehler(exc)

        def _ungelesen() -> int:
            zugaenge = postfach_zugaenge_laden()
            return Postfach(
                zugaenge, postfach_fuer_menschen(zugaenge, user_id)
            ).ungelesen_im_posteingang()

        return JSONResponse(await asyncio.to_thread(
            zustand_lesen, db, user_id=user_id,
            ungelesen=_ungelesen,
            bereit=lambda: _runtime_ready(db, terminals),
        ))

    registriere_postfach_wege(
        app, db=db, mensch_aufloesen=_angemeldeter_mensch,
        antwort_auf_fehler=_antwort_auf_fehler,
    )

    # Das alte Terminal bleibt erreichbar, bis der neue Weg einmal getragen hat.
    @app.get("/terminal", response_class=HTMLResponse)
    async def index():
        key = html.escape(publishable_key, quote=True)
        api = html.escape(frontend_api_url, quote=True)
        if not key or not api:
            return HTMLResponse("Clerk web configuration is incomplete", status_code=503)
        return HTMLResponse(f'''<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>EntityOS</title>
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
        if(m.type==='error'){{terminalReady=false;term.writeln('\\r\\n[EntityOS] '+m.message);return;}}
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

    @app.websocket("/ws/chat")
    async def chat_ws(ws: WebSocket):
        await ws.accept()
        send_lock = asyncio.Lock()
        # Waechter gegen eine kuenftige Nebenlaeufigkeit. Heute gibt es nur diese
        # eine Schleife, also kann er nie greifen -- er steht hier, damit ein
        # spaeterer Umbau auf nebenlaeufige Pumpen nicht still zwei Zuege startet.
        busy = False

        async def send_json(payload: dict) -> None:
            async with send_lock:
                await ws.send_text(json.dumps(payload))

        try:
            first = await asyncio.wait_for(ws.receive_text(), timeout=10)
            hello = _decode_json_object(first, name="auth", max_chars=_AUTH_MESSAGE_MAX_CHARS)
            if hello.get("type") != "auth":
                raise AuthenticationError("authentication must be first message")
            claims = await asyncio.to_thread(verifier.verify, _auth_token(hello))
            auth_expires_at = _auth_expiry_deadline(claims)
            clerk_subject = str(claims["sub"])
            clerk_session_id = str(claims["sid"])

            platz = _CHAT_DEFAULT_PLATZ
            user_id, session_id = identity.resolve(clerk_subject, platz=platz)
            await send_json({
                "type": "ready", "user_id": user_id, "session_id": session_id,
                "platz": platz, "plaetze": identity.plaetze(clerk_subject),
                "auth_expires_at": int(auth_expires_at),
            })

            while True:
                remaining = auth_expires_at - time.time()
                if remaining <= 0:
                    raise AuthenticationError("Clerk session token expired")
                message = await asyncio.wait_for(ws.receive(), timeout=remaining)
                if auth_expires_at <= time.time():
                    raise AuthenticationError("Clerk session token expired")
                if message.get("type") == "websocket.disconnect":
                    return
                if message.get("bytes") is not None:
                    raise ValueError("chat surface does not accept binary frames")
                if message.get("text") is None:
                    raise ValueError("unsupported WebSocket chat frame")

                control = _decode_chat_control(message["text"])
                ctype = control.get("type")

                if ctype == "reauth":
                    refreshed = await asyncio.to_thread(verifier.verify, _auth_token(control))
                    auth_expires_at = _reauthenticated_expiry(
                        refreshed, expected_subject=clerk_subject,
                        expected_clerk_session_id=clerk_session_id)
                    await send_json({"type": "reauthenticated", "auth_expires_at": int(auth_expires_at)})
                    continue

                if ctype == "switch_platz":
                    if busy:
                        await send_json({"type": "error", "message": "cannot switch session while a reply is in flight"})
                        continue
                    try:
                        user_id, session_id = identity.resolve(clerk_subject, platz=control["platz"])
                    except PermissionError:
                        await send_json({"type": "error", "message": "no such session slot"})
                        continue
                    platz = control["platz"]
                    # ⚠️ Die Kennung MUSS mit dem Platz neu aufgeloest werden.
                    # Vorher wurde nur `platz` gesetzt und die alte session_id
                    # weitergemeldet: der Verlauf lud dann die Zuege der
                    # FALSCHEN Sitzung -- mit Status 200, also unauffaellig.
                    # Eine falsche Antwort sieht aus wie eine richtige.
                    user_id, session_id = identity.resolve(clerk_subject, platz=platz)
                    _require_auth_lease_live(auth_expires_at)
                    await send_json({
                        "type": "ready", "user_id": user_id, "session_id": session_id,
                        "platz": platz, "plaetze": identity.plaetze(clerk_subject),
                        "auth_expires_at": int(auth_expires_at),
                    })
                    continue

                if ctype != "message":
                    raise ValueError("unsupported chat control message")
                if busy:
                    await send_json({"type": "error", "message": "a reply is already in flight"})
                    continue

                _require_auth_lease_live(auth_expires_at)
                busy = True
                await send_json({"type": "pending"})
                try:
                    result = await asyncio.to_thread(
                        run_chat_turn, db=db, user_id=user_id, session_id=session_id,
                        message=control["text"], record_via_turnlifecycle=True)
                except Exception as exc:
                    await send_json({"type": "error", "message": str(exc)})
                    continue
                finally:
                    busy = False

                # KEINE Lease-Nachkontrolle hier: der Zug war bei Beginn
                # autorisiert (Pruefung oben) UND ist via TurnLifecycle bereits
                # in der DB. Laeuft das kurzlebige Clerk-Token waehrend eines
                # langen Zugs ab, darf die fertige Antwort NICHT verworfen werden
                # -- das war der Bug 'Fehler im Chat, Antwort erst nach Reload'.
                # Die Lease-Grenze erzwingt der Schleifenkopf beim naechsten
                # Empfang weiter (getestetes Verhalten bleibt).
                await send_json({
                    "type": "reply",
                    "text": result["reply"],
                    # Der Mensch sieht nie, was Zero wirklich sagte. Rohfassung und
                    # ein Beleg, der auf eine DB-Zeile zeigt, fahren deshalb mit --
                    # eine Uebersetzung, die niemand pruefen kann, ist schlechter
                    # als keine.
                    "caveman": result.get("caveman"),
                    "turn_id": result.get("turn_id"),
                    "translator_receipt": result.get("translation_id"),
                    "auth_expires_at": int(auth_expires_at),
                })

        except (WebSocketDisconnect, asyncio.CancelledError):
            pass
        except Exception as exc:
            try:
                await send_json({"type": "error", "message": str(exc)})
            except Exception:
                pass
        finally:
            # Ein nach der Abweisung offen bleibender Socket ist nicht nur ein Leck:
            # er schenkt einem Angreifer einen Wiederholungskanal ohne neuen
            # TLS-Handschlag. Billig zu halten, billig zu haemmern.
            try:
                await ws.close()
            except Exception:
                pass

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
