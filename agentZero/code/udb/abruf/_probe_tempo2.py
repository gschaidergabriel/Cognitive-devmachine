import sqlite3, time, statistics, json, sys
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

c = P._connect()
P._ensure_vp_tables(c)

satz = json.load(open("/opt/unifieddb/udb/abruf/goldsatz.json", encoding="utf-8"))[1::2]

# Sammle echte alle_pfade-Listen wie sie _ort_codependenzen_batch sieht, indem
# wir denselben Weg gehen: tokens -> _ort_kandidaten -> _ort_gruppieren -> ranked
paths_samples = []
for e in satz[:20]:
    tokens = P._tokenisieren(e["frage"]) if hasattr(P, "_tokenisieren") else None
    break
print("hat _tokenisieren:", hasattr(P, "_tokenisieren"))
print([n for n in dir(P) if "token" in n.lower()])
c.close()
