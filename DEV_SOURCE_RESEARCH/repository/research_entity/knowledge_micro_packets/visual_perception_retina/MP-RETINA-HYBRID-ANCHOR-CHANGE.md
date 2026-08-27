<!-- RAE_META
{"packet_id":"MP-RETINA-HYBRID-ANCHOR-CHANGE","title":"Hybrid anchor plus change-driven visual processing","domains":["visual_perception_retina","interfaces_io","performance_economics"],"topics":["event vision","sampling","latency"],"epistemic_class":"WEB_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN_HYPOTHESIS","origin_class":"EXTERNAL_PLUS_INTERNAL_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09","updated_at":"2026-08-09","source_refs":["https://www.nature.com/articles/s41586-024-07409-w","https://arxiv.org/abs/2402.15584"],"evidence_refs":["research_entity/retina/runs/retina-20260809T0615p0700-deep-foundry/SYNTHETIC_MECHANISM_RECEIPT.json"],"related_claim_ids":[],"related_experiment_ids":["RET-E7"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.80,"verification_required":true,"falsifier_or_next_test":"Periodic vs change-only vs hybrid fixed/adaptive anchors on real camera/screen streams.","search_terms":["retina anchor frame change event hybrid visual latency"]}
RAE_META -->

### Core
The strongest current fast-path candidate is not event-only vision but hybrid `anchor evidence + sparse change deltas`. Unchanged state can remain cached/persistent; anchors periodically or adaptively refresh static semantics and allow recovery.

### Evidence / boundary
Peer-reviewed event-camera research demonstrates real latency/bandwidth advantages of hybrid frame+event sensing in an automotive task, while also exposing limitations of event-only signals. State-space event models provide additional precedent for carrying state across asynchronous events. A synthetic FRANK sanity check similarly shows that change-only processing cannot recover deliberately lost static state without anchors. None of these sources measures ordinary-camera FRANK performance.

### Implication
Implement the semantic contract independently of sensor type so desktop frame differencing, Android camera pipelines and future event hardware can lower to the same Evidence/Percept semantics.

### Next test
E7 on frozen streams with static text, slow changes, fast events and crash/restart recovery.
