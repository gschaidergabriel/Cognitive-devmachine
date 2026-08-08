<!-- RAE_META
{"packet_id":"KMP-HYP-H3-TOPOLOGY-BASIS","title":"Compiled cognitive topology requires an explicit epoch basis","domains":["hyperposition","claygraph","frank-gwt","xeno-claycode"],"topics":["TopologyBasis","semantic-epoch","activation-epoch","CognitiveFrame","replay"],"epistemic_class":"SYNTHESIS_HYPOTHESIS_WITH_SYNTHETIC_SUPPORT","claim_status_hint":"OPEN","origin_class":"HYPERPOSITION_H3_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T17:22:00+07:00","source_refs":["ClayGraph G1d Cycle 4","FRANK C4 CognitiveFrame","CC8 OTCC","GWT R3","hyperposition-20260808T1722p0700-chatgpt-secondary-r2"],"related_experiment_ids":["EXP-HYP-H3-EPOCH-001"],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Instrument live Assemblies with semantic_epoch + activation_epoch + CognitiveFrame + projection semantics and test whether basis validation improves replay/causal correctness."}
RAE_META -->

### Core
H3 proposes `TopologyBasis = semantic_epoch + activation_epoch + CognitiveFrame + operation/projection semantics + coverage witness` as the causal identity of a compiled Assembly. These components can advance independently, so one timestamp or graph version is insufficient by construction.

### Evidence / boundary
ClayGraph independently introduced graph/activation epochs; FRANK introduced CognitiveFrames; CC8 added volatile/predicate dependencies; GWT requires projection/uptake receipts. H3's synthetic epoch test showed stale activated support increasing with semantic churn. No live FRANK mixed-basis rate is known.

### Implication
Every disposable cognitive projection should be replayable against an explicit basis tuple; mismatch causes rebase/filter/escalation rather than silent use.
