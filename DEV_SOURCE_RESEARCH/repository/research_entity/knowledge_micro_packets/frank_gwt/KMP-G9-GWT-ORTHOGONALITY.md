<!-- RAE_META
{"packet_id":"KMP-G9-GWT-ORTHOGONALITY","title":"Graph prior, workspace selection, projection and re-entry require orthogonal interventions","domains":["frank_gwt","claygraph","synthetic_clay"],"topics":["gwt","causal_identifiability","projection","graph_prior"],"epistemic_class":"SYNTHETIC_IDENTIFIABILITY_METHOD","origin_class":"CLAY_G9_WITH_FRESH_GWT_C4","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:40:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260808T1721p0700-chatgpt-secondary/EXPERIMENT_RESULTS.json","research_entity/trigger_runs/clay/clay-20260808T1716p0700-chatgpt-secondary-r2/FRESHNESS_DELTA.md"],"verification_required":true}
RAE_META -->

### Core
Fresh GWT Cycle 4 constructed a null where workspace selection had zero causal effect, yet a bundled workspace on/off contrast produced ~0.24 apparent delta because graph-prior/projection changed with it. Orthogonal intervention recovered 0 workspace delta; Judge0 reproduced the direction.

### Method rule
Future FRANK GWT experiments factor `GRAPH_PRIOR × WORKSPACE_SELECTION × PROJECTION × REENTRY`. Pin CognitiveFrame/graph epoch/content/order/token budget wherever the manipulated factor does not require changing them. Gate events, graph activation and transport remain distinct from ignition/reconstruction/uptake.

### Boundary
Toy effect magnitudes are not FRANK effect sizes; the result is an identifiability calibration.
