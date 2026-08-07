<!-- RAE_META
{"packet_id":"KMP-GWT-LOGICAL-AVAILABILITY","title":"Logical global availability need not equal all-to-all physical broadcast","domains":["frank_gwt","ipc_distributed_systems","performance_economics"],"topics":["gwt","broadcast","routing","pull-rescue","fanout"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN_WITH_SYNTHETIC_SUPPORT","origin_class":"GWT_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-07T22:49:00Z","updated_at":"2026-08-07T22:49:00Z","source_refs":["SRC-GWT-GOYAL-2022","SRC-GWT-MOSA-2025"],"evidence_refs":["E-GWT-R2-MULTICAST-002","E-GWT-RUN-ADAPTIVE-001"],"related_claim_ids":["C-GWT-RUN-006","C-GWT-R2-001","C-GWT-R2-004"],"related_experiment_ids":["EXP-GWT-MULTICAST-002","EXP-LIVE-GWT-MULTICAST-SHADOW"],"predecessor_packet_ids":["KMP-GWT-CAUSAL-EPISODE","KMP-GWT-OVERCOUPLING"],"supersedes_packet_ids":[],"confidence":0.76,"verification_required":true,"falsifier_or_next_test":"Run selective router in FRANK shadow mode and measure causal audience recall against later reconstruction/effect receipts before suppressing any actual delivery.","search_terms":["global workspace selective broadcast","logical availability","causal multicast","workspace fanout","pull rescue"]}
RAE_META -->

### Core
Treat global availability as system-wide addressability of the workspace payload, while physical delivery is an adaptive mechanism: selective push to predicted causal audiences, pull rescue for unpushed audiences, and widened/full push when confidence or safety requires it.

### Evidence / boundary
A synthetic 20-audience proxy with router AUC≈0.921 and 95% pull sensitivity retained ~98.73% relevant coverage while reducing physical deliveries ~67.64% and irrelevant deliveries ~89.77% versus full push. This is not functional or safety equivalence; the residual misses are exactly what target replay must measure.

### Implication
CWCC should track causal-audience recall, false deliveries, rescue demand/latency and physical fanout rather than equating broadcast success with message emission.

### Next test
Shadow-run routing on real/twin FRANK without suppressing current broadcast.
