# ClayCode Trigger Run — FINAL REPORT

Run: `20260809_chatgpt_secondary_surface_canon_wasi03_v1`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **none** — run-local research delta only

## Executive result

The highest-value finding is not a new ClayCode primitive. It is a release-blocking implementation inconsistency plus a validated canonicalization invariant.

1. **Current G9 V3 source and current `grammar.ebnf` are not a self-consistent executable surface pair.** G9 V3 contains relational `>`/`<`, `POS|NEG` field syntax, digit-leading `4B_emits`, and an `if` statement not admitted by the current grammar. This is evidence for surface/parser drift, not by itself evidence that the semantic IR must be redesigned.
2. **Type-directed canonicalization is required.** In a 20,000-case local mutation experiment, set reorder/duplication preserved execution and the type-aware semantic hash; ordered-operation swaps changed execution in every tested case. A deliberately over-normalizing canonicalizer generated semantic-hash collisions in all 20,000 ordered-swap cases.
3. **The existing `semantic_hash` vs `contract_hash` separation survives.** Semantic identity should normalize only fields whose static type declares unordered/set semantics. Exact provenance/contract-instance identity remains separate. Ordered/weighted/effect sequences must not be normalized as sets.
4. **WASI 0.3 + the WebAssembly Component Model is a strong first experimental lowering/ABI candidate, not yet a promoted backend.** Current official specifications provide typed component interfaces/resources and stable native async in WASI 0.3. This fits APP-01/02/04 testing and a host-mediated capability boundary, but must be measured against a native lowering before selection.
5. **No dedicated adaptive-visual-learner syntax is justified yet.** Current general records, provenance/version state, Delta, transaction/effect and rollback constructs appear sufficient to represent the FRANK v0.1 Micro Visual Classifier contract. A new primitive requires an H1/executable counterexample.
6. **GWT/Hyperposition/Emergence readouts should initially be typed schema/library values, not new core syntax.** Their required distinctions and intervention receipts can be tested through the ordinary typed IR first.

## Canonical and program grounding

T0 verified RAE-8.8 canonical revision 2 and matching state hash before and immediately before durable write. Current program state reports L0 archive assimilation PASS and `BASE_CLAYCODE_RELEASE` IN_PROGRESS. The ClayCode release workspace still has all 14 work packages OPEN and no application acceptance proof marked passed.

The program's fixed implementation rule therefore dominates this run:

`preserve semantics -> freeze -> compile/lower -> execute -> test -> change language only for a concrete executable counterexample`

## Interconnect / branch findings

All nine registered peer branches were represented in the run's active assembly. Deep inputs were loaded for ClayGraph and UnifiedDB as required.

### FRANK / Harness

The expected current `FRANK_ARCHITECTURE.claycode.json` artifact was not located at the expected path or by connector search; the run records this absence instead of fabricating it. Current `frankv0.1` H1 baseline and owner-fixed adaptive visual learner directive were used as provisional executable requirements.

Implication: H1 remains the decisive downstream semantic oracle. If frozen H1 behavior cannot be represented in released ClayCode without an opaque semantic escape hatch, BASE must reopen.

### ClayGraph

Current graph schemas preserve graph epochs, authority/admissibility, activation, assemblies, selection/projection receipts and higher-order relations. Hyperrelation members carry typed roles and optional ordinal. This independently pressures ClayCode to preserve role/order distinctions rather than flatten every relation into an unordered set. Graph activation remains relevance state, not truth or effect authority.

### UnifiedDB

Current UnifiedDB represents state epochs, semantic transactions, ordered transaction operations (`op_no`), records, query receipts, snapshots and provenance. This reinforces two BASE requirements:

- deterministic state/replay identity;
- ordered transaction semantics must survive parsing, canonicalization and lowering.

Logical semantic unification still does not imply physical store monolith.

### GWT / Hyperposition / Emergenz

Current contracts require typed, epoch-bound measurement and intervention receipts, including delivery/reconstruction/use/outcome/re-entry distinctions and higher-order topology/coupling interventions. The smaller BASE hypothesis is to encode these as ordinary typed data/APIs and prove replayability before adding special syntax.

## Fusion 1

The admitted G9 V3 semantic candidate already contains most of the conceptual material demanded by the current stage: typed records, Set/Ordered distinction, Delta, provenance, capability-bearing effects, state/graph deltas, GWT axes, EffectIntent, bounded rewrite search, reader/context records and explicit invariants.

The first implementation risk is therefore not concept scarcity. It is that the admitted surface grammar cannot parse some constructs used by the admitted specification, preventing a deterministic parser/canonicalizer freeze.

## Executable experiment

Experiment: `CC-LOCAL-20260809-TYPED-CANON-01`

Fresh E2B execution was not possible from the current ChatGPT tool surface even though repository capability state records E2B as runtime-verified. The run therefore used the allowed local sandbox fallback and does not claim fresh E2B evidence.

### Surface-conformance counterexamples

Current G9 V3 constructs not admitted by current grammar:

- relational `>`;
- relational `<`;
- record field union `POS|NEG`;
- digit-leading identifier `4B_emits`;
- `if` statement inside the main cycle.

### Canonicalization fuzz

Seed: `20260809`  
Cases: `20,000`

Type-aware canonicalizer:

- set-field reorder/duplicate semantic hash preserved: `20,000 / 20,000`;
- set-field reorder/duplicate execution preserved: `20,000 / 20,000`;
- ordered operation swap changed execution: `20,000 / 20,000`;
- ordered operation swap changed good semantic hash: `20,000 / 20,000`.

Deliberately bad global over-normalizer:

- semantic-hash collision despite changed ordered execution: `20,000 / 20,000`.

Example:

`[set y 2, set y 3, inc y -1] -> y=2`

Swapping the first two operations gives `y=1`. A global sequence-sorting hash merged them; the type-aware hash did not.

This produces negative result `N-CC-20260809-01` and supports the current two-identity direction.

## External research

Primary/authoritative external documentation was used to test implementation hypotheses rather than search for vocabulary agreement.

### WebAssembly Component Model / WIT

WIT is an interface-description layer for component imports/exports and resources, not a general programming language or a grant of ambient authority. This supports using WIT as an ABI boundary beneath ClayCode rather than replacing ClayCode semantics with WIT syntax.

### WASI 0.3

Current official WASI documentation reports WASI 0.3 stable with native async constructs integrated through the Component Model/Canonical ABI and current Wasmtime support. That materially improves the case for testing ClayCode APP-04 concurrency and HTTP/component adapters on WASI 0.3 rather than assuming an older 0.2-only backend.

This remains `OPEN_EXTERNAL_SUPPORT`: target-runtime ClayCode measurements have not yet been executed.

### Deterministic external encodings

RFC 8785 canonical JSON preserves array element order while canonicalizing object representation. Deterministic CBOR likewise distinguishes deterministic encoding rules from application-level semantic equivalence. These are compatible with the run's finding that Clay semantic canonicalization must be type-aware rather than recursively reorder every sequence.

### MLIR analogue

MLIR's dialect-conversion model is an implementation analogue for staged Clay semantic IR -> target dialect/lowering conversion with explicit conversion rules. This supports, but does not mandate, keeping the stable Clay semantic IR above backend-specific lowering dialects.

## Goodman anti-echo result

Three FRANK-derived assumptions were reviewed with ancestry collapse and counterhypotheses.

1. **Model intent != execution authority** — `SUPPORTED` by independent component/host interface architecture. Clay keeps explicit capability/effect gateway semantics; WIT/FFI resource handles are not authority by naming alone.
2. **Explicit deterministic state/replay/order identity** — `REFINED`: identity is required but canonicalization must be type-directed. Ordered sequences remain ordered; set-like fields may normalize.
3. **Adaptive learner must be expressible in ClayCode** — `REFINED`: the requirement stands, but current evidence favors representing it through ordinary general-purpose typed state/runtime constructs rather than inventing learner-specific syntax.

## Fusion 2 / contradiction map

### Survives

- external effect authority boundary;
- `semantic_hash` distinct from exact provenance-bound `contract_hash`;
- Set vs Ordered distinction;
- graph activation != truth;
- logical UnifiedDB identity != mandatory physical database merge;
- current BASE directive: less semantic change, more compiler/runtime implementation.

### Challenged / narrowed

- the current G9 V3 source + current grammar cannot yet be treated as a frozen executable surface pair;
- a generic global sorting canonicalizer is directly refuted for ordered semantics;
- WASI should not be pinned as canonical backend until matched executable application proofs exist;
- FRANK adaptive learning does not currently justify dedicated language syntax.

### Missing evidence

- complete authoritative parser roundtrip over the current admitted ClayCode corpus;
- full typed IR/type/effect checker integration;
- native vs WASI 0.3 matched lowering results;
- APP-01..10 execution receipts;
- frozen H1 FRANK component compiled through ClayCode;
- live Qwen-class 4B ClayCode reader/working-language measurements.

## Architecture / release delta

Recommended BASE ordering from this run:

1. **CC-WP-01 + CC-WP-02 together:** reconcile/freeze one executable surface and grammar, then parse/canonicalize the entire admitted G9 V3 + dialect corpus.
2. **CC-WP-03:** freeze typed collection semantics and semantic identity rules; carry Set/Map/Ordered distinctions into canonical IR.
3. **CC-WP-04:** implement type/effect/authority diagnostics, keeping expressibility separate from effect authority.
4. **CC-WP-05/06:** reference evaluator plus lowering; test WASI 0.3 as a first component backend against at least one native lowering.
5. **CC-WP-07/08/09:** runtime ABI/FFI, resource identity, stdlib and async/error/memory semantics.
6. **CC-WP-10:** execute APP suite; start with CLI, HTTP website and concurrent service to discriminate backend feasibility early.
7. Add two cross-domain conformance fixtures before semantic expansion:
   - adaptive Micro Visual Classifier state/update/promotion/rollback fixture;
   - WorkspaceEpisode + GWT/Hyperposition/Emergence readout/intervention fixture.

Surface repair should prefer normalization over new semantics where possible. Examples to test:

- relational operators may be admitted explicitly or normalized to calls such as `gt()/lt()`;
- `4B_emits` should become a grammar-valid identifier unless quoted-symbol identifiers are independently justified;
- `POS|NEG` should preferably lower through a named type/enumeration until union-type semantics are formally frozen;
- general-purpose conditional control flow is genuinely required, but integrate the already evidenced universal core rather than inventing multiple competing condition syntaxes.

## Hypotheses generated

- `H-CC-20260809-01`: BASE blocker is surface/grammar drift, not semantic-core insufficiency — supported run-local.
- `H-CC-20260809-02`: semantic canonicalization must be type-directed — supported run-local.
- `H-CC-20260809-03`: WASI 0.3/Component Model is a strong first backend candidate — open, externally supported.
- `H-CC-20260809-04`: adaptive visual learner needs no dedicated core primitive — open.
- `H-CC-20260809-05`: GWT/Hyperposition/Emergence readouts can begin as typed library/schema structures — open.

## Negative results

- `N-CC-20260809-01`: global order-insensitive sequence canonicalization is refuted by the bounded experiment.
- `N-CC-20260809-02`: current G9 V3 source and current grammar are not presently a self-consistent executable surface pair.

## Current-stage impact

This run does **not** close a ClayCode work package and does not change `GENERAL_PURPOSE_GATE = NOT_PASS`. It does reduce uncertainty about what should happen first:

**Do not spend the next BASE cycle inventing more ClayCode concepts. Reconcile the admitted surface, implement the parser/canonicalizer with type-directed identity, then force the existing semantics through real evaluator/lowering/application proofs.**

No canonical claim promotion is requested from this run alone.
