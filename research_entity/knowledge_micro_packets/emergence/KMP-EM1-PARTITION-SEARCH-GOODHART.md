<!-- RAE_META
{"packet_id":"KMP-EM1-PARTITION-SEARCH-GOODHART","title":"Post-hoc macro-partition search can manufacture emergence-looking information scores under a null","domains":["emergence","formal_methods_testing","hyperposition"],"topics":["causal_emergence","effective_information","coarse_graining","partition_search","goodhart","heldout_validation"],"epistemic_class":"EXPERIMENT_MEMORY","claim_status_hint":"CURRENT_METHOD_DELTA","origin_class":"EMERGENZ_E1_SYNTHETIC_NULL_CONTROL_PLUS_JUDGE0","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T18:08:00+07:00","source_refs":["research_entity/trigger_runs/emergenz/emergenz-20260808T1756p0700-chatgpt-secondary/EXPERIMENT_RESULTS.json","research_entity/runtime/tool_results/em1-judge0-nullcontrols-20260808T1756p0700.json"],"evidence_refs":["EXP-EM1-PARTITION-SEARCH-NULL-002","EXP-EM1-JUDGE0-REPLICATION-006"],"confidence":0.95,"verification_required":true,"falsifier_or_next_test":"Run candidate macro discovery with nested held-out interventions and partition-search permutation nulls; the claimed macro advantage must survive out of sample.","search_terms":["causal emergence partition search","coarse graining goodhart","heldout macro partition","effective information selection bias"]}
RAE_META -->

### Core
Under a true independence null, E1 searched many macro partitions on finite training data. The best selected partition reached 0.00774 bit training MI but only 0.000121 bit on a large held-out sample. Independent Judge0 code reproduced the direction: 0.01458 bit selected training MI versus 0.000576 bit held out.

### Boundary
The exact magnitudes depend on sample size and search space. The durable result is the selection-bias mechanism: optimizing the reported macro/assembly definition on the same sample used to score it can create an emergence-looking maximum from noise.

### Implication
Causal-emergence/macroscale discovery needs preregistration, nested holdout/cross-validation, or an explicit null distribution that repeats the entire partition-search procedure. One maximum EI/MI/CE score is not sufficient evidence.
