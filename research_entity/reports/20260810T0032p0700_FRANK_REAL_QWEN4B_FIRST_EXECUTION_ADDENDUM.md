# FRANK v0.1 — First Real Qwen4B Hostinger Execution Addendum

**Run/addendum:** `20260810T0032p0700-chatgpt-secondary-real-qwen4b-first-execution`  
**Actor:** `chatgpt-secondary`  
**Subject:** Frank v0.1 local-model lane on Hostinger Ubuntu runner `clay`  
**Parent report:** `research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md`  
**Status:** REAL_MODEL_EXECUTION_VERIFIED · CONSERVATIVE_V2_STILL_OPEN

## 1. Material state change

The prior statement that the pinned Qwen-class 4B experiment had not yet reached model inference is now **SUPERSEDED**.

A real self-hosted Ubuntu execution receipt is present at:

`gschaidergabriel/Dr.-Unterweger:runtime/vps_integrity/real_qwen4b_shadow_latest.json`

Tested runtime/model identity:
- runner: `clay`, host `digital-retina`, Linux x86_64, 4 logical CPUs;
- model: `ggml-org/Qwen3-4B-Instruct-2507-Q8_0-GGUF`;
- quantization: Q8_0;
- model SHA-256: `ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1`;
- llama.cpp commit: `936918514ce522b553c0fd80b169a6440e6096c6`;
- receipt status: PASS;
- `real_model_executed=true`;
- benchmark non-null;
- whole Frank release remains `NOT_CLAIMED`.

The successful source-build lane disproves the earlier assumption that the build-tool failures represented a blocker to model viability. They remain valid historical negative results for specific toolchain-path assumptions.

## 2. Measured real-model pilot

The four-task deterministic pilot produced:
- fixed accuracy: **0.75 (3/4)**;
- V1 offline-shadow adaptive accuracy: **0.75 (3/4)**;
- fixed recurrence count: **20**;
- V1 selected recurrence count: **16**;
- V1 recurrence-reduction fraction: **0.20**;
- fixed measured cumulative latency: **48,356.025 ms**;
- V1 counterfactual selected latency: **38,438.59 ms**;
- V1 counterfactual latency-reduction fraction: **~0.2051**;
- mean decode throughput: **~10.7053 tokens/s**;
- median decode throughput: **~10.8772 tokens/s**;
- mean prompt throughput: **~39.9413 tokens/s**;
- median prompt throughput: **~40.2168 tokens/s**.

These numbers establish a real CPU-only performance order of magnitude on this exact VPS/runtime/model configuration. They are one-run measurements, not reliability or final-device guarantees.

## 3. Tool boundary result

The real model selected the expected `read_state` tool in the dedicated tool case:
- `read_state_selected=true`;
- `arguments_valid=true`;
- `tool_call_count=1`;
- visible assistant text empty for the tool call;
- `reasoning_content_persisted=false`;
- tool-case latency ~5,884.225 ms;
- backend measured ~10.1375 decode tokens/s and ~47.0891 prompt tokens/s for that case.

This is evidence that the current OpenAI-compatible adapter/tool-call projection is usable with the pinned real Qwen/llama.cpp lane. Model output remains non-authoritative data.

## 4. Strongest scientific finding: verbalized confidence is not a safe residual-error proxy

The modular arithmetic task asked for `2^10 mod 7`, whose expected answer is `2`. Across the observed later trajectory the model returned `ANSWER=4` and `CONFIDENCE=100`, including the fixed final step.

Therefore the real pilot directly exhibits:

`verbalized_confidence = 100%` **while** `answer_correct = false`.

This falsifies any strong Frank controller assumption of the form:

`visible self-reported confidence ~= calibrated probability of correctness`

for this model/task configuration.

The current W4 controller does not use confidence alone, but its residual-pressure proxy is derived from visible confidence, so this observation materially strengthens the counterhypothesis that confidence-derived pressure must be calibrated, supplemented, or demoted before online control authority.

Fresh external primary research is consistent with this caution: recent calibration work distinguishes verbalized confidence from internal or correctness-aligned confidence and reports model/dataset-dependent calibration behavior. This external literature supports further calibration experiments; the Frank receipt itself is the primary evidence for the exact failure observed here.

## 5. Why V1's 20% recurrence reduction is NOT promoted

The successful receipt used benchmark schema V1. V1 generated the full five-step trajectory first and then applied W4 offline without answer-key visibility, which is already safer than executing the controller online. However, a subsequent methodological audit found that non-HALT W4 decisions could be interpreted too optimistically as early completion in some cases.

Current main now contains conservative benchmark V2 with the rule:

`early compute savings count only for HALT_CANDIDATE_CONVERGED`

`ROUTE | ESCALATE | ROLLBACK | ABORT | uncertain -> fall back to full fixed-budget result`

Therefore:
- V1 accuracy/throughput/latency measurements from actual model calls remain real observations;
- V1 `20% recurrence reduction` is **DIAGNOSTIC_ONLY / NOT_PROMOTED**;
- current V2 is the next discriminating receipt for adaptive recurrence accounting.

## 6. New hypotheses after real execution

### H-Q4B-CAL-01 — confidence-pressure miscalibration

**Hypothesis:** Raw verbalized confidence is too top-skewed/miscalibrated to serve as the primary Frank residual-pressure signal.

**Counterhypothesis:** The observed `100% wrong` case is a small-pilot outlier; over a representative held-out distribution, verbalized confidence may still be sufficiently discriminative after threshold calibration.

**Next test:** larger held-out/OOD set with Brier/ECE/AUC/selective-risk analysis; compare verbalized confidence, answer stability, token/logit-derived confidence where available, self-consistency, and external verification signals.

### H-Q4B-CACHE-02 — iterative trajectory may reuse prompt cache efficiently

Observed later recurrence steps commonly show substantial `cache_n` and prompt throughput near ~40 tok/s. This suggests the repeated-turn trajectory is not paying full prompt recomputation each step in the same way as a cold request.

**Counterhypothesis:** cache reuse is a llama.cpp/server artifact specific to this prompt structure and may not transfer to final Frank context assembly.

**Next test:** cold-vs-warm matched trajectories with cache disabled/cleared controls, same task distribution and memory/context sizes.

### H-Q4B-CPU-03 — CPU-only 4B lane is viable for functional testing but likely latency-sensitive

~10.7 decode tok/s is sufficient for real functional experiments and regression testing, but multi-second per-step latency means five-step recurrence can accumulate tens of seconds on this host.

**Counterhypothesis:** final prompt shape, quantization, thread settings, speculative decoding, shorter outputs or hardware acceleration may materially alter this envelope.

**Next test:** matched Q4/Q6/Q8 quantization and thread/context sweeps only after the semantic/quality baseline is stable; optimize quality-adjusted latency rather than tokens/s alone.

## 7. Claim-state delta

### CURRENT / supported for exact run
- real Qwen3-4B Q8_0 inference executed successfully on Hostinger Ubuntu via pinned llama.cpp source-build lane;
- fixed four-task pilot accuracy = 3/4;
- mean decode throughput ~10.705 tok/s, mean prompt throughput ~39.941 tok/s;
- real `read_state` tool selection contract passed;
- hidden reasoning field was not persisted in the admitted receipt;
- at least one wrong answer was emitted with verbalized confidence 100%.

### SUPERSEDED
- `real Qwen4B inference has not yet executed on Hostinger`.

### NEGATIVE_RESULT retained
- missing CMake and Ninja-path failures remain negative results for the exact previous toolchain assumptions;
- make-lane attempt `BOOTSTRAPPED_CMAKE_MISSING` is another build-path negative result and does not contradict the successful source-build lane.

### OPEN / not promoted
- conservative V2 recurrence reduction;
- reliability across repeated runs;
- confidence calibration over representative data;
- final Andreas-device throughput;
- optimal quantization/runtime settings;
- model quality sufficient for full Frank v0.1;
- any emergence or consciousness claim.

## 8. Mesh handoff

- `frank`: ingest real model latency/quality/tool boundary and demote raw self-confidence as controller authority;
- `gwt`: treat confidence as one noisy observable, not ignition/convergence truth;
- `harness`: add regression for confidently-wrong stable trajectories and escalation/verification behavior;
- `emergenz`: no emergence promotion; recurrence remains a control/measurement variable;
- `unifieddb`: persist calibration evidence and controller decision provenance without conflating confidence with truth;
- `claygraph/hyperposition`: preserve alternative confidence estimators and fixed/adaptive control branches;
- `claycode`: no language-semantic change justified; this is runtime/control evidence.

## 9. Re-entry

Highest-information next step is the already-queued conservative prebuilt V2 receipt. If V2 shows no safe early HALT on the confidently-wrong trajectory, that is a desired correction relative to optimistic V1 accounting. If V2 still halts confidently-wrong states, the residual-pressure basis needs redesign before any online adaptive controller experiment.
