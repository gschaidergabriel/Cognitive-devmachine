<!-- RAE_META
{"packet_id":"KMP-CG5-TCQS-ASSEMBLY-IDENTITY","title":"ClayGraph Assembly collection algebra is part of candidate causal identity","domains":["claygraph","claycode","unifieddb","gwt"],"topics":["TCQS","Assembly","candidate topology","selection identity"],"epistemic_class":"EXECUTABLE_MECHANISM_TRANSFER_SHARED_ANCESTRY","status_hint":"OPEN_SUPPORTED_REQUIREMENT","origin_actor":"chatgpt-secondary","source_refs":["research_entity/trigger_runs/claycode/claycode-20260808T2104p0700-chatgpt-secondary-r3/CC_RC1_7_TCQS.claycode.json","research_entity/trigger_runs/clay/clay-20260808T2132p0700-chatgpt-secondary-r4/FINAL_REPORT.md","research_entity/trigger_runs/claygraph/claygraph-20260808T2212p0700-chatgpt-secondary-r3/CLAYGRAPH_SCHEMA.claycode.json"],"verification_required":true}
RAE_META -->

### Contract
ClayGraph should represent:
- root and selected assertion membership as `SET<Ref>`;
- activation/ranking frontier as `WEIGHTED<Ref,Salience>`;
- concrete reader handoff order as `ORDERED<Ref>`;
- multiplicity as `MULTISET<Ref>` only when counts are semantically meaningful.

Collection kind participates in semantic/candidate identity. Identical member bytes do not imply identical candidate state when order, multiplicity or weights affect downstream selection/uptake.

### Consequence
UnifiedDB lowering and GWT attribution must preserve collection semantics and selection-plan identity before claiming a workspace or model effect.
