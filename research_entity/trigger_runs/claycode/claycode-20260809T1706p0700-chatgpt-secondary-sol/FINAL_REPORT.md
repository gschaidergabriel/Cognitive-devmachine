# ClayCode Research Run — 2026-08-09 17:06 +07

## Run identity
- Run ID: `claycode-20260809T1706p0700-chatgpt-secondary-sol`
- Trigger: `claycode`
- Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol
- Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Program stage: `BASE_CLAYCODE_RELEASE`
- v0.1 target: Ubuntu Linux developer system only

## Executive result
This run found a concrete executable BASE conformance defect before changing ClayCode semantics: current G9 V3 uses comparison operators such as `>` / `<` and an `if ... { ... }` conditional, while the checked-in `grammar.ebnf` does not define those comparisons or an `if` production. A local executable parser model of the relevant published grammar subset rejected a current-G9 fixture at `>`. A minimal grammar repair accepted it.

The repaired parser also accepted a typed `LoopDynamicsReadout` + `RecurrenceDecision` fixture using existing G9 semantic forms: records, unions, sets, optional references, rules and authority separation. Therefore this run found no executable reason to add a new loop-specific ClayCode semantic primitive. Highest-value path: grammar self-conformance and compiler/runtime realization, not language reinvention.

The separate scientific claim that FRANK is best modeled as an organism-level hierarchical multiscale loop-of-loops remains `UNRESOLVED`; cross-branch repetition shares one ancestry family and is not independent replication. Generic loop instrumentation can be implemented without promoting that ontology.

## Internal evidence
Primary current inputs:
- `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- `research_entity/claycode/g9/grammar.ebnf`
- `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`
- `research_entity/global/CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md`
- `research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md`
- current FRANK loop mesh feedback
- current ClayGraph V2 hyperrelation/selection schema
- current UnifiedDB V9 dynamic-work schema
- current GWT and Hyperposition emergence-readout contracts
- current Emergenz protocol
- current Harness workspace

Full branch assembly: `INTERCONNECT_MANIFEST.json`.

## Fusion 1
The current program is in compile/realize mode. All 14 BASE work packages remain open and no mandatory application proof is currently passed in the ClayCode release workspace. The newest FRANK feedback asks for executable representation of loop identity, timescale, recurrence budget, dynamics readout, intervention and rollback. Existing G9 semantic forms appeared sufficient in principle; the discriminating question was whether the blocker is missing semantics or parser/compiler realization.

## Hypotheses
Full matrix: `HYPOTHESIS_MATRIX.json`.

- `H-CC-GRAMMAR-01` — published G9 grammar is not executable-conformant with current G9 V3. Result: `SUPPORTED` by the local parser counterexample.
- `H-CC-LOOP-01` — tested loop readout/controller contract fits existing G9 forms. Result: `SUPPORTED_NARROWLY` at parser/representability level; production type/effect/evaluator/lowering and Ubuntu execution remain open.
- `H-CC-IDENTITY-01` — semantic hash can normalize explicitly set-like fields while contract hash preserves exact instance identity and ordered fields stay order-sensitive. Result: `SUPPORTED_NARROWLY` in a deterministic microtest.
- `H-CC-AUTHORITY-01` — typed external capability validation can preserve expressibility without textual/model output minting authority. Result: `SUPPORTED_NARROWLY_SIMULATION_ONLY` in a minimal checker.

## External primary implementation research
External research was used as independent implementation analogy, not evidence for FRANK's loop ontology.

- LLVM MLIR's official design separates typed dialect definitions, parsing/printing, canonicalization and lowering. This supports treating the observed defect as a grammar/toolchain problem before inventing new semantics.
- Tree-sitter's official grammar guidance makes precedence/associativity explicit for expression grammar conflicts; production G9 precedence remains unfrozen.
- WebAssembly Component Model WIT/WASI provide an independent analogue for typed interfaces/resources/handles and capability-bearing host boundaries.

These analogues narrow implementation choices; they do not prove ClayCode correctness.

## Executable experiment
Artifact: `claycode_g9_loop_parser_experiment.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`  
Surface: local ChatGPT container, Python 3 + Lark 1.3.1. Preferred E2B/SandboxAPI were not exposed in this session; no E2B evidence is claimed.

### Fixture A — current G9 surface
Constructs included `diff>0`, `diff<0` and `if residual.effect { ... }`.
- baseline grammar model: REJECT at `>`
- minimal repaired grammar: ACCEPT
- repaired parse-tree hash: `ee2021dd2d5edc4afc93e978e28cd4715a085ced38dfd2942fab11e115422b47`

### Fixture B — loop contract
Represented loop identity, timescale, state delta, unresolved pressure, recurrence count/budget, convergence, marginal utility, stagnation/overthinking, evidence, rollback, decision action and capability reference.
- baseline grammar model: REJECT at `>`
- minimal repaired grammar: ACCEPT
- repaired parse-tree hash: `00738845f6585288e94e0c14571539e28bddb1444c2352e9b8e8a07304019265`

Interpretation: tested loop requirements currently justify implementing the existing language, not adding a loop primitive.

### Identity and authority microtests
Observed:
- duplicate/reordered explicitly set-like `permits` values -> equal semantic hashes;
- exact instances -> distinct contract hashes;
- reordered ordered sequence -> changed semantic identity;
- text-only capability -> rejected;
- valid authority-issued token -> accepted;
- revoked/forged-issuer token -> rejected.

These are microtests, not production canonicalizer/effect-gateway evidence.

## Negative results
Preserved in `NEGATIVE_RESULTS.json`:
1. current published grammar subset fails a current-G9 comparison expression;
2. this run did not establish the FRANK loop-of-loops ontology;
3. local parser success is insufficient for BASE/H2 release evidence.

Source inspection also shows G9 V3 uses line comments while `grammar.ebnf` does not explicitly define comment lexing. The local prototype ignored comments, so this is recorded as a source-level conformance question, not a separately executed failure.

## Goodman anti-echo
Full review: `FRANK_CLAYCODE_GOODMAN_REVIEW.json`.

- Organism-level FRANK loop-of-loops ontology: `UNRESOLVED`. H0-A — ordinary persistent event-driven orchestration plus local loops — remains live until matched H1 causal evidence exists.
- ClayCode requirement for loop semantics: `REFINED`. The representation requirement survives, but current evidence points to grammar/compiler realization rather than a new language primitive.

The expected current `FRANK_ARCHITECTURE.claycode.json` was not located through the available connector search/direct expected path during this run; current FRANK loop directive/feedback was used provisionally rather than fabricating an artifact.

## Cross-branch delta
Full receipts: `BRANCH_FEEDBACK_MANIFEST.json`.

- ClayCode: add machine-enforced full-spec self-parse + deterministic canonical roundtrip; freeze precedence/associativity; then typed IR -> type/effect -> evaluator/lowering.
- FRANK: keep loop ontology open; generic instrumentation can proceed.
- Harness: make ClayCode grammar self-conformance a prerequisite for interpreting H-WP-03/H2 differential failures.
- ClayGraph: `NO_SEMANTIC_CHANGE`; current typed hyperrelation/projection/selection/receiver receipts are adequate for future loop refs.
- UnifiedDB: `NO_SEMANTIC_CHANGE`; current epoch/revision/receipt substrate is adequate at this stage without physical-monolith implications.
- GWT: keep loop stability distinct from selection/delivery/reconstruction/use/effect/outcome/re-entry.
- Hyperposition: no new primitive justified by the tested loop contract.
- Emergenz: recurrence/stability readouts are instrumentation, not emergence evidence without interventions/controls.
- Clay integrated foundry: prioritize grammar self-conformance -> canonical typed IR -> type/effect -> evaluator/lowering -> Ubuntu application proofs.

## Architecture/research delta
New durable finding: `PUBLISHED_G9_GRAMMAR != CURRENT_G9_V3_SURFACE` for the tested comparison/conditional constructs.

Recommended BASE compiler gate before parser/spec freeze completion:
1. one production lexer/parser from a frozen grammar source;
2. self-parse the complete admitted G9 V3 spec;
3. deterministic parser/canonicalizer roundtrip;
4. explicit precedence/associativity plus adversarial tests;
5. every admitted syntax form represented by the grammar or an explicitly contracted dialect;
6. parse success never implies semantic validity or execution authority.

Language-change decision for this run: `NO_NEW_LOOP_PRIMITIVE`. Reopen only on a production type/effect/lowering or real Ubuntu application/FRANK counterexample.

## Highest-information next experiment
Build the production parser/canonicalizer around the admitted G9 grammar, require full G9 V3 self-parse + deterministic roundtrip, then pass `LoopDynamicsReadout` through typed IR and type/effect checking. Replicate the same fixture on the Ubuntu target with a receipt. If successful, continue directly into a small CLI/HTTP proof instead of reopening syntax research.

## Program impact
This run creates research/toolchain evidence but completes no BASE work package and passes no application proof. Strict stage percentage therefore does not increase from this run alone. It reduces uncertainty about the immediate blocker: grammar/compiler conformance, not missing loop semantics.

## Provenance / limits
- ChatGPT-authored durable objects: `chatgpt-secondary`, OpenAI, GPT-5.6 Sol.
- Shared FRANK ancestry was not counted as independent replication.
- External sources are implementation analogues, not FRANK evidence.
- Local executable results are non-target sandbox evidence.
- No hidden chain-of-thought was persisted and no background execution is claimed.

## Run artifacts
`INTERCONNECT_MANIFEST.json`, `TOOL_EXECUTION_MANIFEST.json`, `HYPOTHESIS_MATRIX.json`, `NEGATIVE_RESULTS.json`, `FRANK_CLAYCODE_GOODMAN_REVIEW.json`, `BRANCH_FEEDBACK_MANIFEST.json`, `claycode_g9_loop_parser_experiment.py`, `EXECUTABLE_RESEARCH_RECEIPT.json`, `FINAL_REPORT.md`.
