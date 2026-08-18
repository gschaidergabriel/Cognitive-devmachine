import sqlite3, time, statistics, json, sys
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

c = P._connect()
verz_samples = json.load(open("/tmp/verz_samples.json"))
CAP = 6

def alt(wirt, verz, did):
    rows = c.execute(
        """SELECT DISTINCT d2.id AS did, d2.titel FROM fundort f2 JOIN datei d2 ON d2.id=f2.datei_id
           WHERE f2.wirt=? AND f2.pfad LIKE ? AND d2.id!=? LIMIT ?""",
        (wirt, verz + "%", did, CAP)).fetchall()
    return rows

def neu(wirt, verz, did):
    ober = verz[:-1] + chr(ord(verz[-1]) + 1)
    rows = c.execute(
        """SELECT DISTINCT d2.id AS did, d2.titel FROM fundort f2 JOIN datei d2 ON d2.id=f2.datei_id
           WHERE f2.wirt=? AND f2.pfad>=? AND f2.pfad<? AND d2.id!=? LIMIT ?""",
        (wirt, verz, ober, did, CAP)).fetchall()
    return rows

mismatches = 0
for (wirt, verz, did) in verz_samples:
    a = {(r["did"], r["titel"]) for r in alt(wirt, verz, did)}
    b = {(r["did"], r["titel"]) for r in neu(wirt, verz, did)}
    if a != b:
        mismatches += 1
        if mismatches <= 5:
            print("MISMATCH", wirt, verz, "ALT", a, "NEU", b)
print(f"Korrektheitstest Geschwister: {len(verz_samples)} Faelle, {mismatches} Abweichungen")

def warm():
    for wirt, verz, did in verz_samples[:20]:
        alt(wirt, verz, did); neu(wirt, verz, did)
for _ in range(3): warm()

def bench(fn, label):
    zeiten = []
    for wirt, verz, did in verz_samples:
        t0 = time.perf_counter()
        fn(wirt, verz, did)
        zeiten.append((time.perf_counter()-t0)*1000)
    print(f"{label}: n={len(verz_samples)} median={statistics.median(zeiten):.3f}ms p95={sorted(zeiten)[int(0.95*len(zeiten))]:.3f}ms sum={sum(zeiten):.1f}ms")

for lauf in range(3):
    bench(alt, f"ALT (LIKE)  Lauf{lauf+1}")
    bench(neu, f"NEU (Range) Lauf{lauf+1}")
c.close()
