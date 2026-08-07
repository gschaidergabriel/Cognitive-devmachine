<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-GWS-STATIC-REACHABILITY","title":"Current GWS wiring is not statically demonstrated as an active broadcast network","domains":["frank_gwt","systems_architecture","observability_recovery"],"topics":["global workspace","causal reachability","static wiring"],"epistemic_class":"NEGATIVE_RESULT_SUMMARY","claim_status_hint":"OPEN","origin_class":"CURRENT_CODE_INSPECTION","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:51:00+07:00","updated_at":"2026-08-08T05:51:00+07:00","source_refs":["Project-Frankenstein@abba90a5767d85abc8a1ac340bae92842dab35c1:services/global_workspace.py","Project-Frankenstein@abba90a5767d85abc8a1ac340bae92842dab35c1:services/thalamus.py"],"evidence_refs":[],"related_claim_ids":["H-G3-005"],"related_experiment_ids":["EXP-LIVE-GWT-LESION"],"predecessor_packet_ids":["KMP-FRANK-20260808-GWS-SYNC-CALLBACK"],"supersedes_packet_ids":[],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Instrument a representative live FRANK session and demonstrate nonzero workspace producers, competition/selection, broadcasts, downstream effects, outcomes and reentry receipts.","search_terms":["global_workspace publish subscribe get_workspace GWT wiring causal reachability"]}
RAE_META -->

### Core
At the indexed Project-Frankenstein HEAD, static code search finds `services.global_workspace` references only in the workspace module itself and `services/thalamus.py`; `get_workspace()` is not statically found outside the workspace module. The visible Thalamus subscription is therefore not enough to establish an active multi-producer Global Workspace network.

### Evidence / boundary
This is a code-grounded negative result about *static discoverability*, not proof that runtime reflection, dynamic imports, plugins or external processes never publish. The workspace implementation also broadcasts every `publish()` call directly; its `salience` field is not used there to implement coalition competition/selection.

### Implication
Before optimizing GWS transport, FRANK must prove causal reachability: producer -> candidate/competition -> selected workspace event -> subscriber effect -> outcome -> reentry.

### Next test
Add producer/subscriber identity and causal receipts, then run an instrumented live session. Fail the GWT claim if representative tasks produce no causal workspace episodes.
