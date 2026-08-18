import sys, json, time, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P
from udb.abruf import nachbarschaft as N

c = P._connect()
P._ensure_vp_tables(c)
vor, rueck = N.paare(c)
bias = {r["gewicht"]: r for r in []}  # nicht gebraucht, messen() holt selbst
r1 = N.messen(c, vor, "vorwaerts  A->B")
r2 = N.messen(c, rueck, "rueckwaerts B->A")
c.close()
