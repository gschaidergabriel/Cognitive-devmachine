<!-- RAE_META
{"packet_id":"KMP-GWT-R6-DETERMINISTIC-RECEIVER-RAIL","title":"Deterministic causal normalization before generative receiver interpretation","domains":["frank_gwt","claycode","model_runtime","observability_recovery"],"topics":["receiver-receipt","projection","4b","deterministic-before-generative","causal-rail"],"epistemic_class":"EXTERNAL_GENERIC_4B_PROXY_RESULT_OPEN_FOR_TARGET_REPLICATION","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","created_at":"2026-08-09T02:05:00+07:00","source_refs":["research_entity/trigger_runs/gwt/gwt-20260809T0129p0700-chatgpt-secondary-r6-deep/EXPERIMENT_RESULTS.json"],"evidence_refs":["GitHub Actions run 31273195345 job 93142504735"],"related_experiment_ids":["EXP-GWT-R6-4B-RECEIVER-RAIL-005"],"confidence":0.87,"verification_required":true,"falsifier_or_next_test":"Repeat with target Qwen3-4B using matched raw/typed/deterministically-normalized rails and multiple randomized corpora; verify exact semantic lowering independently of model output."}
RAE_META -->

### Core
Do exact causal receipt arithmetic and identity checks before asking a small generative reader to reason over them when those computations are deterministic.

In the latest NVIDIA Nemotron-Mini-4B validation, semantically related receiver cases were classified at `4/12` with raw prose/numeric receipts, `2/12` in the final typed-ID/raw-numeric repeat with two omitted cases, and `12/12` when the exact `doW_effect = ZERO|NONZERO` predicate and common-driver flag were deterministically normalized before model interpretation. The normalized arm also used fewer prompt tokens than the other two final arms.

### Interpretation
This is evidence for responsibility allocation, not evidence that a particular syntax is intrinsically superior. The normalized arm deliberately moved an exact calculation out of the model. That is the architectural point: generative cognition should consume typed causal primitives where exact host computation is available, while raw evidence/provenance remains auditable.

### Negative result
The typed-ID/raw-numeric arm varied across repeated provider executions despite temperature 0 and remained unreliable. Therefore format compliance and deterministic serving cannot be assumed merely from temperature settings.

### Boundary
Nemotron-Mini-4B is a generic 4B proxy, not Qwen3-4B and not live FRANK. Target replication is mandatory before promotion.
