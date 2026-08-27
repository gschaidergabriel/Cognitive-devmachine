# ClayCode Trigger Run — FINAL REPORT

Run: `claycode-20260809T1602p0700-chatgpt-controlflow-precedence-v1`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **none — run-local research delta only**

## Executive result

This run narrows the ClayCode BASE blocker from “grammar drift” to two executable semantic-contract gaps.

1. **Union types are no longer a current blocker.** Concurrent commit `a8113c4790b234cc0c0637d06d5df554e348f8d6` repaired `type_expr` so `POS|NEG` and `ProvExpr|ProvAtom` are admitted. Older reports must not keep counting that mismatch.
2. **`if` cannot be repaired by naïve eager function-call normalization when effects exist.** With `cond=false`, structured conditional execution produced zero effects while `select(cond, effect(), unit)` evaluated the effect anyway. This is negative result `N-CC-20260809-CF-01`.
3. **The current flat operator-chain grammar does not freeze executable meaning.** In 50,000 deterministic generated arithmetic chains, flat left-fold evaluation and conventional multiplication-before-addition/subtraction grouping diverged in 22,973 cases (45.946%). This is `N-CC-20260809-PREC-01`.
4. **Short-circuit behavior is part of the same problem.** Eager function-call forms for `&&`/`||` changed effect traces relative to lazy boolean evaluation.
5. **`4B_emits` remains a lexical surface mismatch.** The current bare-identifier grammar rejects digit-leading names. A semantic-preserving rename such as `model4B_emits` is lower-risk than globally allowing digit-leading bare identifiers; an escaped/sigiled identifier can remain an alternative hypothesis.
6. **No FRANK-specific new primitive is justified.** The required delta is general-purpose language machinery: structured/lazy control flow, explicit operator binding/evaluation semantics, canonical AST nodes and evaluator tests.

## Fresh concurrent state assimilated

The run reread current GitHub state immediately before durable write.

- Canonical remained RAE-8.8 revision 2 with state hash `04234efd...9346`.
- The union-type mismatch had already been repaired by a concurrent worker.
- A concurrent declared-relation worker preserved a different negative result: arbitrary generic infix without a typed resolver fails closedness. This run does not duplicate that work; it adds control-flow/evaluation-order evidence.
- A concurrent project update narrowed FRANK v0.1 deployment target to Andreas' Ubuntu Linux developer system and explicitly removed Android/mobile edge from the v0.1 gate. That favors prioritizing Linux-native execution and a measured WASI experiment during BASE instead of spending current-gate effort on Android portability.

## Fusion 1

The previous surface/canonicalization run correctly found that the current admitted G9 V3 source and grammar are not a frozen executable pair. The new evidence changes the diagnosis:

`token admission drift`
is only one layer.

The deeper BASE contract is:

`source -> deterministic parse -> explicit canonical AST -> deterministic evaluation order -> effect-safe lowering -> replayable receipts`

A parser that merely accepts all current tokens can still be semantically non-conforming if it groups mixed operators differently or evaluates an unselected effectful branch.

## Executable experiment

Experiment: `CC-LOCAL-20260809-CONTROLFLOW-PRECEDENCE-01`

Execution surface:
- local ChatGPT Python;
- a separate Python process executed the probe;
- no fresh E2B claim because E2B was not exposed on this hosted ChatGPT tool surface.

### Conditional effect counterexample

For a false condition:

- structured/lazy `if`: result `None`, effect count `0`;
- eager ordinary-call/select normalization: result `None`, effect count `1`.

For a true condition both performed the effect once.

Interpretation: eager function-call desugaring is not semantics-preserving for effectful branch bodies.

### Boolean short-circuit counterexample

- `false && effectful_rhs`: lazy form performed `0` RHS effects; eager call performed `1`.
- `true || effectful_rhs`: lazy form performed `0` RHS effects; eager call performed `1`.

Therefore boolean evaluation strategy must be in the semantic contract once effects can appear in expressions.

### Operator-binding fuzz

Seed: `20260809`  
Cases: `50,000`  
Divergences: `22,973`  
Fraction: `45.946%`

Examples:

- `9+5*5+7`: flat-left `77`, conventional precedence `41`;
- `8+3*3`: flat-left `33`, conventional precedence `17`;
- `2+4-5*9*1`: flat-left `9`, conventional precedence `-39`.

This does not itself select ClayCode's final precedence table. It refutes the claim that the current flat grammar can leave grouping unspecified without affecting execution.

## Independent external checks

Primary language/IR documentation was used only as independent architecture evidence, not as authority over ClayCode design.

- LLVM MLIR's structured-control-flow dialect represents conditional regions explicitly and lowers them through dedicated conversion paths.
- MLIR arithmetic comparisons are explicit typed comparison operations.
- The Rust language reference publishes explicit conditional semantics, identifier rules and operator precedence rather than leaving these to evaluator convention.

These analogues support making ClayCode control/evaluation semantics explicit, while the exact ClayCode surface remains research-gated.

## Goodman anti-echo result

### Conditional FRANK effect paths — REFINED

FRANK/ClayCode already require conditional effect execution and an external effect-authority boundary. The independent executable counterexample shows that the requirement survives, but exact syntax is not the point: **unselected effectful regions must not execute**. Structured/lazy canonical semantics are therefore favored over eager call sugar.

### Existing flat operator surface — REFINED

The current operator vocabulary may survive. What cannot survive unfrozen is grouping/evaluation behavior. Before BASE parser/evaluator release, precedence, associativity and short-circuit rules must map to an explicit canonical AST and be differential-tested.

## ClayGraph / UnifiedDB / GWT / Hyperposition impact

- ClayGraph V2 stores typed hyperrelation roles and optional ordinals. This is consistent with preserving order/role structure rather than globally normalizing sequences.
- UnifiedDB replay/transaction/work semantics depend on deterministic state transition interpretation; ambiguous expression grouping undermines replay identity.
- GWT and Hyperposition readouts remain suitable as typed schema/library values for BASE. This run does not discover a reason to add special GWT/emergence syntax.
- Harness H2 remains the decisive full-system oracle: if the frozen H1 conditional/effect/replay behavior cannot be reproduced after ClayCode lowering, BASE must reopen.

## Hypothesis update

- `H-CC-CF-001` — OPEN: canonical IR requires structured/lazy conditional semantics; eager ordinary-call rewrite is refuted for effectful branches.
- `H-CC-PREC-001` — OPEN: precedence/associativity/short-circuit semantics must be frozen before evaluator/lowering conformance.
- `H-CC-ID-001` — OPEN: keep strict bare identifiers and rename/escape `4B_emits` rather than globally admitting digit-leading names.
- `H-CC-20260809-01` — REFINED run-local: BASE blocker is not only grammar token drift; evaluation semantics are unfrozen.
- `H-CC-20260809-02` — SUPPORTED run-local: type-directed canonicalization remains necessary; explicit expression/control-flow AST structure joins it.

## BASE implementation implication

Highest-information order now is:

1. freeze structured conditional + boolean evaluation semantics and an explicit operator-binding table in canonical IR;
2. reconcile remaining current surface mismatches (`<`, `>`, `if`, `4B_emits`) without widening semantics unnecessarily;
3. run the parser/canonicalizer over the complete admitted G9/dialect corpus;
4. mutation-test mixed operators, unselected effectful branches, short-circuit RHS effects and semantic hashes;
5. connect the same canonical AST to the reference evaluator;
6. then lower the same programs to the first Ubuntu-oriented native target and a measured WASI candidate;
7. only change higher-level ClayCode semantics when a real application/FRANK counterexample survives those layers.

This run does **not** close a BASE work package or change `GENERAL_PURPOSE_GATE = NOT_PASS`.
