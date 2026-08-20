# -*- coding: utf-8 -*-
"""CSWT-Z Schicht 1: Kapazitaetsrampe. Ein JSON je Zug auf stdout.

Aufruf:  cswt_lauf.py <kappung> [<epistemik_aus>]

KONTROLLEN (alle drei sind noetig, jede schliesst einen gemessenen Confound):
  1. own_recent wird auf [] gezwungen. Am 20.08. wurde gemessen, dass der
     Gespraechsverlauf die FORM der Antwort diktiert: nach zwei Vorsatz-Zuegen
     beantwortete dieselbe Frage mit demselben Zustand die Vorsatzliste statt
     die Frage. Ohne diese Kontrolle wuerde die Kapazitaetsrampe teilweise die
     Reihenfolge der Bedingungen messen.
  2. gelernter_block() -> "". Sonst waechst waehrend des Laufs ein
     Rueckkopplungssignal aus den eigenen Versuchszuegen in den Kontext.
  3. record_via_turnlifecycle=False. Damit keine Gedaechtnis-Extraktion, keine
     turns-Zeile, keine Kausalkette -- der Versuch veraendert die Entitaet nicht.
     Geschrieben wird nur mv_prestage_turns, und das IST das Versuchsprotokoll.
"""
import os, sys, json, time, random, re
os.environ["CLAYVERSE_MEMORY_EXTRACT"] = "0"
sys.path.insert(0, "/opt/clayverse")
sys.path.insert(0, "/tmp")

from cswt_sonden import SONDEN
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline, prestage
from clayverse.mistral_prestage.store import PrestageStore

KAPPUNG = int(sys.argv[1])
EPISTEMIK_AUS = len(sys.argv) > 2 and sys.argv[2] == "epistemik_aus"

# ── Kontrolle 1: own_recent leer ──────────────────────────────────────
_echt_world = pipeline._gather_world_safe
def _world_ohne_verlauf(db, session_id, message=""):
    w = _echt_world(db, session_id, message)
    w = dict(w)
    w["own_recent"] = []
    return w
pipeline._gather_world_safe = _world_ohne_verlauf

# ── Kontrolle 2: kein gelernter Block ─────────────────────────────────
PrestageStore.gelernter_block = lambda self, *a, **k: ""

# ── Kontrolle 3 steckt im Aufruf (record_via_turnlifecycle=False) ─────

# ── Bedingung: Kapazitaet ─────────────────────────────────────────────
pipeline._VORSTUFE_MAX_CHARS = KAPPUNG

# ── Zusatzarm Schicht 4D: Epistemik-Anforderung entfernen ─────────────
# epistemik erreicht Zero NICHT (gemessen: Zero bekommt nur caveman_prompt).
# Eine direkte Injektion ist deshalb architektonisch unmoeglich -- epistemik
# ist ein MITPRODUKT derselben Erzeugung. Pruefbar ist nur der indirekte Weg:
# die Anforderung aus dem Systemprompt nehmen und sehen, ob sich Genauigkeit
# und Kalibrierung dissoziiert veraendern.
if EPISTEMIK_AUS:
    regeln = prestage._BASE_RULES
    a = regeln.find("(H) ⭐⭐⭐ EPISTEMIK")
    b = regeln.find("(I) ⭐ GELERNT")
    assert a != -1 and b != -1 and a < b, "Regel (H) nicht gefunden"
    regeln = regeln[:a] + regeln[b:]
    regeln = regeln.replace(", epistemik.", ".")
    prestage._BASE_RULES = regeln
    prestage._REQUIRED_KEYS = {k for k in prestage._REQUIRED_KEYS if k != "epistemik"}

def treffer(antwort: str, muster) -> int:
    t = (antwort or "").lower()
    return int(any(re.search(m, t) for m in muster))

db = UnifiedDB("/var/lib/clay/wiki.db")
SITZUNG, NUTZER = "session:gabriel:2", "gabriel"

sonden = list(SONDEN)
random.Random(4711 + KAPPUNG).shuffle(sonden)   # feste Streuung, reproduzierbar

if os.environ.get("CSWT_RAUCH"): sonden = sonden[:3]
for i, (klasse, frage, muster) in enumerate(sonden):
    t0 = time.time()
    zeile = {"kappung": KAPPUNG, "epistemik_aus": EPISTEMIK_AUS,
             "klasse": klasse, "frage": frage, "nr": i}
    try:
        r = pipeline.run_chat_turn(db=db, user_id=NUTZER, session_id=SITZUNG,
                                   message=frage, record_via_turnlifecycle=False)
        ep = r.get("epistemik") or {}
        zeile.update({
            "ok": True,
            "treffer": treffer(r["reply"], muster),
            "antwort": r["reply"][:400],
            "runden": r.get("rounds_used"),
            "werkzeuge": r.get("tool_selection") or [],
            "unbekannt_n": len(ep.get("unbekannt") or []),
            "bekannt_n": len(ep.get("bekannt") or []),
            "ms": r.get("elapsed_ms") or {},
            "s": round(time.time() - t0, 1),
        })
    except Exception as e:
        zeile.update({"ok": False, "treffer": 0, "s": round(time.time() - t0, 1),
                      "fehler": f"{type(e).__name__}: {e}"[:220]})
    print(json.dumps(zeile, ensure_ascii=False), flush=True)
