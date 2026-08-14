<!-- RAE_META
{"packet_id":"FRANK_QWEN4B_CONFIDENCE_ABORTION_PRIMARY_SYNTHESIS_20260810","title":"Primary-source synthesis for Qwen4B confidence, verification and dynamic abstention","domains":["frank","gwt","harness","model_runtime"],"topics":["verbalized confidence","calibration","self verification","dynamic abstention","stable wrong attractor","Qwen3-4B"],"epistemic_class":"LIVE_PRIMARY_RESEARCH_SYNTHESIS","claim_status_hint":"CURRENT","origin_class":"LIVE_WEB_PRIMARY_SOURCES_PLUS_LOCAL_REAL_MODEL_NEGATIVE","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T00:40:00+07:00","source_refs":["https://openreview.net/forum?id=CVRdNQvFPE","https://openreview.net/profile?id=~Yegon_Kim1","https://openreview.net/forum?id=5sgK63Zshg","https://arxiv.org/abs/2604.18419","https://arxiv.org/abs/2607.29211","https://arxiv.org/abs/2605.15588","gschaidergabriel/Dr.-Unterweger@c9d06222643aa9028940cbba24b0421f6ef45ad6"],"evidence_refs":["FRANK_REAL_QWEN4B_FIRST_EXECUTION_20260810"],"related_claim_ids":["FRANK-QWEN4B-CONFIDENCE-NEG-001"],"related_experiment_ids":["FRANK_REAL_QWEN4B_SHADOW_DIFFERENTIAL","FRANK-QWEN4B-CALIBRATION-AND-RESEED"],"confidence":"HIGH_FOR_LOCAL_COUNTEREXAMPLE_MEDIUM_FOR_TRANSFER_DESIGN","verification_required":true,"falsifier_or_next_test":"Run the preregistered held-out/OOD calibration+independent-reseed comparison after conservative V2, with answer keys hidden from controller/verifier.","search_terms":["verbalized confidence calibration","task dependent confidence LLM","dynamic abstention reasoning","stable wrong attractor","independent verification reseed"]}
RAE_META -->

## Local anchor

The primary project evidence remains the real Hostinger Qwen3-4B Q8_0 receipt: one deterministic modular-arithmetic trajectory stayed wrong for all five recurrences (`4` instead of `2`) while verbalizing `CONFIDENCE=100`, and W4 identified the trajectory as a converged fixed point at recurrence four. This directly separates **trajectory stability** from **answer correctness** for the exact tested model/runtime/task.

## Fresh primary-source synthesis

1. **Verbalized confidence is conditional rather than universal.** Yang et al. report that reliability changes substantially with dataset, model and prompting method, even though some prompting methods can improve calibration. The ICML-2026 work listed as *Confidence is Not Universal* explicitly frames calibration behavior as task-dependent. Therefore Frank must not interpret one scalar confidence channel as a domain-invariant probability of correctness.

2. **Confidence can still be useful after calibration or aggregation.** SteerConf uses multiple steered confidence elicitation conditions and consistency aggregation rather than trusting a single raw self-report. Confidence-supervised work reports self-verification effects after dedicated training, which is evidence for a possible learned mechanism, not evidence that the current untrained Qwen verbalization is calibrated.

3. **Dynamic stopping is better formulated against estimated future value/success than raw certainty wording.** Davidov et al. formulate mid-generation abstention as an explicit action tied to a value-function threshold and report improved selective accuracy. The July-2026 *Diagnosing and Training LLMs to Abort Futile Reasoning* work identifies capability overreach, specious reasoning and miscalibration as central failure modes and trains refusal behavior around capability boundaries.

4. **Semantic/correctness-aligned calibration is a distinct target.** Recent semantic-reward calibration work reports improvements over verbalized-confidence baselines and explicitly motivates separating textual confidence expression from semantic correctness calibration. This supports testing an independent verification/reseed branch instead of merely rescaling the present `CONFIDENCE=` field.

## Hypothesis / counterhypothesis

**H-CAL-VALUE:** Frank can retain recurrence convergence as a compute/stability signal while improving safe stopping by pairing it with an independently validated success/verification signal. A fresh answer-key-free verification/reseed branch should correct some initially wrong stable trajectories without materially regressing initially correct trajectories.

**Counterhypothesis:** Independent verification/reseed may reproduce the same model error, add latency, or flip correct answers to wrong ones. Verbalized-confidence calibration may also remain sufficiently discriminative on some domains after task-specific calibration, making a more expensive verifier unnecessary there.

The discriminating experiment is already present in shared work as `FRANK-QWEN4B-CALIBRATION-AND-RESEED`; this packet changes no runtime authority and creates no second unrelated OOB experiment.

## Architecture/test consequence

- Keep `verbalized_confidence` as an **observable feature**, not truth, effect authority, or standalone halt authority.
- Keep W4 convergence as a **stability/compute signal** unless later evidence refutes even that role.
- Before online adaptive authority, measure task-stratified calibration plus an answer-key-free independent verification/reseed arm.
- Required outcomes: high-confidence-wrong rate, Brier/ECE or justified alternatives, selective risk, wrong-to-correct rescue, correct-to-wrong regression, halt/route behavior, latency/token/resource cost and preserved raw trajectories.
- A learned value/success estimator is a future candidate only after Original Baseline, held-out/OOD evidence, authority isolation and rollback; no training is authorized by this packet.
- `NO BENEFIT`, `REGRESSION`, and `RAW_CONFIDENCE_RETAINS_ONLY_DIAGNOSTIC_ROLE` are valid outcomes.

## Promotion

`NONE`. This packet is a live-knowledge delta that sharpens the preregistered falsifier. It does not promote W4, verbalized confidence, a verifier, abstention, training, release readiness, emergence or consciousness.
