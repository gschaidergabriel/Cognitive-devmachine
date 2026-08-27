<!-- RAE_META
{"packet_id":"KMP-FRANK-20260808-COGNITIVE-FRAME","title":"FRANK workspace freshness requires a causally compatible CognitiveFrame","domains":["frank","gwt","claycode","storage-state-memory"],"epistemic_class":"OPEN_ARCHITECTURE_DELTA","claim_status_hint":"OPEN","origin_actor":"chatgpt-secondary","run_id":"20260808T0610+0700-chatgpt-secondary-r2","confidence":0.78,"verification_required":true,"falsifier_or_next_test":"Instrument live FRANK workspace inputs with per-channel revisions; if q is already atomically assembled or mixed incompatible revisions never occur, reduce/remove the frame gate."}
RAE_META -->

### Core
A workspace can be chronologically fresh yet semantically torn if its contributing state sources belong to incompatible logical moments. C4 introduces `CognitiveFrame = {frame_id, basis_state_root, channel_revision_witnesses, dependency_closure_status, age}` as the consistency unit before workspace competition.

### Boundary
The current 2026-08-05 architecture source does not specify whether `baue_broadcast(q)` already receives an atomic snapshot. The new tearing numbers are synthetic, not a production bug report.

### Implication
Use a global root for basis identity, trusted scoped witnesses for relevant freshness/compatibility, and conservative escalation when dependency closure is unknown.
