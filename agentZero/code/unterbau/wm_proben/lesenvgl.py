# -*- coding: utf-8 -*-
"""Vergleicht lesen() vor/nach der Umstellung der Achse 'id'."""
import sys, json, hashlib, time
sys.path.insert(0, "/opt/clayverse/werkzeug")
import weltmodell as W
MARKE = sys.argv[1]
ZIEL = "/opt/clayverse/werkzeug/wm_proben/lesen-%s.json" % MARKE
c = W.verbinden(schreibend=False)
ids = [r[0] for r in c.execute(
    "SELECT DISTINCT artikel_id FROM wm_lesart WHERE gueltig_bis IS NULL "
    "ORDER BY artikel_id LIMIT 800").fetchall()]

def norm(d):
    """Vergleichbar machen: lesart_id + wert je Achse, sortiert."""
    out = {}
    for a, v in d["achsen"].items():
        alle = ([v["gewaehlt"]] if v["gewaehlt"] else []) + v["kandidaten"] + v["verworfen"]
        out[a] = {"status": v["status"],
                  "eintraege": sorted((x["lesart_id"], str(x["wert"])) for x in alle)}
    return out

erg = {}
for kt in ({}, {"identitaetsachse": "id"}, {"identitaetsachse": "inhalt"}):
    schl = json.dumps(kt, sort_keys=True)
    h = hashlib.sha256()
    for i in ids:
        h.update(json.dumps(norm(W.lesen(c, i, kt)), sort_keys=True).encode())
    erg[schl] = h.hexdigest()[:24]

for i in ids[:100]:
    W.lesen(c, i, {"identitaetsachse": "id"})
z = []
for i in ids:
    t0 = time.perf_counter(); W.lesen(c, i, {"identitaetsachse": "id"})
    z.append((time.perf_counter()-t0)*1000)
z.sort()
erg["_latenz_mittel_ms"] = round(sum(z)/len(z), 4)
erg["_latenz_p99_ms"] = round(z[int(len(z)*0.99)-1], 4)
erg["_artikel"] = len(ids)
json.dump(erg, open(ZIEL, "w"), indent=2)
for k, v in erg.items(): print("  %-40s %s" % (k, v))
