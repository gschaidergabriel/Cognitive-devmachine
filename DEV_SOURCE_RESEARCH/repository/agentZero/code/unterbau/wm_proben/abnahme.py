# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P
c = P._ro()
t = c.execute("SELECT titel FROM artikel WHERE titel IS NOT NULL AND length(titel)>20 "
              "ORDER BY id LIMIT 1").fetchone()[0]
pk = P.paket(t, budget=8)
hp = pk["hyperposition"]
print("Abfrage:", t[:70])
print("\n--- QUITTUNG (collapse_preserves_rejected_and_deferred_lineage) ---")
q = hp["quittung"]
print("  zustand      :", hp["zustand"], "| nicht_kollabiert:", hp["nicht_kollabiert"])
print("  gewaehlt     :", [x["id"][:40] for x in q["gewaehlt"]])
print("  nicht_gewaehlt:", len(q["nicht_gewaehlt"]), "Eintraege ->",
      [x["id"][:34] for x in q["nicht_gewaehlt"]][:3], "...")
print("  grund        :", q["nicht_gewaehlt_grund"])
print("  ausloeser    :", q["ausloeser"])
print("  schwellen    :", q["schwellen"])
print("  nichts_geloescht:", q["nichts_geloescht"], "| schema:", q["schema"])
print("\n--- READOUT (no_single_score_replaces_typed_readouts) ---")
for k, v in hp["readout"].items():
    print("   %-30s %s" % (k, json.dumps(v, ensure_ascii=False)[:90]))
print("\n--- TOPOLOGIEN (semantic != active != coordination != physical) ---")
print("  ", json.dumps(pk["topologien"], ensure_ascii=False))
mehr = [e for e in pk["codependenzen"] if len(e.get("topologien", [])) > 1]
print("  Codependenzen mit MEHREREN Topologien:", len(mehr), "von", len(pk["codependenzen"]))
for e in mehr[:3]:
    print("     %s --%s--> %s   %s" % (e["von"][:26], e["art"], e["nach"][:26], e["topologien"]))
print("\n--- SCHEMA einmal nachschlagbar ---")
print("  Schluessel:", list(P.SCHEMA_HINWEISE.keys()))
print("  wm-topologie-1.abbildung['T_KAUSALKREDIT'] =",
      P.SCHEMA_HINWEISE["wm-topologie-1"]["abbildung"]["T_KAUSALKREDIT"])
print("\n--- unveraendert wahr ---")
print("  model_call_count :", pk["beobachtungen"]["model_call_count"])
print("  autoritaet       :", pk["autoritaet"])
print("  gegenseite drin  :", "gegenseite" in pk, "| nie_gekappt:", pk["politik"]["nie_gekappt"])
