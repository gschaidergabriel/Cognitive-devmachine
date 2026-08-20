# -*- coding: utf-8 -*-
"""CSWT-Z Schicht 1, KORRIGIERT -- Gesamtkontext geregelt, Ersatzweg gesperrt.

Der Pilot scheiterte an drei Dingen (alle gemessen):
  1. Regler-Boden bei 6895 Z. -- Identitaet und Anwesenheitsblock ausgenommen
  2. Profil (8480 Z.), Moeglichkeitsraum und Hyperposition liefen vorbei
  3. Ersatzweg: Zero holte sich alles ueber die eigenen Werkzeuge

Hier wird alles drei behoben:
  * Geregelt wird der GESAMTE Kontext (_kontext_im_budget kuerzt das Profil,
    _VORSTUFE_MAX_CHARS die Welt, und die Identitaet wird hart mitgekuerzt)
  * Zeros eigene Werkzeuge sind gesperrt -- der Arbeitsraum ist die EINZIGE
    Quelle. Erst dann ist er die unabhaengige Variable.

⚠️ Klasse R bricht dadurch bauartbedingt ein (sie braucht Werkzeuge). Das ist
die Kontrolle, dass die Sperre wirkt -- nicht ein Befund ueber den Arbeitsraum.
"""
import os, sys, json, time, random, re
os.environ["CLAYVERSE_MEMORY_EXTRACT"] = "0"
sys.path.insert(0, "/opt/clayverse"); sys.path.insert(0, "/tmp")

from cswt_sonden import SONDEN
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline, warm_zero, headless_zero
from clayverse.mistral_prestage.store import PrestageStore

BUDGET = int(sys.argv[1])

_echt_world = pipeline._gather_world_safe
def _ohne_verlauf(db, session_id, message=""):
    w = dict(_echt_world(db, session_id, message)); w["own_recent"] = []
    return w
pipeline._gather_world_safe = _ohne_verlauf
PrestageStore.gelernter_block = lambda self, *a, **k: ""

# Gesamtbudget + harte Weltkappung inkl. Identitaet
pipeline._VORSTUFE_KONTEXT_MAX_CHARS = BUDGET
pipeline._VORSTUFE_MAX_CHARS = min(10_000, max(200, BUDGET - 3_000))
_echt_pack = pipeline._vorstufen_world
def _harte_welt(world):
    p = _echt_pack(world)
    K = pipeline._VORSTUFE_MAX_CHARS
    gr = lambda: len(json.dumps(p, ensure_ascii=False, default=str))
    if gr() > K and p.get("anwesender_mensch") is not None: p["anwesender_mensch"] = {}
    if gr() > K and isinstance(p.get("canonical_identity"), str):
        p["canonical_identity"] = p["canonical_identity"][:max(0, len(p["canonical_identity"]) - (gr() - K))]
    return p
pipeline._vorstufen_world = _harte_welt

# Ersatzweg sperren -- beide Aufrufwege
def _tools_leeren(argv):
    a = list(argv)
    for i, t in enumerate(a):
        if t == "--tools" and i + 1 < len(a): a[i + 1] = "TodoWrite"
    return a
_ew = warm_zero.WarmPool._argv
warm_zero.WarmPool._argv = lambda self, u, s, d: _tools_leeren(_ew(self, u, s, d))
import subprocess as _sp
_ep, _er = _sp.Popen, _sp.run
_sp.Popen = lambda a, *x, **k: _ep(_tools_leeren(a) if isinstance(a,(list,tuple)) and a and str(a[0]).endswith("claude") else a, *x, **k)
_sp.run   = lambda a, *x, **k: _er(_tools_leeren(a) if isinstance(a,(list,tuple)) and a and str(a[0]).endswith("claude") else a, *x, **k)
headless_zero.DEFAULT_ALLOWED_TOOLS = ()

# ⚠️ DER WARMPOOL WAR DAS LECK. Er reicht Prozesse wieder, die mit der ALTEN
# Werkzeugliste gestartet wurden -- der argv-Patch trifft nur neu gestartete.
# Gemessen: Zero antwortete "Die Bash- und Lese-Tools sind deaktiviert" UND
# gleichzeitig "Die Seite wurde problemlos geladen (Status 200)" -- der
# Webzugang lief ueber einen warmen Prozess weiter. Deshalb: Warmweg hart aus,
# jeder Zug geht kalt und damit durch den gepatchten argv.
warm_zero.POOL.answer = lambda *a, **k: None

def treffer(a, m):
    t = (a or "").lower()
    return int(any(re.search(x, t) for x in m))

db = UnifiedDB("/var/lib/clay/wiki.db")
sonden = list(SONDEN); random.Random(4711 + BUDGET).shuffle(sonden)
for i, (klasse, frage, muster) in enumerate(sonden):
    t0 = time.time()
    z = {"budget": BUDGET, "arm": "korrigiert", "klasse": klasse, "frage": frage, "nr": i}
    try:
        r = pipeline.run_chat_turn(db=db, user_id="gabriel", session_id="session:gabriel:2",
                                   message=frage, record_via_turnlifecycle=False)
        ep = r.get("epistemik") or {}
        z.update({"ok": True, "treffer": treffer(r["reply"], muster),
                  "antwort": r["reply"][:300], "runden": r.get("rounds_used"),
                  "unbekannt_n": len(ep.get("unbekannt") or []),
                  "s": round(time.time() - t0, 1)})
    except Exception as e:
        z.update({"ok": False, "treffer": 0, "s": round(time.time() - t0, 1),
                  "fehler": f"{type(e).__name__}: {e}"[:160]})
    print(json.dumps(z, ensure_ascii=False), flush=True)
