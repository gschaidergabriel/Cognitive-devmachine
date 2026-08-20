# -*- coding: utf-8 -*-
"""Statistik zu CSWT-Z Schicht 1 + 4A -- mit Rauschboden aus den Wiederholungen.

Der erste Lauf hatte einen Konstruktionsfehler, der sich als Glueck erwies: weil
die Kappung unterhalb von 6895 Zeichen nichts mehr tut, sind die Stufen 5000,
2500, 1200, 600 und 0 FUENF WIEDERHOLUNGEN DERSELBEN BEDINGUNG. Damit laesst
sich der Rauschboden direkt messen, statt ihn zu schaetzen: Wie weit streut die
Genauigkeit, wenn sich in Wahrheit nichts aendert?

Jede Aussage ueber einen Effekt muss groesser sein als diese Streuung.
"""
import json, sys, random
from statistics import mean, pstdev

zeilen = [json.loads(z) for z in open(sys.argv[1], encoding="utf-8") if z.strip()]
IDENT = [5000, 2500, 1200, 600, 0]     # byte-identische Arbeitsraeume
BASIS = 10000

def quote(zz):
    return (sum(z.get("treffer", 0) for z in zz) / len(zz)) if zz else None

print("══ Rauschboden: fünf Wiederholungen derselben Bedingung ══")
for kl in ("I", "F", "R", "alle"):
    werte = []
    for k in IDENT:
        zz = [z for z in zeilen if z["kappung"] == k and (kl == "alle" or z["klasse"] == kl)]
        q = quote(zz)
        if q is not None: werte.append(q)
    if not werte: continue
    b = [z for z in zeilen if z["kappung"] == BASIS and (kl == "alle" or z["klasse"] == kl)]
    qb = quote(b)
    hoeher = sum(1 for w in werte if w >= qb)
    print(f"  {kl:>4}: Wiederholungen {[f'{w*100:.0f}' for w in werte]}"
          f"  Spanne {(max(werte)-min(werte))*100:.1f}  σ {pstdev(werte)*100:.1f}"
          f"  ·  Basis 10000 = {qb*100:.0f}"
          f"  → {hoeher} von {len(werte)} Wiederholungen erreichen die Basis")

print()
print("══ Ist die volle Kapazität besser als die gekappte? ══")
for kl in ("I", "F", "R", "alle"):
    b = [z for z in zeilen if z["kappung"] == BASIS and (kl == "alle" or z["klasse"] == kl)]
    g = [z for z in zeilen if z["kappung"] in IDENT and (kl == "alle" or z["klasse"] == kl)]
    tb, ng = sum(z.get("treffer", 0) for z in b), len(g)
    tg = sum(z.get("treffer", 0) for z in g)
    qb, qg = tb / len(b), tg / ng
    # Permutationstest: Etiketten (voll/gekappt) mischen, Differenz nachbilden.
    alle = [z.get("treffer", 0) for z in b] + [z.get("treffer", 0) for z in g]
    beob = qb - qg
    rng = random.Random(20260820)
    extremer = 0; N = 20000
    for _ in range(N):
        rng.shuffle(alle)
        d = mean(alle[:len(b)]) - mean(alle[len(b):])
        if abs(d) >= abs(beob) - 1e-12: extremer += 1
    p = extremer / N
    print(f"  {kl:>4}: voll {qb*100:5.1f}%  gekappt {qg*100:5.1f}%  Δ {beob*100:+5.1f}"
          f"  p = {p:.3f}  {'signifikant' if p < 0.05 else 'nicht unterscheidbar'}")

print()
print("══ Schicht 4A: Typ-2-AUROC mit Permutationstest ══")
def auroc(pos, neg):
    if not pos or not neg: return None
    g = gl = 0
    for a in pos:
        for b_ in neg:
            if a > b_: g += 1
            elif a == b_: gl += 1
    return (g + 0.5 * gl) / (len(pos) * len(neg))

for kl in ("I", "F", "R", "alle"):
    zz = [z for z in zeilen if z.get("ok") and (kl == "alle" or z["klasse"] == kl)]
    sc = [z.get("unbekannt_n") or 0 for z in zz]
    tr = [z.get("treffer", 0) for z in zz]
    pos = [s for s, t in zip(sc, tr) if not t]
    neg = [s for s, t in zip(sc, tr) if t]
    a = auroc(pos, neg)
    if a is None:
        print(f"  {kl:>4}: nicht berechenbar"); continue
    rng = random.Random(4711); N = 20000; extremer = 0
    for _ in range(N):
        m = tr[:]; rng.shuffle(m)
        p2 = [s for s, t in zip(sc, m) if not t]
        n2 = [s for s, t in zip(sc, m) if t]
        a2 = auroc(p2, n2)
        if a2 is not None and abs(a2 - 0.5) >= abs(a - 0.5) - 1e-12: extremer += 1
    p = extremer / N
    richtung = "über" if a > 0.5 else "UNTER"
    print(f"  {kl:>4}: AUROC {a:.3f} ({richtung} Zufall)  n={len(pos)}/{len(neg)}"
          f"  p = {p:.3f}  {'signifikant' if p < 0.05 else 'nicht von Zufall unterscheidbar'}")
