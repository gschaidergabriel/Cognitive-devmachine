# SPAWN Research Run — ClayCode / FRANK Loop Evaluator-Lowering Slice

Run: `spawn-20260809T1742p0700-claycode-loop-eval-lowering`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Branch draw: **ClayCode**  
Final microdirection: **FRANK loop -> evaluator/lowering**  
Decision: **RESEARCH DELTA · NO SCIENTIFIC PROMOTION · BASE GATE REMAINS NOT_PASS**

## 1. Spawn selection and duplicate control

OS-CSPRNG branch draw `479699728 / 1e9 = 47.9699728%` selected ClayCode under the current 50% weight.

Fresh parser-conflict and symbol/signature candidates were rejected as duplicates of same-day ClayCode work. The first microdirection selection, async resource identity/lifetimes, was then rejected after a repository scan found fresh FFI resource-identity/TOCTOU/lifetime commits. Per SPAWN protocol only the microdirection was rerolled; the ClayCode branch was retained. The final direction was `frank-loop-evaluator-lowering`.

## 2. Research question

Can the current FRANK `LoopDynamicsReadout` / `RecurrenceDecision` vertical slice be represented, evaluated and lowered through ordinary typed-control IR while preserving epoch, identity and authority boundaries, without introducing a new FRANK-specific ClayCode primitive?

This directly follows current FRANK, GWT and ClayResearch guidance: compile the recurrent exemplar before redesigning language semantics.

## 3. Internal grounding

The current project remains in BASE. All ClayCode release work packages remain OPEN and no mandatory general-purpose application proof is currently recorded as passed. Current G9 V3 is a research candidate and the repository EBNF still has known frontend closure/conflict debt.

Fresh current evidence constrains the slice:

- FRANK defines `LoopDynamicsReadout` and proposal-only `RecurrenceDecision`, with mixed-epoch and effect-authority invariants and an explicit next executable slice through evaluator/lowering.
- GWT R8 adds bounded trajectory/capacity observables plus separate `semantic_state_hash`, `state_version_hash` and `trace_root_hash` witnesses.
- Harness H-WP-02 independently implements the same identity separation at state-ledger level and fails stale epochs closed in its local oracle.
- ClayCode control/effect work already supports ordinary branch/recursion/result/effect closure in a local proxy and keeps static effect summaries separate from runtime authority.

No branch result is treated as independent validation of the FRANK recurrence mechanism merely because this run executes a compiler proxy derived from it.

## 4. Executable discriminator A — canonical-IR evaluator + generated Python lowering

A compact typed-control IR proxy used only ordinary operations: record-field read, comparison, boolean conjunction/disjunction, multiplication, absolute value, nested `if`, and enum-like result. It deliberately contained **no external-effect operation**.

The tested research policy distinguishes mixed epochs, recurrence budget exhaustion, residual pressure, overthinking, divergence/trajectory growth, low-residual convergence, capacity saturation and stagnation. This policy is a compiler discriminator only; it is not a frozen FRANK controller.

Results over **200,000** deterministic randomized inputs:

- reference policy vs IR evaluator: **0 mismatches**;
- reference policy vs generated Python lowering: **0 mismatches**.

Mutation discrimination was nontrivial:

- remove residual-sensitive halt: 78,179 differences;
- ignore recurrence budget: 112,104 differences;
- remove capacity route: 2,615 differences;
- remove mixed-epoch guard: 3,895 differences.

The canonical proxy semantic hash was `f479c4e85f1326257fcd0337caaa845cdf92daa127cc53205a90a02edfea37b1`. Canonical reserialization retained the hash; a semantic threshold mutation changed it; provenance/source metadata changed the exact contract hash without changing the program semantic object.

## 5. Executable discriminator B — native GCC shadow

The same decision policy was independently emitted as a small C function and compiled with GCC 14.2.0. Over **100,000** new randomized inputs:

- reference policy vs native compiled function: **0 mismatches**.

This is useful backend-shadow evidence, not production ClayCode lowering: the C was manually emitted and did not pass through the actual ClayCode compiler.

## 6. External primary-source comparison

Official MLIR SCF/CF, WebAssembly validation/control, and LLVM language-reference material provide independent engineering anchors that typed structured branch/control semantics can be lowered deterministically without embedding domain-specific cognitive policy into the backend. They do **not** select ClayCode syntax, prove the current G9 parser, or validate FRANK's recurrence policy.

## 7. Result

The selected microdirection produced **supporting implementation evidence**, not a language redesign:

> Within the tested evaluator/lowering slice, current FRANK/GWT recurrence-decision requirements can be modeled with ordinary typed control/data operations; no new FRANK-specific ClayCode primitive was forced by the local executable tests.

This narrows the BASE frontier. The higher-information failure surface is now the production chain:

`current source/front-end -> canonical typed IR -> type/effect -> evaluator -> backend lowering -> Ubuntu execution receipt`.

The local proxy bypassed the first part of that chain, so it cannot close CC-WP-02/03/04/05/06 and cannot change the BASE gate.

## 8. Identity / authority refinement

The run supports a strict separation:

- **program semantic identity** covers the decision/control meaning;
- `semantic_state_hash`, `state_version_hash`, `trace_root_hash` are runtime witnesses/receipt identities;
- recurrence/route decisions remain proposals;
- no effect authority is inherited through recurrence;
- mixed-epoch input must fail/route closed unless a future explicit reconciliation semantics is verified.

This is a candidate compiler/runtime contract refinement, not a canonical scientific promotion.

## 9. Negative results and boundaries

- Initial resource-lifetime direction was a duplicate and was discarded rather than double-counted.
- No local semantic counterexample requiring new ClayCode syntax/primitive was found.
- Production parser conflict/closure debt remains unresolved.
- No actual Ubuntu developer-host run was performed.
- No target Qwen-class reader comparison was performed.
- No live FRANK loop benefit, GWT causal benefit, emergence or consciousness claim follows from compiler parity.

## 10. Next discriminating action

Execute the same frozen recurrence-decision fixture through the **production ClayCode parser + canonical IR + type/effect + evaluator + selected Ubuntu backend** on the project Ubuntu developer host, with exact source/program/backend hashes and differential comparison against the local oracle. Include mixed-epoch, retry/replay identity, capability revoke/regrant at the optional effect boundary, and at least one real frozen FRANK loop fixture.

A dynamic-work event is emitted separately so the local/repo build organ can pick this up when the required Ubuntu/compiler surface is available.

## 11. Decision

`SPAWN_BRANCH = claycode`  
`MICRODIRECTION = frank-loop-evaluator-lowering`  
`RESEARCH_DELTA = YES`  
`SCIENTIFIC_PROMOTION = NONE`  
`NEW_CLAYCODE_SEMANTICS = NOT_JUSTIFIED`  
`BASE_GATE = NOT_PASS`  
`NEXT = production parser/IR/evaluator/lowering differential on Ubuntu`
