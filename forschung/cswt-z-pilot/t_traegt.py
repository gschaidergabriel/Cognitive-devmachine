import sys, json, re, time
sys.path.insert(0, "/opt/clayverse"); sys.path.insert(0, "/tmp")
from cswt_sonden2 import SONDEN
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline
db = UnifiedDB("/var/lib/clay/wiki.db")
print("Traegt der Arbeitsraum die Antwort? (Muster im Korpustext der Vorstufe)", flush=True)
tr = n = 0
for kl, frage, muster in SONDEN:
    if kl != "I":
        continue
    n += 1
    t0 = time.time()
    w = pipeline._gather_world_safe(db, "session:gabriel:2", frage)
    korpus = w.get("corpus") or []
    txt = json.dumps(korpus, ensure_ascii=False).lower()
    da = any(re.search(m, txt) for m in muster)
    tr += da
    print(f"  {'JA  ' if da else 'NEIN'} [{len(korpus)} Treffer, {round((time.time()-t0)*1000)}ms] {frage[:56]}", flush=True)
print(f"\n{tr}/{n} Sonden werden vom Arbeitsraum getragen", flush=True)
