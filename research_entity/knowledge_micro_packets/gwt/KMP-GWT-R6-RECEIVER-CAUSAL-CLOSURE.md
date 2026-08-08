<!-- RAE_META
{"packet_id":"KMP-GWT-R6-RECEIVER-CAUSAL-CLOSURE","title":"Global addressability is not causal broadcast","domains":["gwt","frank_gwt","observability_recovery","model_runtime"],"topics":["broadcast","receiver-closure","common-driver","uptake","reentry","RCWC"],"epistemic_class":"OPEN_SYNTHESIS_WITH_EXTERNAL_PRIMARY_SUPPORT_AND_REPLICATED_SYNTHETIC_METHOD_CALIBRATION","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-09T02:05:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260809T0129p0700-chatgpt-secondary-r6-deep/RCWC_R6_ARCHITECTURE.json","research_entity/trigger_runs/gwt/gwt-20260809T0129p0700-chatgpt-secondary-r6-deep/EXPERIMENT_RESULTS.json","https://direct.mit.edu/netn/article/6/4/1186/111960/The-global-neuronal-workspace-as-a-broadcasting"],"evidence_refs":["research_entity/runtime/tool_results/gwt-r6-e2b-causal-calibration-20260809T0143p0700.json"],"related_experiment_ids":["EXP-GWT-R6-GLOBALITY-CONFOUND-001","EXP-GWT-R6-E2B-REPLICATION-004"],"confidence":0.9,"verification_required":true,"falsifier_or_next_test":"On live FRANK/target Qwen, preregister receiver universe and show receiver-specific do(WorkspaceEpisode) effects plus reconstruction/uptake/outcome/reentry closure against common-driver and addressable-but-ignored nulls."}
RAE_META -->

### Core
R6 separates the stages previously overloaded as “broadcast”:

`global addressability != delivery != reconstruction != uptake != causal use != outcome != re-entry`.

A state being visible/readable system-wide is therefore not enough to count as a causal GWT broadcast. A scientific broadcast claim should be relative to a declared receiver universe and carry receiver-specific receipts from delivery through local effect.

### Why
A local seeded calibration and an independent E2B replication both construct `COMMON_DRIVER_FANOUT` states with high passive workspace/receiver integration but `do(W)=0`. In the E2B replication, joint correlation with W is about `0.869` while the stipulated workspace intervention effect is zero. This is a method counterexample, not a FRANK estimate.

### Architecture consequence
Use `BroadcastEnvelope -> ReceiverReceipt[] -> CausalBroadcastMatrix -> BroadcastClosureReceipt`. Preserve a separate `GLOBAL_ADDRESSABLE_PULL` state for information that is available but not causally used.

### Boundary
This does not prove RCWC is the optimal FRANK architecture. It does not establish emergence or phenomenal consciousness. Target-Qwen/live-FRANK intervention remains required.
