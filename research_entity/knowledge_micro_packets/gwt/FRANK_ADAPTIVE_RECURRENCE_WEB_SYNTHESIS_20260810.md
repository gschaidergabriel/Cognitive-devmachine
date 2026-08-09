<!-- RAE_META
{"packet_id":"FRANK_ADAPTIVE_RECURRENCE_WEB_SYNTHESIS_20260810","title":"Adaptive recurrent test-time compute supports a Frank experiment family, not a controller promotion","domains":["gwt","frank","emergenz","harness"],"topics":["adaptive recurrence","test-time compute","early exit","overthinking","recurrent depth","W4"],"epistemic_class":"WEB_RESEARCH_SYNTHESIS","claim_status_hint":"OPEN","origin_class":"PRIMARY_PREPRINT_SYNTHESIS","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T00:20:00+07:00","updated_at":"2026-08-10T00:20:00+07:00","source_refs":["arXiv:2507.13569","arXiv:2504.15895","arXiv:2502.05171","arXiv:2602.07845","research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md"],"evidence_refs":["https://arxiv.org/abs/2507.13569","https://arxiv.org/abs/2504.15895","https://arxiv.org/abs/2502.05171","https://arxiv.org/abs/2602.07845"],"related_claim_ids":[],"related_experiment_ids":["FRANK_REAL_QWEN4B_SHADOW_DIFFERENTIAL"],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"MEDIUM_THAT_ADAPTIVE_DEPTH_IS_WORTH_TESTING_LOW_FOR_FRANK_W4_TRANSFER","verification_required":true,"falsifier_or_next_test":"Run matched real-Qwen trajectories over a larger held-out/OOD task set with fixed-depth, adaptive W4 and confidence-only controls; measure accuracy, recurrence cost, drift, false halt, tail latency and calibration.","search_terms":["adaptive test-time compute","recurrent depth","dynamic early exit","overthinking","W4 recurrence"]}
RAE_META -->

### Core
Recent primary preprints independently motivate variable test-time depth: recurrent-depth models can improve with extra latent iterations, adaptive methods allocate compute by input difficulty/convergence, and dynamic early-exit work reports that unnecessary long reasoning can waste compute and sometimes reduce accuracy. This supports **testing** Frank's adaptive recurrence family rather than assuming fixed maximum depth is always optimal.

### Evidence / boundary
The cited systems differ materially from Frank: SELF-Transformer iterates attention, recurrent-depth LM uses a tied recurrent block, RD-VLA uses a recurrent action head, and Dynamic Early Exit operates on generated reasoning chains. None validates Frank's W4 proxies (visible confidence, state delta, pressure change, cost) or its loop-of-loops semantics. All are preprints rather than Frank-specific replicated evidence.

### Implication
Keep fixed-depth, adaptive multi-signal and simpler confidence/convergence controls alive in Hyperposition. Do not equate recurrence with GWT ignition or emergence.

### Next test
Real Qwen4B matched trajectories with held-out/OOD tasks, calibration, false-halt and overthinking controls.
