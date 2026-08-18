import sys, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P
from udb.abruf import nachbarschaft as N

marke = sys.argv[1] if len(sys.argv) > 1 else "lauf"
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3

c = P._connect()
P._ensure_vp_tables(c)
vor, rueck = N.paare(c)
print(f"=== {marke}: {len(vor)} Vorwaertspaare, {len(rueck)} Rueckwaertspaare ===")

fwd_pct, bwd_pct = [], []
for i in range(runs):
    print(f"-- run {i} --")
    a1 = N.messen(c, vor, f"vorwaerts  A->B ({marke}#{i})")
    a2 = N.messen(c, rueck, f"rueckwaerts B->A ({marke}#{i})")
    fwd_pct.append(a1)
    bwd_pct.append(a2)

print(f"forward %:  {fwd_pct}")
print(f"backward %: {bwd_pct}")
c.close()
