<!-- RAE_META
{"packet_id":"KMP-GWT-CAUSAL-STAGE-ORTHOGONALITY","title":"GWT effects require stage-orthogonal interventions across graph prior, selection and projection","domains":["frank_gwt","claygraph","model_runtime","observability_recovery"],"topics":["gwt","causal-identifiability","stage-orthogonality","projection","candidate-selection"],"epistemic_class":"SYNTHETIC_METHOD_PLUS_8B_PROXY","claim_status_hint":"OPEN_ARCHITECTURE_RULE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:35:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260808T1721p0700-chatgpt-secondary/FINAL_REPORT.md","research_entity/trigger_runs/gwt/gwt-20260808T1721p0700-chatgpt-secondary/EXPERIMENT_RESULTS.json"],"confidence":0.94,"verification_required":true,"falsifier_or_next_test":"Run live/twin FRANK factorials where exactly one of graph field, workspace selection, projection or re-entry changes while the others are pinned/counterbalanced."}
RAE_META -->

### Core
A `GWT on/off` comparison is not causally interpretable if it simultaneously changes ClayGraph activation/candidate membership, CognitiveFrame contents, winner selection, reader projection/order or re-entry. Run 4's constructed null had zero true workspace-selection effect but a bundled ablation reported +0.2396; Judge0 independently reproduced +0.23981 while the orthogonal workspace contrast remained zero.

### Contract
Persist/bind at least: `CognitiveFrame`, graph+activation epochs, Assembly/candidate-set hash, competition/winner, gate policy, WorkspaceEpisode hash, projection hash/order/reader version, uptake, effect, outcome and re-entry receipts. Attribute an effect to one stage only under isolated/randomized/counterbalanced manipulation.

### Boundary
This establishes an identifiability rule, not a live FRANK effect size and not a consciousness claim.
