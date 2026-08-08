<!-- RAE_META
{"packet_id":"KMP-GWT-R6-CAPACITY-FINITE-OPTIMUM","title":"Workspace utility can peak before maximum capacity","domains":["gwt","frank","android_edge_runtime","model_runtime"],"topics":["capacity","competition","distractors","resource-governor","selective-broadcast"],"epistemic_class":"OPEN_MECHANISM_HYPOTHESIS_WITH_REPLICATED_SYNTHETIC_CALIBRATION","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-09T02:05:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260809T0129p0700-chatgpt-secondary-r6-deep/EXPERIMENT_RESULTS.json"],"evidence_refs":["research_entity/runtime/tool_results/gwt-r6-e2b-causal-calibration-20260809T0143p0700.json"],"related_experiment_ids":["EXP-GWT-R6-CAPACITY-OVERCOUPLING-003","EXP-GWT-R6-E2B-REPLICATION-004"],"confidence":0.84,"verification_required":true,"falsifier_or_next_test":"Sweep target FRANK/Qwen workspace capacity under controlled relevant-item and distractor loads while measuring task quality, receiver closure, latency, RAM/KV and false association."}
RAE_META -->

### Core
More available workspace content can improve relevant-item inclusion while simultaneously increasing distractor/nuisance load. Therefore maximum capacity is not necessarily maximum utility.

Two seeded synthetic implementations independently produced the same qualitative curve. In the E2B replication, relevant inclusion rose from about `0.218` at `k=1` to `1.0` at `k=32`, while success peaked near `k=8` (`~0.660`) and fell to `~0.584` at `k=32`.

### Architecture consequence
Treat workspace capacity as an adaptive control parameter and measure quality × causal receiver utility × cost. This supports testing globally addressable but selectively delivered policies rather than defaulting to maximal all-to-all payloads.

### Boundary
The optimal `k=8` belongs only to the constructed calibration family. It is not a FRANK workspace-size recommendation.
