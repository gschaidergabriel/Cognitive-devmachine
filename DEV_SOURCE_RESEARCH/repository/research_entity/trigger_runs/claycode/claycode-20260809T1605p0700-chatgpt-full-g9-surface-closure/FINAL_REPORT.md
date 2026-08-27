# ClayCode Trigger Run — Whole-Current-G9 Surface Closure

Run: `claycode-20260809T1605p0700-chatgpt-full-g9-surface-closure`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (`IN_PROGRESS`)  
Promotion: **none**

## Executive result

This run adds the first whole-current-G9 top-level surface-closure measurement used by this worker and immediately assimilates the concurrent N/S/D surface-policy work rather than duplicating it.

Fresh executable local-fallback result over the complete current `CLAYCODE_G9_FUSION_SPEC_V3.clay` top-level corpus:

- top-level chunks: **86**;
- current checked-in grammar proxy: **61/86 PASS, 25/86 FAIL**;
- strict canonical-call/qualified-field normalization candidate N: **86/86 PASS**;
- candidate N required only four general core-surface additions (`if`, postfix optional value, comparisons `> < >= <=`, `or`) plus **20 explicit source normalizations**;
- no new cognitive/runtime semantic primitive was required to obtain parse closure in the proxy.

This strengthens the hypothesis that the immediate BASE blocker is predominantly surface/parser closure rather than concept scarcity. It does **not** prove semantic equivalence of the normalizations, complete `CC-WP-02`, or select candidate N.

Concurrent evidence now leaves three live policies:

- **N** — strict source normalization to calls/punctuation/qualified fields;
- **S** — lexically explicit `@relation` / quoted relation plus typed resolution;
- **D** — finite declared bare relation words plus typed resolution.

The current Research Center work item correctly requires a matched N/S/D full-corpus comparison before freezing the relation surface. This run therefore explicitly refuses to promote N merely because it reached 86/86 parse closure.

## Canonical/program grounding

T0 was reverified immediately before durable write:

- RAE-8.8;
- canonical revision 2;
- state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`;
- current stage `BASE_CLAYCODE_RELEASE`;
- all 14 BASE ClayCode work packages remain OPEN and the general-purpose gate remains NOT_PASS.

The stage law remains: preserve existing semantics where adequate, implement parser/canonical IR/type-effect/compiler/lowering/runtime/FFI/stdlib/toolchain, and change language semantics only for an executable inadequacy.

## Inputs and concurrency

Current source under test:

- `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay` blob `1a17bba3c835520baff2ac8fa432749ba2165d8e`;
- `research_entity/claycode/g9/grammar.ebnf` blob `ec2f17077333955cfdabe6c64868d597e7e734e3`.

During this run, concurrent ClayCode work established:

1. strict normalization is viable on representative parser cases;
2. a sigil relation surface is viable on sampled cases and 20k relation fuzz;
3. a finite declared bare-relation resolver rejects unknown relation words while preserving sampled readable forms;
4. `WORK-CC-BASE-G9-PARSER-FREEZE-001` was revised into a matched three-arm N/S/D discriminator.

These concurrent runs share project ancestry and are not counted as independent replication.

## Executable experiment

Artifact: `experiments/full_surface_closure_probe.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`

The probe performs brace-balanced top-level chunking of the complete current G9 V3 source and parses every chunk with a Lark translation of the checked-in EBNF for the exercised constructs.

### Baseline

Observed:

- PASS: **61**;
- FAIL: **25**.

Failure families include:

- missing comparison/control/optional-value surface;
- prose-like relation/operator forms;
- digit-leading/noncanonical spellings;
- method-like forms missing explicit call delimiters.

This strengthens earlier sampled grammar-drift negative results from representative subsets to complete current-G9 top-level coverage under this proxy.

### Candidate N

Candidate core grammar additions:

- `if` statement;
- postfix optional value;
- `>`, `<`, `>=`, `<=`;
- `or`.

Twenty exact prose/noncanonical forms were normalized into explicit existing-style calls, fields or qualified identifiers. Examples include:

- `Delta never_implies epistemic_upgrade` -> `never_implies(Delta,epistemic_upgrade)`;
- `effect.Intent may_reference capability_id` -> `may_reference(effect.Intent,capability_id)`;
- `graph.selection_receipt distinct_from graph.provenance_receipt` -> explicit call;
- `4B_emits EffectIntent` -> grammar-valid qualified call;
- `Needle.owns [...]` -> call;
- `external_effect lifecycle=[...]` -> qualified field assignment;
- `Claude_only consumes latest stack + writes task receipts` -> explicit calls over normalized operand identifiers.

Observed: **86/86 PASS**.

Evidence boundary: this is a parser-surface proxy. It does not prove intended typed AST equality, semantic-hash roundtrip, diagnostics quality, production-parser behavior or model-reader cost.

## Fusion 1 — cross-domain constraints

### FRANK

The fixed FRANK v0.1 adaptive visual learner requires versioned classifier/prototype state, trusted training-example provenance/tier, confidence/open-set state, bounded resource state, promotion/rejection/rollback and deterministic replay hooks. These remain representable as general typed state/effects at the current level of evidence. No learner-specific core syntax follows from this run.

### ClayGraph

Current ClayGraph storage separates logical/version identity, graph/source epochs, activation/salience, provenance, admissibility and authority. A source-surface relation spelling must lower without collapsing these distinctions. Graph activation remains relevance state, not truth or effect authority.

### UnifiedDB

Current UnifiedDB cognitive processor materializes semantic dependencies, cognitive views, invalidations, answer capsules, capability sources, affordances, authority references and stack receipts with explicit source/graph epochs and hashes. This reinforces a typed canonical identity/resolution layer: textual relation recognition or an affordance representation must never mint effect authority.

### GWT / Hyperposition / Emergenz / Harness

The prior branch conclusions survive:

- GWT selection/delivery/use/effect/reentry remain distinct typed/receipt states;
- Hyperposition higher-order identities/conflicts must remain explicit;
- parser/compiler success is not emergence evidence;
- H2 remains blocked on BASE and must reproduce frozen H1 semantics rather than simplify them to fit the parser.

## External research

Independent primary implementation analogues were used only as architecture support, not proof of a ClayCode syntax winner.

- WebAssembly Component Model WIT uses explicit lexical/token and grammar categories for an interface language; this is compatible with treating lexical form as an explicit contract rather than arbitrary prose semantics.
- MLIR provides generic operation form plus dialect-specific/custom assembly formats around shared operation semantics. This is a useful independent analogue for separating a stable canonical/semantic layer from reader-facing surface projections.

These analogues support the separation hypothesis but do not select N, S or D.

## Fusion 2 / Goodman anti-echo

The strongest synthesis after concurrency refresh is narrower than the initial N result:

1. **Surface/grammar closure is a real BASE blocker.**
2. **Candidate N demonstrates full-current-G9 parse closure in the local proxy.**
3. **N is not a winner.** S and D have their own executable support and must be compared on identical corpus/oracle.
4. **Parser acceptance must not mint semantic relation identity or effect authority.** Relation resolution belongs in typed semantic state even if D eventually wins source readability.
5. **The semantic IR can remain independent of the winning source spelling.** This is the most useful architecture hypothesis to carry forward.

Goodman verdicts and counterhypotheses are recorded in `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

## Hypotheses

- `H-CC-FULLSURF-001` — OPEN_SUPPORTED_RUN_LOCAL: immediate blocker is predominantly surface closure, not missing semantic core.
- `H-CC-SURFACE-IR-SEPARATION-002` — OPEN_REFINED: source/dialect presentation should remain separable from deterministic typed canonical IR.
- `H-CC-NSD-FULLCORPUS-003` — OPEN_NEXT_DISCRIMINATOR: N/S/D remain live until matched full-corpus typed-IR tests.

## Negative results

- `N-CC-FULL-G9-GRAMMAR-20260809`: current checked-in grammar proxy fails 25/86 complete current-G9 top-level chunks.
- `N-CC-N-WINNER-NOT-ESTABLISHED-20260809`: N's 86/86 parse closure alone is insufficient to select it over S/D.

## Architecture/program implication

Do not spend the next BASE step inventing another cognitive primitive.

Execute `WORK-CC-BASE-G9-PARSER-FREEZE-001` as already revised:

1. use identical complete G9 V3 + dialect corpus;
2. implement N/S/D against one typed canonical-IR oracle;
3. require malformed/undeclared relations to fail closed;
4. measure parse closure, intended AST, diagnostics, semantic-hash roundtrip, mutation survival, migration edits, source/token/context cost, target-reader repair cost, parser/compiler complexity and latency;
5. select/freeze the surface only after matched evidence;
6. then continue directly into typed IR, type/effect checking, evaluator/lowering and real application proofs.

## Durable writeback

Committed in this run:

- `RUN_MANIFEST.json`;
- `INTERCONNECT_MANIFEST.json`;
- `TOOL_EXECUTION_MANIFEST.json`;
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`;
- `experiments/full_surface_closure_probe.py`;
- `EXECUTABLE_RESEARCH_RECEIPT.json`;
- `HYPOTHESES.json`;
- `NEGATIVE_RESULTS.jsonl`;
- `BRANCH_FEEDBACK_MANIFEST.json`;
- this `FINAL_REPORT.md`.

No canonical revision, current G9 source, checked-in grammar, ClayCode authority, BASE work-package state, application-acceptance state or stage gate was changed.