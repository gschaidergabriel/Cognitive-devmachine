from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path

from .. import identity  # coordinator-owned, imported not edited

MANAGED_SETTINGS = "/etc/claude-code/managed-settings.json"
# Dynamically rendered identity -- the SAME file the interactive tmux terminal
# points --append-system-prompt-file at (clayverse.terminal_sessions). NOT the
# static image copy at /opt/clayverse/runtime/CLAUDE.md.
RUNTIME_PROMPT = "/var/lib/clayverse/runtime/CLAUDE.md"

# Everything managed-settings.json currently permits. Callers may pass a
# narrower subset (F74 "pre-selected tools"); anything outside this set is
# outside managed policy and cannot be granted here regardless.
DEFAULT_ALLOWED_TOOLS = (
    "mcp__clayverse__session_state",
    "mcp__clayverse__request_effect",
    "mcp__clayverse__request_autonomy_effect",
    "mcp__clayverse__udb_embedding_search",
    "mcp__clayverse__udb_embedding_store",
    "mcp__clayverse__udb_neuropedia_activation",
    "mcp__clayverse__udb_memory_add",
    "mcp__clayverse__udb_memory_search",
    # Ohne diese zwei ist Zero blind fuer die Menschen: gemessen antwortete es
    # "UNBEKANNT -- fuer beide", weil die Angaben in Tabellen stehen, zu denen
    # memory_search und embedding_search keinen Weg haben.
    "mcp__clayverse__menschen_profil",
    "mcp__clayverse__wiki_zuordnung",
    "mcp__clayverse__lagebild",
    # Der Raum: ohne diese vier sitzt jeder Platz allein und faehrt den anderen
    # in die Arbeit hinein.
    "mcp__clayverse__raum_sehen",
    "mcp__clayverse__raum_sagen",
    "mcp__clayverse__raum_rufen",
    "mcp__clayverse__raum_frei",
    # Zero handelt nicht selbst -- es schnuert. Ohne diese zwei bleibt die
    # Regel eine Absichtserklaerung.
    "mcp__clayverse__paket_schnueren",
    "mcp__clayverse__paket_lage",
    # Faehigkeiten kennen, ohne Schluessel zu sehen.
    "mcp__clayverse__tresor_katalog",
    "mcp__clayverse__tresor_zeigen",
    # Ohne dieses Werkzeug ist der Korpus per Inhaltsfrage unerreichbar:
    # embedding_search liefert nur Kennungen ohne Text, der lexikalische Weg
    # nur Dateinamen. Gemessen: die Antwort stand in der Datenbank und Zero
    # sagte korrekt "unbekannt".
    "mcp__clayverse__korpus_suchen",
    "mcp__clayverse__artikel_lesen",
    "mcp__clayverse__dateien_suchen",
    "mcp__clayverse__korpus_tief",
    # ⭐ Handlungsfaehigkeit ohne Schale: lesen, suchen, aendern,
    # veroeffentlichen -- jede Faehigkeit benannt und eingezaeunt, statt Bash.
    "mcp__clayverse__werkbank_liste",
    "mcp__clayverse__werkbank_lesen",
    "mcp__clayverse__werkbank_suchen",
    "mcp__clayverse__werkbank_aendern",
    "mcp__clayverse__werkbank_stand",
    "mcp__clayverse__werkbank_veroeffentlichen",
    # Zero haelt selbst Platz auf dem Wirt -- Auftrag des Eigners 18.08.
    "mcp__clayverse__seite_pruefen",
    "mcp__clayverse__speicher_lage",
    "mcp__clayverse__speicher_aufraeumen",
    "mcp__clayverse__speicher_rueckweg",
    "mcp__clayverse__speicher_abschaffen",
    # Nachgereicht 18.08.: beide standen in policy/managed-settings.json, fehlten
    # aber hier -- die engere Liste gewinnt, also war die Freigabe wirkungslos.
    "mcp__clayverse__bahn_faehigkeit",
    "mcp__clayverse__bahn_lage",
    # Ohne dieses Werkzeug gibt es keinen Weg vom Urteil eines Menschen zum
    # Lernen des Abrufs -- die Belohnungsfunktion haette dann nur eine Quelle
    # (verifizierte Wirkungen), und die springt fast nie an.
    "mcp__clayverse__abruf_rueckmeldung",
)

MAX_PROMPT_CHARS = 20_000
# Gemessen 2026-08-18 als Andreas: eine normale, belegte Antwort brauchte 102 s,
# eine zweite lief bei 90 s in die Frist und war verloren. Zero schlaegt mehrere
# Werkzeuge nach, bevor es antwortet -- genau das wollen wir.
# Eine zu knappe Frist ist die teuerste Art zu scheitern: die Arbeit wird
# vollstaendig geleistet, bezahlt und dann weggeworfen.
DEFAULT_TIMEOUT_SECONDS = 240
_BLOCKED_PREFIX = "UserPromptSubmit operation blocked by hook"


class HeadlessZeroError(RuntimeError):
    pass



# ── Der anwesende Mensch, deterministisch an die Systemanweisung ───────────

_ANWESEND_UNBEKANNT = """<anwesender_mensch status="NICHT_ERMITTELBAR">
  Es wurde nachgesehen. Der kanonische Zustand liefert fuer diese Sitzung keinen
  Menschen. Sage, dass du nicht weisst, mit wem du sprichst -- und leite es NICHT
  aus einer Kennung, einer Mailadresse oder dem Gespraechstext ab.
</anwesender_mensch>"""


def _anwesenheitsblock(db_path: str, user_id: str, session_id: str) -> str:
    """Kanonischer Anwesenheitsbeleg, aus der Datenbank, ohne Modell dazwischen.

    Faellt auf einen ausdruecklichen NICHT_ERMITTELBAR-Block zurueck. Nie auf
    Schweigen: ein fehlender Block und ein leerer Block sehen fuer Zero gleich
    aus, aber nur beim zweiten weiss es, dass nachgesehen wurde.
    """
    try:
        from ..store import UnifiedDB
        from .. import profile as _profile
        return _profile.sitzungsvorspann(UnifiedDB(db_path), user_id, session_id)
    except Exception:
        return _ANWESEND_UNBEKANNT


def _systemanweisung(db_path: str, user_id: str, session_id: str) -> str:
    """Laufzeitidentitaet + Anwesenheit in EINER Datei, weil das Flag nur eine nimmt."""
    grund = Path(RUNTIME_PROMPT).read_text(encoding="utf-8")
    return grund.rstrip() + "\n\n" + _anwesenheitsblock(db_path, user_id, session_id) + "\n"


def run_headless(
    caveman_prompt: str,
    *,
    user_id: str,
    session_id: str,
    tool_selection: list[str] | None = None,
    home: str = "/var/lib/clay",
    db_path: str = "/var/lib/clay/wiki.db",
    state_root: str = "/var/lib/clayverse",
    max_turns: int = 6,
    timeout: int = DEFAULT_TIMEOUT_SECONDS,
    pipeline_managed: bool = True,
) -> dict:
    """One headless, non-interactive, tool-capable Zero call.

    Mirrors clayverse.terminal_sessions.TerminalSessionManager.ensure()'s proven
    claude_argv/env_argv shape (same --settings/--setting-sources/--tools/
    --allowedTools/--permission-mode/--append-system-prompt-file) so headless
    Zero gets the SAME identity and policy surface as the interactive terminal,
    not a weaker ad-hoc one. Differs only in invocation shape: -p one-shot
    instead of a long-lived tmux pty session, --no-session-persistence (product
    law: Claude Code is runtime cognition, never durable identity/memory --
    UnifiedDB is; a stateless one-shot call is what forces that).

    ⚠️ READ BEFORE CALLING WITH A REAL user_id/session_id -- history and
    current state, in that order:
    the managed UserPromptSubmit/Stop/StopFailure hooks (/etc/claude-code/
    managed-settings.json, allowManagedHooksOnly=true) fire on `claude -p`
    exactly as they do interactively -- there is no CLI flag that skips them
    without also losing OAuth auth (--bare requires ANTHROPIC_API_KEY, this
    deployment authenticates via the OAuth credential at
    /var/lib/clay/.claude/.credentials.json, not an API key). Firing means the
    hook independently calls TurnLifecycle.begin_admission()/complete() using
    the raw CAVEMAN prompt as if a human had typed it -- a second, colliding
    admission path, on top of whatever this module's caller does with
    TurnLifecycle itself.

    pipeline_managed=True (the default here) sets CLAYVERSE_PIPELINE_MANAGED=1
    in the subprocess env for exactly this reason. MEASURED 2026-08-18: at
    that point the flag genuinely had NO EFFECT -- terminal_hooks.py did not
    check it yet, and two colliding turns landed in session:andreas from this
    module's own measurement runs (disclosed in the report, not cleaned up;
    turns are an append-only causal ledger by design -- raw deletion would be
    more destructive than the noise it removes). THAT WAS A REAL BUG.

    IT IS NOW FIXED: clayverse/terminal_hooks.py's _main() checks
    CLAYVERSE_PIPELINE_MANAGED as the very first thing it does, before
    touching stdin or the DB, and returns {"suppressOutput": true} right
    there. It is positioned deliberately ahead of user_prompt()'s
    begin_admission() call so a pipeline-managed invocation never reaches
    admission at all -- the cheapest way to not double-admit is to never
    start. Re-verified against the live DB: active_turns is empty (no turn
    stuck mid-admission), and the leftover session:andreas turns from the
    2026-08-18 measurement runs sit 49s-8min apart -- repeated manual test
    calls, not a real collision (a genuine double-admission would land
    milliseconds apart).

    The danger below is still real if you override the default:
    pipeline_managed=False omits CLAYVERSE_PIPELINE_MANAGED from the env, so
    terminal_hooks.py's hook takes its normal path and calls
    TurnLifecycle.begin_admission()/complete() on the raw CAVEMAN prompt as if
    a human had typed it -- the exact second-admitter collision described
    above, now guaranteed rather than theoretical. Only pass
    pipeline_managed=False if the hook path is disabled some other way (e.g.
    a non-managed settings file) and you know that for a fact.
    """
    if user_id not in {"gabriel", "andreas"}:
        raise HeadlessZeroError("headless Zero requires a canonical user id")
    if not identity.ist_kanonische_sitzung(session_id, user_id):
        raise HeadlessZeroError("session id must be one of the user's canonical session slots")
    if not isinstance(caveman_prompt, str) or not caveman_prompt or len(caveman_prompt) > MAX_PROMPT_CHARS:
        raise HeadlessZeroError("invalid caveman prompt")

    tools = list(tool_selection) if tool_selection else list(DEFAULT_ALLOWED_TOOLS)
    if not tools:
        raise HeadlessZeroError("tool selection must not be empty")
    unknown = set(tools) - set(DEFAULT_ALLOWED_TOOLS)
    if unknown:
        raise HeadlessZeroError(f"tool selection outside managed policy: {sorted(unknown)}")
    if not Path(RUNTIME_PROMPT).is_file():
        raise HeadlessZeroError("runtime identity file missing -- cannot call headless without it")

    # Eine Wegwerfdatei je Aufruf: --append-system-prompt-file nimmt genau eine,
    # und der Anwesenheitsblock ist je Sitzung verschieden. Eindeutiger Name,
    # damit zwei gleichzeitige Sitzungen sich nicht gegenseitig ueberschreiben.
    import tempfile
    _fd, _sysdatei = tempfile.mkstemp(prefix="zero-sys-", suffix=".md", dir="/tmp")
    with os.fdopen(_fd, "w", encoding="utf-8") as _f:
        _f.write(_systemanweisung(db_path, user_id, session_id))

    argv = [
        "claude", "-p", caveman_prompt,
        "--settings", MANAGED_SETTINGS,
        "--setting-sources", "",
        "--tools", "",
        "--allowedTools", *tools,
        "--permission-mode", "dontAsk",
        "--append-system-prompt-file", _sysdatei,
        "--output-format", "json",
        "--no-session-persistence",
        "--max-turns", str(max_turns),
    ]
    env = {
        "HOME": home,
        "PATH": "/usr/local/bin:/usr/bin:/bin",
        "LANG": "C.UTF-8",
        "PYTHONPATH": "/opt/clayverse",
        "CLAYVERSE_STATE_ROOT": state_root,
        "CLAYVERSE_DB_PATH": db_path,
        "CLAYVERSE_USER_ID": user_id,
        "CLAYVERSE_SESSION_ID": session_id,
        "DISABLE_UPDATES": "1",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
        "CLAUDE_CODE_SKIP_PROMPT_HISTORY": "1",
        "CLAUDE_CODE_DISABLE_AUTO_MEMORY": "1",
        "CLAUDE_CODE_DISABLE_CLAUDE_MDS": "1",
        "CLAUDE_CODE_DISABLE_BACKGROUND_TASKS": "1",
    }
    if pipeline_managed:
        env["CLAYVERSE_PIPELINE_MANAGED"] = "1"

    started = time.perf_counter()
    try:
        cp = subprocess.run(
            argv, env=env, capture_output=True, text=True, timeout=timeout, check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HeadlessZeroError("headless Zero call timed out") from exc
    finally:
        # Die Datei nennt einen Menschen beim Namen. Sie liegt in einem tmpfs,
        # aber liegenbleiben darf sie trotzdem nicht -- auch nicht nach einem
        # Zeitueberlauf, gerade dann nicht.
        try:
            os.unlink(_sysdatei)
        except OSError:
            pass
    wall_ms = (time.perf_counter() - started) * 1000.0

    if cp.returncode != 0:
        # ⚠️ stdout MUSS mit in die Meldung. Die Claude-CLI schreibt ihre
        # Fehler ueberwiegend nach stdout, nicht nach stderr -- die alte
        # Fassung zeigte deshalb `stderr=''` und sah aus, als sei der Prozess
        # wortlos gestorben. Vier Testlaeufe lang war das die einzige Auskunft.
        raise HeadlessZeroError(
            f"headless Zero exited rc={cp.returncode} "
            f"stderr={(cp.stderr or '')[:400]!r} stdout={(cp.stdout or '')[:900]!r}")
    try:
        envelope = json.loads(cp.stdout)
    except json.JSONDecodeError as exc:
        raise HeadlessZeroError("headless Zero output is not JSON") from exc
    if not isinstance(envelope, dict):
        raise HeadlessZeroError("headless Zero envelope must be an object")
    if envelope.get("is_error"):
        raise HeadlessZeroError(f"headless Zero returned an error envelope: {str(envelope.get('result',''))[:500]}")

    result_text = envelope.get("result")
    if not isinstance(result_text, str) or not result_text:
        raise HeadlessZeroError("headless Zero returned no result text")
    if result_text.startswith(_BLOCKED_PREFIX):
        raise HeadlessZeroError(f"blocked by managed hook: {result_text[:300]}")

    return {
        "caveman_answer": result_text,
        "num_turns": envelope.get("num_turns"),
        "duration_ms_claude_code": envelope.get("duration_ms"),
        "duration_ms_api": envelope.get("duration_api_ms"),
        "cost_usd": envelope.get("total_cost_usd"),
        "wall_ms": wall_ms,
        "claude_session_id": envelope.get("session_id"),
    }
