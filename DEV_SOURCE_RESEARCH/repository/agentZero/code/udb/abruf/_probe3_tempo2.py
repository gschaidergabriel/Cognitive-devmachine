import sqlite3, time, statistics, json, sys
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P

c = P._connect()
pfade_samples = json.load(open("/tmp/pfade_samples.json"))
CAP = 5

def warmup():
    for _ in range(3):
        for pf in pfade_samples[:10]:
            qm = ",".join("?" for _ in pf)
            c.execute(f"SELECT id FROM taetigkeit WHERE ziel_pfad IN ({qm}) ORDER BY id DESC", pf).fetchall()

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
    sql = " UNION ALL ".join(parts)
    rows = c.execute(sql, params).fetchall()
    return len(rows)

def zeit(fn, n=3):
    ergebnisse = []
    zeiten = []
    for pf in pfade_samples:
        t0 = time.perf_counter()
        n_rows = fn(pf)
        zeiten.append((time.perf_counter()-t0)*1000)
        ergebnisse.append(n_rows)
    return zeiten, ergebnisse

warmup()

for name, fn in [("ALT (IN, kein LIMIT)", variante_alt), ("UNION-ALL (je Pfad LIMIT 5)", variante_union)]:
    for lauf in range(3):
        zeiten, rows = zeit(fn)
        gesamt_rows = sum(rows)
        print(f"{name}  Lauf {lauf+1}: median={statistics.median(zeiten):.2f}ms  "
              f"p95={sorted(zeiten)[int(0.95*len(zeiten))]:.2f}ms  sum={sum(zeiten):.1f}ms  "
              f"gefetchte_zeilen_gesamt={gesamt_rows}")
c.close()
