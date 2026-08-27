"""Die MOTOR-KASKADE -- EIN Router, den BEIDE Rollen (Vorstufe, Zeros
Hauptgehirn) rufen, wenn ihr PRIMAERER Motor hart ausfaellt. Ersetzt die zwei
zuvor einzeln gedachten Fallbacks (Vorstufe->Claude, Hauptgehirn->Mistral) zu
EINER Kaskade ueber den GANZEN Schluesselpool -- "Umstellen statt anbauen":
kein neuer Anbieter-Client, nur vorhandene Transporte in Reihenfolge
geschaltet.

ZWEI Rollen, ZWEI Kaskaden, GEGENLAEUFIGE Primaermotoren:

  VORSTUFE     Mistral (transport.mistral_chat_json_rotating, primaer)
               -> stehender warmer Claude-Notweg (warm_claude_prestage.py)
               -> Bahnrouter-Pool (clayverse/bahnen.py, Prozess
               "vorstufe_notweg": glm_52/nvidia_nim/groq_gptoss_120b/
               groq_gptoss_20b -- glm_52 zuerst, Owner-Entscheidung
               2026-08-22).
  HAUPTGEHIRN  Claude (der Aufrufer reicht seinen eigenen Aufruf ein, z.B.
               headless_zero.run_headless -- NICHT hier neu gebaut) -> bei
               HARTEM Ausfall (ist_hart_erschoepft(), Kredit/Kontingent,
               NICHT ein Ratenlimit) GLM-Direktantwort (Prozess
               "hauptgehirn_glm": glm_45_air/glm_47, klein statt
               Flaggschiff) -> Mistral-Direktantwort (alle lebenden
               Schluessel aus secrets.mistral_keys()) -> Nemotron-
               Direktantwort (Prozess "hauptgehirn_nemotron":
               NVIDIA nvidia-nemotron-nano-9b-v2) -> Bahnrouter-Pool-Rest
               (Prozess "hauptgehirn_notweg": nvidia_nim/groq_gptoss_120b/
               groq_gptoss_20b, glm_52 NICHT dabei -- schon Stufe 1).
               Reihenfolge Claude->GLM->Mistral->Nemotron->Pool-Rest ist
               Owner-Entscheidung 2026-08-22 (vorher Claude->Mistral->Pool).

Die LETZTE Stufe (Bahnrouter-Pool) traegt selbst schon eine Kaskade UEBER
mehrere Anbieter -- inklusive taggenauem Erschoepfungsgedaechtnis
(bahn_nutzung-Tabelle) und Ausschluss frisch ausgefallener Bahnen
(LEBEND_SCHWELLE/LEBEND_ABKUEHLUNG_SEK in bahnen.py). Das IST die "per-key
exhaustion memory" + "skip-on-recent-failure", die diese Aufgabe verlangt --
WIEDERVERWENDET (clayverse.bahnen.Bahnrouter), NICHT neu gebaut.

Jede Stufe liefert ihren eigenen Vertrag unveraendert zurueck (Vorstufe:
{"payload": dict, "receipt": dict} wie transport.mistral_chat_json_rotating;
Hauptgehirn: dieselbe Form wie headless_zero.run_headless()) -- "welcher
Motor geliefert hat" steht in receipt["motor"] bzw. zero["engine"], das ist
die Telemetrie-Spur (wandert unveraendert in mv_prestage_turns.prestage_model/
innen_model bzw. in den Zug selbst).

⚠️ EHRLICHE GRENZE: Der Bahnrouter-Pool UND der Mistral-Direktweg liefern
Text/JSON, KEINE Werkzeugausfuehrung. Fuer die Hauptgehirn-Rolle heisst das:
dieser eine Zug kann keine Datei lesen/schreiben/Bash ausfuehren, bis ein
werkzeugfaehiger Motor (Claude) wieder verfuegbar ist -- kein verschwiegener
Kompromiss, siehe hauptgehirn_kaskade()-Docstring.

⚠️ bahnen.json traegt den Hinweis "Ausgeleitet, nicht abgeschrieben -- die
Wahrheit bleibt im Clay-Unterbau (/opt/clayverse/werkzeug/verdrahtung.py)".
Die zwei neuen Prozesse ("vorstufe_notweg"/"hauptgehirn_notweg") sind NUR in
der Repo-Kopie ergaenzt (die dieser Code tatsaechlich liest, Bahnrouter.
__init__ laedt sie ueber Path(__file__).with_name("bahnen.json")) -- OB/WIE
sie in den Clay-Unterbau selbst nachgezogen werden muessen, damit eine
kuenftige Ableitung sie nicht wieder verliert, ist eine Betriebsfrage
ausserhalb dieses Repos/Branches und wird hier NICHT beantwortet.
"""
from __future__ import annotations

import json
import re
from typing import Any, Callable

from . import secrets, transport, warm_claude_prestage

_HART_MUSTER = re.compile(
    r"credit balance|insufficient_quota|quota exceeded|payment required|"
    r"billing|out of credit|no credit|\b402\b",
    re.IGNORECASE,
)
_TRANSIENT_MUSTER = re.compile(
    r"rate.?limit|\b429\b|overloaded|timed? ?out|timeout|econnreset|"
    r"temporarily unavailable|\b529\b",
    re.IGNORECASE,
)


def ist_hart_erschoepft(fehlertext: str) -> bool:
    """Kredit-/Kontingent-Erschoepfung (Rechnungsstopp) -- NICHT ein
    Ratenlimit oder ein Timeout. Ein Text, der BEIDE Muster traefe, zaehlt
    NICHT als hart -- ein echtes Erschoepfungssignal ist eindeutig, ein
    mehrdeutiger Text bleibt sicherheitshalber transient (kein voreiliger
    Motorwechsel bei einem blossen Ausrutscher)."""
    text = fehlertext or ""
    if _TRANSIENT_MUSTER.search(text):
        return False
    return bool(_HART_MUSTER.search(text))


class KaskadeErschoepft(RuntimeError):
    """Jede Stufe der Kaskade ist ausgefallen -- kein Motor hat diesen Zug
    geliefert. Traegt alle Einzelfehler fuer die Quittung/Diagnose."""

    def __init__(self, rolle: str, versuche: list[tuple[str, str]]):
        self.rolle = rolle
        self.versuche = versuche
        super().__init__(
            f"Kaskade '{rolle}' komplett ausgefallen: "
            + "; ".join(f"{motor}: {grund}" for motor, grund in versuche)
        )


# ── Bahnrouter-Pool-Stufe, fuer BEIDE Rollen gemeinsam ────────────────────

def _pool_direktantwort(
    *, prozess: str, auftrag: str, max_tokens: int, router_factory: Callable[[], Any],
) -> dict[str, Any]:
    """Ruft clayverse.bahnen.Bahnrouter.rufe() -- die bereits gebaute
    Kaskade ueber Groq/NVIDIA/GLM/... mit Tagesdeckel + Erschoepfungs-
    gedaechtnis. `schema_pflicht: 1` (in bahnen.json fuer beide neuen
    Prozesse gesetzt) erzwingt JSON serverseitig, also ist `roh["text"]`
    hier ein JSON-Objekt-String."""
    router = router_factory()
    roh = router.rufe(prozess, auftrag, max_token=max_tokens)
    payload = json.loads(roh["text"])
    if not isinstance(payload, dict):
        raise RuntimeError(f"Pool-Bahn {roh.get('bahn')} lieferte kein JSON-Objekt")
    return {
        "payload": payload,
        "receipt": {
            "motor": f"pool:{roh.get('bahn')}",
            "modell": roh.get("modell"),
            "token": roh.get("token"),
            "ms": roh.get("ms"),
            "verworfene_bahnen": roh.get("verworfene_bahnen"),
        },
    }


def _echter_router_factory():
    """Der ECHTE Bahnrouter gegen die Live-DB -- nur hier, nie in einem
    Test (dort wird router_factory IMMER injiziert, dieselbe Konvention wie
    ueberall sonst im Paket)."""
    from ..bahnen import Bahnrouter
    from ..store import UnifiedDB
    return Bahnrouter(UnifiedDB("/var/lib/clay/wiki.db"))


# ── Vorstufen-Kaskade ──────────────────────────────────────────────────────

def vorstufe_notweg(
    *, system: str, user: str, modus: str, max_tokens: int = 900,
    router_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Die ZWEI Notweg-Stufen NACH Mistral: stehender warmer Claude-Notweg
    -> Bahnrouter-Pool. Ruft NICHT selbst Mistral -- prestage.run_prestage/
    innenraum.run_innere_vorstufe versuchen Mistral bereits SELBST zuerst
    (eigener try/except um transport.mistral_chat_json_rotating, mit ihrem
    eigenen stabilen prompt_cache_key) und rufen diese Funktion nur in ihrem
    except-Zweig -- ein zweiter Mistral-Versuch HIER waere eine unnoetige
    Verdopplung. `modus` ist "aussen" (Chat-Vorstufe) oder "innen" (autonome
    Vorstufe) -- waehlt den richtigen stehenden Claude-Prozess (siehe
    warm_claude_prestage.py). Wirft KaskadeErschoepft nur, wenn BEIDE Stufen
    fehlschlagen."""
    if modus not in ("aussen", "innen"):
        raise ValueError(f"unbekannter Vorstufen-Modus: {modus}")
    versuche: list[tuple[str, str]] = []

    # 1. Stehender warmer Claude-Notweg.
    try:
        aufruf = warm_claude_prestage.aussen_zug if modus == "aussen" else warm_claude_prestage.innen_zug
        return aufruf(system=system, user=user)
    except Exception as exc:
        versuche.append(("claude-fallback-warm", str(exc)))

    # 2. Bahnrouter-Pool (Groq/NVIDIA/GLM/...).
    try:
        faktorie = router_factory or _echter_router_factory
        auftrag = f"{system}\n\nCONTEXT:\n{user}" if system else user
        return _pool_direktantwort(
            prozess="vorstufe_notweg", auftrag=auftrag, max_tokens=max_tokens,
            router_factory=faktorie)
    except Exception as exc:
        versuche.append(("pool", str(exc)))

    raise KaskadeErschoepft(f"vorstufe:{modus}", versuche)


# ── Hauptgehirn-Kaskade ─────────────────────────────────────────────────────

_MISTRAL_ANTWORT_SYSTEM = (
    "You are answering directly, as Zero's stand-in (no native tools "
    "available this turn -- Claude Code is temporarily out of quota, "
    "another engine is standing in for the main answer only). Respond in "
    "plain caveman English, one direct answer to the instruction in "
    "CONTEXT. Respond with ONLY a JSON object of the exact form "
    '{"caveman_answer": "<your answer>"} -- no other keys, no prose '
    "outside the JSON."
)
_MISTRAL_ANTWORT_MODEL = "mistral-small-latest"

_LEERE_SPUR = {"werkzeuge": [], "n": 0, "aussenwirkung": [], "fremdtext": []}


def _envelope_zu_zero_form(payload: dict, *, engine: str, receipt: dict) -> dict[str, Any]:
    """Formt EIN {"caveman_answer": ...}-Envelope in dieselbe Ergebnisform
    wie headless_zero.run_headless() um -- damit pipeline.run_chat_turn
    stromabwaerts UNVERAENDERT weiterlaeuft (Uebersetzung, DB-Schreibung,
    alles, was zero["caveman_answer"]/zero.get("werkzeuge")/... liest)."""
    text = str((payload or {}).get("caveman_answer") or "").strip()
    if not text:
        raise RuntimeError(f"{engine} lieferte keinen caveman_answer")
    return {
        "caveman_answer": text,
        "num_turns": 1,
        "warm": False,
        "usage": {
            "input_tokens": receipt.get("prompt_tokens") or receipt.get("token"),
            "output_tokens": receipt.get("completion_tokens"),
            "cache_read_input_tokens": None, "cache_creation_input_tokens": None,
        },
        "engine": engine,
        "kaskade_receipt": receipt,
        **_LEERE_SPUR,
    }


def hauptgehirn_kaskade(
    caveman_prompt: str, *, claude_fehler: Exception,
    router_factory: Callable[[], Any] | None = None,
) -> dict[str, Any]:
    """Wird vom Aufrufer NUR gerufen, nachdem dessen eigener Claude-Aufruf
    (z.B. headless_zero.run_headless) mit `claude_fehler` fehlgeschlagen
    ist UND ist_hart_erschoepft(str(claude_fehler)) wahr ist -- diese
    Funktion selbst prueft das NICHT nochmal (der Aufrufer hat schon
    entschieden, dass es sich um einen harten Ausfall handelt, nicht ein
    Ratenlimit). Kaskadiert: GLM -> Mistral -> Nemotron -> Bahnrouter-Pool
    (Rest).

    ⚠️ REIHENFOLGE (Owner-Entscheidung 2026-08-22): Claude (primaer, beim
    Aufrufer) -> GLM (1. Notweg, Prozess "hauptgehirn_glm":
    glm_45_air/glm_47 -- bewusst KLEINER als das glm_52-Flaggschiff) ->
    Mistral (2. Notweg, alle lebenden Schluessel aus secrets.mistral_keys())
    -> Nemotron (3. Notweg, Prozess "hauptgehirn_nemotron": NVIDIA
    nvidia-nemotron-nano-9b-v2, live gemessen) -> Bahnrouter-Pool-Rest
    (Prozess "hauptgehirn_notweg": generisches NVIDIA/Groq, glm_52 bleibt
    dort bewusst DRAUSSEN -- schon in Stufe 1 versucht, keine Dopplung).
    Jeder Fehlschlag (429/Kontingent, bei GLM haeufig gemessen) ist KEIN
    Sonderfall -- dieselbe skip-on-failure-Kaskade wie jede Stufe faengt
    ihn stumm ab und faellt zur naechsten durch; die per-Bahn-
    Erschoepfungserinnerung (bahn_livestreak, LEBEND_SCHWELLE/-ABKUEHLUNG
    in bahnen.py) sorgt dafuer, dass eine frisch tote Bahn nicht bei jedem
    Zug erneut angefragt wird.

    ⚠️ EHRLICHE GRENZE: liefert IMMER dieselbe Form wie headless_zero.
    run_headless() (fuer Uebersetzung/DB-Schreibung), aber IMMER mit
    werkzeuge=[] -- KEINE der vier Notweg-Stufen (GLM/Mistral/Nemotron/
    Pool) kann Zeros native Werkzeuge (Bash/Read/Write/Edit/MCP)
    ausfuehren. Dieser eine Zug beantwortet den Auftrag als reine
    Textantwort; sobald Claude wieder Kontingent hat, laeuft der NAECHSTE
    Zug wieder normal mit vollen Werkzeugen (kein Zustand ueberdauert
    diesen einen Zug). Werkzeugfaehiger Notweg (z.B. ueber ein
    NVIDIA-Modell mit echter Funktionsaufruf-/Ausfuehrungsbruecke) ist eine
    EIGENE, groessere Erweiterung -- Sicherheitsbruecke zu Bash/Read/Write
    fehlt hier komplett und wird NICHT stillschweigend in diesem Zug
    nachgezogen."""
    versuche: list[tuple[str, str]] = [("claude", str(claude_fehler))]

    # 1. GLM-Direktantwort (eigener Bahnrouter-Prozess, glm_45_air/glm_47).
    try:
        faktorie = router_factory or _echter_router_factory
        ergebnis = _pool_direktantwort(
            prozess="hauptgehirn_glm", auftrag=caveman_prompt, max_tokens=900,
            router_factory=faktorie)
        return _envelope_zu_zero_form(
            ergebnis["payload"], engine=ergebnis["receipt"]["motor"], receipt=ergebnis["receipt"])
    except Exception as exc:
        versuche.append(("glm", str(exc)))

    # 2. Mistral-Direktantwort.
    try:
        keys = secrets.mistral_keys()
        if not keys:
            raise RuntimeError("no Mistral key available")
        ergebnis = transport.mistral_chat_json_rotating(
            keys=keys, model=_MISTRAL_ANTWORT_MODEL, system=_MISTRAL_ANTWORT_SYSTEM,
            user=f"CONTEXT:\n{caveman_prompt}", temperature=0.3, max_tokens=900,
            prompt_cache_key="entityos-hauptgehirn-kaskade-mistral",
        )
        return _envelope_zu_zero_form(
            ergebnis["payload"], engine="mistral-fallback", receipt=ergebnis["receipt"])
    except Exception as exc:
        versuche.append(("mistral", str(exc)))

    # 3. Nemotron-Direktantwort (eigener Bahnrouter-Prozess, NVIDIA).
    try:
        faktorie = router_factory or _echter_router_factory
        ergebnis = _pool_direktantwort(
            prozess="hauptgehirn_nemotron", auftrag=caveman_prompt, max_tokens=900,
            router_factory=faktorie)
        return _envelope_zu_zero_form(
            ergebnis["payload"], engine=ergebnis["receipt"]["motor"], receipt=ergebnis["receipt"])
    except Exception as exc:
        versuche.append(("nemotron", str(exc)))

    # 4. Bahnrouter-Pool (Rest: NVIDIA/Groq -- glm_52 schon in Stufe 1 dran).
    try:
        faktorie = router_factory or _echter_router_factory
        ergebnis = _pool_direktantwort(
            prozess="hauptgehirn_notweg", auftrag=caveman_prompt, max_tokens=900,
            router_factory=faktorie)
        return _envelope_zu_zero_form(
            ergebnis["payload"], engine=ergebnis["receipt"]["motor"], receipt=ergebnis["receipt"])
    except Exception as exc:
        versuche.append(("pool", str(exc)))

    raise KaskadeErschoepft("hauptgehirn", versuche)
