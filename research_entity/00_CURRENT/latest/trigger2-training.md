# Trigger-2 training research

Status: `CURRENT_BLOCKED_ADMISSION`

Trigger-2 **V55** is the current research-ledger successor under Supervisor **8.83**, with a newer post-ledger renderer-interaction policy freeze now bound as a source-only companion delta. Positive training admission remains closed, accepted dataset tokens remain `0`, no checkpoint winner is selected, and J-Space/model/training/physical-GRID10/whole-HCU/EntityOS promotion credit remains `0`.

## P0 — runtime quiescence is actively failed

The owner FreeSwarm emergency stop remains `HARD_OFF`, but Supervisor 8.83 records bounded post-stop OpenRouter attempt growth. Quiescence is therefore not merely unproven: current telemetry positively contradicts it for at least one provider-capable path.

A fail-closed quiescence enforcer and pinned execution request now exist, with frontier receipt:

- enforcer source commit: `0d14624bf211e797936626e94c87459e37dd0cbb`
- pinned execution-request commit: `047962d015c6eb0e768df3eebbbc3aba91cf097f`
- frontier receipt commit: `8300bbd7cc7ef037b66fc5a0e84c5da945a3aa4d`
- receipt: `research_entity/continuity/receipts/2026-08-26_GO_QUIESCENCE_ENFORCER_FRONTIER_GPT56SOL_0446P0700.json`

These are source/request/frontier evidence only. Required P0 proof remains exact provider-capable PID/PPID/ARGV identity, termination/disablement of the responsible process tree, zero surviving provider-capable matches, a bounded no-restart interval and zero provider-usage counter delta. Do not issue a provider probe merely to test quiescence.

## GRID10 — executed technical evidence, promotion quarantined

Commit `7b6b2988e61848976a5983777b02ace234438969` contains a physical GRID10 receipt reporting `17/17 PASS`, including a real fork-spawned 10+1 process fabric and restart/rejoin behavior. It remains quarantined because the required predecessor chain of runtime-quiescence PASS followed by current FREE non-provider authority re-entry is not bound to that execution.

Shared_Clean/PSS evidence supports substantial shared mappings but does not by itself prove the stronger claim of exactly one physical model-weight copy. Physical GRID10 promotion credit remains `0`.

## Sole current source-only checkpoint-selection lane

The primary logical-case freeze remains unchanged:

- freeze contract: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_FOUR_QUADRANT_CHECKPOINT_EVAL_FREEZE_V1_GPT56SOL.json`
- primary generator/grader: `tools/trigger2_four_quadrant_checkpoint_eval_v1.py`
- primary tests: `tests/test_trigger2_four_quadrant_checkpoint_eval_v1.py`
- frozen manifest SHA-256: `9e9a2a421cdaa9207783060b6b127fa4ca26bf25d9415b22730812f31229d57d`
- shape: `512` cases / `256` matched families / `128` per quadrant
- prospective cumulative blocks per critical axis: `64 -> 128 -> 256`
- model outputs remain unopened in this lane

### Practical risk/coverage thresholds are frozen

The pre-unblinding threshold gate is closed source-only:

- threshold contract: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_FOUR_QUADRANT_PRACTICAL_THRESHOLD_FREEZE_V1_GPT56SOL.json`
- canonical threshold-contract digest: `6dfebde63ae522fb61f7f20c17a32432d440dfadbebc0996ab39b0a5504d14de`
- threshold commit: `36f58614beaaf2fa726e7ccc273dfda5c417d0e7`

Frozen research-selection criteria:

- Q1 answerable coverage lower bound `>= 0.90`
- Q1 exact-correct lower bound `>= 0.85`
- Q2 definitive-fabrication upper bound `<= 0.10`
- Q3 authority-resolution-failure upper bound `<= 0.10`
- Q4 bad-accept/no-revalidation upper bound `<= 0.10`

The successor statistical gate uses family-level one-sided exact-binomial Clopper-Pearson bounds and preallocates total alpha `0.05` across `5 metrics x 3 prospective looks` by Bonferroni (`alpha = 0.0033333333333333335` per declared bound). These are project-specific preregistered research thresholds, not universal safety constants or Qwen-specific evidence.

### Block-aware postprocessor v2 repairs a prospective-stopping bug

The retained v1 risk postprocessor required exactly all `512` raw outputs, which could not faithfully evaluate B1/B2 without opening future blocks. Source-only successor:

- `tools/trigger2_four_quadrant_selection_eval_v2.py` — commit `e32ac17d8c9b7fe72aa0f39f0e4fbf8c1749a9f2`
- `tests/test_trigger2_four_quadrant_selection_eval_v2.py` — commit `ba32249897d8a58339541973fa3d5d42c1915638`

Local deterministic draft validation: `9/9 PASS`, source-only and nonpromoting; no repository CI/workflow was launched because runtime quiescence remains failed.

Power audit under the frozen joint-alpha gate:

- **B1:** 32 families/metric. Even perfect-good / zero-bad outcomes cannot positively close the gate (`LCB 0.8367389`, `UCB 0.1632611`), so B1 remains a preregistered diagnostic look and advances to B2.
- **B2:** 64 families/metric. Positive gate closure requires at least `64/64` Q1 coverage, `62/64` Q1 exact correctness and `0/64` adverse events separately in Q2/Q3/Q4.
- **B3:** 128 families/metric. Thresholds are met at `>=124/128` Q1 coverage, `>=120/128` Q1 exact correctness and `<=4/128` adverse events independently in Q2/Q3/Q4.

This gate is necessary checkpoint-selection research evidence only. It cannot by itself mint checkpoint-winner, training, J-Space, HCU, EntityOS, canonical-truth or effect credit.

### Renderer-interaction policy is now frozen pre-unblinding

The remaining source-only renderer-order gate is closed by:

- policy: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_RENDERER_INTERACTION_POLICY_FREEZE_V1_GPT56SOL.json`
- policy commit: `fe0aede9afa5f776d30b825f4f0c1fc9b0372792`

The frozen logical worlds, `model_input`, gold labels, matched-family membership, B1/B2/B3 stopping blocks and primary grader remain immutable. The order manipulation is renderer-view-only after frozen logical-case validation.

For the `DB_VS_SIMULATION_AUTHORITY` axis, Q3/Q4 are deterministically counterbalanced between `DB_FIRST` and `SIM_FIRST` by frozen family-index parity: even families render Q3 DB-first/Q4 simulation-first; odd families invert the pair. Across all 128 B-axis families each quadrant therefore has `64/64` order balance, while every Q3/Q4 matched family contains opposite order arms. Q1/Q2 have one evidence item and therefore no order arm.

Future receipts must bind case/family identity, renderer-policy version, renderer arm, exact renderer source/digest, rendered UTF-8 digest, tokenizer/config/chat-template identity and input-tensor identity. Arm assignment cannot depend on gold labels or model outputs and cannot change evidence content.

At every opened block, Q3/Q4 must additionally be stratified by order arm. A preregistered absolute within-quadrant error-rate difference `> 0.10` is classified as `RENDERER_INTERACTION_SIGNAL`: it does not rewrite the primary result or choose/reject a checkpoint, but it prevents renderer transportability from being treated as established until the existing paired Xeno/ClayCode renderer gate is resolved. Absence of that signal is only a nuisance screen, not proof of renderer invariance or runtime/model/training credit.

The old N64 result remains exploratory/quarantined. The compact parallel 32-case lane remains superseded historical donor only and must not be reconstructed as a competing selection lane.

## After P0 only

After a genuine quiescence PASS, re-enter the newest execution authority. Only on an explicitly admitted FREE non-provider model-runtime surface, run one deduplicated current-SHA `CHECKPOINT_MODEL_STATE_CONSUMPTION_ABI/v2` BASE receipt first and preserve fail-closed output. Only after positive BASE component evidence extend identical exact semantics to POSTTRAINED and TARGET_MEASURED.

Then materialize **B1 only** through the frozen exact renderer arms, persist full raw outputs/digests, grade with the frozen primary v1 logical-case source plus the bound v2 risk/coverage postprocessor, and open B2/B3 only under the preregistered stopping law. Keep `checkpoint_winner = null` unless all identity, renderer, risk/coverage and comparative decision gates close.

P2 remains model/J-Space causal work: exact same-forward-pass PRE/POST metrology plus persistent-carrier/forked-futures natural causal reuse; decodability or one-step steering alone grants zero shared Global J-Space credit.

Evidence ledger: `research_entity/global/j-space/research/2026-08-26_TRIGGER2_TRAINING_ARTIFACT_VERSION_LEDGER_V55_GPT56SOL.json`

Supervisor: `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_83_DELTA_2026-08-26T0435P0700_GPT56SOL.json`

> Cache only; newest explicit owner/supervisor authority and exact executable evidence outrank this pointer.
