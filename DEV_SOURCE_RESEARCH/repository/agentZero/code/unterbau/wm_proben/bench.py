# -*- coding: utf-8 -*-
"""Vor/Nach-Messung fuer paket(). Dieselben Abfragen, dieselbe Reihenfolge."""
import sys, time, json, os
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

MARKE = sys.argv[1]                      # "vorher" | "nachher"
ZIEL = "/opt/clayverse/werkzeug/wm_proben/bench-%s.json" % MARKE
N = 100

c = P._ro()
# Feste Abfrageliste, deterministisch nach id sortiert -> vorher == nachher
titel = [r[0] for r in c.execute(
    "SELECT titel FROM artikel WHERE titel IS NOT NULL AND length(titel)>20 "
    "ORDER BY id LIMIT ?", (N,)).fetchall()]
assert len(titel) == N, len(titel)

for t in titel[:10]:
    P.paket(t, budget=8)                 # aufwaermen

zeiten, zeichen = [], []
hp_da = kand_sichtbar = kand_verloren = 0
mcc_ok = True
topo_kanten = topo_mehrfach = 0
readout_da = quittung_da = 0
for t in titel:
    tok = P._tokens(t)
    r = P.resolve_entities(c, tok, t)
    t0 = time.perf_counter()
    pk = P.paket(t, budget=8)
    zeiten.append((time.perf_counter() - t0) * 1000)
    s = json.dumps(pk, ensure_ascii=False)
    zeichen.append(len(s))
    if pk["beobachtungen"]["model_call_count"] != 0:
        mcc_ok = False
    hp = pk.get("hyperposition")
    nicht_gewaehlt = [x for x in r.candidates if x not in set(r.anchors)]
    if hp:
        hp_da += 1
        if hp.get("quittung"):
            quittung_da += 1
            kand_sichtbar += len(hp["quittung"]["nicht_gewaehlt"])
        if hp.get("readout"):
            readout_da += 1
    # verloren = berechnet, aber nirgends im Paket sichtbar
    sichtbar = set()
    if hp and hp.get("quittung"):
        sichtbar = {x["id"] for x in hp["quittung"]["nicht_gewaehlt"]}
    elif hp:
        sichtbar = {x["id"] for x in hp.get("kandidaten", [])} - set(r.anchors)
    kand_verloren += len([x for x in nicht_gewaehlt if x not in sichtbar])
    for e in pk.get("codependenzen", []):
        ts = e.get("topologien") or []
        if ts:
            topo_kanten += 1
        if len(set(ts)) > 1:
            topo_mehrfach += 1

zs = sorted(zeiten)
erg = {
    "marke": MARKE, "n": N,
    "latenz_mittel_ms": round(sum(zs)/len(zs), 2),
    "latenz_median_ms": round(zs[len(zs)//2], 2),
    "latenz_p95_ms": round(zs[int(len(zs)*0.95)-1], 2),
    "zeichen_mittel": round(sum(zeichen)/len(zeichen)),
    "token_schaetzung": round(sum(zeichen)/len(zeichen)/4),
    "pakete_mit_hyperposition": hp_da,
    "pakete_mit_quittung": quittung_da,
    "pakete_mit_readout": readout_da,
    "nicht_gewaehlte_SICHTBAR": kand_sichtbar,
    "nicht_gewaehlte_VERLOREN": kand_verloren,
    "abfragen_mit_verlust": None,
    "codep_kanten_mit_topologie": topo_kanten,
    "codep_kanten_mehrfach_topologie": topo_mehrfach,
    "model_call_count_immer_0": mcc_ok,
}
# Abfragen mit Verlust separat zaehlen
verlust_abfragen = 0
for t in titel:
    tok = P._tokens(t)
    r = P.resolve_entities(c, tok, t)
    pk = P.paket(t, budget=8)
    hp = pk.get("hyperposition")
    nicht = [x for x in r.candidates if x not in set(r.anchors)]
    if not nicht:
        continue
    sichtbar = set()
    if hp and hp.get("quittung"):
        sichtbar = {x["id"] for x in hp["quittung"]["nicht_gewaehlt"]}
    elif hp:
        sichtbar = {x["id"] for x in hp.get("kandidaten", [])} - set(r.anchors)
    if [x for x in nicht if x not in sichtbar]:
        verlust_abfragen += 1
erg["abfragen_mit_verlust"] = verlust_abfragen

os.makedirs(os.path.dirname(ZIEL), exist_ok=True)
json.dump(erg, open(ZIEL, "w"), ensure_ascii=False, indent=2)
for k, v in erg.items():
    print("  %-34s %s" % (k, v))
