# -*- coding: utf-8 -*-
"""Grundlinie paket() + wie viele Alternativen heute still verschwinden."""
import sys, time, json, sqlite3, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

c = P._ro()
titel = [r[0] for r in c.execute(
    "SELECT titel FROM artikel WHERE titel IS NOT NULL AND length(titel)>20 "
    "ORDER BY id LIMIT 120").fetchall()]

print("=== resolve_entities: was passiert mit den nicht gewaehlten Kandidaten ===")
klassen = {}
verloren = 0
faelle_verloren = 0
hp_gebaut = 0
for t in titel:
    tok = P._tokens(t)
    r = P.resolve_entities(c, tok, t)
    klassen[r.resolution_class] = klassen.get(r.resolution_class, 0) + 1
    if r.resolution_class in ("AMBIGUOUS", "LOW_CONFIDENCE") and r.candidates:
        hp_gebaut += 1
    elif r.candidates and len(r.candidates) > len(r.anchors):
        # Kandidaten berechnet, aber NICHT im Paket sichtbar
        verloren += len(r.candidates) - len(r.anchors)
        faelle_verloren += 1
for k, v in sorted(klassen.items(), key=lambda x: -x[1]):
    print("   %-16s %d" % (k, v))
print("   Abfragen, bei denen hyperposition gebaut wird : %d" % hp_gebaut)
print("   Abfragen, bei denen Kandidaten STILL wegfallen: %d" % faelle_verloren)
print("   dabei verworfene Kandidaten ohne jede Spur    : %d" % verloren)

print("\n=== Grundlinie paket() — VOR jeder Aenderung ===")
proben = titel[:30]
for t in proben[:5]:
    P.paket(t, budget=8)          # aufwaermen
zeiten, groessen, hp = [], [], 0
for t in proben:
    t0 = time.perf_counter()
    pk = P.paket(t, budget=8)
    zeiten.append((time.perf_counter() - t0) * 1000)
    groessen.append(len(json.dumps(pk, ensure_ascii=False)))
    if pk.get("hyperposition"):
        hp += 1
    assert pk["beobachtungen"]["model_call_count"] == 0
zeiten.sort()
print("   n=%d" % len(zeiten))
print("   Latenz  mittel %.1f ms | median %.1f ms | p95 %.1f ms"
      % (sum(zeiten)/len(zeiten), zeiten[len(zeiten)//2], zeiten[int(len(zeiten)*0.95)-1]))
print("   Paketgroesse mittel %.0f Zeichen (~%.0f Token bei 4 Z/Token)"
      % (sum(groessen)/len(groessen), sum(groessen)/len(groessen)/4))
print("   Pakete MIT hyperposition: %d von %d" % (hp, len(proben)))
print("   model_call_count == 0 in allen %d Paketen: ja" % len(proben))
