import sys, json
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import messgeraet as M

halb = sys.argv[1]   # "A" oder "B"
marke = sys.argv[2]

satz = json.load(open(M.GOLD, encoding="utf-8"))
idx = range(0, len(satz), 2) if halb == "A" else range(1, len(satz), 2)
teil = [satz[i] for i in idx]
tmp = f"/tmp/goldsatz_halb_{halb}.json"
json.dump(teil, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
M.GOLD = tmp  # dasselbe messen() wiederverwenden, nur die Datenmenge wechseln

erg = M.messen(marke, zeige_fehler=0)
print(json.dumps(erg, ensure_ascii=False, indent=2))
