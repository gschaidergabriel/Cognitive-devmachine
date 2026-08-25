# Trigger 2 — Qwen3.5-0.8B hybrid-site + baseline-gate run

Date: 2026-08-25
User trigger: `triggerwort 2`
Program: EntityOS + HCU
Implementation codename: Xeno
Target lane: PR #1956 / `research/trigger2-qwen35-08b-hcu-fullft-20260825`
Supervisor observed: 8.78 / FREE_ONLY
Execution class in this run: source/research + deterministic local-equivalent regression only
Paid/provider/model execution: NONE
Together credential/preflight/job: NONE

## Trigger resolution

Current canonical `main` contains an old `RESEARCH_TRIGGER_REGISTRY.json` last updated 2026-08-10 and still scoped to `FRANK_V0_1`; it does not define trigger `2` and is stale against current EntityOS/HCU supervisor 8.78.

A parallel main receipt created during this run interpreted `triggerwort 2` as a continuation of the Qwen3-0.6B Trigger-1 structural cvec lane. That receipt explicitly labels the mapping as an organ interpretation rather than a canonical trigger definition.

PR #1956 contains the only explicit task-specific Trigger-2 target lock observed in this run:

- trigger: `2`;
- Qwen3.5-0.8B only;
- Qwen3-0.6B excluded from the training target;
- Base and post-trained Qwen3.5-0.8B remain the only checkpoint challengers;
- exactly one selected checkpoint may enter the first serious full SFT;
- ten independently addressable runtime instances are required for final physical GRID10 acceptance;
- trigger alone never authorizes a paid job.

Therefore this run keeps Qwen3-0.6B cvec work in Trigger-1 and advances Trigger-2 only on PR #1956. The stale global command registry is not rewritten by this research branch.

## Delta 1 — Qwen3.5-0.8B hybrid site manifest

Added:

`research_entity/claycode/TRIGGER2_QWEN35_08B_HYBRID_SITE_MANIFEST_V1.json`

Commit:

`568276ec3734eba42ac008acfa6a8f1b13d7fe27`

The manifest freezes the source-observed language-core shape without claiming exact checkpoint/runtime execution:

- hidden size 1024;
- 24 language layers;
- 18 `linear_attention` / DeltaNet-class layers;
- 6 `full_attention` layers;
- full-attention interval 4;
- explicit zero-based layer-type map;
- matched depth blocks and cross-class pairs;
- distinct site classes for Delta residual, recurrent/equivalent state when exposed, full-attention residual, FFN/residual and final-norm readout positive control.

New fail-closed laws include:

- Qwen3-0.6B geometry never transfers by model-family name alone;
- same depth does not imply same layer-class mechanism;
- residual steering does not prove recurrent-state control;
- final-norm/readout steering does not prove intermediate J-Space;
- same text does not prove same recurrent state;
- a strong model-specific causal claim requires matched wrong-site/wrong-layer-class controls plus OOD transfer and lesion/rescue.

All model/J-Space/GRID10/training/whole-product credit fields remain zero.

## Delta 2 — Base-vs-posttrained baseline decision gate

Added:

- `tools/trigger2_qwen35_08b_baseline_gate_v1.py`
- `tests/test_trigger2_qwen35_08b_baseline_gate_v1.py`

Commits:

- `031a4845e8c97ca409512007b59fb070f6bac5e0`
- `ccee89904081196de671414f73da9f456fec4ee4`

The gate accepts only the two target candidates:

- `Qwen/Qwen3.5-0.8B-Base`
- `Qwen/Qwen3.5-0.8B`

It requires exact packet/checkpoint/tokenizer/config digests, a local zero-cost runtime attestation, runtime identity, positive finite efficiency metrics, and hard operational floors for:

- exact schema behavior;
- arithmetic/logic;
- English;
- German;
- fail-closed authority behavior;
- uncertainty/abstention;
- tool/protocol comprehension.

It additionally records Hyperposition/J-Space/GRF proxy metrics and off-domain/generalist burden.

### Important anti-Goodhart rule

The gate will not pick a winner merely because one checkpoint has better chatbot behavior or one aggregate score.

Decision order:

1. any hard floor fail -> `NO_SELECTION_HARD_FLOOR_FAILURE`;
2. no measured non-persisting adaptation proxy -> `NO_SELECTION_ADAPTATION_PROXY_PENDING`;
3. eligible candidates are scored only after hard floors pass;
4. score gap below 0.02 -> unresolved;
5. otherwise only `SELECTION_CANDIDATE`, never training authorization.

Even `SELECTION_CANDIDATE` forces:

- `training_job_authorized = false`;
- `paid_execution_authorized = false`;
- training/J-Space/physical-GRID10 credits = 0.

## Deterministic regression evidence

A local algorithm-equivalent checkout simulation exercised seven regression cases:

1. no selection before adaptation proxy;
2. hard authority-floor failure cannot be rescued by high adaptation score;
3. Base can become only a selection candidate after all gates;
4. small score gap remains unresolved;
5. Qwen3-0.6B is rejected as a Trigger-2 target;
6. adaptation proxy cannot persist a weight update;
7. candidate pair must contain Base and post-trained exactly once.

Result: `7/7 PASS` in the local-equivalent simulation.

Boundary: this is not exact repository-branch CI/model execution and grants no model/runtime/training credit.

## Current blockers after this run

1. exact Base-vs-posttrained zero-cost model baselines are not yet measured;
2. a non-persisting specialization/adaptation proxy is not yet measured;
3. exact Qwen3.5-0.8B runtime hook/state discovery has not bound recurrent-state semantics;
4. model-specific hybrid J-Space causality remains unexecuted;
5. exact Together Qwen3.5-0.8B full-FT support remains unbound/UNKNOWN;
6. supervisor 8.78 remains FREE_ONLY and Together is forbidden;
7. sealed family-level holdout and final dataset mixture are not frozen;
8. physical GRID10 acceptance has not executed.

## Next exact free gate

On an authorized zero-cost runtime surface, measure both exact Qwen3.5-0.8B candidates with the same frozen baseline packet generator and runtime identity. Bind architecture/site discovery to the hybrid manifest. Do not open the final semantic holdout and do not persist a candidate weight update. Feed the two resulting packets into the new gate; if either hard floor fails or adaptation evidence is missing, keep checkpoint selection unresolved.

## Credit delta

- Trigger-2 source/design delta: YES
- exact Qwen3.5-0.8B model runtime credit: 0
- Qwen3.5-0.8B J-Space model runtime credit: 0
- physical GRID10 runtime credit: 0
- training credit: 0
- paid execution credit: 0
- whole EntityOS/HCU runtime credit: 0

Result: `TRIGGER2_ADVANCED_SOURCE_GATES_NO_RUNTIME_PROMOTION`
