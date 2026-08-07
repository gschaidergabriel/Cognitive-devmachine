<!-- RAE_META
{"packet_id":"KMP-HYP-REBUILD-CROSSOVER","title":"Incremental propagation needs a measured rebuild crossover","domains":["systems-architecture","memory-state","synthetic-clay"],"topics":["incremental-computation","revocation","rebuild","cascade-tail","projection"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_ARCHITECTURE_WITH_SYNTHETIC_SUPPORT","origin_class":"HYPERPOSITION_H2_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:50:00+07:00","updated_at":"2026-08-08T05:50:00+07:00","source_refs":["DBSP arXiv:2203.16684","Feldera documentation","hyperposition-20260808T0550p0700-chatgpt-secondary:EXP-HYP-H2-REVOKE-002"],"related_claim_ids":["H-HYP2-011","H-HYP2-012"],"related_experiment_ids":["EXP-HYP-H2-REVOKE-002"],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Measure real FRANK projection update/rebuild cost across revocation breadth and cascade-tail regimes, then test an online mode selector."}
RAE_META -->

### Core
Incremental maintenance is beneficial only while the affected dependency scope is sufficiently small. H2 measured an exact synthetic crossover: incremental invalidation was ~35.6× faster than rebuild when one of 100 clusters was touched, near parity around 60 clusters, and slower than rebuild by 80–100 clusters.

### Evidence / boundary
The benchmark is a 50k-node Python DAG proxy with AND-style dependencies; its numerical crossover is not transferable as a production threshold. External IVM work likewise shows update cost depends on query/algebra structure.

### Implication
Hyperposition projections should expose touched-state fraction, cascade tails and rebuild cost, then choose incremental, partial rebuild or full rebuild dynamically.
