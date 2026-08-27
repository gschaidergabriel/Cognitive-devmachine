# -*- coding: utf-8 -*-
"""Was kostet welcher neue Block? Exakt, durch Weglassen und neu serialisieren."""
import sys, json, copy
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P
c = P._ro()
titel = [r[0] for r in c.execute(
    "SELECT titel FROM artikel WHERE titel IS NOT NULL AND length(titel)>20 "
    "ORDER BY id LIMIT 100").fetchall()]
GRUND = 34715.0   # Zeichen/Paket vorher, gemessen
voll = 0
ohne = {"hyperposition": 0, "hyperposition.quittung": 0, "hyperposition.readout": 0,
        "topologien": 0, "codep.topologien": 0, "readout.nicht_abgeleitet": 0}
for t in titel:
    pk = P.paket(t, budget=8)
    voll += len(json.dumps(pk, ensure_ascii=False))
    for k in ohne:
        p2 = copy.deepcopy(pk)
        if k == "hyperposition":
            p2["hyperposition"] = None
        elif k == "hyperposition.quittung" and p2.get("hyperposition"):
            p2["hyperposition"].pop("quittung", None)
        elif k == "hyperposition.readout" and p2.get("hyperposition"):
            p2["hyperposition"].pop("readout", None)
        elif k == "topologien":
            p2.pop("topologien", None)
        elif k == "codep.topologien":
            for e in p2.get("codependenzen", []):
                e.pop("topologien", None)
        elif k == "readout.nicht_abgeleitet" and p2.get("hyperposition"):
            r = p2["hyperposition"].get("readout") or {}
            r.pop("nicht_abgeleitet", None); r.pop("nicht_abgeleitet_grund", None)
        ohne[k] += len(json.dumps(p2, ensure_ascii=False))
n = len(titel)
print("Grundlinie vorher      : %8.0f Zeichen/Paket" % GRUND)
print("jetzt voll             : %8.0f Zeichen/Paket  (%+.1f %%)" % (voll/n, 100*(voll/n-GRUND)/GRUND))
print("\nKosten je Block (Zeichen/Paket, und Anteil an der Grundlinie):")
for k, v in sorted(ohne.items(), key=lambda x: -(voll-x[1])):
    d = (voll - v) / n
    print("  %-28s %7.0f   %+5.2f %% der Grundlinie" % (k, d, 100*d/GRUND))
