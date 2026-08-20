import json, random, sys
z = [json.loads(l) for l in open("/root/cswt-batterie.jsonl", encoding="utf-8") if l.strip()]
if not z:
    sys.exit("noch keine Daten")
modi = []
for x in z:
    if x["modus"] not in modi: modi.append(x["modus"])
def q(zz, kl=None):
    y = [x for x in zz if kl is None or x["klasse"] == kl]
    return (sum(x.get("treffer", 0) for x in y) / len(y), len(y)) if y else (0, 0)
print(f"{'Modus':<22} | {'I':>12} | {'F':>12} | {'R':>12} | {'gesamt':>8} | Latenz")
print("-" * 88)
for m in modi:
    zm = [x for x in z if x["modus"] == m]
    zellen = []
    for kl in ("I", "F", "R"):
        a, n = q(zm, kl); zellen.append(f"{int(a*n)}/{n} {a*100:5.1f}%")
    ok = [x for x in zm if x.get("ok")]
    g, _ = q(zm)
    lat = sum(x.get("s", 0) for x in ok) / len(ok) if ok else 0
    print(f"{m:<22} | " + " | ".join(f"{c:>12}" for c in zellen) + f" | {g*100:7.1f}% | {lat:5.1f}s")

def perm(a, b, N=20000, seed=5):
    ta = [i.get("treffer", 0) for i in a]; tb = [i.get("treffer", 0) for i in b]
    if not ta or not tb: return None, None
    o = sum(ta)/len(ta) - sum(tb)/len(tb); pool = ta + tb; r = random.Random(seed); e = 0
    for _ in range(N):
        r.shuffle(pool)
        if abs(sum(pool[:len(ta)])/len(ta) - sum(pool[len(ta):])/len(tb)) >= abs(o) - 1e-12: e += 1
    return o, e/N

basis = [x for x in z if x["modus"] == modi[0]]
print(f"\n── gegen die Grundlinie ({modi[0]}) ──")
for m in modi[1:]:
    zm = [x for x in z if x["modus"] == m]
    zeile = f"  {m:<22}"
    for kl in ("I", None):
        a = [x for x in basis if kl is None or x["klasse"] == kl]
        b = [x for x in zm if kl is None or x["klasse"] == kl]
        d, p = perm(a, b)
        if d is None: continue
        zeile += f"  {(kl or 'alle')}: Δ {d*100:+6.1f} p={p:.3f}"
    print(zeile)
