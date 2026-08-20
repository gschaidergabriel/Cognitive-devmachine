# -*- coding: utf-8 -*-
"""CSWT-Z Schicht 1, dritter Arm: Kompensationsweg blockiert.

BEFUND, der diesen Arm noetig macht (gemessen 2026-08-20):
Weder die weiche noch die harte Kapazitaetsrampe erzeugte eine Degradation.
Klasse I lag bei voller Kapazitaet sogar NIEDRIGER als bei fast leerem
Arbeitsraum. Der Grund ist kein fehlender Arbeitsraum, sondern ein zweiter,
vollstaendig ausreichender Weg: Zero holt sich denselben Inhalt selbst -- ueber
korpus_suchen, artikel_lesen, dateien_suchen, Bash, Websuche. Solange dieser
Weg offen ist, misst die Rampe den Werkzeuggebrauch eines Sprachmodells, NICHT
den Beitrag des Arbeitsraums.

Genau das erklaert auch das natuerliche Experiment N-1: der Korpus war
monatelang leer, und es fiel niemandem auf.

Dieser Arm schliesst den Ersatzweg. Zero behaelt nur das, was die Vorstufe ihm
gibt. Erst so ist der Arbeitsraum ueberhaupt eine unabhaengige Variable.

⚠️ Klasse R wird dadurch in BEIDEN Bedingungen zusammenbrechen -- sie braucht
Werkzeuge. Das ist kein Fehler, sondern die Kontrolle, dass die Sperre wirkt.
"""
import os, sys, json, time, random, re
os.environ["CLAYVERSE_MEMORY_EXTRACT"] = "0"
sys.path.insert(0, "/opt/clayverse"); sys.path.insert(0, "/tmp")

from cswt_sonden import SONDEN
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline, warm_zero, headless_zero
from clayverse.mistral_prestage.store import PrestageStore

KAPPUNG = int(sys.argv[1])

_echt_world = pipeline._gather_world_safe
def _ohne_verlauf(db, session_id, message=""):
    w = dict(_echt_world(db, session_id, message)); w["own_recent"] = []
    return w
pipeline._gather_world_safe = _ohne_verlauf
PrestageStore.gelernter_block = lambda self, *a, **k: ""

_echt_pack = pipeline._vorstufen_world
def _harte_kappung(world):
    p = _echt_pack(world)
    gr = lambda: len(json.dumps(p, ensure_ascii=False, default=str))
    if gr() > KAPPUNG and p.get("anwesender_mensch") is not None: p["anwesender_mensch"] = {}
    if gr() > KAPPUNG and isinstance(p.get("canonical_identity"), str):
        p["canonical_identity"] = p["canonical_identity"][:max(0, len(p["canonical_identity"]) - (gr() - KAPPUNG))]
    return p
pipeline._vorstufen_world = _harte_kappung
pipeline._VORSTUFE_MAX_CHARS = KAPPUNG

# ── Der Eingriff: kein Ersatzweg ──────────────────────────────────────
# Nur TodoWrite bleibt -- ein Werkzeug ohne Erkenntniswert, damit die
# --tools-Liste nicht leer ist und der Aufruf sich nicht anders verhaelt.
# Zwei Wege muessen zu: der warme Pool (warm_zero.WarmPool) UND der kalte
# Aufruf in headless_zero. Beide bauen ihre eigene --tools-Liste; wer nur einen
# patcht, misst weiter den Ersatzweg und merkt es nicht.
def _tools_leeren(argv):
    a = list(argv)
    for i, t in enumerate(a):
        if t == "--tools" and i + 1 < len(a):
            a[i + 1] = "TodoWrite"      # ein Werkzeug ohne Erkenntniswert
    return a

_echt_warm_argv = warm_zero.WarmPool._argv
warm_zero.WarmPool._argv = lambda self, u, s, d: _tools_leeren(_echt_warm_argv(self, u, s, d))

import subprocess as _sp
_echt_popen = _sp.Popen
def _popen(args, *a, **k):
    if isinstance(args, (list, tuple)) and args and str(args[0]).endswith("claude"):
        args = _tools_leeren(args)
    return _echt_popen(args, *a, **k)
_sp.Popen = _popen
_echt_run = _sp.run
def _run(args, *a, **k):
    if isinstance(args, (list, tuple)) and args and str(args[0]).endswith("claude"):
        args = _tools_leeren(args)
    return _echt_run(args, *a, **k)
_sp.run = _run

headless_zero.DEFAULT_ALLOWED_TOOLS = ()      # keine MCP-Werkzeuge zur Auswahl

def treffer(a, m):
    t = (a or "").lower()
    return int(any(re.search(x, t) for x in m))

db = UnifiedDB("/var/lib/clay/wiki.db")
sonden = list(SONDEN); random.Random(4711 + KAPPUNG).shuffle(sonden)
for i, (klasse, frage, muster) in enumerate(sonden):
    t0 = time.time()
    z = {"kappung": KAPPUNG, "arm": "ohne_werkzeuge", "klasse": klasse, "frage": frage, "nr": i}
    try:
        r = pipeline.run_chat_turn(db=db, user_id="gabriel", session_id="session:gabriel:2",
                                   message=frage, record_via_turnlifecycle=False)
        ep = r.get("epistemik") or {}
        z.update({"ok": True, "treffer": treffer(r["reply"], muster),
                  "antwort": r["reply"][:400], "runden": r.get("rounds_used"),
                  "werkzeuge": r.get("tool_selection") or [],
                  "unbekannt_n": len(ep.get("unbekannt") or []),
                  "ms": r.get("elapsed_ms") or {}, "s": round(time.time() - t0, 1)})
    except Exception as e:
        z.update({"ok": False, "treffer": 0, "s": round(time.time() - t0, 1),
                  "fehler": f"{type(e).__name__}: {e}"[:200]})
    print(json.dumps(z, ensure_ascii=False), flush=True)
