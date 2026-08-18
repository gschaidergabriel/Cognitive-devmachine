import sqlite3, time, statistics, json, sys
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

c = P._connect()
P._ensure_vp_tables(c)

satz = json.load(open("/opt/unifieddb/udb/abruf/goldsatz.json", encoding="utf-8"))[1::2]

pfade_samples = []
verz_samples = []  # (wirt, verzeichnis, datei_id) fuer Geschwister-Test
for e in satz:
    tokens = P._tokens(e["frage"])
    rows = P._ort_kandidaten(c, tokens)
    grouped = P._ort_gruppieren(rows)
    if not grouped:
        continue
    ranked = list(grouped.values())[:P.CAP_ORT_RESULT]
    alle_pfade = []
    seen = set()
    for g in ranked:
        for o in g["orte"][:2]:
            if o["pfad"] not in seen:
                seen.add(o["pfad"]); alle_pfade.append(o["pfad"])
    alle_pfade = alle_pfade[:40]
    if alle_pfade:
        pfade_samples.append(alle_pfade)
    for g in ranked:
        if g["orte"]:
            o = g["orte"][0]
            verz = o["pfad"].rsplit("/", 1)[0] + "/"
            verz_samples.append((o["wirt"], verz, g["datei_id"]))

print("Anzahl pfade_samples:", len(pfade_samples))
print("durchschnittliche Pfadanzahl je Aufruf:", sum(len(p) for p in pfade_samples)/max(1,len(pfade_samples)))
print("Anzahl verz_samples:", len(verz_samples))

with open("/tmp/pfade_samples.json", "w") as f:
    json.dump(pfade_samples, f)
with open("/tmp/verz_samples.json", "w") as f:
    json.dump(verz_samples, f)
c.close()
