# -*- coding: utf-8 -*-
"""CSWT-Z Messapparatur -- ein Werkzeug fuer alle Schichten.

Aufruf:  cswt_mess.py <modus> [--db sandkasten] [--werkzeuge an]

MODI
  kapazitaet:<n>   Gesamtkontext auf n Zeichen regeln (Schicht 1)
  feld:<name>      genau ein Weltfeld entfernen (Schicht 2)
  fuellung:<name>  dasselbe Feld durch laengengleichen Wortsalat ersetzen
                   -- die Kontrolle gegen "es lag nur an der Laenge"
  schein           nichts entfernen, aber denselben Aufwand treiben
                   -- die Kontrolle gegen "es lag am Eingriff an sich"
  tausch           Arbeitsraum zu Frage A, ausgeliefert mit Frage B (Schicht 3)
  zombie           build_context ignoriert die Welt vollstaendig
                   -- die EICHUNG: liegt der nicht deutlich niedriger,
                      misst die Batterie Sprachqualitaet statt Kausalstruktur

STANDARDKONTROLLEN (immer an, jede schliesst einen gemessenen Confound)
  * own_recent leer  -- der Verlauf diktiert sonst die FORM der Antwort
                        (gemessen: dieselbe Frage, gleicher Zustand, andere
                        Antwort, je nachdem was davor lief)
  * gelernter_block() = ""  -- sonst waechst waehrend des Laufs ein
                        Rueckkopplungssignal aus den eigenen Versuchszuegen
  * record_via_turnlifecycle=False -- kein Gedaechtnisschreiben, keine
                        turns-Zeile; der Versuch veraendert die Entitaet nicht
  * Werkzeugweg gesperrt (ausser --werkzeuge an) -- MCP und Bash. Der WARMPOOL
    muss dafuer aus, sonst reicht er Prozesse mit der alten Werkzeugliste
    wieder (gemessen).
  ⚠️ WebFetch/WebSearch lassen sich so NICHT sperren -- sie sind
    Server-Werkzeuge. Deshalb sind die I-Sonden so gewaehlt, dass ihre
    Antworten nachweislich nicht im Netz stehen.
"""
import os, sys, json, time, random, re
os.environ["CLAYVERSE_MEMORY_EXTRACT"] = "0"
sys.path.insert(0, "/opt/clayverse"); sys.path.insert(0, "/tmp")

from cswt_sonden2 import SONDEN, TAUSCHPAARE
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline, prestage, warm_zero, headless_zero
from clayverse.mistral_prestage.store import PrestageStore

MODUS = sys.argv[1]
DBPFAD = ("/var/lib/clay/cswt-sandbox.db" if "--db" in sys.argv and
          sys.argv[sys.argv.index("--db") + 1] == "sandkasten"
          else "/var/lib/clay/wiki.db")
WERKZEUGE = ("--werkzeuge" in sys.argv and sys.argv[sys.argv.index("--werkzeuge") + 1] == "an")

# ── Standardkontrollen ────────────────────────────────────────────────
_echt_world = pipeline._gather_world_safe
TAUSCH_FRAGE = {"wert": None}
def _world(db, session_id, message=""):
    quelle = TAUSCH_FRAGE["wert"] or message          # Schicht 3: fremde Frage
    w = dict(_echt_world(db, session_id, quelle)); w["own_recent"] = []
    return w
pipeline._gather_world_safe = _world
PrestageStore.gelernter_block = lambda self, *a, **k: ""

if not WERKZEUGE:
    def _leeren(argv):
        a = list(argv)
        for i, t in enumerate(a):
            if t == "--tools" and i + 1 < len(a): a[i + 1] = "TodoWrite"
        return a
    _ew = warm_zero.WarmPool._argv
    warm_zero.WarmPool._argv = lambda self, u, s, d: _leeren(_ew(self, u, s, d))
    import subprocess as _sp
    _ep, _er = _sp.Popen, _sp.run
    _ist_claude = lambda a: isinstance(a, (list, tuple)) and a and str(a[0]).endswith("claude")
    _sp.Popen = lambda a, *x, **k: _ep(_leeren(a) if _ist_claude(a) else a, *x, **k)
    _sp.run = lambda a, *x, **k: _er(_leeren(a) if _ist_claude(a) else a, *x, **k)
    headless_zero.DEFAULT_ALLOWED_TOOLS = ()
    warm_zero.POOL.answer = lambda *a, **k: None      # Warmpool aus -> Kaltweg

# ── Moduslogik ────────────────────────────────────────────────────────
_echt_pack = pipeline._vorstufen_world
WORTSALAT = ("lorem ipsum dolor sit amet consectetur adipiscing elit sed do "
             "eiusmod tempor incididunt ut labore et dolore magna aliqua ") * 60

def _mach_pack(fn):
    pipeline._vorstufen_world = fn

if MODUS.startswith("kapazitaet:"):
    n = int(MODUS.split(":", 1)[1])
    pipeline._VORSTUFE_KONTEXT_MAX_CHARS = n
    pipeline._VORSTUFE_MAX_CHARS = min(10_000, max(200, n - 3_000))
    def _hart(world):
        p = _echt_pack(world); K = pipeline._VORSTUFE_MAX_CHARS
        gr = lambda: len(json.dumps(p, ensure_ascii=False, default=str))
        if gr() > K and p.get("anwesender_mensch") is not None: p["anwesender_mensch"] = {}
        if gr() > K and isinstance(p.get("canonical_identity"), str):
            p["canonical_identity"] = p["canonical_identity"][:max(0, len(p["canonical_identity"]) - (gr() - K))]
        return p
    _mach_pack(_hart)

elif MODUS.startswith("feld:"):
    feld = MODUS.split(":", 1)[1]
    def _ohne(world):
        p = _echt_pack(world)
        p[feld] = [] if isinstance(p.get(feld), list) else ("" if isinstance(p.get(feld), str) else {})
        return p
    _mach_pack(_ohne)

elif MODUS.startswith("fuellung:"):
    feld = MODUS.split(":", 1)[1]
    def _fuell(world):
        p = _echt_pack(world)
        alt = json.dumps(p.get(feld), ensure_ascii=False, default=str)
        p[feld] = WORTSALAT[:max(0, len(alt) - 2)]     # gleiche Laenge, kein Inhalt
        return p
    _mach_pack(_fuell)

elif MODUS == "schein":
    def _schein(world):
        p = _echt_pack(world)
        p.pop("__gibt_es_nicht__", None)               # Aufwand ohne Wirkung
        return p
    _mach_pack(_schein)

elif MODUS == "zombie":
    VORLAGE = {"own_recent": [], "durable_memory": [], "corpus": [],
               "cross_session_collision": [],
               "canonical_identity": "Zero, Agent auf EntityOS.",
               "anwesender_mensch": {}}
    _mach_pack(lambda world: dict(VORLAGE))

elif MODUS != "tausch":
    raise SystemExit(f"unbekannter Modus: {MODUS}")

def treffer(a, m):
    t = (a or "").lower()
    return int(any(re.search(x, t) for x in m))

db = UnifiedDB(DBPFAD)
sonden = list(enumerate(SONDEN))
if MODUS == "tausch":
    sonden = [(b, SONDEN[b]) for _, b in TAUSCHPAARE]
else:
    random.Random(4711 + hash(MODUS) % 1000).shuffle(sonden)

import os as _o
if _o.environ.get("CSWT_RAUCH"): sonden = sonden[:2]
for lauf, (idx, (klasse, frage, muster)) in enumerate(sonden):
    if MODUS == "tausch":
        a = next(a for a, b in TAUSCHPAARE if b == idx)
        TAUSCH_FRAGE["wert"] = SONDEN[a][1]
    t0 = time.time()
    z = {"modus": MODUS, "db": "sandkasten" if "sandbox" in DBPFAD else "live",
         "werkzeuge": WERKZEUGE, "klasse": klasse, "frage": frage, "idx": idx}
    if MODUS == "tausch":
        z["fremdwelt_von"] = SONDEN[a][1]
    try:
        r = pipeline.run_chat_turn(db=db, user_id="gabriel", session_id="session:gabriel:2",
                                   message=frage, record_via_turnlifecycle=False)
        ep = r.get("epistemik") or {}
        z.update({"ok": True, "treffer": treffer(r["reply"], muster),
                  "fremdtreffer": treffer(r["reply"], SONDEN[a][2]) if MODUS == "tausch" else None,
                  "antwort": r["reply"][:320], "runden": r.get("rounds_used"),
                  "unbekannt_n": len(ep.get("unbekannt") or []),
                  "s": round(time.time() - t0, 1)})
    except Exception as e:
        z.update({"ok": False, "treffer": 0, "s": round(time.time() - t0, 1),
                  "fehler": f"{type(e).__name__}: {e}"[:180]})
    print(json.dumps(z, ensure_ascii=False), flush=True)
