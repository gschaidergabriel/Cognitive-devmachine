# -*- coding: utf-8 -*-
"""Exakter Beweis: erzeugt die Laufzeit dieselben id-Lesarten wie die geloeschten?"""
import sys, json, glob, time
sys.path.insert(0, "/opt/clayverse/werkzeug")
import weltmodell as W
c = W.verbinden(schreibend=False)
pfad = sorted(glob.glob("/opt/clayverse/werkzeug/wm_proben/wm_lesart-id-*.json"))[-1]
d = json.load(open(pfad))
sp = d["spalten"]; ix = {n: i for i, n in enumerate(sp)}
alt = {}
for z in d["zeilen"]:
    alt.setdefault(z[ix["artikel_id"]], set()).add(
        (z[ix["lesart_id"]], z[ix["achse"]], str(z[ix["wert"]]), z[ix["kontext_json"]],
         z[ix["domaene"]], z[ix["quelle"]], z[ix["kandidat"]], z[ix["offen"]]))
print("Sicherung:", pfad)
print("Artikel in der Sicherung:", len(alt), "| Zeilen:", len(d["zeilen"]))

fehlt = ueber = ungleich = 0
geprueft = 0
for aid, soll in alt.items():
    ist = {(r["lesart_id"], r["achse"], str(r["wert"]), r["kontext_json"],
            r["domaene"], r["quelle"], r["kandidat"], r["offen"])
           for r in W._id_lesarten(c, aid)}
    geprueft += len(soll)
    if soll - ist: fehlt += len(soll - ist)
    if ist - soll: ueber += len(ist - soll)
    if soll != ist: ungleich += 1
print("gepruefte Zeilen        :", geprueft)
print("in der Laufzeit FEHLEND :", fehlt)
print("in der Laufzeit ZUVIEL  :", ueber)
print("Artikel mit Abweichung  :", ungleich)
print("ERGEBNIS                :", "IDENTISCH" if (fehlt or ueber)==0 else "ABWEICHUNG")

# Latenz auf FESTER Liste aus artikel (unabhaengig von wm_lesart)
ids = [r[0] for r in c.execute("SELECT id FROM artikel ORDER BY id LIMIT 800")]
for i in ids[:100]: W.lesen(c, i, {"identitaetsachse": "id"})
z = []
for i in ids:
    t0 = time.perf_counter(); W.lesen(c, i, {"identitaetsachse": "id"}); z.append((time.perf_counter()-t0)*1000)
z.sort()
print("\nlesen() auf fester Liste (800 Artikel aus `artikel`):")
print("  mittel %.4f ms | p99 %.4f ms | max %.4f ms" % (sum(z)/len(z), z[int(len(z)*0.99)-1], z[-1]))
