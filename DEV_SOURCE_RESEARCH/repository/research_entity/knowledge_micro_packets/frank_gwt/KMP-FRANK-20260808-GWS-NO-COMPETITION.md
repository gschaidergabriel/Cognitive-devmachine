<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-GWS-NO-COMPETITION","title":"GlobalWorkspace publish path does not currently implement coalition competition","domains":["frank_gwt","systems_architecture"],"topics":["global workspace","competition","selection","ignition"],"epistemic_class":"NEGATIVE_RESULT_SUMMARY","claim_status_hint":"OPEN","origin_class":"CURRENT_CODE_INSPECTION","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T05:51:00+07:00","updated_at":"2026-08-08T05:51:00+07:00","source_refs":["Project-Frankenstein@abba90a5767d85abc8a1ac340bae92842dab35c1:services/global_workspace.py"],"evidence_refs":["N-G3-005"],"related_claim_ids":["H-G3-005"],"related_experiment_ids":["EXP-LIVE-GWT-LESION"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.95,"verification_required":true,"falsifier_or_next_test":"Identify an external or dynamically composed competition/selection layer that deterministically controls which candidate reaches `GlobalWorkspace.publish()`; otherwise implement and lesion such a layer.","search_terms":["GlobalWorkspace salience coalition competition selection ignition publish"]}
RAE_META -->

### Core
The current `GlobalWorkspace.publish()` implementation is a synchronous broadcast bus: every call creates a `WorkspaceEvent`, appends it to history and dispatches it to every subscriber. The `salience` field is carried on the event and used for summaries, but the visible publish path does not compare candidates, choose a winner or implement an ignition threshold.

### Evidence / boundary
This directly contradicts the module docstring's stronger mechanism description that only one coalition wins workspace access. A separate upstream competition layer could exist dynamically or under another name, so the negative result is scoped to the inspected GlobalWorkspace path and static repository evidence.

### Implication
Calling this component a Global Workspace does not establish GWT selection. This is a concrete code-level instance of RAE `N-G3-005`: stage labels/presence are insufficient without causal mechanism.

### Next test
Trace a representative live episode from simultaneous candidate generation through winner selection. If all candidates are simply published, the current GWT competition claim fails for that path.
