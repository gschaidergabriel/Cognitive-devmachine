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
    # ⭐ Sehen. Ohne diese zwei kann Zero ein hochgeladenes Bild zwar mit Read
    # oeffnen, aber nichts davon bleibt: kein Gegenstand mit stabiler Kennung,
    # keine Evidenzspur, kein Wiedererkennen beim naechsten Foto. Der
    # Unterschied ist der zwischen Anschauen und Gedaechtnis.
    "mcp__clayverse__bild_ansehen",
    "mcp__clayverse__bild_gedaechtnis",
    # (Arbeitspakete entfernt 19.08.: Zero handelt jetzt direkt mit nativen Tools.)
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
    # Das Messgeraet fuer den eigenen Abruf: Kartenversion, Wegehierarchie
    # samt Urteil, Erfolgsquote. Rein lesend, speist die Karte NICHT.
    "mcp__clayverse__abruf_lage",
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
    "mcp__clayverse__seite_diagnose",
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
    "mcp__clayverse__pc_lage",
    "mcp__clayverse__pc_bildschirme",
    "mcp__clayverse__pc_fenster",
    "mcp__clayverse__pc_fenster_holen",
    "mcp__clayverse__pc_sehen",
    "mcp__clayverse__pc_eingabe",
    "mcp__clayverse__pc_ausfuehren",
    "mcp__clayverse__browser_oeffnen",
    "mcp__clayverse__browser_lesen",
    "mcp__clayverse__browser_screenshot",
    "mcp__clayverse__browser_klick",
    "mcp__clayverse__browser_tippen",
    "mcp__clayverse__browser_formular",
    "mcp__clayverse__browser_navigieren",
    "mcp__clayverse__schluessel_anlernen",
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


# ── GRF-Denkrahmen, jede Runde -- der erste sichere Schritt Richtung ClayCode-
# only-Kognition (Gabriel 2026-08-22, VERFASSUNG.md: "Der GWT/ClayCode-Minimal-
# Meta-Prompt wird JEDE RUNDE injiziert -- auch beim normalen Zero, nicht nur
# beim Architekten"). Angepasst aus GRF_CLAYCODE_INJEKTION.md: jener Meta-Prompt
# ist fuer ARCHITEKTUR-ERZEUGUNG formuliert ("execute all architecture
# generations") -- das waere bei "wie spaet ist es" falsch woertlich injiziert.
# Dieser Rahmen ist die ALLGEMEINE Fassung: DENKDISZIPLIN (kausaler Zustands-
# uebergang statt Korrelation, harte Invarianten statt weicher Kommentare,
# keine Hypothesen-Monopolisierung) fuer JEDE Runde -- nicht der Sprachwechsel.
# Die ClayCode-Output-/Uebersetzer-Umstellung ist ein SPAETERER, eigens
# gemessener Schritt (siehe VERFASSUNG.md) -- hier NICHT angefasst.
#
# ⚠️ MUSS byte-identisch ueber alle Runden bleiben: er steht im gecachten
# Praefix (angehaengt an RUNTIME_PROMPT), VOR dem sitzungseigenen Anwesenheits-
# block -- sonst reisst er den 92%-Cache-Treffer ab (TOKEN-KETTE-Kommentar in
# run_headless() oben). Deshalb ein fester Python-String ohne DB-/Zeit-/
# Sitzungsdaten, und der Schalter wird VOR dem Einsetzen entschieden, nie
# nachtraeglich im schon gebauten Text veraendert.
_GRF_RAHMEN = """[SYSTEM-FRAME: GRF COGNITIVE MODE -- every turn, not only architecture design]
Reason inside the Generative Reality Framework for THIS turn, whatever kind it
is (factual question, fix, small talk, architecture):
1. CAUSAL STATE-TRANSITION: this turn is R_t+1 = F(R_t, E_t) -- R_t is what is
   already established (canonical state, prior tool results), E_t is the new
   evidence this turn (the human's words, tool output). Derive the answer FROM
   R_t and E_t causally. Never answer from surface correlation, vibes, or the
   most fluent-sounding guess.
2. HARD INVARIANTS: treat limits, budgets and safety gates as invariants that
   stop the turn on violation -- not soft suggestions to reason around.
3. NO MONOPOLY: do not let one hypothesis or one tool result monopolize the
   answer uncontested -- weigh competing evidence before committing.
This is an internal reasoning discipline, not a new output vocabulary: keep
this frame's own words (GRF, R_t, E_t, state-transition, invariant) OUT of
what you say to the human, same as your other internal wiring (core_identity,
UnifiedDB, ClayCode)."""


def _grf_injektion_aktiv() -> bool:
    """Schalter fuer den GRF-Denkrahmen, Voreinstellung AN (Gabriel 22.08.).

    Sofort umkehrbar: ENTITYOS_GRF_INJEKTION=0 in der Dienstumgebung setzen und
    neu starten -- kein Codepfad aendert sich sonst, kein Rollback noetig. Bei
    jedem Aufruf frisch aus os.environ gelesen (kein Modul-Caching), damit ein
    Test ihn ohne Reload umschalten kann und ein Neustart der Dienstumgebung
    reicht, um live umzuschalten.
    """
    return os.environ.get("ENTITYOS_GRF_INJEKTION", "1").strip() == "1"


def _systemanweisung(db_path: str, user_id: str, session_id: str) -> str:
    """Laufzeitidentitaet + GRF-Denkrahmen + Anwesenheit in EINER Datei.

    Reihenfolge ist Absicht: grund (RUNTIME_PROMPT) + Rahmen sind fuer eine
    feste Flag-Stellung IMMER gleich, unabhaengig von user_id/session_id --
    das haelt sie im gecachten Praefix. Der Anwesenheitsblock (sitzungseigen,
    variiert je Zug) kommt zuletzt, so bricht er nur den Teil NACH sich selbst.
    """
    grund = Path(RUNTIME_PROMPT).read_text(encoding="utf-8").rstrip()
    if _grf_injektion_aktiv():
        grund = grund + "\n\n" + _GRF_RAHMEN
    return grund + "\n\n" + _anwesenheitsblock(db_path, user_id, session_id) + "\n"


# ⚠️ Waehlt die Vorstufe kein Werkzeug (oder nur erfundene), bekommt Zero NICHT
# alle 38 -- das liesse ihn wild explorieren, jede Runde kostet Sekunden.
# Stattdessen ein kleiner Satz der ueblichen Lese-Werkzeuge, mit denen sich die
# meisten Fragen in ein, zwei Runden beantworten lassen. Gemessen: 'ZVR nummer'
# gab tools=0 -> alle 38 -> 16s Exploration.
_LEER_RUECKFALL = (
    "mcp__clayverse__korpus_suchen",
    "mcp__clayverse__menschen_profil",
    "mcp__clayverse__artikel_lesen",
    "mcp__clayverse__seite_diagnose",
    "mcp__clayverse__speicher_lage",
)


# ── Die Werkzeugspur ─────────────────────────────────────────────────────
# ⭐⭐ BIS 2026-08-21 GAB ES SIE NICHT. Der Kaltweg lief mit
# `--output-format json` und bekam nur das Endergebnis: Antworttext, Dauer,
# Kosten. WELCHE Werkzeuge Zero angefasst hat, stand nirgends -- weder im
# Protokoll noch in der Datenbank. Damit war zweierlei unmoeglich:
#   * eine Herkunftsmarke ("dieser Gedaechtniseintrag entstand in einem Zug, in
#     dem fremder Text aus dem Netz gelesen wurde"),
#   * jede Form von Absichtspruefung ("hat dieser Zug etwas getan, wonach der
#     Mensch nicht gefragt hat?").
# Beides braucht die Spur. Der Warmweg streamte ohnehin schon; hier wird der
# Kaltweg nachgezogen, damit beide Wege dasselbe liefern.
_AUSSENWIRKUNG = frozenset({
    # Werkzeuge, deren Wirkung den Behaelter verlaesst oder dauerhaft bleibt.
    "Write", "Edit", "MultiEdit", "NotebookEdit", "Bash", "KillShell",
    "WebFetch", "WebSearch",
    "mcp__clayverse__request_effect", "mcp__clayverse__request_autonomy_effect",
    "mcp__clayverse__udb_memory_add", "mcp__clayverse__udb_embedding_store",
    "mcp__clayverse__postfach_senden", "mcp__clayverse__werkbank_veroeffentlichen",
    "mcp__clayverse__abruf_rueckmeldung",
})
_FREMDTEXT = frozenset({"WebFetch", "WebSearch"})


def spur_aus_strom(stdout: str):
    """(Endumschlag, Werkzeugliste) aus einem stream-json-Strom.

    Reihenfolge bleibt erhalten und Wiederholungen bleiben stehen: dass ein
    Werkzeug DREIMAL lief, ist eine andere Aussage als dass es lief.
    """
    umschlag, werkzeuge = None, []
    for zeile in (stdout or "").splitlines():
        zeile = zeile.strip()
        if not zeile or not zeile.startswith("{"):
            continue
        try:
            ev = json.loads(zeile)
        except Exception:
            continue
        if ev.get("type") == "result":
            umschlag = ev
            continue
        inhalt = ((ev.get("message") or {}).get("content")
                  if isinstance(ev.get("message"), dict) else None)
        for block in (inhalt or []):
            if isinstance(block, dict) and block.get("type") == "tool_use":
                name = str(block.get("name") or "")
                if name:
                    werkzeuge.append(name)
    return umschlag, werkzeuge


def spur_deuten(werkzeuge) -> dict:
    """Was die Spur bedeutet -- rein mechanisch, ohne Modellurteil."""
    w = list(werkzeuge or [])
    return {
        "werkzeuge": w,
        "n": len(w),
        "aussenwirkung": sorted({x for x in w if x in _AUSSENWIRKUNG}),
        "fremdtext": sorted({x for x in w if x in _FREMDTEXT}),
    }


def nutzung_aus_envelope(envelope: dict) -> dict:
    """Die echten Claude-Token-/Kostenzahlen aus dem `result`-Ereignis lesen.

    ⭐⭐ TOKEN-KETTE 2026-08-22: bis heute wurde `envelope["usage"]` an dieser
    Stelle NIRGENDS gelesen -- cost_usd/num_turns liefen zwar schon durch,
    aber genau die Felder, die einen Cache-Treffer BEWEISEN
    (cache_read_input_tokens vs. cache_creation_input_tokens), gingen im
    result-Dict unter. Ohne sie war jede Aussage ueber Ersparnis eine Behaup-
    tung. Gemessen (echte `claude -p`-Antwort, --output-format json/
    stream-json liefern dieselbe usage-Form): ein Cache-Treffer zeigt sich als
    cache_read_input_tokens gross UND cache_creation_input_tokens klein: ein
    Kaltschreiber zeigt genau das Gegenteil. .get()-Kette, nie werfend --
    fehlt ein Feld (aeltere CLI-Version, anderer Provider), bleibt es None
    statt den Zug zu kippen.
    """
    u = envelope.get("usage") or {}
    return {
        "input_tokens": u.get("input_tokens"),
        "output_tokens": u.get("output_tokens"),
        "cache_read_input_tokens": u.get("cache_read_input_tokens"),
        "cache_creation_input_tokens": u.get("cache_creation_input_tokens"),
    }


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

    # ⭐⭐ Der dauerhafte Zero-Prozess: erst einen VORGEWAERMTEN Prozess versuchen
    # (Boot schon bezahlt, ~2,2s gespart). Klappt es nicht -- kein warmer bereit,
    # Fehler, kein sauberes Ergebnis -- faellt es lautlos auf den Kaltweg unten
    # zurueck. Der Dauerprozess ist eine Abkuerzung, nie eine Verschlechterung.

    if pipeline_managed:
        try:
            from .warm_zero import POOL as _WARM
            _WARM.starten()
            _warm_res = _WARM.answer(caveman_prompt, user_id=user_id,
                                     session_id=session_id, timeout=timeout)
            if _warm_res is not None:
                return _warm_res
        except Exception:
            pass  # jeder Fehler im Warmweg -> Kaltweg

    # ⚠️ Die Vorstufe ERFINDET manchmal Werkzeugnamen (gemessen: read_resource,
    # search_wiki -- gibt es nicht). Ein erfundener Name darf NICHT den ganzen
    # Zug toeten. Also FILTERN statt hart abweisen: unbekannte Namen fallen weg,
    # die gueltigen bleiben. Sicher, weil ein Name, den es nicht gibt, ohnehin
    # kein Werkzeug freischaltet -- und --allowedTools setzt die echte Grenze.
    # Bleibt nach dem Filtern nichts, nimm die volle erlaubte Liste (Zero waehlt
    # dann selbst), statt mit leerer Auswahl abzubrechen.
    if tool_selection:
        gefiltert = [t for t in tool_selection if t in DEFAULT_ALLOWED_TOOLS]
        verworfen = sorted(set(tool_selection) - set(DEFAULT_ALLOWED_TOOLS))
        if verworfen:
            import sys as _sys
            print("headless: erfundene Werkzeugnamen verworfen: " + str(verworfen), file=_sys.stderr)
        tools = gefiltert or list(_LEER_RUECKFALL)
    else:
        tools = list(_LEER_RUECKFALL)
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
        # ⭐ Schnelles Modell pro Runde: die harte Reasoning-Arbeit macht schon
        # die Mistral-Vorstufe. Zeros Job ist Anweisung lesen, Werkzeug rufen,
        # knapp melden -- dafuer ist Sonnet schnell genug, und jede agentische
        # Runde kostet auf Opus ~4s, auf Sonnet deutlich weniger.
        "--model", "sonnet",
        "--settings", MANAGED_SETTINGS,
        "--setting-sources", "",
        # ⭐ Native Werkzeuge EXPLIZIT (inkl. WebSearch/WebFetch): ohne die Liste
        # lud der Default-Satz zwar Bash/Read, aber NICHT die Web-Tools (gemessen
        # 19.08.: Zero sagte "kein Web-Such-Tool"). Zero handelt direkt wie
        "--tools", "Bash,BashOutput,KillShell,Read,Write,Edit,MultiEdit,NotebookEdit,Glob,Grep,WebSearch,WebFetch,TodoWrite,Task",
        # eine echte Claude-Code-Sitzung. Die Grenze setzt die managed
        # permissions.allow (native + MCP) plus der PreToolUse-Zaun-Hook --
        # NICHT mehr eine enge --allowedTools-Liste. tool_selection der
        # Vorstufe ist jetzt nur noch Hinweis; Zero waehlt selbst.
        "--permission-mode", "dontAsk",
        "--append-system-prompt-file", _sysdatei,
        # ⭐⭐ TOKEN-KETTE 2026-08-22 (KORREKTUR: das eigentliche Zahlziel ist
        # dieser Claude-Aufruf, nicht die Mistral-Vorstufe -- Gabriel 22.08.).
        # GEMESSEN gegen die echte CLI (zwei aufeinanderfolgende `claude -p
        # --no-session-persistence`-Prozesse, identischer angehaengter
        # Systemprompt ~18,6k Token): der ZWEITE Aufruf liest 21.418 von 21.650
        # Token aus dem Cache statt sie neu zu bezahlen -- 92,4 % weniger Kosten
        # fuer diesen Zug ($0,1132 -> $0,0086). Anthropic-Promptcaching lief also
        # schon automatisch, OHNE dieses Flag, OHNE cache_control-Code hier --
        # `claude -p` setzt die Cache-Haltepunkte selbst.
        # Dieses Flag beseitigt den EINEN gemessenen Risikofaktor: Claude Codes
        # EIGENER Standard-Systemprompt (der vor unserem angehaengten Text
        # steht) traegt von sich aus pro-Maschine-Abschnitte (cwd, Env-Info,
        # Speicherpfade, Git-Status). Aendert sich einer davon zwischen zwei
        # Zuegen, bricht der Praefix VOR unserem Text ab -- und alles danach
        # (der ganze angehaengte RUNTIME_PROMPT) kann dann nicht mehr treffen,
        # egal wie stabil er selbst ist. Das Flag zieht genau diese Abschnitte
        # in die erste User-Nachricht um (Dokumentation: "Improves cross-user
        # prompt-cache reuse"). Gemessen wirkungslos auf die Antwort selbst
        # (identischer Text in zwei Proben mit/ohne Flag), nur auf den
        # Cache-Praefix. Reines Risiko-Wegnehmen, kein neuer Mechanismus.
        "--exclude-dynamic-system-prompt-sections",
        # ⭐ stream-json statt json: nur so sieht man die Werkzeugaufrufe. Der
        # Warmweg macht es seit jeher so; der Kaltweg zog 2026-08-21 nach.
        "--output-format", "stream-json", "--verbose",
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
    envelope, _werkzeuge = spur_aus_strom(cp.stdout)
    if not isinstance(envelope, dict):
        raise HeadlessZeroError(
            "headless Zero lieferte kein result-Ereignis im Strom: "
            f"{(cp.stdout or '')[:400]!r}")
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
        "warm": False,
        "usage": nutzung_aus_envelope(envelope),
        **spur_deuten(_werkzeuge),
    }
