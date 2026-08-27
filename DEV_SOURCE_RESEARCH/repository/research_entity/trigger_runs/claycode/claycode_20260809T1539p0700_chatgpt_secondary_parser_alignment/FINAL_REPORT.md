# ClayCode Trigger Run — Parser Alignment + Fused FRANK Gate Representability

Run: `claycode_20260809T1539p0700_chatgpt_secondary_parser_alignment`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (IN_PROGRESS)

## Executive result

This run separated two questions that had been easy to conflate:

1. **Semantic expressibility:** the tested fused FRANK RecognitionValidity, AdaptiveStatePromotion and semantic-publication gate logic is expressible and executable with existing G9-compatible generic constructs. No dedicated new ClayCode primitive is justified by this test.
2. **Production parser readiness:** the published CURRENT G9 source and `grammar.ebnf` are not surface-closed. The first minimal `if` + union repair is also insufficient. BASE therefore needs a strict surface/AST freeze and full-corpus parser conformance before any parser work package can pass.

No CURRENT-stack, BASE-stage or canonical scientific promotion is requested.

## Internal evidence

Primary repository inputs:

- `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- `research_entity/claycode/g9/grammar.ebnf`
- `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`
- `research_entity/global/CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md`
- `research_entity/global/FRANK_V0_1_ADAPTIVE_VISUAL_LEARNING_DIRECTIVE.md`
- `research_entity/runtime/RAE_CLAYGRAPH_V2_HYPERRELATION_SELECTION.sql`
- `research_entity/runtime/RAE_UNIFIEDDB_V9_DYNAMIC_WORK_FABRIC.sql`
- current GWT/Hyperposition/Emergenz contracts and latest Clay stack

Concurrent material assimilated before final synthesis:

- `research_entity/trigger_runs/fusion/fusion-20260809T1538p0700-frank-architecture-lineage/FRANK_ARCHITECTURE_LINEAGE.json`
- `research_entity/trigger_runs/fusion/fusion-20260809T1538p0700-frank-architecture-lineage/FUSED_FRANK_TARGET_ARCHITECTURE.json`

The concurrent FRANK fusion preserves C9 as the latest explicit pre-overlay architecture base and adds mandatory current extensions including dissolved Retina, Unified Memory <-> Retina recurrent learning, separate recognition/promotion gates, atomic semantic publication and common-driver-aware causal receipts. This is an OPEN fused target overlay, not canonical promotion.

## Experiment 1 — grammar self-alignment

Artifacts:

- `grammar_probe.py`
- `CLAYCODE_G9_GRAMMAR_PATCH_CANDIDATE.ebnf`
- `EXECUTABLE_RESEARCH_RECEIPT.json`

Observed proxy behavior:

```text
current grammar
  union_field: FAIL
  if_cycle: FAIL
  baseline Delta<T>: PASS
minimal repair
  union_field: PASS
  if_cycle: PASS
  baseline Delta<T>: PASS
```

This proves a concrete executable mismatch in the published surface contract, but not yet full-file parser conformance.

## Experiment 2 — adversarial minimal-patch sufficiency

Artifact: `GRAMMAR_ADVERSARIAL_EXTENSION_RECEIPT.json`

Three additional exact CURRENT-G9 forms were tested against both the current proxy grammar and the minimal `if` + union repair:

```text
rule external_effect lifecycle=[...]
rule 4B_emits EffectIntent
rule NativeCognitionTask.forbidden_burden includes [...]
```

All three remained rejected by both grammars.

**Negative result:** the minimal `if` + union patch is not sufficient to claim CURRENT G9 surface closure. Do not accrete ad-hoc tokens directly into CURRENT. Freeze one strict BASE surface/AST and decide explicitly which prose-like existing forms are normalized sugar versus retained grammar.

## Experiment 3 — Unified Memory <-> Retina gate representability

Artifacts:

- `UM_RETINA_GATE_PROBE.clay`
- `generated_um_retina_gate_cli.py`
- `EXECUTABLE_RESEARCH_RECEIPT_UM_RETINA_GATE.json`

Hashes:

- Clay source SHA-256: `533cd82763ccb7db39ea687d00632112ed63f2f1d99fd00cacb096bfff1d9a7c`
- generated target SHA-256: `24d82e7649394ec051b083af812202aec0ae4147b2ce06e42a5491c224574674`

The probe used only grammar-compatible G9 constructs for three independent controls:

- RecognitionValidity fast-path gate;
- AdaptiveStatePromotion gate;
- semantic-publication gate.

A conservative run-local lowering generated a Python CLI and executed it in a separate Python process with `-S`.

Fixture classes:

1. all pass;
2. open-set/unknown veto;
3. stale-calibration veto;
4. sensor/conflict veto;
5. untrusted/BRONZE-like promotion veto;
6. candidate-evaluation veto;
7. incomplete projection/retraction closure veto;
8. replay-not-ready publication veto.

Observed: **8/8 MATCH**, all process exit statuses `0`, stderr empty.

Interpretation: tested recognition truth, durable promotion and CURRENT publication can remain explicitly distinct using existing generic G9-compatible constructs. This is evidence against inventing a dedicated new Retina/learning/publication primitive now.

Limitations: this is a partial research compiler probe. It does not execute real Retina features, classifier training, resource budgets, UnifiedDB transactions, ClayGraph projection, target-machine effects or a full rollback state machine. It does not qualify APP-01, APP-09 or any BASE work package as PASS.

## Cross-branch feedback

- **FRANK:** keep RecognitionValidity separate from AdaptiveStatePromotion; current sensor evidence retains veto over memory/familiarity. Compile the real fused component before requesting language growth.
- **Clay/Harness:** H1/H2 semantics must not be simplified to fit an incomplete parser. BASE must freeze and implement one parser/IR surface first.
- **ClayGraph:** publication closure is representable as a gate, but PATCH vs COMPLETE_SNAPSHOT/retraction and invalidation require the stronger runtime/IR contract plus crash/replay tests.
- **UnifiedDB:** source admission, schema preflight and atomic publication are representable as typed conditions; this does not imply physical DB monolith consolidation.
- **GWT:** recognition/promotion/publication state is control/readout, not truth or emergence proof.
- **Hyperposition:** UNKNOWN/AMBIGUOUS/CONFLICT alternatives remain explicit rather than collapsed into familiar certainty.
- **Emergenz:** neither parser success nor gate execution is emergence evidence; later claims still require intervention/lesion/rescue controls.
- **ClayCode:** immediate discriminator is parser/canonical-IR closure under frozen semantics.

## External triangulation

Primary/official technical evidence was used only as independent triangulation:

- Bytecode Alliance WIT/Component Model: typed interfaces/worlds/resources are a plausible FFI lowering surface, but interface membership does not replace Clay dynamic capability/commit authorization.
- MLIR dialect conversion: progressive typed lowering with explicit legality/conversion targets supports a staged compiler architecture rather than a monolithic translation jump.
- independent effect-typed agent-language research: keeping requested/handled/denied/committed action states explicit is a plausible typed design pattern, but not FRANK-specific proof.

No external source is promoted into FRANK-specific evidence.

## Goodman anti-echo

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

- `FRANK-CC-AUTHORITY-BOUNDARY`: `REFINED` — external typed interface boundaries help lowering but do not confer runtime authority.
- `FRANK-MVC-STATE-EXPRESSIBILITY`: moved from `UNRESOLVED` to `REFINED` after `EXP-CC-G9-UM-RETINA-GATE-001`; narrow fused gate logic is executable without new primitives, while full versioned learner/replay behavior remains open.

Shared FRANK/ClayCode ancestry was collapsed and was not counted as independent replication.

## Hypotheses / counterhypotheses

1. `H-CC-PARSER-ALIGN-001` — `SUPPORTED_FOR_GRAMMAR_DEFECT/PATCH_CANDIDATE_ONLY`. Falsifier: a parser generated directly from published EBNF accepts all cited CURRENT forms without extension or normalization.
2. `H-CC-WASI-COMPONENT-001` — `OPEN`. Falsifier: real APP lowerings show semantic gaps, excessive adapter complexity, or material cost/latency reversal.
3. `H-CC-FUSED-GATE-SUFFICIENCY-001` — `OPEN_REFINED_BY_EXECUTABLE_PROXY`. Falsifier: the real frozen Retina/Unified-Memory component cannot type/check/lower/replay without opaque host-only state or a semantic escape hatch.

## Negative results

- `NR-CC-G9-GRAMMAR-SELFALIGN-001`: published grammar is not aligned with admitted CURRENT source for at least union types and conditionals.
- `NR-CC-G9-MINIMAL-PATCH-SUFFICIENCY-002`: adding only `if` plus union support does not close the CURRENT surface.
- `NR-CC-NEW-PRIMITIVE-FUSED-GATES-003`: tested fused FRANK gate logic produced no language inadequacy that would justify a new dedicated primitive.

Surface/parser closure is defective while tested semantic expressibility remains adequate; these are different layers and are preserved separately.

## Tool/capability evidence

See `TOOL_EXECUTION_MANIFEST.json`.

- GitHub connector: verified read/write in this session.
- local ChatGPT Python sandbox: used for executable grammar and gate probes.
- E2B: current registry status is `ADAPTER_READY_CREDENTIAL_UNAVAILABLE`, and E2B is not exposed directly to this worker surface. No credential workaround was attempted.
- Judge0: repository registry marks it `RUNTIME_VERIFIED`, but it is not directly exposed to this worker surface and was not invoked because the protocol-allowed local fallback had already produced the required executable evidence.
- official `research_interconnect_preflight.py`: blocked because this worker has connector reads/writes but no repository checkout on its local execution surface.

Therefore the **official interconnect completion gate remains incomplete**. The run uses a fail-closed manual manifest from verified GitHub files and does not pretend the preflight passed.

## Release/workspace implication

- Keep `CC-WP-02-PARSER-CANON` open.
- Keep all application acceptance rows unpassed.
- Do not promote the minimal grammar patch to CURRENT.
- Freeze one strict BASE surface and typed AST policy.
- Run the real repository parser over the complete admitted G9 V3 corpus and require parse/roundtrip/mutation/semantic-hash stability.
- Then compile a real Unified-Memory <-> Retina adaptive component through parser -> typed IR -> type/effect -> lowering -> runtime, including versioning, open-set/conflict, candidate promotion/rejection, rollback/replay, publication/crash semantics and resource budgets.
- Reopen semantics only on executable inadequacy.

## Durable research delta

Committed by this run:

- grammar self-alignment negative result;
- minimal grammar repair candidate;
- executable parser proxy receipt;
- adversarial falsification of minimal-patch sufficiency;
- OPEN WIT/Component-Model FFI hypothesis;
- executable G9-compatible Unified-Memory/Retina gate probe with 8/8 fixtures;
- refined Goodman verdict for adaptive-visual expressibility;
- updated hypothesis matrix;
- concurrent FRANK architecture-lineage assimilation;
- updated fail-closed interconnect/tool manifests;
- no semantic/current-stack/BASE promotion.

## Final synthesis

**Do not redesign ClayCode now.** The tested FRANK fused learning/publication controls already fit the existing semantic basis. The release blocker exposed by this trigger is implementation-contract closure: one strict parser surface, typed AST/canonical IR, then a real compiler/runtime path over the full CURRENT corpus and the first real Retina/Unified-Memory component.
