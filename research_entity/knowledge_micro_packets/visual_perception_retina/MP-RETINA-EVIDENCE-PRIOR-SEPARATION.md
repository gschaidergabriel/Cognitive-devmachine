<!-- RAE_META
{"packet_id":"MP-RETINA-EVIDENCE-PRIOR-SEPARATION","title":"Visual evidence must remain distinct from priors","domains":["visual_perception_retina","frank_gwt","synthetic_clay"],"topics":["PerceptualField","predictive perception","calibration"],"epistemic_class":"ARCHITECTURE_DECISION_SUMMARY","claim_status_hint":"OPEN_MECHANISM_UNDER_FIXED_OWNER_TARGET","origin_class":"RESEARCH_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-09","updated_at":"2026-08-09","source_refs":["research_entity/retina/RETINA_RESEARCH_FOUNDATION.md","https://www.nature.com/articles/s44159-023-00254-0"],"evidence_refs":["research_entity/retina/runs/retina-20260809T0615p0700-deep-foundry/SYNTHETIC_MECHANISM_RECEIPT.json"],"related_claim_ids":[],"related_experiment_ids":["RET-E4","RET-E5"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Run recurrence factorial plus misleading-prior/no-signal battery on real Retina fixtures.","search_terms":["retina prior evidence precision hallucination PerceptualField"]}
RAE_META -->

### Core
World, memory and scene context may participate in visual inference, but they must never be recorded as if they were current sensor evidence. FRANK should retain distinguishable bottom-up evidence precision, world/learned prior precision and goal/context gain.

### Evidence / boundary
External object-scene research supports bidirectional contextual influence. The deep-run synthetic sweep additionally shows the expected failure mode: as synthetic sensor evidence weakens, a correlated prior can improve nominal accuracy while sharply increasing acceptance of deliberately wrong priors. This is mechanism plausibility only, not live Retina evidence.

### Implication
A percept can be highly probable because of prior state without being strongly observed. Downstream memory/action consumers need that distinction for safe abstention, active sensing and replay.

### Next test
E4/E5: matched feedforward/recurrent conditions with congruent, misleading and no-signal priors; measure calibration, wrong-prior acceptance and lesion/rescue.
