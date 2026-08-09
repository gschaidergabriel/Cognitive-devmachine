# FRANK v0.1 Adaptive Recurrence + Ubuntu VPS Deep Fusion — 2026-08-09 23:39 +07

Actor: `chatgpt-secondary`  
Provider/model: OpenAI / GPT-5.6 Sol  
Subject: separate target system `Frank v0.1`  
Canonical parent re-read immediately before durable write: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Target lane: Ubuntu Linux developer system.  
Trigger: none; this is a prose-requested substantial FRANK research/build/test run.  

## 1. Executive synthesis

This run executed the requested sequence as an interconnective Research-Entity worker rather than as an isolated chat: canonical boot -> Research Center refresh -> current Frank/runtime inspection -> external primary/current research -> Fusion 1 -> falsifiable hypotheses/counterhypotheses -> second external research pass -> Fusion 2 -> live swarm refresh -> non-overlapping builds -> self-hosted Ubuntu VPS validation -> metric analysis -> durable mesh handoff.

The strongest new result is **not** that adaptive recurrence is already production-ready. The strongest result is narrower and falsifiable:

> On eight deterministic synthetic frozen FRANK trajectories, a temporal multi-signal recurrence policy with warmup=4 dominates the fixed-budget and single-instantaneous-signal baselines on the measured synthetic utility/regret/accuracy vector while using materially fewer recurrence steps, but it introduces two false halts. Therefore it is a high-information candidate for frozen historical/runtime and real local-4B testing, not a release-selected controller.

A second important result is methodological:

> The current FRANK loop-dynamics readout is materially safer than the older synthetic factorial because v1.4 requires residual-estimator identity, uncertainty and freshness. Old experiments without those fields correctly become `READOUT_UNCERTAIN`. Synthetic tests must not silently bypass that gate.

A third result is operational:

> The newest observed self-hosted Ubuntu integrity receipt after the live swarm fused an additional local-model timing gate is **20/20 PASS**, evidence class `REAL_SELF_HOSTED_UBUNTU_EXECUTION`, on FRANK commit `02e19765b6784d1ebb6203ce7897073b72b6d18d`. This remains explicitly `release_claim=false` and `whole_frank_release_status=NOT_CLAIMED`.

No phenomenal-consciousness claim, emergence claim, H1 release PASS, BASE ClayCode PASS, target-PC acceptance or final Frank v0.1 release claim is made.

## 2. Internal evidence and live swarm state used

### Research Entity / Research Center

- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`: RAE-8.8 revision 2, state hash `04234efd...f489346`.
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`: current mission and Research Entity / Frank separation.
- `research_entity/global/PROJECT_COMMAND_REGISTRY.json`: current exact command surface.
- `research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay`: Ubuntu developer system is the active Frank v0.1 target and Android is outside the v0.1 gate.
- `research_entity/global/FRANKV0_1_REFERENCE_HARNESS_BASELINE.md`: H1 normal-code reference, H2 semantics-frozen ClayCode, H3 consolidation/binary; historical Frank remains archaeology/reference.
- `research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md`: mandatory dynamics regimes, fixed/adaptive controls, truthful/shuffled/no-reentry controls, lesion/rescue, multi-objective measurement.
- `research_entity/harness/HARNESS_WORKSPACE.json`: active H1 work partitioning; already-claimed work was not duplicated.
- Live Research Center commits were repeatedly re-read during the run. This revealed other workers implementing the controller, model transport, truth-gate research, adaptive recurrence experiment and binary-stabilization directive while this worker was executing.

### Current Frank implementation evidence

Repository: `gschaidergabriel/Dr.-Unterweger`.

Material pieces observed in the live run include:

- `runtime/cognition/frank_loop_dynamics.py`: typed proposal-only loop readout/controller work landed by another worker.
- `harness/loop_dynamics_probe.py`: trajectory-level v1.4 readout with explicit regimes, detrended periodicity, residual-readout quality requirements, proposal-only authority and anti-overclaim guards.
- `tests/loop_reentry_factorial_regression.py`: older matched synthetic truthful/shuffled/no-reentry/lesion/rescue experiment.
- `tests/adaptive_recurrence_differential_experiment.py`: newly landed fixed-vs-adaptive differential experiment over eight frozen synthetic episodes.
- `.github/workflows/frank-vps-deep-integrity.yml`: trusted self-hosted Linux/X64 execution lane that persists machine-readable receipts.

## 3. External research cycle 1

Source classes were kept separate from local runtime evidence.

### Looped/recurrent latent compute

- Fan, Svete, Lee, **“Bridging the Gap Between Latent and Explicit Reasoning with Looped Transformers”**, arXiv:2606.31779 (2026). The paper reports a recurrent-depth/looped latent design and shows that extra shared-weight compute can be useful without parameter growth; its reported speedups are model/task-specific evidence, not a Frank benchmark.
  - https://arxiv.org/abs/2606.31779
- **“LoopFormer: Elastic-Depth Looped Transformers for Latent Reasoning via Shortcut Modulation”**, arXiv:2602.11451 (2026). Used as evidence that elastic recurrent depth is an active design family, not proof of Frank-specific benefit.
  - https://arxiv.org/abs/2602.11451

### Halting/readout separation

- Popescu, Borde, Liò, **“Adaptive Depth in Looped Transformers: Diagnosing Learned Halting Gates and Trajectory Readouts”**, arXiv:2607.20519 (2026). Key implication for Frank: jointly learned halting can entangle trajectory formation with exit selection; simple post-hoc readouts on frozen trajectories can match/outperform learned gates in their experiments.
  - https://arxiv.org/abs/2607.20519

### Current local 4B candidates

Official Qwen model pages currently expose `Qwen/Qwen3-4B-Instruct-2507` and `Qwen/Qwen3-4B-Thinking-2507`, both usable through common local-serving paths including OpenAI-compatible vLLM examples. These are candidate backends only; this run does not select either as the Frank production model.

- https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- https://huggingface.co/Qwen/Qwen3-4B-Thinking-2507

## 4. Fusion 1: hypotheses and counterhypotheses

### H-AR-1 — Adaptive temporal evidence should beat fixed recurrence on cost-aware outcomes

Hypothesis: a temporal multi-signal policy that observes trajectory change, residual pressure and recent utility can stop/reroute recurrent computation more efficiently than a uniform fixed budget while avoiding some overthinking drift.

Counterhypothesis H0-AR-1: fixed budget is more robust; adaptive stopping merely trades compute for premature exits and hidden accuracy loss.

Discriminating test: same frozen trajectories, same observable signals, offline oracle only for evaluation, compare accuracy, task score, recurrence count, compute proxy, regret, false halts and correct-to-wrong drift.

### H-AR-2 — One instantaneous signal is insufficient

Hypothesis: instantaneous residual pressure alone can falsely signal convergence and should not be the sole stop criterion.

Counterhypothesis H0-AR-2: a single threshold is simpler and sufficiently robust; temporal aggregation adds complexity without measurable benefit.

Discriminating test: include a constructed instantaneous-low-pressure false-halt episode plus stalled, delayed-correction, overthinking and productive-cycle episodes.

### H-AR-3 — Readout and authority must remain separate

Hypothesis: classifying a loop state and proposing `CONTINUE/HALT/ROUTE/ROLLBACK` can be useful without granting the readout execution authority.

Counterhypothesis H0-AR-3: proposal-only separation adds latency/complexity with no safety benefit.

Required evidence: effect-authority receipts, zero unauthorized mutation, and later end-to-end latency/cost measurements.

### H-AR-4 — Readout-quality metadata is a necessary epistemic gate

Hypothesis: convergence decisions should be invalid when residual-pressure estimator identity, uncertainty or freshness are missing/stale.

Counterhypothesis H0-AR-4: synthetic fixtures are controlled enough that estimator metadata is unnecessary ceremony.

Discriminating test: run legacy fixture unchanged under current v1.4 readout. Correct safe behavior is `READOUT_UNCERTAIN`, then separately rerun with explicit synthetic estimator metadata.

## 5. External research cycle 2

The second pass focused on stopping dynamics and overthinking rather than merely recurrent architectures.

- Li et al., **TRACE: “Efficient Test-Time Scaling via Temporal Reasoning Aggregation”**, Findings of ACL 2026. TRACE explicitly argues that instantaneous signals are unreliable for convergence and aggregates answer consistency plus confidence trajectories over time; reported token savings are 25–30% on their evaluated tasks with accuracy near full reasoning.
  - https://aclanthology.org/2026.findings-acl.651/
- Sun et al., **REFRAIN: “Stop When Enough: Adaptive Early-Stopping for Chain-of-Thought Reasoning”**, ACL 2026. It combines a stop discriminator with adaptive thresholding; the paper reports 20–55% token savings across its evaluated benchmarks/model families while maintaining or improving accuracy.
  - https://aclanthology.org/2026.acl-long.1256/
- Zhou et al., **“When More Thinking Hurts: Overthinking in LLM Test-Time Compute Scaling”**, Findings of ACL 2026. It reports diminishing returns and cases where longer reasoning abandons previously correct answers; problem-dependent compute allocation is therefore a real competing explanation to “always think longer”.
  - https://aclanthology.org/2026.findings-acl.1199/

These sources support the *form* of H-AR-1/H-AR-2 but do not validate Frank’s thresholds, signals or controller.

## 6. Fusion 2: architecture and experiment consequences

1. **Readout first, policy second.** Current literature and Frank’s own safety boundary converge on keeping observable trajectory readout separable from the stop/route policy. A learned or hard-coded gate must not quietly reshape the evidence it is meant to read.
2. **No scalar-optimum policy selection.** Accuracy, utility, false halts, drift, compute, route cost and recovery must stay visible. The live Research Center independently tightened this into a `BinaryFreezeCandidate`/operating-window rule: choose a reproducible Pareto region, not one lucky maximum.
3. **Fixed budget remains a mandatory control.** It is not “obsolete”; it exposes whether adaptive savings are purchased with premature stops or route overhead.
4. **Warmup is itself a safety/performance parameter.** Short warmups save compute but can route too early; long warmups preserve more of fixed-budget cost and can reintroduce overthinking drift.
5. **Synthetic frozen episodes are only a pre-falsification layer.** Next evidence must come from frozen historical/runtime episodes and matched real local-4B runs on the Ubuntu lane.

## 7. Live build delta

### Build A — v1.4 re-entry factorial gate

This worker committed in Frank repo:

`806dbfe599a7d5c5d70b7d9c0222b1076de06d4a`  
`test(loop): gate reentry factorial against v1.4 readout quality`

File:
`tests/test_loop_reentry_factorial_v14_gate.py`

Purpose and invariants:

- preserve the old standalone factorial as a negative result: its embedded v1.4 readout is expected to be `READOUT_UNCERTAIN` because it predates mandatory residual-quality metadata;
- rerun the same matched trajectories with explicit synthetic estimator identity/version, uncertainty=0 and age=0;
- truthful + rescued arms must classify `CONVERGING_FIXED_POINT` and propose `HALT_CANDIDATE_CONVERGED`;
- shuffled/no-reentry/lesioned arms must classify `STALLED` and propose `ESCALATE_STALLED`;
- require ten deterministic replays for each principal control arm;
- assert readout authority remains `PROPOSAL_ONLY`, final state authority remains unchanged and no effect-authority receipt is granted.

### Build B — make the adaptive experiment part of standard pytest integrity

Another worker committed the adaptive differential experiment itself:

`8dc7260a96c54c5224fc627ca87afefd8a9296e0`  
`tests/adaptive_recurrence_differential_experiment.py`

A parallel worker then added a direct VPS gate for it:

`c06a86d4fdba56c6f53ddf66c49a610b31ade426`.

This worker additionally committed:

`4cdf06ce735a4cf941aab52f43a4351e5c1f89de`  
`test(h1): execute adaptive recurrence differential in pytest gate`

File:
`tests/test_adaptive_recurrence_differential_gate.py`

This prevents a research script from being “present but not collected” by standard pytest integrity. `experiment.main()` and its deterministic/negative-control assertions are now part of the pytest lane.

## 8. Bug found, falsified interpretation, repair and retest

A live self-hosted Ubuntu run at FRANK commit `d1727c1...` temporarily fell to 17/18 gates because `local_model_endpoint_boundary` failed.

Observed mechanism:

- the chunked streaming oversize test intended to prove `MODEL_RESPONSE_TOO_LARGE`;
- on Ubuntu/Python 3.12 the server/client timing produced a TCP connection reset while the client was still reading;
- the adapter correctly normalized that to fail-closed `MODEL_RESPONSE_TRANSPORT_ERROR`;
- the test asserted only `MODEL_RESPONSE_TOO_LARGE`, so the test failed despite fail-closed runtime behavior.

Initial interpretation considered broadening the assertion to accept either fail-closed outcome. A concurrent worker found a cleaner falsifier: the mock HTTP server had not consumed the complete request body before emitting/closing a large HTTP/1.1 response. Commit `c901358039c542678cf866876bc01b5539e15956` drains that request body and stabilizes the test so it measures the intended response-size boundary rather than half-duplex teardown behavior.

After that change, the real VPS returned 18/18 PASS. Subsequent adaptive and model-metric gates raised the current matrix to 20/20 PASS.

Negative result preserved: a network-level transport reset is not evidence that the model boundary accepted an oversized response; both observed paths remained fail-closed. The test harness, not the safety invariant, was the defect.

## 9. Adaptive recurrence measurements

Truth class: `SYNTHETIC_FROZEN_DIFFERENTIAL_EXPERIMENT`.  
Episodes: 8.  
Policies: fixed budget, one instantaneous residual-pressure signal, temporal multi-signal warmups 2/3/4/5/6.  
Controller semantic version: `trajectory-probe-v1.4-proxy-safe`.

| policy | accuracy | recurrences | total cost | mean utility | total regret | false halts | correct->wrong drift |
|---|---:|---:|---:|---:|---:|---:|---:|
| fixed_budget | 0.625 | 52 | 2.21 | 0.42000 | 1.38 | 0 | 1 |
| single_signal | 0.500 | 43 | 1.83 | 0.43375 | 1.27 | 1 | 1 |
| temporal_w2 | 0.500 | 30 | 1.29 | 0.49750 | 0.76 | 2 | 0 |
| temporal_w3 | 0.625 | 35 | 1.50 | 0.50000 | 0.74 | 2 | 0 |
| temporal_w4 | **0.750** | **38** | **1.63** | **0.51250** | **0.64** | 2 | **0** |
| temporal_w5 | 0.625 | 46 | 1.96 | 0.47625 | 0.93 | 1 | 1 |
| temporal_w6 | 0.625 | 51 | 2.16 | 0.42625 | 1.33 | 0 | 1 |

The experiment’s own multi-objective receipt selects `temporal_multi_signal_w4` as best by **synthetic utility** and **synthetic regret**, not as a production controller.

### Derived deltas: temporal_w4 vs fixed_budget

- accuracy: 0.750 vs 0.625 = +12.5 percentage points;
- recurrences: 38 vs 52 = **26.9% fewer**;
- total synthetic cost: 1.63 vs 2.21 = **26.2% lower**;
- mean utility: 0.5125 vs 0.4200 = **22.0% higher**;
- total regret: 0.64 vs 1.38 = **53.6% lower**;
- correct-to-wrong drift: 0 vs 1;
- false halts: 2 vs 0, an explicit regression that blocks promotion.

### Derived deltas: temporal_w4 vs single_signal

- accuracy: +25.0 percentage points;
- recurrences: **11.6% fewer**;
- total synthetic cost: **10.9% lower**;
- mean utility: **18.2% higher**;
- total regret: **49.6% lower**;
- correct-to-wrong drift: 0 vs 1;
- false halts: 2 vs 1.

### Anti-Goodhart finding

`temporal_w2` has the highest measured `outcome_gain_per_cost` (~4.085) among the displayed temporal candidates, but only 0.50 accuracy and two false halts. Therefore maximizing efficiency/cost ratio alone would select a worse behavioral operating point. This directly supports the new Research Center rule to freeze a Pareto/robust operating region rather than one scalar optimum.

### Warmup tradeoff

- w2/w3 are compute-efficient but prematurely route/stop in two episodes.
- w4 raises accuracy to 0.75 and eliminates the constructed correct->wrong drift while preserving material compute savings, but still has two false halts.
- w6 removes false halts in this tiny synthetic set but consumes 51/52 of fixed-budget recurrences and reintroduces one correct->wrong drift, largely erasing the intended adaptive-compute advantage.

This is evidence for a tradeoff surface, not a universal optimum at warmup=4.

## 10. Current self-hosted Ubuntu measurement

Newest receipt re-read during this run:

- evidence class: `REAL_SELF_HOSTED_UBUNTU_EXECUTION`;
- FRANK source commit under test: `02e19765b6784d1ebb6203ce7897073b72b6d18d`;
- host: `digital-retina`;
- runner: `clay`;
- OS/arch: Linux X64;
- kernel/platform: Linux 6.8.0-117-generic x86_64 / glibc 2.39;
- Python: 3.12.3;
- gate count: 20;
- PASS: 20;
- FAIL: 0;
- adaptive recurrence differential: PASS;
- local model endpoint boundary: PASS;
- local model tool metrics: PASS;
- full pytest gate: PASS;
- `release_claim=false`;
- `whole_frank_release_status=NOT_CLAIMED`.

This is real Ubuntu VPS integrity evidence. It is **not** Andreas-PC acceptance and **not** a full Frank v0.1 release receipt.

## 11. What is now supported vs not supported

### Supported working conclusions

- A temporal multi-signal recurrence family deserves higher-priority real-episode testing than the single instantaneous threshold.
- Warmup/depth allocation is a first-class control variable and must be swept, not fixed from one toy run.
- Current v1.4 residual-quality gating catches stale/underspecified readout experiments instead of silently minting convergence decisions.
- The live self-hosted Ubuntu integrity lane can execute and persist reproducible FRANK code/test receipts; the newest observed run is 20/20 PASS.
- Readout and execution authority can remain separated in the current design and tests.

### Not supported / blocked

- `temporal_w4` is not a production-selected policy.
- No real local-Qwen 4B recurrence comparison was executed in this experiment.
- No target-PC acceptance was executed.
- Historical services-tree exact 74-module conservation remains a separate whole-FRANK completion blocker until source-resolved ledger evidence closes it.
- 71 historical DB identities being accounted for does not prove complete semantic migration of all 71.
- Passing the integrity matrix does not prove the one-module/binary loop core is release-ready.
- Recurrence, stable loops, GWT ignition or adaptive stopping do not establish phenomenal consciousness or causal emergence.

## 12. Highest-information next experiments

1. **Frozen historical/runtime replay:** construct a corpus of real FRANK episodes with observable `state_delta`, residual-pressure estimator metadata, outcomes and route/recovery receipts. Run fixed/single/temporal policies without changing trajectories first.
2. **Matched real local-4B episodes:** use the engine-neutral OpenAI-compatible local model boundary and compare candidate Qwen-class 4B runs under controlled prompts/seeds where feasible. Do not bind the policy to one engine.
3. **False-halt decomposition:** explicitly label whether a route/halt that precedes the offline local oracle is actually harmful after downstream route benefit/cost is included. Current synthetic scoring conservatively treats route at current local score and does not model downstream benefit.
4. **Validated next-step utility:** replace the historical recent-net-utility proxy with an independently validated estimate/predictor of the causal marginal value of one more recurrence.
5. **Operating-window sweep:** jointly vary warmup, residual thresholds, trend epsilon, cycle criteria and route/escalation thresholds; keep a Pareto set across accuracy, regret, false halt, drift, recurrence cost, latency and recovery.
6. **OOD/seed robustness:** freeze the policy-selection procedure before held-out evaluation; reject one-seed/one-fixture optima.
7. **Lesion/rescue under runtime episodes:** truthful vs shuffled/no re-entry; lesion critical recurrence/coupling mechanisms; rescue and require matched restoration of selective causal signatures.
8. **Binary differential:** only after a robust operating region exists, compile/freeze it and prove the binary reproduces the reference dynamics/Needle/recovery signatures after clean restart.
9. **Andreas-PC acceptance:** final v0.1 promotion requires receipts on the actual target system, not only the Hostinger/self-hosted Ubuntu lane.

## 13. Mesh feedback

The attached `BRANCH_FEEDBACK_MANIFEST.json` sends an explicit delta to `frank`, `harness`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`, `unifieddb`, and `clayresearch` so this result is available to parallel research branches.

Primary program recommendation:

`TEMPORAL_MULTI_SIGNAL_W4 = HIGH_PRIORITY_FALSIFICATION_CANDIDATE`, **not selected**, until frozen historical/runtime + real local-4B + downstream route-cost + OOD/seed + recovery evidence exists.

Final epistemic status:

- scientific generation/promotion: NO automatic promotion;
- research delta: YES;
- code delta: YES;
- Ubuntu VPS evidence: YES, 20/20 latest observed;
- full Frank v0.1 release: NOT CLAIMED;
- next falsifier: real episodes and real local 4B on the target-compatible Ubuntu lane.
