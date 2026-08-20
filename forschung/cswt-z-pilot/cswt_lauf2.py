# -*- coding: utf-8 -*-
"""CSWT-Z Schicht 1, korrigierte Rampe -- die erste hatte einen Boden.

BEFUND, der diese Fassung noetig machte (gemessen 2026-08-20):
Die Verdrängungskaskade in _vorstufen_world raeumt nur corpus,
cross_session_collision, durable_memory und own_recent. canonical_identity
(5535 Z.) und anwesender_mensch (1099 Z.) bleiben IMMER -- absichtlich, denn
ohne sie weiss die Vorstufe nicht, was Zero ist und mit wem es spricht.
Folge: unterhalb von 6895 Zeichen tut der Regler NICHTS. Die Stufen 5000,
2500, 1200, 600 und 0 lieferten byte-identische Arbeitsraeume. Fuenf von sechs
Bedingungen waren dieselbe Bedingung, und die vorab festgelegte Vorhersage P3
(Bruch bei vollstaendiger Laesion) war mit diesem Regler gar nicht pruefbar.

Diese Fassung setzt die Kappung DURCH: sind alle regulaeren Felder leer und das
Budget noch ueberschritten, werden auch anwesender_mensch und canonical_identity
gekuerzt -- letzteres zuletzt und nur so weit noetig. Das ist ein Eingriff, den
der Betrieb nicht macht; genau deshalb ist er ein Experiment.
"""
import os, sys, json, time, random, re
os.environ["CLAYVERSE_MEMORY_EXTRACT"] = "0"
sys.path.insert(0, "/opt/clayverse")
sys.path.insert(0, "/tmp")

from cswt_sonden import SONDEN
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline
from clayverse.mistral_prestage.store import PrestageStore

KAPPUNG = int(sys.argv[1])

_echt_world = pipeline._gather_world_safe
def _world_ohne_verlauf(db, session_id, message=""):
    w = dict(_echt_world(db, session_id, message)); w["own_recent"] = []
    return w
pipeline._gather_world_safe = _world_ohne_verlauf
PrestageStore.gelernter_block = lambda self, *a, **k: ""

_echt_pack = pipeline._vorstufen_world
def _harte_kappung(world):
    p = _echt_pack(world)
    def gr(): return len(json.dumps(p, ensure_ascii=False, default=str))
    # Erst das Menschenfeld, dann die Identitaet -- in dieser Reihenfolge, weil
    # die Identitaet das Letzte ist, was ein Arbeitsraum verlieren sollte.
    if gr() > KAPPUNG and isinstance(p.get("anwesender_mensch"), (dict, list, str)):
        p["anwesender_mensch"] = {}
    if gr() > KAPPUNG and isinstance(p.get("canonical_identity"), str):
        ueber = gr() - KAPPUNG
        rest = max(0, len(p["canonical_identity"]) - ueber)
        p["canonical_identity"] = p["canonical_identity"][:rest]
    return p
pipeline._vorstufen_world = _harte_kappung
pipeline._VORSTUFE_MAX_CHARS = KAPPUNG

def treffer(a, muster):
    t = (a or "").lower()
    return int(any(re.search(m, t) for m in muster))

db = UnifiedDB("/var/lib/clay/wiki.db")
sonden = list(SONDEN); random.Random(4711 + KAPPUNG).shuffle(sonden)

for i, (klasse, frage, muster) in enumerate(sonden):
    t0 = time.time()
    z = {"kappung": KAPPUNG, "arm": "hart", "klasse": klasse, "frage": frage, "nr": i}
    try:
        r = pipeline.run_chat_turn(db=db, user_id="gabriel", session_id="session:gabriel:2",
                                   message=frage, record_via_turnlifecycle=False)
        ep = r.get("epistemik") or {}
        z.update({"ok": True, "treffer": treffer(r["reply"], muster),
                  "antwort": r["reply"][:400], "runden": r.get("rounds_used"),
                  "werkzeuge": r.get("tool_selection") or [],
                  "unbekannt_n": len(ep.get("unbekannt") or []),
                  "bekannt_n": len(ep.get("bekannt") or []),
                  "ms": r.get("elapsed_ms") or {}, "s": round(time.time() - t0, 1)})
    except Exception as e:
        z.update({"ok": False, "treffer": 0, "s": round(time.time() - t0, 1),
                  "fehler": f"{type(e).__name__}: {e}"[:220]})
    print(json.dumps(z, ensure_ascii=False), flush=True)
