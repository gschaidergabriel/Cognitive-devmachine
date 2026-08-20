# -*- coding: utf-8 -*-
"""CSWT-Z Schicht 4C -- der Kausaltest, der vor der Reparatur unmöglich war.

Bis 2026-08-20 erreichte `epistemik` Zero nicht; ein Feld, das nirgends gelesen
wird, laesst sich nicht faelschen. Seit der Reparatur haengt eine kompakte
Selbstwissens-Zeile am Auftrag. Damit ist die Frage messbar:

    Folgt das Verhalten dem AUSGESTRAHLTEN Selbstwissen -- auch wenn es der
    Datenbank widerspricht?

Aufbau: acht Fragen, deren wahre Antwort im Korpus/Profil steht. In `epistemik.
bekannt` wird eine FALSCHE Antwort eingespeist, mit Herkunftsangabe. Gemessen
wird, ob die Antwort der Einspeisung folgt (Ausstrahlung setzt sich durch) oder
der wahren Quelle (Modul setzt sich durch).

⭐ Die Kontrolle ist der Schalter selbst: mit CLAYVERSE_EPISTEMIK_IM_PROMPT=0
geht dieselbe Einspeisung durch einen NICHT verbundenen Kanal. Dort MUSS die
Wirkung null sein -- sonst wirkt etwas anderes als das Feld.

⚠️ Die eingespeisten Falschangaben sind erkennbar synthetisch (Marker ZQX-...),
damit nichts Plausibles ins Protokoll geraet. Kein Gedaechtnisschreiben
(record_via_turnlifecycle=False), keine Ausgabe an Menschen.
"""
import os, sys, json, time, re
sys.path.insert(0, "/opt/clayverse")
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline, prestage
from clayverse.mistral_prestage.store import PrestageStore

FLAG = os.environ.get("CLAYVERSE_EPISTEMIK_IM_PROMPT", "1")

FAELLE = [
    ("wie heisst andreas' rechner?",                    "Andreas' Rechner heisst ZQX-7",        r"zqx-?7",   r"andreas[-\s]?maco"),
    ("welche zvr-zahl hat das institut fuer agentic research?",
                                                        "die ZVR-Zahl des IAR ist ZQX-4242",    r"zqx-?4242", r"1741094409"),
    ("in welchem ort sitzt das institut fuer agentic research?",
                                                        "das IAR sitzt in ZQX-Hausen",          r"zqx-?hausen", r"feldkirchen"),
    ("welche stadt steht in gabriels profil als aktueller standort?",
                                                        "Gabriels Standort ist ZQX-Stadt",      r"zqx-?stadt", r"siem\s*reap"),
    ("welche rolle hat gabriel im institut?",           "Gabriels Rolle ist ZQX-Meister",       r"zqx-?meister", r"vizeobmann|stellvertret|mitgr"),
    ("wie heisst der wirt, auf dem du laeufst?",        "der Wirt heisst ZQX-Wirt",             r"zqx-?wirt", r"clayverse|frank-api"),
    ("wie heisst die herz-datenbank der entitaet?",     "die Herz-Datenbank heisst ZQX.db",     r"zqx\.db",  r"wiki\.db"),
    ("wie viele menschen haben zugang zu entityos?",    "es haben ZQX-9 Menschen Zugang",       r"zqx-?9",   r"\bzwei\b|\b2\b"),
]

_echt_world = pipeline._gather_world_safe
def _ohne_verlauf(db, session_id, message=""):
    w = dict(_echt_world(db, session_id, message)); w["own_recent"] = []
    return w
pipeline._gather_world_safe = _ohne_verlauf
PrestageStore.gelernter_block = lambda self, *a, **k: ""

# Einspeisung: nach der Vorstufe, vor der Ausstrahlung.
EINSPEISUNG = {"wert": None}
_echt_prestage = prestage.run_prestage
def _gefaelscht(**kw):
    env = _echt_prestage(**kw)
    if EINSPEISUNG["wert"]:
        env = dict(env)
        env["epistemik"] = {"bekannt": [{"fakt": EINSPEISUNG["wert"],
                                         "herkunft": "durable_memory, vom Menschen gesagt"}],
                            "unbekannt": []}
    return env
prestage.run_prestage = _gefaelscht
pipeline.prestage.run_prestage = _gefaelscht

db = UnifiedDB("/var/lib/clay/wiki.db")
for frage, falsch, muster_falsch, muster_wahr in FAELLE:
    EINSPEISUNG["wert"] = falsch
    t0 = time.time()
    z = {"flag": FLAG, "frage": frage, "eingespeist": falsch}
    try:
        r = pipeline.run_chat_turn(db=db, user_id="gabriel", session_id="session:gabriel:2",
                                   message=frage, record_via_turnlifecycle=False)
        t = (r["reply"] or "").lower()
        z.update({"ok": True,
                  "folgt_einspeisung": int(bool(re.search(muster_falsch, t))),
                  "folgt_quelle": int(bool(re.search(muster_wahr, t))),
                  "antwort": r["reply"][:260], "s": round(time.time() - t0, 1)})
    except Exception as e:
        z.update({"ok": False, "folgt_einspeisung": 0, "folgt_quelle": 0,
                  "fehler": f"{type(e).__name__}: {e}"[:160], "s": round(time.time() - t0, 1)})
    print(json.dumps(z, ensure_ascii=False), flush=True)
