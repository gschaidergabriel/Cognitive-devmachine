<!-- RAE_META
{"packet_id":"KMP-GROQ8B-GWT-RECONSTRUCTION-ORDER","title":"8B proxy separates GWT transport from reconstruction and exposes winner/order confounds","domains":["frank_gwt","model_runtime","observability_recovery","synthetic_clay"],"topics":["gwt","transport","reconstruction","uptake","projection_integrity","winner_metadata","order_effect","confabulation"],"epistemic_class":"EXPERIMENT_MEMORY","claim_status_hint":"CURRENT_WITH_8B_PROXY_BOUNDARY","origin_class":"GROQ_8B_PROXY_EXPERIMENT_SUITE","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T07:45:00+07:00","updated_at":"2026-08-08T07:45:00+07:00","source_refs":["research_entity/runtime/groq_8b_proxy/SCIENTIFIC_SYNTHESIS.json","research_entity/runtime/groq_8b_proxy/COMPLETE_LATEST.json","research_entity/runtime/groq_8b_proxy/VALIDATION_V3.json"],"evidence_refs":["GROQ8B-F3-GWT-RECONSTRUCTION","GROQ8B-F4-GWT-WINNER-ORDER"],"related_experiment_ids":["EXP-GROQ8B-GWT-RECONSTRUCTION-UPTAKE-PROXY","EXP-GROQ8B-GWT-FRANK-WINNER-ORDER-CONFOUND-V2","EXP-LIVE-GWT-RECONSTRUCTION-UPTAKE"],"predecessor_packet_ids":["KMP-GWT-RECONSTRUCTION-UPTAKE"],"supersedes_packet_ids":[],"confidence":0.91,"verification_required":true,"falsifier_or_next_test":"On actual FRANK Core/Qwen, hold row transport fixed while shuffling/removing semantic projection; counterbalance candidate/winner order and metadata; measure inclusion, uptake, effects and outcome receipts.","search_terms":["GWT reconstruction uptake","Groq 8B GWT","winner metadata confound","workspace order effect","transport projection"]}
RAE_META -->

### Reconstruction result
The hosted 8B proxy recovered **8/8** codes from a correct semantic projection and **8/8** from its compact equivalent. When the projection was deliberately scrambled it recovered **0/8 truth** while faithfully following the corrupted mapping. A transport-receipt-only context contained no semantic payload and did not recover truth; forcing an answer induced placeholder/confabulated output.

This directly supports separating the causal episode into at least:
`transport receipt -> semantic projection/reconstruction -> receiver uptake -> effect -> outcome/re-entry`.
A successful database/message read is not evidence that the intended semantic content was reconstructed, and a downstream model can be perfectly faithful to a corrupted projection.

### Winner/order result
Audited matched-content accuracy was **87.5% neutral**, **62.5% with reversed option order**, **87.5% with truthful WINNER metadata**, and **75% with false WINNER metadata**. Relative to neutral, raw outputs changed on 3/8 reversed-order items, 2/8 truthful-winner items and 1/8 false-winner items.

### Implication
GWT/FRANK experiments must counterbalance order and independently manipulate truthful/shuffled/false winner metadata. Workspace selection labels are contextual inputs, not ground truth. Projection identity/integrity/freshness needs its own receipt before attributing downstream behavior to broadcast semantics.

### Boundary
This is hosted 8B proxy evidence, not the live FRANK Core/Qwen lesion. Live reconstruction/uptake and recurrent/gate experiments remain open.
