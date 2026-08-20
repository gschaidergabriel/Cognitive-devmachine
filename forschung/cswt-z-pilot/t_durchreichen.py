import sys, json, re
sys.path.insert(0, "/opt/clayverse"); sys.path.insert(0, "/tmp")
from cswt_sonden2 import SONDEN
from clayverse.store import UnifiedDB
from clayverse.mistral_prestage import pipeline, prestage
db = UnifiedDB("/var/lib/clay/wiki.db")
print("Reicht die Vorstufe den Korpusinhalt an Zero weiter?\n")
tr = n = 0
for kl, frage, muster in SONDEN:
    if kl != "I":
        continue
    n += 1
    w = pipeline._gather_world_safe(db, "session:gabriel:2", frage)
    vw = pipeline._vorstufen_world(w)
    im_raum = any(re.search(m, json.dumps(vw.get("corpus") or [], ensure_ascii=False).lower())
                  for m in muster)
    env = prestage.run_prestage(raw_prompt=frage, world=vw, current_user="gabriel",
                                current_user_profile=pipeline._profil_safe(db, "gabriel"))
    cp = (env.get("caveman_prompt") or "")
    im_auftrag = any(re.search(m, cp.lower()) for m in muster)
    tr += im_auftrag
    print(f"  Raum={'JA ' if im_raum else 'NEIN'}  Auftrag={'JA ' if im_auftrag else 'NEIN'}  {frage[:44]}")
    print(f"      -> {cp[:150]}")
print(f"\n{tr}/{n} Antworten stehen im Auftrag, den Zero bekommt")
