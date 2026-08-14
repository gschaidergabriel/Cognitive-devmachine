# FRANK v0.1 — Qwen4B V2 Pipeline Fusion Addendum

**Run/addendum:** `20260810T0110p0700-chatgpt-secondary-qwen4b-v2-pipeline-fusion`  
**Parent:** `research_entity/reports/20260810T0032p0700_FRANK_REAL_QWEN4B_FIRST_EXECUTION_ADDENDUM.md`  
**Actor:** `chatgpt-secondary`  
**Subject:** Frank v0.1 real Qwen4B control/measurement pipeline on Hostinger Ubuntu  
**Status:** CODE_AND_METHOD_REPAIRS_COMMITTED · REMOTE_POST_FIX_RECEIPT_PENDING

## 1. Material delta since the first real-model receipt

The first successful real Qwen3-4B Q8_0 receipt exposed a stable wrong modular answer with verbalized confidence 100%. Subsequent live swarm work produced three independent methodology/infrastructure repairs:

1. **HALT-only V2 accounting:** only `HALT_CANDIDATE_CONVERGED` may count as early completion; route/escalate/rollback/abort/uncertain decisions fall back to the full fixed budget for counterfactual comparison.
2. **Confidence-readout quality guard:** because a real confidently-wrong case exists, V2 no longer declares the visible-confidence residual proxy uncertainty `0.08` by fiat. Commit `302066f72cb45930927c4f086d0c709e2c5a4fac` rebuilds V2 traces with residual uncertainty `1.0` / `UNCALIBRATED_REAL_QWEN_SELF_REPORT` until admitted calibration evidence justifies a lower value. Generic W4 semantics are unchanged.
3. **Producer/writer schema repair:** a concurrent isolated receipt writer initially admitted benchmark schema `2.0` while the current V2 producer emits `2.1`. Commit `7b5da2877b04e14f978b117a6c669e3a0846705e` aligns the writer with schema `2.1` and adds a synthetic admission regression requiring `2.1` accepted / stale `2.0` rejected.

## 2. Execution-authority / infrastructure delta

GitHub-hosted Actions exhibited a pre-step capacity/outage failure in the current run window. The Research Entity did not attribute this to Frank or Qwen. Concurrent main changes added a degraded but explicit fallback:

- model executor remains self-hosted and repository `contents:read`;
- checkout credentials are not persisted;
- model output has no repository write authority;
- executor emits bounded artifact transport;
- persistence occurs in a **separate writer job after model process termination**;
- during the hosted-capability outage the writer may run on the same Hostinger physical machine, which is explicitly marked weaker than the preferred separate GitHub-hosted writer.

This preserves authority separation at the job/model boundary while honestly recording weaker physical isolation.

## 3. Independent reseed experiment

ChatGPT added and merged a 24-task answer-key-free offline intervention experiment (`7b461d8bb6de1ce18ee669e7ccc781eb9231682e`). The design compares a third same-path recurrence against a fresh-context same-model verifier under the same selected three-call budget when the first two answers agree and both report >=95% confidence.

A parallel worker subsequently strengthened its evidence semantics (`bbe72ee81bea0cce2d820d39a909fb815303f428`):
- the fresh-context same-model verifier is **not independent replication**;
- three tasks are historical anchors and 21 are manually constructed stress-expansion cases;
- the set is not called held-out, OOD, representative, or population evidence;
- partitioned metrics and receipt assertions preserve these limitations.

Another concurrent change (`964b2c09466662c96b65cdb37211fc52f32cd233`) makes the research dependency executable: the ReSeed lane waits for an admitted conservative V2 PASS receipt before consuming the 4B model runner.

## 4. Runner/dispatch security delta

The runner cross-repository token-scope probe is read-only. ChatGPT merged `75e8d9d6ce658d3eaccf32a8b51db1d8a6eb88c6`, replacing moving artifact action tags with exact commit pins already used by the canonical V2 lane.

A bounded dispatch bridge exists on Frank main. It accepts only an exact whitelisted trigger title and can dispatch only three named research workflows (V2, residual calibration, cross-repo scope). Dispatch HTTP acceptance is explicitly distinct from execution/PASS. Multiple trigger issues were created by parallel organs, but no bounded-dispatch receipt was available during this addendum, so dispatch remains `PENDING_RECEIPT`, not verified success.

## 5. New regression boundary

The normal Hostinger deep-integrity matrix now includes `qwen4b_confidence_quality_gate`. Its deterministic counterexample proves:

- historical benchmark metadata `residual_uncertainty=0.08` + stable delta `0` + residual pressure `0` can satisfy W4 quality and emit convergence HALT;
- identical observed trajectory with uncertainty `1.0` fails readout quality and routes `READOUT_UNCERTAIN`;
- generic W4 code is not altered.

The merged code is present on main. A new post-fix remote deep-integrity/V2 receipt was still pending at report time, so no remote PASS is claimed for this final repair yet.

## 6. Current scientific state

**CURRENT for exact evidence:** real Qwen4B executes on Hostinger; 3/4 first-pilot fixed accuracy; ~10.7 decode tok/s; real tool-call boundary works; a wrong answer with verbalized confidence 100% exists.

**REFINED:** visible confidence remains an observable but is no longer admitted as low-uncertainty residual evidence without calibration.

**DIAGNOSTIC_ONLY:** V1 20% recurrence/latency reduction.

**OPEN:** conservative post-guard V2 behavior; residual calibration audit; gated ReSeed intervention; cross-repo token-scope receipt; hosted-vs-same-machine writer isolation comparison.

**NOT CLAIMED:** whole Frank v0.1 release readiness, confidence calibration, adaptive-recurrence superiority, model population reliability, emergence/consciousness, final Andreas-device performance.

## 7. Re-entry

The highest-information next receipt is the post-guard conservative V2 run. If it returns full-budget fallback / readout uncertain on the confidently-wrong stable trajectory, the evidence-quality repair is validated. If it still produces a convergence HALT, the remaining mechanism must be isolated before the gated calibration/ReSeed branch is admitted.
