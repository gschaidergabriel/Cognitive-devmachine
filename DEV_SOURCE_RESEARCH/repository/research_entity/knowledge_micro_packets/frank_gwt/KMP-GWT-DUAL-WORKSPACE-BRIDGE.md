<!-- RAE_META
{"packet_id":"KMP-GWT-DUAL-WORKSPACE-BRIDGE","title":"Separate latent model workspace from receipt-defined event workspace","domains":["frank_gwt","model_runtime","observability_recovery"],"topics":["gwt","j-space","dual-workspace","cross-lesion","reentry"],"epistemic_class":"WEB_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN","origin_class":"GWT_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-07T22:29:00Z","updated_at":"2026-08-07T22:29:00Z","source_refs":["SRC-GWT-ANTHROPIC-2026","SRC-GWT-JLENS-CODE","SRC-GWT-GOYAL-2022"],"evidence_refs":["E-G3-GWT-001","E-G3-CHK-002"],"related_claim_ids":["C-GWT-RUN-005"],"related_experiment_ids":["EXP-LIVE-GWT-LESION","EXP-GWT-DUALWS-CROSSLESION"],"predecessor_packet_ids":["KMP-GWT-CAUSAL-EPISODE"],"supersedes_packet_ids":[],"confidence":0.78,"verification_required":true,"falsifier_or_next_test":"Align synchronized FRANK event episodes with a pinned open-model latent workspace probe and independently lesion both channels with compute-matched controls.","search_terms":["global workspace","J-space","latent workspace","event workspace","cross lesion","reentry receipts"]}
RAE_META -->

### Core
A model-internal latent workspace and FRANK's system-level event workspace should be represented as distinct mechanisms. Current 2026 J-space evidence supports a sparse, limited-capacity, broadcast-like latent substrate inside transformers, but the primary authors explicitly distinguish it from a full recurrent specialist-module GWT. FRANK's event workspace instead requires temporally linked candidate, competition, broadcast, reconstruction, effect, outcome and re-entry receipts.

### Evidence / boundary
The bridge between these layers is an OPEN hypothesis. Existing RAE causal-episode evidence is sandbox-only; J-space evidence is external model research. Neither proves that the two channels mediate the same event.

### Implication
Strong future FRANK GWT claims should use cross-predictive alignment and cross-lesions rather than treating a latent probe or an external message bus as sufficient evidence.

### Next test
Run a pinned Qwen-class latent/event cross-lesion after obtaining synchronized FRANK traces.
