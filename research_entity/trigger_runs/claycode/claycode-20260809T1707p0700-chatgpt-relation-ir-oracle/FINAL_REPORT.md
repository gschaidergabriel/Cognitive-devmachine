# ClayCode Trigger Run — Typed Relation IR Oracle

Run: `claycode-20260809T1707p0700-chatgpt-relation-ir-oracle`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## Executive result

This run does not redesign ClayCode and does not repeat the already-completed 86-chunk surface-closure measurement. It executes the next missing slice of `WORK-CC-BASE-G9-PARSER-FREEZE-001`: a matched typed canonical Relation-IR oracle.

Three live-safe surface families were tested:

- finite declared bare relation words;
- a lexically disjoint compact sigil (`^relation`) as a control against the already-challenged `@relation` form;
- explicit generic `relation("name", lhs, rhs)` calls.

All three lower into the same typed node:

`Relation { relation_id, relation_class, arity, operands, authority=NONE, semantic_version }`

Observed:

- **4/4 semantic equivalence cases:** all three surfaces produced identical canonical IR semantic hashes;
- **3/3 unknown-relation mutations rejected** fail-closed;
- **3/3 surfaces preserved existing `@ref` operands**;
- **3,000/3,000 whitespace variants per surface** preserved the semantic hash;
- local micro proxy mean parse+lower latency: declared bare ~17.31 us, disjoint sigil ~17.44 us, generic call ~25.20 us;
- source bytes for the baseline `depends` form: 11 / 12 / 23 respectively.

The latency/byte results are not release benchmarks. The important result is architectural: **surface spelling can be separated from one deterministic semantic relation identity without letting relation resolution create execution authority.**

## Evidence boundary

Evidence class is `LOCAL_EXECUTABLE_PROXY` on Linux/Python/Lark. It is **not**:

- the full 86-chunk N/S/D corpus benchmark;
- the production BASE parser;
- an Ubuntu developer-system target receipt;
- an E2B receipt in this session;
- a Qwen-4B reader/repair-cost result;
- a type/effect/compiler/lowering/application-suite PASS.

Therefore `CC-WP-02`, `CC-WP-03`, all other BASE work packages, application acceptance and both ClayCode release gates remain unchanged/open.

## Concurrency assimilation

Before durable synthesis the run assimilated four material same-window findings rather than counting them as independent replication:

1. Whole-current-G9 surface closure: current proxy **61/86 PASS, 25/86 FAIL**; strict normalization candidate N reached **86/86** with four general grammar additions plus 20 explicit source normalizations, but N was not selected.
2. Relation namespace discriminator: current `@relation` collides with existing `@ref` under LALR modes; a disjoint sigil and generic quoted form survived the bounded combined-namespace corpus.
3. Declared relation resolver: finite typed relation admission rejected 50k unknown relation words while preserving sampled readable relation forms.
4. Source-chain integrity correction: manually lowered runtime fixtures cannot count as end-to-end compiler evidence when source->parser->IR->lowering ancestry is broken; `emit` vs `return` was behaviorally material in 17,693/20,000 cases.

The current run therefore labels its own result narrowly as `surface -> parser proxy -> typed Relation IR -> semantic_hash`, not as source-to-execution compiler evidence.

## Fusion 1

The common problem across current parser work is no longer lack of semantic concepts. It is keeping several identities separate and mechanically bound:

- source spelling;
- lexical/parser identity;
- typed semantic relation identity;
- semantic hash;
- authority/effect capability;
- lowering/artifact/execution identity.

The new executable oracle supports a stable semantic center: multiple source projections may lower to one canonical Relation IR, while the eventual surface winner is selected on full-corpus correctness and cost rather than on meaning.

## External triangulation

Primary compiler documentation was used as independent architecture analogy only.

- MLIR explicitly distinguishes identifier classes and supports generic plus custom textual assembly around a stable operation representation.
- Tree-sitter explicitly distinguishes lexical-token conflicts from parse precedence and exposes context-aware lexing/conflict handling.

These sources do not select a ClayCode syntax. They independently support treating lexical presentation, parser ambiguity and internal semantic identity as separable engineering layers.

## Fusion 2 / Goodman anti-echo

The FRANK<->ClayCode loop was ancestry-collapsed.

- External-authority preservation was **REFINED** into a mechanical IR rule: resolving a `RelationId` creates semantic/type identity only; canonical Relation nodes carry `authority=NONE`; capability/effect authority is separate.
- A FRANK-specific relation spelling remains **UNRESOLVED / not justified**. No real FRANK component in this run forces one.
- Full adaptive visual learner sufficiency remains **UNRESOLVED** because this relation experiment is orthogonal to the full learner compile/replay proof.

See `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## Hypotheses

### H-CC-REL-SURFACE-IR-SEPARATION-20260809-01

Status: `OPEN_SUPPORTED_RUN_LOCAL`.

Prediction succeeded in the bounded oracle: intended-equivalent declared-bare, disjoint-sigil and generic-call forms map to identical typed canonical Relation IR/hash.

Falsifier: production full-corpus comparison finds intended-equivalent forms with unequal typed IR/semantic hashes or silent ambiguous admission.

### H-CC-REL-AUTHORITY-SEPARATION-20260809-02

Status: `OPEN_SUPPORTED_RUN_LOCAL`.

Unknown relation names fail closed and no relation surface creates authority in this oracle.

Falsifier: later type/effect/lowering path authorizes an external effect from RelationId alone.

### H-CC-REL-SURFACE-WINNER-20260809-03

Status: `OPEN_UNRESOLVED`.

This run cannot choose the source surface. A generic canonical form plus restricted verified sugar may also remain a valid outcome.

## Negative results

1. `NR-CC-REL-SEMANTIC-HASH-NOT-SURFACE-WINNER-20260809`: semantic equivalence cannot itself choose between the surviving source surfaces because all tested arms satisfy the same typed-IR/hash oracle.
2. `NR-CC-REL-ORACLE-NOT-BASE-PASS-20260809`: a successful relation micro-oracle cannot satisfy a parser/type/compiler/application release work package.

Prior current `@relation` collision evidence remains preserved; this run deliberately uses a lexically disjoint sigil control instead of reviving the challenged form.

## Mesh feedback

- FRANK: no special relation primitive justified; preserve relation/authority separation.
- Clay Research: strengthens `less change, more compile`.
- Harness: bind relation semantic identity into trace/replay while checking capability non-expansion separately.
- ClayGraph: parse text must resolve into typed relation identity before graph mutation/projection; activation remains non-authoritative.
- UnifiedDB: persist relation identity separately from work/capability/execution authority identities.
- GWT: no causal workspace semantic change.
- Hyperposition: canonical identity may be shared across surface projections without collapsing alternatives/conflicts.
- Emergenz: no emergence claim.
- ClayCode: typed Relation IR is strengthened as the common comparator, but no syntax winner is promoted.

## Highest-information next execution

Do not invent another ClayCode generation.

1. Put this typed Relation node into the production-bound canonical IR.
2. Run the **complete admitted G9+dialects corpus** through matched N / declared relation / generic canonical / any compact disjoint-sigil projection.
3. Require intended AST equality and semantic-hash equality where semantics are meant to match.
4. Fail malformed/undeclared relations closed and preserve `@ref` plus all overlapping lexical namespaces.
5. Measure diagnostics, mutation survival, migration edits, token/context cost, Qwen-4B reader/repair cost and parser/compiler complexity/latency.
6. Bind the winning/retained projections into the source-hash -> parser -> AST -> typed-IR -> semantic-hash ancestry chain identified by the source-chain worker.
7. Continue directly into type/effect checking and Ubuntu lowering/application proofs.
8. Only reopen semantics if a real compiled application or FRANK component produces an executable inadequacy.

## Durable artifacts

- `RUN_MANIFEST.json`
- `INTERCONNECT_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `HYPOTHESIS_MATRIX.json`
- `NEGATIVE_RESULTS.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `experiments/relation_canonical_ir_discriminator.py`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- this `FINAL_REPORT.md`

No canonical revision, current G9 source, release workspace state, application PASS or ClayCode semantic authority was changed.
