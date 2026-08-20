# -*- coding: utf-8 -*-
"""Sandkastenkopie der Herz-DB fuer die CSWT-Z-Schichten 5 und 6.

Loeschen, Implantieren und Forken der Lebensgeschichte gehoeren NIE an die
laufende Entitaet. Diese Kopie ist das Versuchsobjekt; die echte wiki.db wird
nur gelesen.
"""
import os, shutil, sqlite3, subprocess, time

QUELLE = "/var/lib/clay/wiki.db"
ZIEL = "/var/lib/clay/cswt-sandbox.db"

frei = shutil.disk_usage("/").free / 1024**3
gross = os.path.getsize(QUELLE) / 1024**3
print(f"Quelle {gross:.2f} GB · frei {frei:.1f} GB")
if frei < gross * 1.5:
    raise SystemExit("zu wenig Platz -- abgebrochen, nichts angefasst")

t0 = time.time()
for endung in ("", "-wal", "-shm"):
    q = QUELLE + endung
    if os.path.exists(q):
        shutil.copy2(q, ZIEL + endung)
print(f"kopiert in {time.time()-t0:.1f}s")

c = sqlite3.connect(ZIEL)
c.execute("PRAGMA wal_checkpoint(TRUNCATE)")
n = c.execute("SELECT COUNT(*) FROM artikel").fetchone()[0]
m = c.execute("SELECT COUNT(*) FROM durable_memory").fetchone()[0]
t = c.execute("SELECT COUNT(*) FROM turns").fetchone()[0]
c.close()

for endung in ("", "-wal", "-shm"):
    p = ZIEL + endung
    if os.path.exists(p):
        os.chown(p, 5001, 5001)      # der Container laeuft als 5001
        os.chmod(p, 0o664)
print(f"Sandkasten bereit: {n} Artikel · {m} Gedaechtniseintraege · {t} Zuege")
print("Groesse:", round(os.path.getsize(ZIEL)/1024**3, 2), "GB")
