# ClayCode Trigger Run — G9 admitted-source self-conformance boundary

Run: `claycode-20260809T1657p0700-g9-self-conformance`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**  
Gate advancement: **NONE**

## Executive result

The prior run correctly found that G9 V3 uses comparison operators and `if` absent from its admitted EBNF. This run tested whether that minimal repair is sufficient.

It is not.

A deterministic local Lark probe over current G9 V3 plus the dialect registry found:

- current grammar: **34/58** sampled `rule` declarations parse;
- previous comparison repair: **38/58** parse;
- **20/58 still fail** after that repair;
- bounded normalization into the existing call/operator expression shape reaches **58/58 parser-shape coverage**;
- current interface declarations: **6/9** parse; three fail at typed method signatures;
- `outcome=verify(receipt? or residual)` is not admitted by the current expression grammar;
- eager versus lazy fallback is observably different;
- the flat expression grammar has no explicit precedence/associativity contract: `1+2*3` yields 9 under flat left fold and 7 under multiplication precedence.

During this run a concurrent ClayCode worker completed a distinct typed Relation-IR oracle. Its bounded result is compatible with the present direction: three safe source-surface families lower to identical typed Relation IR semantic hashes, while semantic equivalence does not by itself choose the preferred surface syntax.

The combined result supports **less change, more compile**:

1. normalize prose-like rules into explicit calls/operators where typed Relation-IR equivalence can be proven;
2. do not grow an arbitrary word-operator grammar merely to accept prose;
3. add only counterexample-justified missing compiler contracts: typed method signatures, precedence/associativity, and explicit fallback/control evaluation semantics;
4. define an admitted BASE compilation-unit boundary so RESEARCH_CANDIDATE `.clay` artifacts do not silently enlarge the executable language.

No canonical G9 file is changed by this run.

## Current-state grounding

Verified current canonical state at boot: RAE-8.8, r2, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.

Current program stage remains `BASE_CLAYCODE_RELEASE`. The general-purpose gate remains `NOT_PASS`. The current acceptance law is preserve semantics -> freeze -> compile/lower -> execute -> test -> change language only when a real counterexample forces it.

The latest completed FRANK architecture-lineage fusion keeps BASE as the immediate bottleneck and requires typed multi-rate state, epochs, causal/GWT receipts, replay/recovery and explicit effect-authority separation. Current loop-of-loops feedback is retained as test-driver ancestry, not independent evidence for special syntax.

## Interconnected branch findings

### ClayGraph

Current ClayGraph requires epoch-bound versioned nodes/edges, typed hyperrelation members, projection receipts, selection receipts, receiver delivery/reconstruction/use/effect/outcome/reentry receipts, and invalidation state.

No new graph primitive is justified here. The next test is executable compilation of a projection/selection/receiver receipt fixture through the real ClayCode pipeline.

### UnifiedDB

Current UnifiedDB requires state epochs, semantic transactions with idempotency/base epoch/authority scope, semantic records with epistemic/source identity, query receipts, revisioned dynamic work, freshness-bounded capability observations and execution truth classes.

No new database primitive is justified here. The next test is executable compilation/replay of a semantic transaction and snapshot/replay fixture.

### Harness

Current H-WP-02 local evidence already demonstrates deterministic semantic hashes, stale-CAS rejection, idempotent replay, explicit UNKNOWN/CONFLICT/REVOKED preservation, snapshot equivalence and tamper checks after an initial ordering defect was repaired. This remains synthetic/local evidence and does not pass H1.

## Executable research

Durable receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`.

The executed local probe is identified by SHA-256:

`09d07c4114bab0c2fabfb8596edce397e511c9580aee3307aa0890f438883fe2`

Its result digest is:

`218b2ec7dfba7fb6d8f193d91574bc4bbd620d27fedb4380473a9bb125f2f7bf`

Execution used hosted Linux/Python because E2B and Andreas' Ubuntu developer host were not exposed to this worker.

### Rule corpus

58 current rule declarations from G9 V3 plus the dialect registry were tested.

Results:
- original grammar: 34 pass / 24 fail;
- prior minimal relational repair: 38 pass / 20 fail;
- bounded normalization candidate + relational repair: 58 pass / 0 fail.

The residual failures cluster around prose-like pseudo-infix relation words (`never_implies`, `may_reference`, `distinct_from`, `owns`, `includes`, etc.) and digit-leading names such as `4B_*`.

The concurrent typed Relation-IR oracle materially sharpens the interpretation: surface syntax should be judged against typed semantic identity, not by parser acceptance alone. Full G9 source -> parser -> AST -> typed Relation IR ancestry is still required before any source normalization is promoted.

### Typed interface signatures

Of 9 current interfaces, three fail at typed method signatures:

- `projection(reader:ReaderId)->Ref`
- `verify(receipt:ReceiptRef)->Verification`
- `delta(input:Delta)->Delta`

This is a concrete current-source counterexample. A minimal typed method/function-signature declaration is justified for investigation; treating these as fields/actions is not an adequate compiler contract.

### Optional/fallback evaluation

G9 contains `receipt? or residual`, while `?` is currently defined in type syntax rather than as a value-level fallback/try operator.

The local probe shows why semantics cannot be guessed:
- lazy fallback with a present receipt does not evaluate the fallback;
- eager fallback with a present receipt does evaluate it.

For effectful code this is observable. Use explicit control flow or an explicitly specified lazy fallback form; do not silently assign semantics to the existing text.

### Precedence / associativity

The admitted EBNF uses a flat `primary { operator primary }` expression shape without a frozen precedence table. General-purpose compilation therefore lacks a unique semantic parse unless the canonicalizer supplies one.

The local 9-vs-7 arithmetic probe demonstrates observable divergence, and current G9 already combines comparisons with boolean operators.

## Research-candidate compilation boundary

The current stack also references `CLAYCODE_G9_DYNAMIC_BINDING_LATTICE_CANDIDATE.clay`, explicitly marked `RESEARCH_CANDIDATE`. It uses declaration forms such as `projection`, `experiment`, `hypothesis`, `counterhypothesis`, and `falsifier` absent from the G9 EBNF.

This should not automatically expand the BASE grammar. A compiler-facing admitted-unit/dialect registry is required: research syntax may remain machine-readable without becoming executable BASE syntax until explicitly admitted.

## Goodman anti-echo

FRANK loop requirements are **REFINED**: keep LoopDynamicsReadout as a BASE/H2 fixture, but no recurrence-specific language primitive is justified.

Effect-authority separation is also **REFINED**: external authority remains separate, while compiler evaluation order must become explicit because eager fallback may execute work a lazy fallback would not.

The concurrent Relation-IR worker is recorded as a distinct executable test with shared project ancestry, not as an independent popularity vote.

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## New claim state

New hypotheses are in `HYPOTHESIS_MATRIX.json`.

New negative results:
- `NR-CC-20260809-MINIMAL-REPAIR-INCOMPLETE`
- `NR-CC-20260809-OPTIONAL-FALLBACK-UNDEFINED`
- `NR-CC-20260809-PRECEDENCE-UNSPECIFIED`

They extend rather than erase the earlier G9 self-conformance negative result.

## BASE delta

### Justified next implementation sequence

1. Freeze the admitted BASE compilation unit: current G9 V3 + admitted dialect registry first.
2. Use typed `RelationId` / typed Relation IR as the semantic comparator for surface normalization.
3. Add/freeze the minimal typed interface method/function signature required by current source.
4. Freeze operator precedence/associativity and longest-match lexing before semantic hashing.
5. Replace ambiguous optional fallback with explicit control flow or an explicitly lazy typed special form.
6. Build the real parser -> AST -> typed canonical IR -> semantic hash -> type/effect pipeline.
7. Make G9 V3 + dialect registry mandatory self-conformance fixtures.
8. Compile LoopDynamicsReadout, one ClayGraph receipt fixture and one UnifiedDB transaction/replay fixture.
9. Then continue native-vs-WASI Ubuntu application exemplars and APP-01..APP-10.

### Not justified

- no broad word-operator ecology;
- no FRANK-specific relation syntax;
- no new GWT/Hyperposition/Emergenz primitive;
- no new ClayGraph primitive;
- no new UnifiedDB primitive;
- no canonical promotion;
- no BASE gate advancement.

## External research class

Official language/parser documentation was used as independent engineering analogy for explicit operator precedence/lexing and explicit optional/fallback evaluation behavior. It does not determine ClayCode design by authority.

## Limitations

- hosted Linux, not target Ubuntu;
- no E2B surface exposed;
- no native/WASM backend execution;
- no full canonical IR implementation in this worker;
- full semantic preservation of 58-rule normalization is therefore not yet proven;
- repo-local interconnect/Goodman scripts were not executable from this surface; equivalent artifacts were produced, but script execution is not claimed.

## Required next discriminating test

On the Ubuntu target:

`G9 V3 + dialect registry -> real parser -> explicit precedence -> typed interface signatures -> AST -> typed Relation IR/canonical IR -> semantic hash -> type/effect -> executable fixtures`

Required fixtures:
1. LoopDynamicsReadout/control;
2. ClayGraph projection/selection/receiver receipt;
3. UnifiedDB semantic transaction + replay;
4. effectful fallback mutant proving no hidden eager execution.

If normalization changes typed relation identity, semantic hash or observable behavior, preserve the counterexample and reopen only the smallest required language change. Otherwise freeze the normalized executable surface and continue compiler/runtime implementation.

## Provenance

Origin actor: `chatgpt-secondary`  
Provider/model: OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Executable evidence: local synthetic compiler research + fused distinct sibling Relation-IR oracle  
Canonical promotion: none  
Stage advancement: none
