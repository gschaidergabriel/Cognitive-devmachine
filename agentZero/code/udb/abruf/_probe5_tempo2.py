import sqlite3, time, statistics, json, sys, random
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

c = P._connect()
pfade_samples = json.load(open("/tmp/pfade_samples.json"))
heavy = [r[0] for r in c.execute(
    "SELECT ziel_pfad, count(*) c FROM taetigkeit WHERE ziel_pfad IS NOT NULL "
    "GROUP BY ziel_pfad ORDER BY c DESC LIMIT 30").fetchall()]
random.seed(42)
mixed_samples = []
for pf in pfade_samples:
    pf2 = list(pf)
    if random.random() < 0.4:
        pf2 = pf2 + random.sample(heavy, k=min(2, len(heavy)))
    mixed_samples.append(pf2)
worstcases = [heavy[:8], heavy[:16], heavy[:3]]
CAP = 5

def variante_alt(pf):
    qm = ",".join("?" for _ in pf)
    rows = c.execute(
        f"SELECT id,werkzeug,aktion,zeit,wirt,ziel_pfad FROM taetigkeit WHERE ziel_pfad IN ({qm}) ORDER BY id DESC",
        pf).fetchall()
    return rows

def variante_union_sorted(pf):
    parts = []
    params = []
    for p in pf:
        parts.append("SELECT id,werkzeug,aktion,zeit,wirt,ziel_pfad FROM taetigkeit WHERE ziel_pfad=? ORDER BY id DESC LIMIT ?")
        params.extend([p, CAP])
    inner = " UNION ALL ".join(f"SELECT * FROM ({p})" for p in parts)
    sql = f"SELECT * FROM ({inner}) ORDER BY id DESC"
    rows = c.execute(sql, params).fetchall()
    return rows

# KORREKTHEITSTEST: pro Datei (did) exakt wie im echten Code nachbauen, capped bei 5,
# und vergleichen ob ALT vs NEU dieselben (id,ziel_pfad)-Mengen je pfad liefern.
def cap5_per_pfad(rows):
    out = {}
    for r in rows:
        p = r["ziel_pfad"]
        out.setdefault(p, [])
        if len(out[p]) < CAP:
            out[p].append(r["id"])
    return out

mismatches = 0
checked = 0
for pf in mixed_samples + worstcases:
    a = cap5_per_pfad(variante_alt(pf))
    b = cap5_per_pfad(variante_union_sorted(pf))
    checked += 1
    if a != b:
        mismatches += 1
        print("MISMATCH fuer pf[:3]=", pf[:3])
        for k in a:
            if a.get(k) != b.get(k):
                print(" pfad", k, "ALT", a.get(k), "NEU", b.get(k))

print(f"Korrektheitstest: {checked} Faelle geprueft, {mismatches} Abweichungen")

def bench(fn, samples, label):
    zeiten = []
    for pf in samples:
        t0 = time.perf_counter()
        fn(pf)
        zeiten.append((time.perf_counter()-t0)*1000)
    print(f"{label}: n={len(samples)} median={statistics.median(zeiten):.3f}ms sum={sum(zeiten):.1f}ms")

for _ in range(2):
    bench(variante_alt, pfade_samples[:5], "warm")
    bench(variante_union_sorted, pfade_samples[:5], "warm")

print("\n=== gemischt (mit sortiertem UNION-ALL, korrekt) ===")
for lauf in range(3):
    bench(variante_alt, mixed_samples, f"ALT   Lauf{lauf+1}")
    bench(variante_union_sorted, mixed_samples, f"NEU   Lauf{lauf+1}")

print("\n=== worst case ===")
for lauf in range(3):
    bench(variante_alt, worstcases, f"ALT-worst Lauf{lauf+1}")
    bench(variante_union_sorted, worstcases, f"NEU-worst Lauf{lauf+1}")
c.close()
