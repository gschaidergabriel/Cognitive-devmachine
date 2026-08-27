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
# und ein paar reine Schwerfaelle
worstcases = [heavy[:8], heavy[:16], heavy[:3]]

CAP = 5

def variante_alt(pf):
    qm = ",".join("?" for _ in pf)
    rows = c.execute(
        f"SELECT id,werkzeug,aktion,zeit,wirt,ziel_pfad FROM taetigkeit WHERE ziel_pfad IN ({qm}) ORDER BY id DESC",
        pf).fetchall()
    return len(rows)

def variante_union(pf):
    parts = []
    params = []
    for p in pf:
        parts.append("SELECT id,werkzeug,aktion,zeit,wirt,ziel_pfad FROM taetigkeit WHERE ziel_pfad=? ORDER BY id DESC LIMIT ?")
        params.extend([p, CAP])
    sql = " UNION ALL ".join(f"SELECT * FROM ({p})" for p in parts)
    rows = c.execute(sql, params).fetchall()
    return len(rows)

def bench(fn, samples, label):
    zeiten, rows = [], []
    for pf in samples:
        t0 = time.perf_counter()
        n_rows = fn(pf)
        zeiten.append((time.perf_counter()-t0)*1000)
        rows.append(n_rows)
    print(f"{label}: n={len(samples)} median={statistics.median(zeiten):.2f}ms p95={sorted(zeiten)[int(0.95*len(zeiten))] if len(zeiten)>1 else zeiten[0]:.2f}ms sum={sum(zeiten):.1f}ms total_rows_fetched={sum(rows)}")

# warmup
for _ in range(3):
    bench(variante_alt, pfade_samples[:5], "warmup-alt")
    bench(variante_union, pfade_samples[:5], "warmup-union")

print("\n=== gemischte Stichprobe (40% mit 2 Schwer-Pfaden angereichert) ===")
for lauf in range(3):
    bench(variante_alt, mixed_samples, f"ALT       Lauf{lauf+1}")
    bench(variante_union, mixed_samples, f"UNION-ALL Lauf{lauf+1}")

print("\n=== reine Schwerfaelle (heavy hitters) ===")
for lauf in range(3):
    bench(variante_alt, worstcases, f"ALT-worst       Lauf{lauf+1}")
    bench(variante_union, worstcases, f"UNION-worst Lauf{lauf+1}")
c.close()
