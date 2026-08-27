# ClayCode Trigger Run — G9 Definition→Call Closure

**run_id:** `claycode-20260809T1711p0700-chatgpt-secondary-fn-closure`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**decision:** **RESEARCH DELTA COMMITTED · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## 1. Executive result

The current ClayCode BASE problem is narrower than “invent a more powerful language”. Prior CC14 research already produced a bounded universal-core proxy with `20,000` two-counter-machine cases and `0` differential mismatches, and its handoff explicitly requires composable functions/calls among the minimal general-purpose core.

The current admitted G9 V3 stack, however, does not close that contract at the executable source surface:

- the published expression grammar includes `call`;
- the published statement grammar has no general function-definition production;
- the moving Dialect Registry describes cognitive/project dialects but does not expose the prior universal-core function-definition contract as an admitted executable construct.

Therefore:

> **universal-core research evidence != current admitted executable language surface**

and, more specifically:

> **call syntax without deterministic definition/signature binding is not general-purpose definition→call closure**

This run tested a deliberately minimal candidate bridge: one typed, expression-bodied function declaration that reuses existing `module`, `type_expr`, `expr` and `call` concepts. The local checker/interpreter executed `20,000` randomized composed calls with **0 differential mismatches**, while undefined target, arity mismatch and undefined variable cases failed closed.

The result supports a BASE frontend/canonical-IR integration repair. It does **not** justify a new FRANK-specific or cognitive primitive and does **not** pass any BASE work package.

## 2. Non-duplication boundary

The 17:06–17:10 concurrent ClayCode wave had already established:

1. G9 grammar/spec self-inconsistency around comparison operators and `if`;
2. a rule-surface `PredicateIR/ConstraintIR` partition candidate;
3. resource lifetime/generation/type/borrow constraints;
4. source-chain / canonical semantic-ID minting constraints.

This run does not repeat those findings. Its new question is **definition→call closure**: whether the previously researched universal computation contract is actually reachable from the current moving G9 language surface.

## 3. Internal evidence

### Current G9

Inputs:

- `research_entity/claycode/g9/grammar.ebnf` blob `ec2f17077333955cfdabe6c64868d597e7e734e3`;
- `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay` blob `1a17bba3c835520baff2ac8fa432749ba2165d8e`;
- `research_entity/claycode/g9/DIALECT_REGISTRY_V3.clay` blob `dbb72460bc5a049c784d1acd1aaef152fa37f797`;
- admitted moving stack `RAE_LATEST_COGNITIVE_STACK.clay` epoch 17.

The grammar has call expressions but no `fn_decl`-equivalent statement. `needle` is an effect-lowering declaration and `cycle` is a specific cycle body; neither is presently specified as a general reusable typed function definition.

### Prior universal core

`EXP-CC14-UNIVERSAL-CORE-001` established only that a tested ClayCore instruction shape can realize the chosen bounded universal-machine subset. The accompanying A→B handoff separately requires:

- typed scalar/algebraic values;
- product/sum/record/variant + pattern match;
- composable functions/calls;
- branching;
- universal iteration/recursion;
- state;
- modules/separate compilation;
- structured failures;
- systems-profile memory/concurrency primitives.

That is strong design ancestry but not proof that G9 V3 currently exposes those constructs through the production compiler path.

## 4. Eight-neighbor / nine-branch mesh synthesis

`INTERCONNECT_MANIFEST.json` records the current nine-branch research snapshot.

### FRANK

The latest full architecture/lineage fusion keeps FRANK as a multi-plane recurrent runtime with exact state, cognitive frames, GWT, reader/model uptake, observability, external authority and persistence. Nothing in this run requires a FRANK-specific function primitive. FRANK supplies application pressure; the compiler should solve it generically.

### Clay

The moving stack is the admitted per-turn substrate. A historical or side-run universal-core experiment does not become executable merely because it exists in Git history. The gap is therefore an admission/integration problem.

### Harness

The current SourceChainEvidence refinement says canonical `ProgramSemanticId` belongs at deterministic canonical semantic IR, not at raw source/parse stages. Function definition/signature identity should therefore be carried into canonical typed IR and then linked to lowering/executable hashes. A source-level name alone is not semantic authority.

### ClayGraph

G3's negative self-use result rejects universal graph propagation for exact/high-confidence identity queries. Function resolution is an even harder exact-identity case. **No nearest-neighbor/activation fallback** is acceptable for a missing or ambiguous call target.

### UnifiedDB

U9 keeps resources, capabilities, work revisions and execution receipts distinct. Compiler symbol identity may be stored/referenced by UnifiedDB, but semantic proximity or a work/resource record does not define the callee and never mints authority.

### GWT

`global addressability != delivery != reconstruction != uptake != causal use != outcome != reentry`. Function-call binding is a compiler semantic relation, not workspace salience/selection.

### Hyperposition

Alternative implementations/topologies may remain concurrently represented during search/research. Once a compiled artifact is selected, each call site still needs one explicit semantic/signature binding under that artifact's identity.

### Emergenz

Universal computation, function composition, recursion or recurrent loops are not emergence evidence. E-CERT2 remains orthogonal.

### ClayCode

Route this delta to BASE frontend + canonical IR + typechecker + compiler. Preserve `less change, more compile`.

## 5. External primary-source check

These sources are independent comparison anchors, not mandates to copy syntax.

### WebAssembly Core Specification 3.0

Official module syntax explicitly contains function definitions, and its control instruction set separately contains call/control instructions. This supports an explicit binding boundary between a callable function identity/signature/body and the call instruction.

Source: `https://webassembly.github.io/spec/core/syntax/modules.html`

### LLVM Language Reference

LLVM explicitly defines function definitions/basic blocks and typed `call` semantics. A call transfers control to a specified function with arguments bound to that function, and signature compatibility matters.

Source: `https://llvm.org/docs/LangRef.html`

Transfer boundary: WebAssembly/LLVM do not prove the optimal ClayCode syntax. They independently support the narrower design principle that executable calls need deterministic definition/signature semantics in the IR/toolchain.

## 6. Executable experiment

Artifacts:

- `EXPERIMENT_FUNCTION_CLOSURE.py`;
- `EXECUTABLE_RESEARCH_RECEIPT.json`;
- `REPRODUCTION_RECEIPT.json`;
- `CANDIDATE_FUNCTION_SURFACE.ebnf`.

Runtime:

- OpenAI hosted Linux container;
- Debian 13;
- Python 3.13.5;
- x86_64;
- **not** Andreas' target Ubuntu developer host.

Candidate surface:

```text
fn_decl = "fn", ident, "(", [param_list], ")", "->", type_expr, "=", expr, [";"]
```

This is intentionally small. It reuses the prior function/call semantic requirement and existing expression/type concepts.

Test program defines and composes three typed integer functions. With seed `202608091711`:

- randomized calls: **20,000**;
- differential mismatches vs direct reference: **0**;
- undefined function: **REJECT**;
- arity mismatch: **REJECT**;
- undefined variable: **REJECT**.

The archived reproducer was executed again with the same qualitative and quantitative result.

### What the experiment proves

It is possible, in the tested pure subset, to bridge the missing definition side of the existing call concept with a small typed surface and fail-closed exact function table semantics.

### What it does not prove

It does not establish:

- production G9 parsing;
- canonical IR completeness;
- branching;
- recursion/iteration;
- pattern matching;
- structured error values;
- memory/resource semantics;
- async/concurrency/atomics;
- FFI/effects;
- native/WASM lowering;
- Ubuntu target execution;
- any mandatory APP-01..APP-10 pass.

## 7. Goodman anti-echo review

Verdict: **REFINED**.

FRANK's need for a general-purpose ClayCode execution path survives independent checks, but the strongest interpretation is narrowed:

- do **not** add FRANK-specific function semantics;
- do **not** infer that cognitive `rule`/`cycle` prose already supplies a verified general function ABI;
- do materialize the already-researched generic function/call contract in canonical frontend/IR if the production compiler confirms the gap;
- do require explicit symbol/signature binding and preserve authority separation.

`FRANK_CLAYCODE_GOODMAN_REVIEW.json` preserves the counterhypothesis and falsifier.

## 8. Candidate compiler law

The run proposes, but does not promote, this implementation law:

```text
source call
 -> module/symbol/signature resolution
 -> canonical typed function identity
 -> canonical ProgramSemanticId derivation
 -> type/effect closure
 -> lowering-contract identity
 -> executable symbol/call relocation
 -> execution receipt
```

Hard boundaries:

```text
ClayGraph activation != function resolution
UnifiedDB proximity != function resolution
GWT selection != function resolution
model text != function authority
function definition/call != capability authority
```

Missing/ambiguous/signature-incompatible binding fails closed.

## 9. Hypotheses and negatives

See `HYPOTHESIS_MATRIX.json` and `NEGATIVE_RESULTS.json`.

Strongest current hypothesis:

> The lowest-risk BASE repair is to materialize the already-researched function-definition/signature contract in the production frontend + canonical typed IR before adding new high-level sugar or FRANK-specific constructs.

Strongest counterhypothesis:

> Existing `rule`/Needle/host semantics can already compile the full mandatory application suite without explicit source-level function definitions.

Highest-information discriminator: implement the production parser/IR on the current BASE branch and attempt reusable typed function compilation with full source-chain receipts. If existing constructs already provide equivalent deterministic semantics, reject this surface candidate.

## 10. Branch feedback

`BRANCH_FEEDBACK_MANIFEST.json` returns explicit refinement/NO_CHANGE receipts to all nine branches.

Key feedback:

- FRANK: no semantic change;
- Harness: add definition/signature call-binding evidence to source-chain oracle;
- ClayGraph: exact symbol binding; no graph fallback;
- UnifiedDB: no schema merge/change required;
- GWT: no change;
- Hyperposition: alternative implementations remain separate from concrete compiled binding;
- Emergenz: no change;
- ClayCode: candidate action in BASE frontend/canonical IR/compiler;
- Clay: admitted moving stack should only point to the universal-core frontend after production validation.

## 11. Highest-information next tests

1. **Production frontend closure** — extend/build the real parser and canonical typed IR with the smallest function-definition contract; self-host/roundtrip canonical hashes.
2. **Control-flow closure** — independently close branching + loop/recursion + pattern match + structured Result/error semantics; do not bundle into the function result.
3. **Typed effect closure** — make function effect summaries compositional and verify no capability widening across calls.
4. **Native target lowering** — compile the same pure function corpus to the selected Ubuntu-native backend and compare canonical semantic/output receipts.
5. **WASM shadow** — lower the same canonical IR to WebAssembly as an independent backend shadow; equality target is semantic result/receipt, not identical bytes.
6. **APP-01 CLI slice** — first real application proof should use the production compiler, stdlib and effect boundary; local proxy evidence cannot substitute.
7. **APP-02 HTTP/website** — only after function/control/error/async/resource closure; execute a real HTTP stack on the Ubuntu developer target.

## 12. Decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`CLAYCODE_CORE_CHANGE = NO`  
`CANDIDATE_FRONTEND_DELTA = TYPED_FUNCTION_DEFINITION_SURFACE`  
`ROUTE = BASE parser + canonical IR + typechecker + compiler`  
`BASE_GATE = NOT_PASS`

The central outcome is a stack-integration correction, not language reinvention:

> **The project already has evidence for a viable universal computation core. The next compiler task is to make that core reachable, typed, identity-bound and executable from the admitted G9 stack.**
