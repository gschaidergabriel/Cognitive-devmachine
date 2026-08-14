# FRANK v0.1 — Integrated H1 Sandbox Build

Run: `frank-20260809T2118p0700-chatgpt-secondary-integrated-sandbox`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 · 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Evidence class: `REMOTE_SANDBOX_DETERMINISTIC_TEST`  
Owner evidence rule for this phase: `SANDBOX_SUFFICIENT_FOR_NOW`

## Result

`ARCHITECTURE_FIDELITY = IMPROVED`

A compact executable H1 integration spine was added at:

- `research_entity/harness/reference/frank_integrated_spine.py`
- `research_entity/harness/reference/test_frank_integrated_spine.py`

The artifact links the current architecture freeze into one reference-oriented process over the existing canonical StateLedger and Needle boundary while preserving each semantic module as an independently testable/lesionable step. This is a reference integration surface, not a claim that H1 is release-complete.

## Coverage

All 15 modules in the current H1 architecture freeze are exercised in one end-to-end cycle:

`adaptive_state_promotion · causal_observability_replay · clay_model_4b · claygraph_memory · digital_retina · effect_gateway · gwt_workspace · hyperposition · loop_dynamics_controller · micro_visual_classifier · needle_bridge · perceptual_field · semantic_state · thalamus_attention · unifieddb_plane`

The integration spine also contains explicit successor mappings for 29 catalogued historical organ/service families from the lineage fusion. No family is marked omitted. Historical service/process boundaries are allowed to dissolve while the supported semantics and known failure constraints survive.

## Exact artifact/dependency identity

The sandbox-tested integration files were compared with their committed GitHub blobs:

- integrated spine Git blob: `2ae526e5c33b7804246957cda0bec52ed2715a59`
- integrated spine test Git blob: `1cff91346f902dfdc7491ed401beb11e219c237c`
- StateLedger Git blob and sandbox blob: `821f023ea166e45975045b29ff2b120770573c3e`
- Needle boundary Git blob and sandbox blob: `ecfbeb0fae6ff3acbf36f264fe66d64dab621943`

The first local dependency copies were not byte-identical. That evidence-integrity gap was detected, corrected by replacing them with exact current GitHub content, and all reported final tests were rerun afterward.

## Executed sandbox evidence

Final exact-dependency results:

- compact repository integration suite: **14/14 PASS**;
- detailed integration suite: **27/27 PASS**;
- Python compileall over the reference package: **PASS**;
- stress: **100 full cycles**, **300 persisted events**, final epoch **300**;
- observed stress throughput: **59.2 cycles/s** in this sandbox; this is a proxy benchmark, not target-PC performance;
- deterministic recovery: semantic-state hash equal **true**, trace-root hash equal **true**, epoch equal **true**;
- `PRAGMA wal_checkpoint(PASSIVE)`: `(0, 170, 170)`.

The tests cover module/lineage coverage, Needle/model authority denial, fresh capability-bound effect permits, stale epochs, WAL/FULL, deterministic replay, snapshots, visual conflict vs familiarity, learned-state promotion guards, derived ClayGraph authority separation, GWT stage separation, recurrence/convergence rules and Qwen-class model-mode ABI separation.

## Negative results found and fixed

1. The larger prototype initially serialized the Needle ingress object for observability and accidentally returned that serialization to the next typed stage. The contract requires recording the serialized form while returning the typed `ClayIngressEnvelope`. Fixed; rerun passed.
2. The compact stress oracle initially expected four persisted events per cycle although the compact spine intentionally persists three. This was a test assumption defect, corrected before the final run.
3. Initial local dependency copies were not byte-identical to current GitHub. This was treated as an evidence defect, corrected, hash-verified and rerun.

These failures remain part of the run history; they are not hidden by the final green state.

## Live external research used in the architecture decision

Current SQLite documentation supports the chosen reference direction: WAL permits concurrent readers and a writer but still has one writer at a time; checkpoint behavior must be managed; `synchronous=FULL` syncs WAL commits and is the durable WAL setting. The H1 stale-epoch/single-writer test and checkpoint instrumentation therefore remain architecture-relevant, while later performance work must measure checkpoint/tail-latency costs.

Current Qwen3 primary documentation confirms a dense 4B member, switchable thinking behavior and tool/function-calling support. The H1 model slot therefore treats `instruct`/`thinking` as ABI/capability modes rather than identity or authority. Model output remains proposal-only.

The 2025 preregistered adversarial GNWT/IIT collaboration is used as an anti-overclaim reminder: functional GWT-style routing measurements in FRANK are not evidence of phenomenal consciousness. The spine explicitly keeps recurrence and GWT stage receipts separate from any emergence/consciousness claim.

## Research-center feedback

A branch feedback manifest was written for all currently registered scientific branches:

`clayresearch · frank · claycode · harness · claygraph · unifieddb · gwt · hyperposition · emergenz`

Main cross-branch consequence: this integrated H1 spine can now serve as a compact executable semantic oracle for later H2 ClayCode differential work, while each branch retains its own falsifiers and richer experiments.

## What is still open

This run does **not** claim H1 release PASS. The highest-value remaining integration gaps are:

- real/direct Claude Code peer-tool and independent peer/backflow/capability failure semantics;
- richer UnifiedDB selection/query/transaction/recovery behavior beyond the core ledger;
- full diagnostic ClayGraph and dynamic causal graph contracts;
- deeper GWT lesions, receiver reconstruction/uptake instrumentation and recurrence factorials;
- real Digital Retina/MVC measurement, open-set calibration, candidate shadow evaluation and rollback suite;
- effect/recovery/adversarial/fuzz/race/partial-effect testing at broader scope;
- target-shaped local Qwen-class 4B adapter execution;
- target Ubuntu resource/latency/RAM/KV measurements;
- H2 ClayCode execution/differential after BASE ClayCode release.

## Evidence boundary

The user explicitly designated sandbox evidence as sufficient for the present development phase. This receipt honors that development rule, but evidence remains labeled `REMOTE_SANDBOX_DETERMINISTIC_TEST`; it is not upgraded to `LIVE_PC_FRANK`, `TARGET_4B` or H1 release evidence.

Canonical scientific revision was not promoted by this run. The executable delta and receipts are committed as research/build evidence under canonical parent r2.
