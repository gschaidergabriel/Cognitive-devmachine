"""Die INNERE Vorstufe -- dieselbe Vorstufen-Maschinerie wie `prestage.py`,
aber fuer den Zug, in dem KEIN Mensch im Gespraech ist.

Gabriels Auftrag 2026-08-22 (Koordinator-Nachtrag, zwei Praezisierungen):

  1. Der Architekt soll seine Vorstufe zurueckbekommen -- aber NICHT als
     zweites, paralleles Geruest (kein Split-Brain). Dieselbe Maschinerie
     (`mistral_prestage`: Vorstufe, headless_zero, pipeline, Abruf, GWT-
     Anbauten) wird NICHT neu gebaut, nur die REIHENFOLGE gedreht: bei einem
     Menschen im Gespraech laeuft Mensch -> Vorstufe -> Zero -> Antwort
     (`prestage.py` + `pipeline.run_chat_turn`, UNVERAENDERT). Bei einem
     autonomen Zug denkt die Engine ZUERST einen rohen Gedanken, DIESER
     Gedanke geht als Eingabe in dieselbe Vorstufen-Maschinerie (Abruf,
     Welt-Montage, Werkzeug-Wahl, GRF-Rahmen, GWT, watch_out), und das
     Ergebnis geht zurueck an die Engine wie ein normales Vorstufen-Paket --
     "die Vorstufe ist nach INNEN gewandert".
  2. NICHT nur fuer den Architekten: JEDER autonome Zug (Architekt-
     Selbstverbesserung, ein spaeterer Governor/wake-getriebene Ziele,
     Hintergrundarbeit) soll durch DENSELBEN inneren Weg laufen. Der Architekt
     ist nur der ERSTE Verbraucher. Die Weiche ist denkbar einfach und
     wird NICHT hier entschieden: sie ist eine Frage des EINTRITTSPUNKTS,
     nicht einer Erkennung zur Laufzeit --
       * Chat-Pfad (`pipeline.run_chat_turn`, von terminal_hooks.py/der
         Chat-Gateway aufgerufen) -> Vorstufe AUSSEN (prestage.py,
         unveraendert).
       * ALLES ANDERE (jeder Aufrufer, der NICHT run_chat_turn ist --
         Architekt, ein spaeterer Governor, Hintergrundarbeit) -> Vorstufe
         INNEN (dieses Modul, ueber pipeline.run_autonomous_turn), OHNE
         Ausnahme, OHNE Fall-Erkennung ("ist ein Mensch da?"). Der
         Aufrufer WEISS, ob er der Chat-Pfad ist -- er muss es nicht raten.
     Dieses Modul kennt also gar keinen Menschen/keine Session-Kanonik --
     das ist genau der Punkt: es ist fuer JEDEN Aufrufer gleich.

  ⚠️⭐ ClayCode-only: Eingabe, Denken UND Ausgabe dieses Wegs sind ClayCode,
  nicht Hoehlenmensch-Englisch und nicht Deutsch. Kein Uebersetzer haengt
  hier dran -- der Uebersetzer (translator.py) ist NUR fuer die Antwort an
  einen Menschen da (pipeline.run_chat_turn), und ein autonomer Zug hat
  keinen Menschen, dem geantwortet wird. Der Transport bleibt das gleiche
  JSON-Umschlag-Muster wie prestage.py (das Netzwerkprotokoll aendert sich
  nicht) -- aber der INHALT der Werte in diesem Umschlag ist ClayCode-Text,
  keine englische/deutsche Prosa.

Wiederverwendet, NICHT neu gebaut:
  * `transport.mistral_chat_json_rotating` + `secrets.mistral_keys()` --
    derselbe Mistral-Aufrufer wie prestage.py.
  * `pipeline._gather_world_safe`/`_hyperposition_safe`/`_weltmodell_safe`/
    `_vorstufen_world` -- dieselbe Abruf-/Welt-Montage-Maschinerie
    (Gedaechtnis-Abruf LAEUFT auch hier, Gabriel explizit: "memory-retrieval
    MUST run in autonomous processes too"). Aufgerufen aus
    `pipeline.run_autonomous_turn`, NICHT hier -- dieses Modul bekommt die
    fertige `world`, genau wie `prestage.run_prestage` sie bekommt.
  * `tools/claycode_base_compiler.py` (`build()`) -- der ECHTE ClayCode-BASE-
    Compiler, der im Repo bereits existiert und dessen V7-Slice (typisierte
    reine Funktionen, `fn name(p:Typ,...)->Typ=ausdruck`) MESSBAR compiliert
    (`tools/claycode_base_compiler_validation.py`, CI-Workflow
    `claycode-base-compiler-slice.yml`). `GENERAL_PURPOSE_GATE` steht laut
    `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json` auf FAIL -- freie Denk-
    prosa in voller ClayCode-Grammatik zu pruefen ist NICHT moeglich. Was
    dieses Modul deshalb tut: es sucht `fn ...`-Zeilen (typisierte reine
    Behauptungen/Pruefungen) IN der vom Modell gelieferten `claycode_direktive`
    und versucht NUR DIESE gegen die V7-Grammatik zu compilieren -- ein
    ECHTER Compile-Versuch auf dem Teil, der compilierbar sein KANN, kein
    Vortaeuschen fuer den Rest. Schlaegt der Versuch fehl (oder gibt es keine
    `fn`-Zeile), wird das GEMELDET (`claycode_kompiliert`), nie der Zug
    gekippt -- derselbe "_safe"-Grundsatz wie ueberall sonst in diesem Paket.
"""
from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

from . import secrets, transport

# ── Der echte ClayCode-BASE-Compiler, per Pfad geladen (kein Paket-Import --
# tools/ liegt ausserhalb von clayverse/, siehe claycode_base_compiler_
# validation.py fuer denselben Lademechanismus) ────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]  # .../the artefact
_COMPILER_PFAD = _REPO_ROOT / "tools" / "claycode_base_compiler.py"
_GRAMMATIK_PFAD = (
    _REPO_ROOT
    / "research_entity" / "claycode" / "base"
    / "D_LALR_GRAMMAR_REPAIR_CANDIDATE_V7_OPERATOR_FN.lark"
)

_FN_ZEILE_RE = re.compile(r"^\s*fn\s+\w+\s*\([^)]*\)\s*->\s*\w+\s*=.+$", re.MULTILINE)


def _lade_compiler():
    """Laedt tools/claycode_base_compiler.py per Dateipfad. `lark` fehlt in
    manchen Umgebungen (gemessen: keines der Projekt-venvs hat es
    vorinstalliert) -- dann liefert dieser Loader None, und der Aufrufer
    meldet 'versucht: false', statt zu crashen."""
    try:
        spec = importlib.util.spec_from_file_location(
            "claycode_base_compiler", _COMPILER_PFAD)
        modul = importlib.util.module_from_spec(spec)
        # ⭐ MUSS vor exec_module in sys.modules stehen -- dataclasses'
        # `@dataclass(frozen=True)` (Param/Function in claycode_base_compiler.py)
        # sucht bei _is_type() sein eigenes Modul ueber sys.modules[__module__]
        # nach, sonst AttributeError auf None. Derselbe Lademechanismus wie
        # tools/claycode_base_compiler_validation.py (dort exakt so geloest).
        sys.modules[spec.name] = modul
        assert spec.loader is not None
        spec.loader.exec_module(modul)
        return modul
    except Exception:
        sys.modules.pop("claycode_base_compiler", None)
        return None


_CC = None  # lazy, einmal pro Prozess


def claycode_compile_probe(text: str) -> dict[str, Any]:
    """Sucht `fn`-Zeilen in `text` (der `claycode_direktive`) und versucht sie
    GENAU SO gegen die echte V7-BASE-Grammatik zu compilieren, wie
    `claycode_base_compiler_validation.py` es fuer den CI-Slice tut. Nie
    werfend -- ein Compile-Fehlschlag ist ein MESSWERT (`kompiliert: false`,
    `fehler`), kein Grund, den Zug zu kippen.

    Rueckgabe:
      versucht    -- gab es ueberhaupt eine `fn`-Zeile zu pruefen?
      kompiliert  -- hat sie die V7-Grammatik + Typ-/Symbolpruefung bestanden?
      semantic_hash -- die kanonische IR-Pruefsumme bei Erfolg, sonst None.
      fehler      -- Fehlertext bei Misserfolg, sonst None.
    """
    treffer = _FN_ZEILE_RE.findall(text or "")
    if not treffer:
        return {"versucht": False, "kompiliert": False, "semantic_hash": None, "fehler": None}

    global _CC
    if _CC is None:
        _CC = _lade_compiler() or False
    if _CC is False:
        return {"versucht": True, "kompiliert": False, "semantic_hash": None,
                "fehler": "claycode_base_compiler nicht ladbar (lark fehlt?)"}

    quelle = "\n".join(t.strip() for t in treffer) + "\n"
    try:
        grammatik = _GRAMMATIK_PFAD.read_text(encoding="utf-8")
        ergebnis = _CC.build(quelle, grammatik)
        return {"versucht": True, "kompiliert": True,
                "semantic_hash": ergebnis["semantic_hash"], "fehler": None}
    except Exception as exc:
        return {"versucht": True, "kompiliert": False, "semantic_hash": None,
                "fehler": f"{type(exc).__name__}: {str(exc)[:300]}"}


# ── Denkraum: architekt-/autonomie-getunt, NICHT der Chat-Denkraum ─────────
#
# Das ist bewusst KEIN Abklatsch von prestage._BASE_RULES -- jene Regeln
# sind fuer ein GESPRAECH MIT EINEM MENSCHEN geschrieben (Pronomen-Umkehr,
# Begruessungs-Erkennung, "sag dem Menschen", Job-Basket fuer Bildschirm-
# Vorschau). Ein autonomer Zug hat keinen Menschen -- diese Regeln wuerden
# hier falsch liegen, nicht nur ungenutzt sein. Was UEBERLEBT (dieselbe
# Denkdisziplin, andere Zielsprache):
#   * die Selbstpruefungspflicht (H): bekannt/unbekannt VOR der Direktive,
#   * hyperposition/Moeglichkeitsraum als Mehrdeutigkeits-Signal, nie als
#     Erlaubnis, eine Lesart heimlich zu waehlen,
#   * "nie raten, nie erfinden" (die Kernregel aus (C)/(H) uebersetzt auf
#     Code-/Systemzustand statt auf einen Chat-Fakt),
#   * die Auswahl-statt-Volltext-Disziplin fuer `broadcast_ids`.
_INNEN_DENKRAUM = """You are the INNER PRE-STAGE of EntityOS' autonomous cognition -- the same \
role prestage.py plays for a human chat turn, but this turn has NO human. The caller (the \
architect's self-improvement engine now; a later goal-driven governor or background process \
next) already produced ONE RAW THOUGHT about its own current work (goal, hypothesis, symptom, \
plan step) -- that thought is CONTEXT.gedanke below, in ClayCode. Your job is the same shape as \
the chat pre-stage's: run memory-retrieval + world-montage + tool-selection + the GRF frame + \
GWT broadcast-selection + risk-surfacing over that thought, and hand back a package the caller's \
next engine step can act on -- but EVERYTHING here, INPUT AND OUTPUT, is ClayCode. Never English \
prose, never German, never "caveman" -- this loop never reaches a human, so there is nothing to \
translate for.

⭐⭐⭐ SELECTION, NOT CUSTODY (same discipline as the chat pre-stage). `CONTEXT.world.corpus` and \
`CONTEXT.world.durable_memory` are candidates with an id, a title/subject and a score -- not \
full text. Choose the ones the thought actually needs into `broadcast_ids`; never invent a path, \
file, or fact that is not literally present in CONTEXT. If a candidate is admitted \
(`gw_zugelassen: true`) and relevant, select it -- do not silently drop it and go invent \
something to read instead.

⭐⭐ EPISTEMIK, AUTONOMOUS FORM. Before writing `claycode_direktive`, name in `epistemik.bekannt` \
every fact this thought's next step genuinely needs that CONTEXT actually contains (with its \
`herkunft`), and in `epistemik.unbekannt` every fact it needs that CONTEXT does NOT contain. A \
gap in `unbekannt` is never a reason to stop or to invent -- it is a reason for \
`claycode_direktive` to point the next engine step at ONE concrete way to close it (read a named \
file, run a named measurement, check a named log) -- never a menu, never "ask the human" (there \
is no human here).

⭐ HYPERPOSITION / MOEGLICHKEITSRAUM. `CONTEXT.hyperposition` is the same set-valued world-model \
readout the chat pre-stage sees: an entry with 2+ facets is a live contradiction in the corpus \
itself, not yours to resolve. Surface it in `risiken`; never silently pick one facet as settled.

⭐ WERKZEUG-WAHL. `CONTEXT.available_tools` lists what this caller's next step MAY use (may be \
empty -- some callers, like the architect's text-only diff engine, have no tool surface of their \
own; `werkzeug_wahl` then stays `[]`, that is correct, not an omission). Never invent a tool name \
not in that list.

⭐⭐⭐ CLAYCODE-ONLY OUTPUT. `claycode_direktive` is written in ClayCode surface syntax as far as \
the content allows: declarative statements (`module`, `law`, `rule`, `invariant`, `record`) for \
anything that IS a claim, a constraint, or a goal state; a typed pure-function line \
(`fn name(param:Type,...)->Type=expr`) for anything that IS a checkable boolean/numeric \
condition (budget left, risk threshold, invariant to hold) -- write these whenever the thought \
produces one, because they are the part of your answer that can be MECHANICALLY VERIFIED by the \
real ClayCode BASE compiler downstream, not just read. For the imperative part (what to actually \
DO next) that has no ClayCode statement form yet, use the shortest `rule`/`law` phrasing that \
carries the imperative as a named relation (e.g. `law naechster_schritt = pruefe(hypothese_x)`) \
rather than a free English sentence. Never restate this system frame's own vocabulary \
(pre-stage, envelope, JSON, ClayCode-only) inside `claycode_direktive` itself -- it is the \
directive, not a description of the mechanism producing it.

You return EXACTLY these keys, no others: claycode_direktive, ziel_zustand, werkzeug_wahl, \
gedaechtnis_belege, risiken, hypothesen, gegenhypothesen, epistemik, broadcast_ids. \
`ziel_zustand` is one short ClayCode `law`/`rule` line naming the state this step pursues. \
`risiken` is ClayCode-flavored (an `invariant` line where the risk IS an invariant to guard; \
otherwise the shortest neutral statement of what could go wrong). `hypothesen`/`gegenhypothesen` \
are short lists of ClayCode `rule`/`law` lines, correlated with CONTEXT (world/hyperposition), \
never free invention. Respond with ONLY the JSON object -- no prose outside it."""

_ERFORDERLICHE_SCHLUESSEL = {
    "claycode_direktive", "ziel_zustand", "werkzeug_wahl", "gedaechtnis_belege",
    "risiken", "hypothesen", "gegenhypothesen", "epistemik", "broadcast_ids",
}

_STANDARD_ENVELOPE = {
    "ziel_zustand": "", "werkzeug_wahl": [], "gedaechtnis_belege": [],
    "broadcast_ids": [], "risiken": "", "hypothesen": [], "gegenhypothesen": [],
    "claycode_direktive": "", "epistemik": {"bekannt": [], "unbekannt": []},
}

INNEN_MODEL = "mistral-small-latest"


def build_context_innen(
    *,
    gedanke: str,
    world: dict[str, Any] | None,
    ziel_kontext: dict[str, Any] | None = None,
    available_tools: list[str] | None = None,
    hyperposition: list[dict[str, Any]] | None = None,
    gelernt: str | None = None,
) -> str:
    """Analog zu prestage.build_context, aber ohne alles, was einen Menschen
    voraussetzt (current_user, current_user_profile, moeglichkeitsraum als
    Chat-Erwartungsfeld, recent_turns als Gespraechsverlauf, zero_suggestion/
    Verhandlungsrunde -- dieser Weg hat keine Verhandlungsrunde, ein
    autonomer Zug fragt nicht nach einem besseren Paket, er macht mit dem
    weiter, was er bekommt)."""
    kontext = {
        "gedanke": gedanke,
        "ziel_kontext": ziel_kontext or {},
        "available_tools": available_tools or [],
        "world": world or {},
        "hyperposition": hyperposition or [],
    }
    if gelernt:
        kontext["gelernt"] = gelernt
    return json.dumps(kontext, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def run_innere_vorstufe(
    *,
    gedanke: str,
    world: dict[str, Any] | None = None,
    ziel_kontext: dict[str, Any] | None = None,
    available_tools: list[str] | None = None,
    hyperposition: list[dict[str, Any]] | None = None,
    gelernt: str | None = None,
    model: str = INNEN_MODEL,
    api_key: str | None = None,
) -> dict[str, Any]:
    """Der innere Vorstufen-Zug, EIN Aufruf (keine Verhandlungsrunde -- siehe
    build_context_innen-Docstring). Wirft nur bei Eingabefehlern (leerer
    Gedanke, kein Schluessel) -- ein unvollstaendiger Modell-Envelope wird
    wie in prestage.run_prestage mit sicheren Defaults gefuellt, nie ein
    Absturz."""
    if not gedanke or not isinstance(gedanke, str) or len(gedanke) > 100_000:
        raise ValueError("invalid gedanke")
    keys = [api_key] if api_key else secrets.mistral_keys()
    if not keys:
        raise RuntimeError("no Mistral key available")

    context = build_context_innen(
        gedanke=gedanke, world=world, ziel_kontext=ziel_kontext,
        available_tools=available_tools, hyperposition=hyperposition, gelernt=gelernt,
    )
    ergebnis = transport.mistral_chat_json_rotating(
        keys=keys, model=model, system=_INNEN_DENKRAUM,
        user=f"CONTEXT:\n{context}", temperature=0.2, max_tokens=900,
        # ⭐ Eigener Cache-Eimer, getrennt vom Chat-Weg (prestage.py nutzt
        # entityos-prestage-r1/r2) -- derselbe fixe System-Praefix bei jedem
        # inneren Zug, damit Mistral ihn treffen KANN.
        prompt_cache_key="entityos-innere-vorstufe",
    )
    payload = ergebnis["payload"]
    if not isinstance(payload, dict):
        payload = {}
    payload = dict(payload)
    fehlend = [k for k in _ERFORDERLICHE_SCHLUESSEL if k not in payload or payload.get(k) is None]
    for k in fehlend:
        payload[k] = _STANDARD_ENVELOPE.get(k, "")
    if not str(payload.get("claycode_direktive") or "").strip():
        payload["claycode_direktive"] = (
            "law fortsetzen = mit_verfuegbarem_kontext_weiterarbeiten\n"
            "// leere Direktive -- Envelope unvollstaendig, autonom weiterarbeiten, nicht anhalten"
        )
    if fehlend:
        print("innenraum: unvollstaendiger Envelope, Defaults gefuellt: " + str(sorted(fehlend)),
              file=sys.stderr)
    payload["claycode_kompiliert"] = claycode_compile_probe(payload["claycode_direktive"])
    payload["innen_model"] = model
    payload["innen_receipt"] = ergebnis["receipt"]
    return payload
