import sys, json, statistics
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import messgeraet as M

satz_full = json.load(open(M.GOLD, encoding="utf-8"))
halb_b = [satz_full[i] for i in range(1, len(satz_full), 2)]
tmp = "/opt/unifieddb/_zulauf-2026-08-16/goldsatz_halb_B_mine.json"
json.dump(halb_b, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
M.GOLD = tmp

marke = sys.argv[1] if len(sys.argv) > 1 else "lauf"
runs = int(sys.argv[2]) if len(sys.argv) > 2 else 3

ergs = []
for i in range(runs):
    e = M.messen(f"{marke}_{i}", zeige_fehler=0)
    ergs.append(e)
    print(json.dumps(e, ensure_ascii=False))

med = [e["latenz_median_ms"] for e in ergs]
print(f"--- {marke}: n={len(halb_b)} runs={runs} ---")
print(f"  anker  : {[e['ankerquote'] for e in ergs]}")
print(f"  genau  : {[e['treffsicher_von_gesetzten'] for e in ergs]}")
print(f"  ausbeute (=treffsicher_absolut): {[e['treffsicher_absolut'] for e in ergs]}")
print(f"  auffind: {[e['auffindbar'] for e in ergs]}")
print(f"  median ms: {med}  (spread {max(med)-min(med):.1f})")
print(f"  p95 ms: {[e['latenz_p95_ms'] for e in ergs]}")
