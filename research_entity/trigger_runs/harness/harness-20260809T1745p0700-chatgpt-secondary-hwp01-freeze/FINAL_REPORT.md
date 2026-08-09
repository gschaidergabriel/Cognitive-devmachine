# Harness Run — H-WP-01 Deterministic Architecture Freeze

**run_id:** `harness-20260809T1745p0700-chatgpt-secondary-hwp01-freeze`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**trigger:** `harness`  
**work package:** `H-WP-01-FREEZE-COMPILER`  
**decision:** **COMPONENT COMPLETE CANDIDATE · H1 RELEASE NOT_PASS · NO CANONICAL PROMOTION**

## Executive result

This run built and executed a deterministic Reference Harness architecture-freeze compiler rather than writing another architecture summary.

The compiler binds the current compatible FRANK architecture into a source-locked Harness contract using two separate identities:

- `architecture_semantic_hash` — normalized architecture meaning;
- `exact_contract_hash` — normalized meaning plus exact Git-source identities.

The Ubuntu repository-checkout run produced:

- **13 logical architecture planes**;
- **15 semantic modules/organs**;
- explicit `PerceptualField`, `VisualPercept`, adaptive Micro Visual Classifier and AdaptiveStatePromotion overlays;
- explicit GWT R8 semantic/version/trace witness separation;
- explicit visual causal path into Thalamus/GWT and outcome/re-entry;
- exact Source Lock over six upstream artifacts;
- `architecture_semantic_hash = b92521a77690fcee8e6e247597e091c1478f790d38f780381d899b1200e85a0f`;
- `exact_contract_hash = 73450c51d1ca84f63556ba3d8adad3eb663ec848b02384e744af9ebd28421540`;
- freeze verification: **PASS, 0 violations**.

The generated artifact is `REFERENCE_HARNESS_ARCHITECTURE_FREEZE.json`.

## Architecture-source decision

A key implementation finding was that the newest FRANK `FRANK_ARCHITECTURE.claycode.json` is a **loop/base vertical-slice projection**, not a complete organism definition. Treating it as the whole Reference Harness would silently drop lineage-surviving functions and mandatory owner-fixed overlays.

The freeze therefore uses:

`C9 lineage-fused architecture`
`+ owner-fixed Clay-native contract`
`+ owner-fixed Digital Retina contract`
`+ owner-fixed adaptive visual-learning directive`
`+ newest compatible FRANK loop/base projection`
`+ GWT R8 observation overlay`

The loop projection contributes current executable-facing semantics but does not replace the complete architecture basis.

## Frozen logical planes

1. sensor/reflex ingress;
2. recurrent PerceptualField;
3. Unified Memory/world/self/goals;
4. RecognitionValidity + AdaptiveStatePromotion;
5. CognitiveFrame/epochs/Active Assembly;
6. Thalamus/attention/access control;
7. GWT competition/WorkspaceEpisode;
8. typed reader/model uptake;
9. personality/value/goals/slow adaptation;
10. causal observability/replay;
11. external effect authority/sandbox;
12. UnifiedDB/ClayGraph publication;
13. runtime placement/one-module lowering.

These planes are logical semantics. They do not require 13 physical processes and do not prejudge H3 one-module placement.

## Frozen module set

The compiler retains the ten modules from the current FRANK loop projection:

- `needle_bridge`;
- `digital_retina`;
- `clay_model_4b`;
- `semantic_state`;
- `claygraph_memory`;
- `gwt_workspace`;
- `hyperposition`;
- `loop_dynamics_controller`;
- `unifieddb_plane`;
- `effect_gateway`.

It then explicitly materializes five required lineage/overlay modules that must not disappear merely because the newest FRANK projection is narrow:

- `perceptual_field`;
- `thalamus_attention`;
- `micro_visual_classifier`;
- `adaptive_state_promotion`;
- `causal_observability_replay`.

## Digital Retina / adaptive visual learning closure

H-WP-01 now fails closed if the owner-fixed visual contracts are missing or no longer contain the mandatory invariants.

The freeze explicitly represents:

- `PerceptualField` epistemic state including `KNOWN | UNKNOWN | CONFLICT | SET_VALUED`;
- `VisualPercept` audit materialization and source/capture/provenance identity;
- Adaptive Visual Readout outcomes `KNOWN_HIGH_CONFIDENCE | KNOWN_NEEDS_CONFIRMATION | AMBIGUOUS | UNKNOWN | CONFLICT`;
- GOLD/SILVER/BRONZE example trust tiers;
- BRONZE self-generated examples not becoming autonomous positive truth;
- classifier/prototype version and frozen feature-backbone compatibility;
- calibration identity;
- candidate/shadow state;
- atomic promotion;
- last-known-good rollback;
- resource budget;
- training-example provenance;
- mandatory MVC-E1..E7 test families.

Hard boundaries remain:

`micro_classifier_prediction != sensor_truth`

`familiarity != evidence`

`confidence != authority`

## Identity and replay closure

H-WP-02 current evidence and UnifiedDB U2 motivated, but did not independently validate, the freeze identity split.

The compiler distinguishes:

`architecture semantic meaning`

from

`exact source/contract identity`.

Its regression suite proves that source-formatting/representation changes can alter exact contract identity while normalized architecture meaning remains unchanged. Missing source blobs, changed locked blobs, missing visual-contract markers and missing required organs all fail closed.

GWT R8's separate runtime witnesses are also retained:

`semantic_state_hash != state_version_hash != trace_root_hash`.

These are runtime/replay witnesses, not architecture-freeze hashes.

## Executed evidence

### Local Linux component falsification

The compiler and regression suite passed:

- Python compile;
- 4/4 regressions;
- deterministic build/verify;
- semantic-vs-exact identity discrimination;
- missing MVC-contract marker rejection;
- Git blob mismatch rejection;
- missing required-organ rejection.

### Ubuntu repository-checkout CI

GitHub Actions then executed the exact committed compiler against the real repository sources.

Receipt: `EXECUTION_RECEIPT_CI.json`.

Observed:

- `py_compile = PASS`;
- unit regressions `4/4 PASS`;
- exact source-lock build `PASS`;
- source/freeze verify `PASS`;
- `15 modules`;
- `13 planes`;
- `0 violations`.

This is repository-checkout Ubuntu component evidence. It is **not** Andreas' designated Ubuntu developer-host H1 acceptance and is not live-FRANK evidence.

## Research-mesh preflight repair

During final validation, the official `tools/research_interconnect_preflight.py` was found to still encode legacy branch key `clay` even though the registry now defines `clayresearch`. The tool intentionally failed closed under this governance drift.

The Research Entity repaired this **research-center infrastructure**, not Franks Harness:

- priority tables now use `clayresearch`;
- packet budgets/overrides now use `clayresearch`;
- aliases retain `clay` as a search/history alias;
- historical `research_entity/trigger_runs/clay/` remains readable for existing ClayResearch runs.

Ubuntu CI then produced `PREFLIGHT_RECEIPT_CI.json`:

- Python compile `PASS`;
- Harness interconnect preflight `PASS`;
- 9/9 registered branches;
- 0 violations;
- `frank_harness_modified = false`.

## Late live-worker review

Fresh concurrent work was reread after the freeze.

### ClayCode FRANK-loop evaluator/lowering

The late spawn run reports 200,000 evaluator/lowering proxy cases and 100,000 GCC-shadow cases with zero mismatches, while explicitly leaving production parser/IR/lowering and target-host gates open. This is compatible with the freeze and does not change it.

### ClayGraph RAB

Reversal-Aware Binding adds an OPEN/HOLD future H1 discriminator around true reversal versus duplicated-source echo. It is preserved as future Harness test material; it does not promote a new accepted graph architecture and therefore does not invalidate H-WP-01.

### GWT adaptive recurrence

The late adaptive-recurrence run asks H1 to compare fixed recurrence budgets with pressure/trend-aware controllers and lesion/shuffle controls. It remains a future H1 experiment and does not alter the frozen base architecture.

See `LIVE_DELTA_REVIEW.json`.

## Cross-branch feedback

Explicit receipts were routed to all nine current branches in `BRANCH_FEEDBACK_MANIFEST.json`.

Most important consequences:

- **Harness:** H-WP-01 has an executable, source-locked architecture-freeze candidate ready for component completion; H1 release remains NOT_PASS.
- **Frank:** newest loop projection remains a delta/vertical slice, never a substitute for the complete fused organism.
- **ClayCode:** the freeze becomes an exact future H2/FRANK compilation target but does not bypass BASE.
- **GWT/ClayGraph:** late new research becomes future H1 fixtures unless/until separately promoted.
- **UnifiedDB:** semantic and exact representation/source identities remain distinct.
- **Emergenz:** no emergence/consciousness inference is made.

## What is not complete

This run does not complete H1. It does not execute the full Reference Harness, Digital Retina perception loop, MVC-E1..E7 experiments, effect authority suite, crash/recovery suite, Golden Traces, dynamic ClayGraph, long-horizon E2E, target-Qwen adapter or project-host acceptance.

BASE ClayCode remains the current program gate. H-WP-03 and H2 remain blocked accordingly.

## Decision

`H-WP-01-FREEZE-COMPILER = COMPLETE_COMPONENT_CANDIDATE`

`REFERENCE_HARNESS_ARCHITECTURE_FREEZE = GENERATED_AND_VERIFIED`

`H1_REFERENCE_HARNESS_RELEASE_GATE = NOT_PASS`

`BASE_CLAYCODE_RELEASE = STILL_CURRENT`

`CANONICAL_SCIENTIFIC_PROMOTION = NONE`

The next Harness work must remain non-overlapping with active H-WP-02. The highest-value open implementation lanes after this component completion are the frozen architecture's executable module surfaces — especially Digital Retina/MVC, Needle boundary, UnifiedDB/ClayGraph, GWT, effect authority, trace/replay and recovery — while H-WP-03/H2 wait on the ClayCode BASE gate.
