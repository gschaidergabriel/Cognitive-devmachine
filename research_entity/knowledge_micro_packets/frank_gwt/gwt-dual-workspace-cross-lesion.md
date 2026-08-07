<!-- RAE_META
{"packet_id":"KMP-GWT-DUALWS-CROSSLESION","title":"Dual-workspace topology should be identified by factorial cross-lesions","domains":["frank_gwt","model_runtime","formal_methods_testing"],"topics":["gwt","latent-workspace","event-workspace","causal-mediation","lesion"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"GWT_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-07T22:49:00Z","updated_at":"2026-08-07T22:49:00Z","source_refs":["SRC-GWT-ANTHROPIC-2026","SRC-GWT-JLENS-CODE"],"evidence_refs":["E-GWT-EXT-ANTHROPIC-2026","E-G3-GWT-001"],"related_claim_ids":["C-GWT-RUN-005"],"related_experiment_ids":["EXP-GWT-DUALWS-CROSSLESION"],"predecessor_packet_ids":["KMP-GWT-DUAL-WORKSPACE"],"supersedes_packet_ids":[],"confidence":0.72,"verification_required":true,"falsifier_or_next_test":"Pin an instrumentable Qwen-class model, align latent probe windows with FRANK event episodes, then run paired compute-matched 2x2 latent/event lesions.","search_terms":["dual workspace cross lesion","J-space intervention","event workspace mediation","GWT factorial lesion"]}
RAE_META -->

### Core
Do not infer that a model-internal J-space-like substrate and FRANK's receipt-defined event workspace are one mechanism merely because both correlate with flexible reasoning. Identify their relation with a paired `LATENT_WS lesion × EVENT_WS lesion` factorial.

### Evidence / boundary
External work establishes causal J-space effects in language models, while RAE sandbox work establishes that event-level causal receipts discriminate malformed workspace episodes. Their bridge remains untested.

### Implication
Interaction signatures are diagnostic candidates: serial mediation predicts lesion occlusion; redundant parallel channels predict a strong double-lesion penalty; additive channels approximate additivity; an epiphenomenal channel has little unique lesion effect. These signatures must be preregistered and tested under matched compute.

### Next test
Qwen-class open-model latent/event cross-lesion aligned to episode IDs and downstream FRANK state/effect outcomes.
