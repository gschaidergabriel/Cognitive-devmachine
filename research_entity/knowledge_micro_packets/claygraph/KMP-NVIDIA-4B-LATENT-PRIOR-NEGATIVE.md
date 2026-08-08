<!-- RAE_META
{"packet_id":"KMP-NVIDIA-4B-LATENT-PRIOR-NEGATIVE","title":"Shuffled relevance prior can dominate an actual 4B reader while truthful benefit remains unresolved","domains":["claygraph","gwt","clay"],"topics":["latent-field","activation-prior","shuffled-control"],"epistemic_class":"NEGATIVE_RESULT_SUMMARY","claim_status_hint":"HOLD","origin_class":"NVIDIA_HOSTED_RUNTIME_EXPERIMENT","origin_actor":"chatgpt-secondary","created_at":"2026-08-08T13:15:00Z","updated_at":"2026-08-08T13:15:00Z","source_refs":["nvidia-crossbranch-20260808T2015p0700-chatgpt-secondary"],"evidence_refs":["research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-latent-neutral-v2-20260808T2007p0700.json","research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-latent-truth-v2-20260808T2007p0700.json","research_entity/runtime/tool_results/nvidia-nemotron-mini-4b-latent-shuffled-v2-20260808T2007p0700.json"],"related_claim_ids":[],"related_experiment_ids":["NV-XB-LATENT-PRIOR-003"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":0.86,"verification_required":true,"falsifier_or_next_test":"Rerun a stricter per-case matched no-field/truthful/shuffled factorial with deterministic output scoring and calibrated prior strength.","search_terms":["ClayGraph NVIDIA 4B latent prior","shuffled field","activation prior"]}
RAE_META -->

### Core
In a matched visible-fact NVIDIA Nemotron-Mini-4B experiment, an intentionally shuffled `ACTIVATION_PRIOR` produced 0/8 correct answers and outputs dominated by irrelevant-prior values. Neutral and truthful arms failed the output contract, so beneficial truthful-field effect was not estimable.

### Evidence / boundary
The experiment demonstrates behavioral influence and a strong negative-control hazard, not G1d benefit. It does not test actual ClayGraph state before explicit retrieval or a live FRANK memory loop.

### Implication
G1d remains HOLD. Relevance/activation priors require provenance, bounded gain, selection integrity and explicit shuffled/no-field controls.

### Next test
Per-case matched 4B factorial with deterministic scorer, equal facts/order/budget and calibrated prior injection.
