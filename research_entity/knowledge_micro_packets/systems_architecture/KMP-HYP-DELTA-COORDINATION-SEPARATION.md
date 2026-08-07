<!-- RAE_META
{"packet_id":"KMP-HYP-DELTA-COORDINATION-SEPARATION","title":"Change polarity and coordination requirement are separate runtime dimensions","domains":["systems-architecture","ipc-distributed-systems","memory-state"],"topics":["signed-delta","revocation","coordination","DBSP","invariant-interference"],"epistemic_class":"SYNTHESIS_HYPOTHESIS","claim_status_hint":"OPEN_WITH_IMPLEMENTATION_AND_LITERATURE_SUPPORT","origin_class":"HYPERPOSITION_H2_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:50:00+07:00","updated_at":"2026-08-08T05:50:00+07:00","source_refs":["DBSP arXiv:2203.16684","Feldera DBSP documentation","LoRe arXiv:2304.07133","arXiv:2412.12493","hyperposition-20260808T0550p0700-chatgpt-secondary"],"related_claim_ids":["H-HYP2-002","H-HYP2-003","H-HYP2-009","H-HYP2-017"],"related_experiment_ids":["EXP-HYP-H2-SCOPE-001"],"confidence":0.88,"verification_required":true,"falsifier_or_next_test":"Classify live FRANK ADD/RETRACT/REPLACE/COMPENSATE transitions and separately infer invariant scopes; test whether non-monotone but non-interfering changes remain safe without global coordination."}
RAE_META -->

### Core
H2 weakens H1's monotonicity-only gate. A negative/replacing delta describes **what changed**; invariant interference describes **what must coordinate**. External effect authority is a third independent question.

### Evidence / boundary
DBSP/Feldera processes insertions and deletions incrementally while explicitly not supplying transaction/concurrency control. LoRe selectively coordinates interactions that threaten declared invariants. This supports architectural separation, not unrestricted coordination-free mutation in FRANK.

### Implication
Use a three-axis transition classifier: `delta semantics × invariant-interference scope × effect authority`.
