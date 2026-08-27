<!-- RAE_META
{"packet_id":"KMP-HYP-H3-NARY-ACTIVATION-SAFETY","title":"Pairwise flattening can create false associative activation paths","domains":["hyperposition","claygraph","memory-state"],"topics":["nary","role-binding","spreading-activation","pairwise-ambiguity"],"epistemic_class":"MEASURED_SYNTHETIC_COUNTEREXAMPLE","claim_status_hint":"CURRENT_WITH_SYNTHETIC_BOUNDARY","origin_class":"HYPERPOSITION_H3_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:22:00+07:00","source_refs":["EXP-HYP-H3-NARY-ACT-002","Judge0 hyp-h3-1722-judge0","KMP-GROQ8B-HYP-ROLE-PROJECTION"],"related_experiment_ids":["EXP-HYP-H3-NARY-ACT-002"],"confidence":0.93,"verification_required":true,"falsifier_or_next_test":"Target-4B randomized-order activation/retrieval test over real relation-instance corpus."}
RAE_META -->

### Core
When ternary `(sender, recipient, asset)` events are flattened into independent pairwise edges, activation from `sender + asset` can intersect edges originating from different events and produce recipients that never participated in the same relation instance.

### Evidence
In H3's synthetic workload, mean pairwise precision fell from ~0.834 at 3k relations to ~0.038 at 40k as overlap increased. Judge0 independently reproduced the 12k condition at 0.20656 pairwise precision versus 1.0 for exact relation-instance matching.

### Boundary / implication
This rejects naive pairwise activation as universally safe; it does not require a native hypergraph database. Relation-instance identity plus role bindings remain a portable exact representation.
