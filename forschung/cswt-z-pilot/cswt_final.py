# -*- coding: utf-8 -*-
"""Gesamtauswertung CSWT-Z Pilot."""
import json, sys, random
from statistics import pstdev

def lade(p):
    try:
        return [json.loads(z) for z in open(p, encoding="utf-8") if z.strip()]
    except FileNotFoundError:
        return []

def quote(zz): return (sum(z.get("treffer", 0) for z in zz) / len(zz)) if zz else None
def m(v): return sum(v) / len(v) if v else 0

def tabelle(titel, zeilen, schluessel="kappung"):
    print(f"\n══ {titel} ══")
    stufen = sorted({z[schluessel] for z in zeilen}, reverse=True)
    print(f"{'Stufe':>7} | {'I':>12} | {'F':>12} | {'R':>12} | {'gesamt':>8} | Latenz  unbek.")
    print("-" * 82)
    for k in stufen:
        zk = [z for z in zeilen if z[schluessel] == k]
        zellen = []
        for kl in ("I", "F", "R"):
            zz = [z for z in zk if z["klasse"] == kl]
            t, n = sum(z.get("treffer", 0) for z in zz), len(zz)
            zellen.append(f"{t}/{n} {t/n*100 if n else 0:5.1f}%")
        ok = [z for z in zk if z.get("ok")]
        print(f"{k:>7} | " + " | ".join(f"{c:>12}" for c in zellen) +
              f" | {quote(zk)*100:6.1f}% | {m([z.get('s',0) for z in ok]):5.1f}s  "
              f"{m([z.get('unbekannt_n') or 0 for z in ok]):4.2f}")

def perm(a, b, N=20000, seed=1):
    """Zweiseitiger Permutationstest auf Trefferanteile."""
    ta, tb = [z.get("treffer", 0) for z in a], [z.get("treffer", 0) for z in b]
    if not ta or not tb: return None, None, None
    beob = sum(ta)/len(ta) - sum(tb)/len(tb)
    pool = ta + tb; rng = random.Random(seed); extrem = 0
    for _ in range(N):
        rng.shuffle(pool)
        d = sum(pool[:len(ta)])/len(ta) - sum(pool[len(ta):])/len(tb)
        if abs(d) >= abs(beob) - 1e-12: extrem += 1
    return beob, extrem/N, (len(ta), len(tb))

weich = lade("/root/cswt-schicht1.jsonl")
hart  = lade("/root/cswt-schicht1-hart.jsonl")
vier  = lade("/root/cswt-4d.jsonl")
ohne  = lade("/root/cswt-ohne-werkzeuge.jsonl")

if weich: tabelle("Arm A: Regler wie gebaut (Boden bei 6895 Z. -- Stufen <=5000 identisch)", weich)
if hart:  tabelle("Arm B: harte Kappung (Identitaet mitgekuerzt, echte Rampe)", hart)
if ohne:  tabelle("Arm C: Ersatzweg gesperrt (Zero ohne eigene Werkzeuge)", ohne)

for name, daten in (("Arm B", hart), ("Arm C", ohne)):
    if not daten: continue
    st = sorted({z["kappung"] for z in daten}, reverse=True)
    voll = [z for z in daten if z["kappung"] == st[0]]
    leer = [z for z in daten if z["kappung"] == st[-1]]
    print(f"\n── {name}: voller gegen leersten Arbeitsraum ──")
    for kl in ("I", "F", "R", "alle"):
        a = [z for z in voll if kl == "alle" or z["klasse"] == kl]
        b = [z for z in leer if kl == "alle" or z["klasse"] == kl]
        d, p, n = perm(a, b)
        if d is None: continue
        print(f"  {kl:>4}: Δ {d*100:+6.1f} Punkte   n={n[0]}/{n[1]}   p={p:.3f}   "
              f"{'signifikant' if p < 0.05 else 'nicht unterscheidbar'}")

if vier and weich:
    print("\n══ Schicht 4D: Epistemik-Anforderung entfernt (volle Kapazitaet) ══")
    basis = [z for z in weich if z["kappung"] == 10000]
    print(f"{'Klasse':>7} | {'mit Epistemik':>14} | {'ohne':>14} | Δ      p")
    for kl in ("I", "F", "R", "alle"):
        a = [z for z in basis if kl == "alle" or z["klasse"] == kl]
        b = [z for z in vier if kl == "alle" or z["klasse"] == kl]
        d, p, n = perm(a, b, seed=7)
        if d is None: continue
        print(f"{kl:>7} | {quote(a)*100:13.1f}% | {quote(b)*100:13.1f}% | {d*100:+5.1f}  p={p:.3f}")
    la = m([z.get("s", 0) for z in basis if z.get("ok")])
    lb = m([z.get("s", 0) for z in vier if z.get("ok")])
    print(f"  Latenz {la:.1f}s → {lb:.1f}s     "
          f"Werkzeugwahl leer: {sum(1 for z in basis if not z.get('werkzeuge'))}/{len(basis)}"
          f" → {sum(1 for z in vier if not z.get('werkzeuge'))}/{len(vier)}")
