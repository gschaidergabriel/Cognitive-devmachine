# FRANK H1 causal loop replay adapter — implementation/research delta

Status: OPEN_IMPLEMENTATION_EVIDENCE_NOT_SCIENTIFIC_PROMOTION  
Date: 2026-08-09  
Origin actor: chatgpt-secondary  
Provider/model: OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Mission: `FRANK_V0_1_ANDREAS_PC` / Ubuntu developer system  
Frank identity boundary: Research Entity worker != Frank; Frank self-Harness authority was not used.

## Research gap

FRANK's trajectory probe is already quality-gated and proxy-safe, but trajectory classification alone does not establish causal regulator value. The next high-information discriminator is matched frozen replay:

`BASELINE -> LESION -> RESCUE`

plus recurrence/re-entry comparisons.

## Implemented candidate

Frank branch: `research/frank-h1-causal-loop-replay-20260809`  
Draft PR: `gschaidergabriel/Dr.-Unterweger#5`  
Module: `harness/loop_causal_replay.py`  
Regression: `tests/test_loop_causal_replay.py`  
Dedicated CI: `.github/workflows/frank-h1-causal-loop-replay.yml`

Adapter schema: `frank-h1-causal-loop-replay-v0.2`  
Authority: `PROPOSAL_ONLY`

It executes no effects, grants no Harness mutation authority, and makes no emergence/consciousness inference.

## Two different match contracts

A key adversarial-review finding was that regulator interventions and policy interventions need different matching semantics.

### Regulator lesion/rescue

`BASELINE`, `LESION`, and `RESCUE` require the same:

- frozen input hash;
- loop id/family;
- semantic state epoch;
- graph epoch;
- regulator;
- controller policy hash;
- residual estimator id/version.

LESION and RESCUE require real intervention references. A successful RESCUE requires a rollback reference.

### Policy comparison

When comparing fixed recurrence against trend-safe, proxy-safe, or calibrated-next-step adaptive recurrence, the controller policy hash is intentionally allowed to differ because policy is the treatment. The frozen episode/state basis must still match.

Explicit policy arms now include:

- `FIXED_BUDGET`;
- `ADAPTIVE_TREND_SAFE`;
- `ADAPTIVE_PROXY_SAFE`;
- `ADAPTIVE_CALIBRATED_NEXT_STEP`.

Truthful-vs-shuffled/no-reentry controls retain the stricter same-configuration requirement because re-entry, not policy identity, is the intended treatment.

## Evidence semantics

- `HISTORY_PROXY` != `VALIDATED_NEXT_STEP_ESTIMATE`.
- A validated next-step estimate is calibrated against actually observed next-step utility delta.
- Provenance origin is separate from attestation layer.
- `SELF_ATTESTED` and `UNVERIFIED` cannot yield strong candidate causal support.
- A matched replay is not independent replication.
- `CANDIDATE_CAUSAL_SUPPORT` is not scientific promotion.
- Negative lesion outcomes remain `NEGATIVE_RESULT_CANDIDATE`, not discarded.

## Persistence choice

No new database migration was introduced. The current Frank branch already has an admitted-schema coordination hazard around V13 versus the required applied schema manifest, while an independent bug-feedback repair is active. Coupling this experiment to another migration would add avoidable failure modes.

The adapter projects onto the existing central UnifiedDB causal spine:

`episodes -> predictions -> prediction_outcomes -> causal_credit_receipts`

Durable writes remain central-materializer/runtime only. Node-local fallback databases remain forbidden.

## Local execution evidence

Isolated Python regression executed by `chatgpt-secondary` after two adversarial review passes:

- 14 tests executed;
- 14 PASS;
- 0 FAIL.

Coverage includes:

- matched lesion/rescue candidate support;
- material-lesion negative result;
- frozen-input mismatch rejection;
- graph-epoch mismatch rejection;
- controller-policy hash validation;
- successful-rescue rollback binding;
- self-attestation blocked from strong causal support;
- history proxy excluded from validated estimator calibration;
- validated estimator calibrated against observed next-step utility;
- policy treatment allowed to change policy hash while preserving frozen episode basis;
- policy comparison rejected when graph epoch drifts;
- deterministic receipt identity;
- non-finite telemetry rejection;
- duplicate observation-id rejection.

This is component evidence only. Andreas Ubuntu H1 execution was not performed by this worker.

## GitHub CI negative evidence

The existing `Frank Deep Integrity` workflow does not execute the new H1 regression suite and does not compile `harness/`, so a dedicated H1 workflow was added on the draft branch.

Observed on 2026-08-09:

- `Frank Deep Integrity`: FAILURE;
- dedicated `Frank H1 Causal Loop Replay`: FAILURE;
- both returned completed failed jobs with empty step lists;
- GitHub job-log retrieval returned `BlobNotFound`;
- rerunning the failed Deep Integrity job reproduced the same pre-step failure surface.

Therefore the CI result is currently classified as `CI_INFRASTRUCTURE_OR_PRESTEP_FAILURE_UNRESOLVED`, not as evidence that the H1 Python tests failed. Local 14/14 PASS remains the only executable component receipt from this worker. This negative result must remain visible until GitHub exposes a step/log or another runner reproduces it.

## Highest-information target experiment

On the registered Andreas Ubuntu target, run frozen accepted H1 episodes with target-runtime receipts. Start with a reversible regulator already exposed by the harness, preferably GWT ignition/gain or habituation/damping if real lesion and rescue operations exist.

For each episode preserve exact semantic/graph epoch, frozen input hash, policy hash, residual-estimator identity/quality, intervention/rollback refs, task correctness/utility, recurrence count, latency/compute, actual next-step outcome, provenance origin and attestation layer.

Then compare:

A. fixed recurrence budget;  
B. pre-proxy-safety trend-safe policy;  
C. current proxy-safe policy;  
D. genuinely calibrated next-step adaptive policy, only when such an estimator exists.

Also run truthful-vs-shuffled/no-reentry controls and benign one-axis-growth exploration cases so conservative routing can be falsified.

## Claim-state decision

Implementation evidence: COMMITTED to draft Frank research PR #5.  
Scientific promotion: NONE.  
Canonical RAE revision bump: NONE.  
Target Ubuntu H1 causal replay: NOT_EXECUTED in this worker.  
CI gate: PRESTEP_FAILURE_UNRESOLVED.  
Next dependency: verified target execution through the Research Center/local Ubuntu organ plus recoverable repository CI.
