<!-- RAE_META
{"packet_id":"KMP-HYP-THREE-TOPOLOGY-SEPARATION","title":"Hyperposition should separate semantic, coordination and physical topology","domains":["systems-architecture","ipc-distributed-systems","memory-state","synthetic-clay"],"topics":["hyperposition","dynamic-topology","coordination","locality","invariants"],"epistemic_class":"SYNTHESIS_HYPOTHESIS","claim_status_hint":"OPEN_WITH_CROSS_DOMAIN_SUPPORT","origin_class":"HYPERPOSITION_H2_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:50:00+07:00","updated_at":"2026-08-08T05:50:00+07:00","source_refs":["LoRe arXiv:2304.07133","DBSP arXiv:2203.16684","OSDI26 SBB","OSDI26 Soul/GCP","hyperposition-20260808T0550p0700-chatgpt-secondary"],"related_claim_ids":["H-HYP2-001","H-HYP2-003","H-HYP2-013","H-HYP2-016"],"related_experiment_ids":["EXP-HYP-H2-SCOPE-001"],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Instrument real FRANK semantic dependencies, invariant-conflict scopes and hardware locality; test whether independent remapping improves latency/correctness versus one fused topology."}
RAE_META -->

### Core
H2 proposes three independently evolving topologies: `S` semantic dependency, `C` invariant/coordination interference and `P` physical locality/execution. Treating them as one graph forces semantic closeness to imply synchronization and colocation, which current theory and systems evidence do not justify.

### Evidence / boundary
LoRe supports selecting coordination from invariant-threatening interactions. DBSP shows rich signed/non-monotone computation without itself defining concurrency control. OSDI 2025/26 systems show that physical synchronization/coherence topology materially affects performance. The transfer to FRANK remains OPEN.

### Implication
A compiler/controller should map `S → C,P` dynamically rather than storing one universal coupling topology.
