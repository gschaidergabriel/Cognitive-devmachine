# ClayCode Trigger Run — Executable G9 Conformance / BASE Gate

**Run:** `claycode-20260809T155134p0700-chatgpt-58f84b`  
**Actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**Canonical parent:** RAE-8.8 · r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**Program stage:** `BASE_CLAYCODE_RELEASE`  
**Promotion:** none; research delta only.

## Executive result

This run found one concrete BASE-stage language-toolchain defect and one de-risking result:

1. **Negative result — current G9 grammar/spec drift.** The checked-in G9 EBNF rejects syntax already used by the current G9 candidate. A 10-case sampled parser corpus passed **2/10** with the current grammar. The rejected families were comparison `>/<`, union types including unions inside generics, `returns`, `includes`, `if`, and postfix optional + `or`.
2. **Minimal repair hypothesis survives.** A parser-side grammar alignment that added only those already-used forms passed **10/10** on the same corpus. No semantic redesign was needed for this sample.
3. **Adaptive visual learner / effect lowering prototype passed.** Existing record/rule/effect concepts encoded trusted GOLD/SILVER admission, BRONZE rejection, candidate promotion, budget fallback, rollback and external effect commit/deny semantics. The fragment lowered to generated Python, executed in a separate process and passed **9/9** deterministic semantic cases.

The correct BASE direction is therefore **less change, more compile**: repair grammar/parser conformance, then build full parser/canonical IR/type-effect/evaluator/compiler/runtime/FFI application proofs. This run does not justify a new ClayCode primitive.

## Internal evidence used

- current G9 candidate and EBNF
- current BASE workspace and compiler acceptance contract
- FRANK v0.1 adaptive visual learning fixed requirement
- FRANK first-principles/emergent-coupling lens
- current Harness workspace
- ClayGraph hyperrelation/selection substrate
- UnifiedDB dynamic work/capability/execution-receipt substrate
- GWT and Hyperposition measurement contracts
- pinned Android R1 cross-branch evidence, preserved at original evidence class
- Goodman anti-echo protocol

The preferred `FRANK_ARCHITECTURE.claycode.json` / `CLAYCODE_ARCHITECTURE_MAPPING.md` was not discoverable through the current GitHub file-search surface and was not fabricated.

## External independent checks

- **WASI capability boundary:** official capability documentation independently supports outside-world access through runtime capabilities/handles rather than ambient authority. This supports ClayCode's `expressibility != authority` boundary, not its exact ABI.
- **MLIR dialect conversion:** official documentation independently supports multiple typed dialects with explicit conversion targets, legality and type conversion. This supports the general architecture but not ClayCode-specific semantic-hash rules.
- **Effect-typed agent-language research:** a recent preprint provides an independent analogue for request/handled/denied/commit semantics with authorization retained at runtime/deployment/policy boundaries. It is supporting research evidence, not a standard or proof of ClayCode correctness.

## Hypotheses

- `H-CC-G9-GRAMMAR-01`: checked-in G9 grammar is not faithful to current G9 source — sampled support.
- `H-CC-G9-GRAMMAR-02`: minimal parser alignment can repair observed syntax drift without semantic redesign — open, sample-supported.
- `H-CC-MVC-03`: existing record/rule/effect concepts can represent core adaptive learner transitions without a new primitive — open, prototype-supported.
- `H-CC-AUTH-04`: external non-textual authority can preserve general-purpose expressibility while preventing model-text authority minting — architectural boundary supported; final implementation open.

## Executable experiment 1 — G9 grammar/spec sampled conformance

- G9 spec blob SHA: `1a17bba3c835520baff2ac8fa432749ba2165d8e`
- G9 grammar blob SHA: `80028aae6d9d26ac96fa7179dbccc7e467740990`
- corpus SHA-256: `a6236678998cea480b6f3b8611cca1cb8b7d1c8617159b1947ee1a14f64ab750`
- checked-in grammar: **2/10**
- minimal aligned grammar: **10/10**

Boundary: sampled evidence only. Complete G9 parse, ambiguity/precedence, canonicalization and type/effect closure remain open.

## Executable experiment 2 — MVC/effect compiler lowering fragment

- source SHA-256: `d36503ded796b7f672a61a500fec1909919560c1e4241a00f7f3342222360b90`
- canonical semantic hash: `f7f6ea5da349189ca99e48deb4b404ddd471dd47e6fbf2848e529b027ab6d657`
- generated Python SHA-256: `731e5adaa2248ba769cd85b110dae6ea94fe20054020f750d9b56177415a6df6`
- semantic tests: **9/9 PASS**

Covered: trusted training-example admission, BRONZE rejection, candidate promotion, evaluation/budget fallback, last-known-good rollback, commit requiring capability+witnesses, missing-capability denial.

Boundary: prototype compiler fragment only; no full compiler/runtime, transaction/replay, atomic promotion or H1/H2 parity claim.

## Goodman anti-echo

- Effect authority separation: **SUPPORTED** at architectural-boundary level by independent capability/effect evidence plus current adversarial tests.
- Typed dialect/lowering architecture: **REFINED**; independent analogue exists, exact ClayCode conversion rules remain unvalidated.
- Adaptive learner representability: **REFINED**; core transitions fit existing concepts, full frozen H1 semantics remain the discriminating test. No new primitive is warranted now.

## Negative result — interconnect preflight governance drift

Current `RESEARCH_TRIGGER_REGISTRY.json` names the integrated branch `clayresearch`; `tools/research_interconnect_preflight.py` still hard-codes `clay` in its priority sets and intentionally raises when the branch sets differ. The mandatory preflight is therefore currently **fail-closed blocked**.

A manual nine-branch coverage manifest records what was actually read but does **not** claim the mandatory preflight passed. Strong promotion is blocked until the tool is repaired and rerun.

## Cross-branch synthesis

- **ClayGraph:** NO_CHANGE. Activation/relevance remains distinct from truth/effect authority; no graph mechanism executed.
- **UnifiedDB:** NO_CHANGE. Revisioned capability/work/execution receipts remain compatible; no real transaction/storage/replay test executed.
- **GWT:** NO_CHANGE. No workspace intervention; delivery/use/outcome/re-entry distinctions remain required.
- **Hyperposition:** NO_CHANGE. No topology/coupling intervention; n-ary/topology primitives remain release constraints.
- **Emergenz:** NO_CHANGE. Compiler success creates no emergence or consciousness evidence.
- **Harness:** parser/spec drift is a real BASE blocker; MVC lowering partially de-risks future H2 semantic parity but is not parity evidence.
- **FRANK:** no new ClayCode primitive is justified by this run; publish/freeze a discoverable full ClayCode architecture mapping and use H1 as the next adequacy oracle.

## Highest-information next sequence

1. align production parser/EBNF with source-used G9 forms;
2. parse the complete current G9 candidate;
3. deterministic canonical IR + full roundtrip + separate semantic/contract identity;
4. type/effect/capability checker with negative diagnostics;
5. reference evaluator;
6. compiler/lowering + runtime ABI/typed FFI;
7. compile the full frozen FRANK adaptive-learner transition contract;
8. execute generated target code separately and differential-replay against H1;
9. expand to APP-01..APP-10 acceptance applications.

Any semantic change still requires an executable application/FRANK counterexample showing existing semantics cannot express/lower the required behavior.

## Program impact

No BASE work package is marked complete by this sampled run. The BASE gate remains `NOT_PASS`. The run converts two uncertainties into actionable engineering evidence: grammar alignment is a reproducible blocker, while core MVC/effect transition expressibility is partially de-risked.

## Final synthesis

The current ClayCode candidate is **semantically promising but toolchain-inconsistent**. The immediate BASE risk is not missing conceptual primitives; it is that the checked-in grammar cannot yet serve as the executable contract for the source that already exists. Fix that seam first, then let full parser/type/effect/lowering and real FRANK/application counterexamples decide whether any semantic change is actually needed.
