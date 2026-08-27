<!-- RAE_META
{"packet_id":"KMP-G6-CAUSAL-BUDGET-VECTOR","title":"Clay control should use a causal budget vector rather than one universal scalar","domains":["synthetic-clay","frank-gwt","model-runtime"],"topics":["causal-budget","resource-control","r-delta","goodhart"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"OPEN_WITH_SYNTHETIC_COUNTEREXAMPLE","origin_class":"CLAY_G6_TRIGGER_RUN","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:25:00+07:00","updated_at":"2026-08-08T05:25:00+07:00","source_refs":["clay-20260808T0525p0700-chatgpt-secondary:EXP-G6-BUDGET-VECTOR-002","arXiv:2603.08727","arXiv:2606.23001"],"evidence_refs":[],"related_claim_ids":["H-G6-011","H-G6-T01"],"related_experiment_ids":["EXP-G6-BUDGET-VECTOR-002"],"predecessor_packet_ids":["KMP-G5-RDELTA-CHANGE-AMPLIFICATION"],"supersedes_packet_ids":[],"confidence":0.84,"verification_required":true,"falsifier_or_next_test":"Fit scalar, vector and hierarchical controllers on real FRANK traces with equal observation and compute budgets.","search_terms":["causal budget vector","resource governor","R_delta","adaptive context","thermal governor"]}
RAE_META -->

### Core
G6 weakens the idea of one scalar causal budget. Context/KV, active workspace, recomputation, coupling/re-entry, speculation and coordination can face non-collinear pressures and should remain independently adjustable even if a shared governor observes them.

### Evidence / boundary
In a constructed four-regime test, vector-control loss was 0.02862 versus 0.18102 for a one-scalar controller, an 84.19% reduction. Current adaptive KV and energy/thermal inference research independently supports state-dependent resource allocation. This is not a measured FRANK optimum.

### Implication
Represent `B_t=[context_KV, active_workspace, recompute, coupling_reentry, speculation, coordination]` plus uncertainty/shadow metrics rather than maximizing one scalar.

### Next test
Compare fixed, scalar, vector and hierarchical control on real or high-fidelity FRANK traces with task quality, tails, energy and recovery co-primary.
