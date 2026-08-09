# ClayCode Trigger Run — Parser Alignment + Fused FRANK Gate Representability / BASE Compiler Gate

Run: `claycode_20260809T1539p0700_chatgpt_secondary_parser_alignment`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (IN_PROGRESS)

## Executive result

This run produced two complementary results.

First, it found and executed a concrete current-language tooling counterexample: admitted G9 V3 source uses constructs that admitted `grammar.ebnf` does not cover. The initial executable proxy demonstrated missing type-level unions and an explicit `if` statement. A minimal grammar repair accepts those two cases while preserving a baseline `Delta<T>` record, but an adversarial extension then showed that the minimal repair is **not sufficient**: other exact CURRENT-G9 forms (`external_effect lifecycle=...`, digit-prefixed `4B_...` symbols and the `includes` relation word) remain rejected. Therefore the BASE parser task needs a strict surface/AST freeze plus full-current-corpus conformance, not incremental keyword accretion.

Second, after a concurrent FRANK architecture-lineage Fusion materialized the fused C9+overlay target, this run compiled a focused Unified-Memory/Retina gate probe using only a grammar-compatible G9 subset. It represented independent RecognitionValidity, AdaptiveStatePromotion and semantic-publication gates, lowered the rules to a deterministic Python CLI and matched **8/8** positive/veto fixtures with exit status 0 and empty stderr. This is executable evidence that the tested fused gate logic does **not** require a new dedicated ClayCode primitive. It is not a production compiler or APP acceptance result.

No CURRENT-stack, BASE-stage or canonical scientific promotion is requested.

## Evidence

### Parser self-alignment

- Current source: `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- Current grammar: `research_entity/claycode/g9/grammar.ebnf`
- Initial executable receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`
- Candidate grammar repair: `CLAYCODE_G9_GRAMMAR_PATCH_CANDIDATE.ebnf`
- Probe: `grammar_probe.py`
- Adversarial follow-up: `GRAMMAR_ADVERSARIAL_EXTENSION_RECEIPT.json`

Initial proxy result:

```text
old
  union_field: FAIL
  if_cycle: FAIL
  baseline: PASS
repaired
  union_field: PASS
  if_cycle: PASS
  baseline: PASS
```

Adversarial minimal-repair result:

```text
external_effect_lifecycle: current FAIL / minimal_repair FAIL
4B_emits:                  current FAIL / minimal_repair FAIL
includes operator:         current FAIL / minimal_repair FAIL
```

Evidence boundary: these are executable Lark translations/probes of the published EBNF, not the final repository parser. They prove concrete surface-closure gaps and falsify sufficiency of the two-feature minimal patch; they do not enumerate every full-file defect.

### Unified Memory <-> Retina fused gate probe

Artifacts:

- ClayCode source: `UM_RETINA_GATE_PROBE.clay`
- generated target: `generated_um_retina_gate_cli.py`
- receipt: `EXECUTABLE_RESEARCH_RECEIPT_UM_RETINA_GATE.json`
- Clay source SHA-256: `533cd82763ccb7db39ea687d00632112ed63f2f1d99fd00cacb096bfff1d9a7c`
- generated target SHA-256: `24d82e7649394ec051b083af812202aec0ae4147b2ce06e42a5491c224574674`

Executed fixture classes:

1. all gates pass;
2. open-set/unknown veto;
3. stale-calibration veto;
4. sensor/conflict veto;
5. untrusted/BRONZE-like promotion veto;
6. candidate-evaluation veto;
7. incomplete projection/retraction closure veto;
8. replay-not-ready publication veto.

Observed: `8/8 MATCH`, all exit statuses `0`, stderr empty.

Interpretation: the three control surfaces can be expressed separately using existing generic typed records/type aliases/rules in the tested subset. Recognition truth, durable learning promotion and CURRENT publication therefore remain distinct without a new language primitive.

Limitations: the probe does not execute real Retina features, classifier training, resource budgets, UnifiedDB transactions, ClayGraph projection, target-machine effects or a full rollback state machine. It does not qualify APP-01, APP-09 or any BASE work package as PASS.

## Concurrent FRANK architecture assimilation

During the run, `fusion-20260809T1538p0700-frank-architecture-lineage` materialized the full historical FRANK architecture lineage and an OPEN fused target overlay. The target keeps C9 typed causal/admission/effect architecture as the latest explicit base and adds mandatory current overlays including dissolved Retina, Unified Memory <-> Retina recurrent learning, two separate learning/recognition gates, atomic semantic publication and common-driver-aware causal receipts.

This newer material was re-read before final synthesis and added to `INTERCONNECT_MANIFEST.json`. It is research input, not canonical promotion.

The ClayCode result is compatible with that fusion: current fused gate requirements are representable in the tested existing G9 subset, while the production parser surface remains the immediate toolchain blocker.

## Cross-branch fusion

- **FRANK:** preserve RecognitionValidity separately from AdaptiveStatePromotion; current sensor evidence retains veto over memory/familiarity. No dedicated new language primitive is justified by the gate probe.
- **Clay/Harness:** BASE should freeze/parser-normalize one strict surface and compile the real fused component before H1/H2; do not simplify H1 semantics to fit an incomplete parser.
- **ClayGraph:** `projection_closed` is representable as a publication condition, but PATCH versus COMPLETE_SNAPSHOT/retraction semantics still require the stronger runtime/IR contract and crash/replay tests from prior research.
- **UnifiedDB:** source admission, schema preflight and atomic publication can be represented as typed conditions; physical DB consolidation is not implied.
- **GWT:** recognition/promotion/publication signals are control/readout state, not truth or causal-emergence evidence.
- **Hyperposition:** UNKNOWN/AMBIGUOUS/CONFLICT alternatives remain explicit rather than being collapsed into familiar certainty.
- **Emergenz:** neither parser success nor gate execution is evidence of emergence; later causal claims still require intervention/lesion/rescue controls.
- **ClayCode:** parser/canonical-IR closure is now the immediate BASE engineering discriminator; semantic growth remains evidence-gated.

## External triangulation

Primary technical sources were used as triangulation only:

- Bytecode Alliance WIT/Component Model provides a typed interface/world/resource boundary that is a plausible future FFI lowering surface, but does not replace Clay dynamic capability/commit authorization.
- MLIR dialect-conversion documentation supports the implementation pattern of progressive typed lowering with explicit legality/conversion targets rather than one monolithic compiler jump.
- independent effect-typed agent-language research provides conceptual support for keeping requested/handled/denied/committed action states explicit; it is not proof of FRANK or ClayCode semantics.

No external source is promoted into FRANK-specific proof.

## Hypotheses / counterhypotheses

1. `H-CC-PARSER-ALIGN-001` — **SUPPORTED_FOR_DEFECT / PATCH-CANDIDATE ONLY**. Current grammar/source mismatch is executable. Counterhypothesis: proxy translation artifact. Falsifier: a parser generated directly from the published EBNF accepts all cited CURRENT forms without extension or normalization.
2. `H-CC-WASI-COMPONENT-001` — **OPEN**. WIT/Component Model is a candidate typed FFI lowering target. Falsifier: executable APP lowerings show semantic gaps, excessive adapter complexity or material cost/latency reversal.
3. `H-CC-FUSED-GATE-SUFFICIENCY-001` — **OPEN_REFINED_BY_EXECUTABLE_PROXY**. Existing generic G9 constructs are sufficient for the tested fused RecognitionValidity/AdaptiveStatePromotion/publication logic. Falsifier: the real frozen Retina/Unified-Memory component cannot type/check/lower/replay without opaque host-only state or a semantic escape hatch.

## Goodman anti-echo

`FRANK_CLAYCODE_GOODMAN_REVIEW.json` was updated after the executable gate test.

- Authority/host-boundary claim remains `REFINED`: typed external interfaces are useful lowerings but do not confer execution authority.
- Adaptive-visual expressibility moved from `UNRESOLVED` to `REFINED`: the narrow three-gate logic is executable with existing G9-compatible constructs; full versioned learning/replay behavior remains open until a real component executes.

Shared FRANK/ClayCode ancestry was not counted as independent replication. The new local execution is recorded as a new discriminating experiment with its own limitations.

## Negative results

- `NR-CC-G9-GRAMMAR-SELFALIGN-001`: admitted current grammar is not self-aligned with admitted current source for at least union types and conditionals.
- `NR-CC-G9-MINIMAL-PATCH-SUFFICIENCY-002`: adding only `if` plus type-union grammar is insufficient; other exact CURRENT-G9 forms remain rejected.
- `NR-CC-NEW-PRIMITIVE-FUSED-GATES-003`: the tested fused FRANK gate logic produced no language inadequacy that would justify a dedicated new primitive.

These negative results concern different layers: surface/parser closure is defective; tested semantic expressibility remains adequate.

## Release/workspace implication

- Do **not** mark `CC-WP-02-PARSER-CANON` complete.
- Do **not** mark any application acceptance item PASS from this run.
- Do **not** promote the minimal grammar patch directly to CURRENT.
- Freeze one strict BASE surface and typed AST policy, explicitly deciding which existing prose-like forms are normalized sugar versus retained grammar.
- Run a real repository parser over the complete admitted G9 V3 corpus; require parse/roundtrip/mutation/semantic-hash stability.
- Then compile the real Unified-Memory <-> Retina adaptive component through parser -> typed IR -> type/effect -> lowering -> runtime and test versioning, open-set/conflict, promotion/rejection, rollback/replay, publication/crash semantics and resource budgets.
- Reopen ClayCode semantics only if that real component produces an executable inadequacy.

## Protocol limitations

The official `research_interconnect_preflight.py` could not be executed because this ChatGPT organ has GitHub connector access but no repository checkout exposed to its execution surface. A fail-closed manual interconnect manifest was materialized from verified GitHub files and updated for concurrent FRANK lineage work. Therefore the **official interconnect completion gate remains incomplete** and is not claimed as PASS.

E2B is repository-marked `RUNTIME_VERIFIED` but is not exposed as a tool in this session. The protocol fallback used the local Python sandbox and records the evidence class explicitly.

## Research delta

Durable run delta now includes:

- grammar self-alignment negative result;
- minimal grammar repair candidate;
- executable parser proxy receipt;
- adversarial falsification of minimal-patch sufficiency;
- OPEN WIT/Component-Model FFI hypothesis;
- executable G9-compatible Unified-Memory/Retina three-gate probe with 8/8 fixtures;
- refined Goodman verdict for adaptive-visual expressibility;
- updated hypothesis matrix;
- concurrent FRANK architecture-lineage assimilation;
- cross-branch fail-closed manifest and tool manifest;
- no semantic/current-stack/BASE promotion.

## Final synthesis

The highest-information result is a separation of two questions that had been easy to conflate:

1. **Can current ClayCode semantics express the fused FRANK learning/publication control logic?** For the tested gate subset, yes.
2. **Can the published current ClayCode surface/grammar already serve as the BASE production parser contract?** No; executable self-conformance counterexamples remain, and the first minimal repair is incomplete.

Therefore BASE should not redesign the cognitive language now. It should freeze and implement the compiler surface rigorously, then let the first real Retina/Unified-Memory component decide whether any semantic primitive is actually missing.
