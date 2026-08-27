# ClayCode Trigger Run — Source→IR→Lowering Evidence-Chain Integrity

Run: `claycode_20260809T1702p0700_chatgpt_source_chain_integrity`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` — IN_PROGRESS  
Promotion: **NONE**

## Executive result

This run contributes a narrow compiler-evidence correction, not another ClayCode redesign.

The current checked G9 grammar defines an anonymous cycle header:

`cycle_decl = "cycle", "(", [params], ")", block ;`

but the prior loop-dynamics executable fixture uses:

`cycle classify(x:LoopInput) { ... }`

The minimal grammar repair produced by that run adds comparison operators and `if_stmt` but does not change `cycle_decl`. Therefore the fixture is still not admitted by the inspected source grammar even after that repair.

A second, more important gap appears one stage later. The Clay source uses `emit("...")` inside conditional blocks and then a final `emit("CONVERGING_FIXED_POINT")`. The generated Python lowering replaces branch `emit(...)` calls with `return`. Current G9/grammar material inspected in this run does not define `emit` as a terminating return operation.

A deterministic 20,000-case discriminator showed that this missing decision is behaviorally material: treating `emit` as a nonterminating emitted event versus the prior generated `return` changed the observable trace in **17,693 / 20,000** cases. This does not establish that nonterminating `emit` is the correct ClayCode semantics. It establishes that the prior lowering injected a semantically consequential termination rule not proven by the source/IR contract.

Accordingly, the prior loop-dynamics Python result remains useful as a **manually lowered behavior fixture**, but it must not be counted as end-to-end ClayCode parser/compiler semantic-preservation evidence.

The run proposes one acceptance invariant:

`source_hash -> grammar/parser identity -> AST_hash -> typed_IR_hash -> semantic_hash -> lowering identity -> artifact_hash -> execution receipt`

If any stage is manually synthesized or bypassed, the receipt must say so and cannot satisfy an end-to-end compiler gate.

## Internal grounding / Fusion 1

The current project stage remains `BASE_CLAYCODE_RELEASE`; all 14 ClayCode work packages and all application acceptance items remain open. The governing law remains **less change, more compile**.

Current G9 already carries typed state, provenance, effects, graph state, epochs and capability separation. Concurrent ClayCode work has independently within the same project lineage shown:

- full checked-grammar closure is currently false;
- type-directed canonicalization is required;
- semantic, contract, artifact and deployment/execution identities must remain distinct;
- behavior-changing scheduler/order/halting dimensions must participate in typed semantic identity;
- bounded HTTP lowering can use typed host-resource adaptation without an HTTP-specific core primitive.

This run therefore does not request a new FRANK-specific cycle primitive or a new HTTP/graph/database primitive.

## Executable experiment

Artifact: `SOURCE_CHAIN_PROBE.py`  
SHA-256: `c0b2dafb9ce7a8db4bc929cbc90682bb66894b3d91ba15926c882661fd267eb1`  
Runtime: Linux 6.18.35 x86_64 / Python 3.13.5; Lark 1.3.1 was also used for an adversarial parse check.

### Header conformance

A bounded LALR proxy implementing the repaired control subset:

- rejected `cycle classify(x:LoopInput) {...}`;
- accepted the anonymous form `cycle(x:LoopInput) {...}`.

This is consistent with the literal checked G9 `cycle_decl`. The result is about the tested frontend contract, not about an undiscovered alternative parser.

### `emit` vs `return` discriminator

Seed: `20260809`  
Cases: **20,000**

Prior generated-return arm:

- PRODUCTIVE_LIMIT_CYCLE: 13,204
- DIVERGING_OR_OVERTHINKING: 4,097
- STALLED: 392
- CONVERGING_FIXED_POINT: 2,307

When `emit` is instead interpreted as an event that does not itself terminate the cycle, **17,693** cases produce a different output trace because the final converging emission is still reached after at least one earlier emission.

Verdict: termination semantics are missing/ambiguous and materially observable. **Neither arm is promoted as ClayCode truth.**

### Fixture label / identity discriminator

For this unreferenced research-only cycle label, a candidate typed fixture body can keep one semantic hash while 10,000 different harness labels retain 10,000 different contract/provenance identities.

This supports only a narrow test-harness rule: an unreferenced fixture label may be metadata. It does **not** authorize stripping names from callable/exported program entities.

## New negative results

### `N-CC-SOURCE-CHAIN-BYPASS-007`

The inspected prior loop-dynamics receipt does not establish an uninterrupted source-parser-typed-IR-lowering-execution chain. Its source fixture is not admitted by the current/minimal-repair cycle production.

The behavior experiment itself remains valid for the generated Python target; its evidential class is narrowed.

### `N-CC-EMIT-RETURN-SEMANTIC-LEAK-008`

The generated Python target silently gives `emit` return/termination behavior that is not established by the inspected G9 grammar/semantic source. The 20k discriminator shows the choice is behaviorally material.

This does not prove what the correct final `emit` semantics should be.

## External triangulation / Fusion 2

Independent primary compiler documentation supports treating terminators/results as explicit semantic structure rather than an incidental code-generator choice.

MLIR SCF represents conditional regions with explicit `scf.yield` result/termination semantics, and its loop/if verifiers constrain what values are yielded. LLVM IR likewise requires basic blocks to end in explicit terminator instructions and defines `ret` as a control-flow return to the caller.

These are architecture analogues, not ClayCode-specific proof. They strengthen the falsifiable engineering requirement that the ClayCode typed IR must explicitly represent emit/event, yield/result and return/termination distinctions if those distinctions are observable.

## ClayGraph finding

ClayGraph V2 already stores graph epochs, typed hyperrelation members/roles/ordinals and separate projection, selection and receiver receipts. The new compiler finding does not require a graph primitive.

Instead, compiler-stage ancestry should use the same discipline: derived representations must retain explicit source/derivation identity rather than allowing a downstream executable artifact to retroactively imply source conformance.

## UnifiedDB finding

UnifiedDB V9 already separates revisioned work specs, capability observations, leases and execution receipts with explicit truth classes. No physical or semantic database merge is required.

The new compiler evidence chain can be persisted using existing provenance/execution planes: source/AST/IR/artifact identities and their parent links can remain distinct from runtime capability/resource instances.

## FRANK / Harness finding

FRANK's loop-of-loops research does not justify special ClayCode syntax from this result. The stronger requirement is that H1/H2 recurrent fixtures bind their source, typed semantic identity, schedule/halting semantics, lowering artifact and replay trace.

A manually created IR or generated target may still be a useful experiment, but it cannot masquerade as source compilation.

Frank retains proposal-only authority over Frank Harness changes; this Research Entity result does not delegate self-modification authority.

## GWT / Hyperposition / Emergenz

No causal GWT distinction changes. Selection, delivery, reconstruction, use, effect, outcome and re-entry remain separate.

No Hyperposition semantic change is justified. Typed role/order/topology identity still constrains canonicalization.

No emergence claim changes. Parser closure, loop classification or successful lowering are not evidence of causal emergence.

## Goodman anti-echo

The run does not accept a ClayCode rule because FRANK and ClayCode agree.

- special FRANK cycle syntax: **UNRESOLVED / NOT JUSTIFIED**;
- prior loop source semantic-preservation claim: **REFUTED FOR END-TO-END EVIDENCE**;
- joined source-to-execution ancestry requirement: **REFINED / SUPPORTED** by the direct counterexample plus independent compiler control-flow semantics.

Shared ChatGPT/FRANK/ClayCode ancestry is not counted as independent replication.

## Hypotheses carried forward

1. `H-CC-SOURCE-CHAIN-018` — OPEN_SUPPORTED_FOR_TESTED_FIXTURE: gate evidence needs a joined compiler-stage ancestry chain.
2. `H-CC-EMIT-TERMINATOR-019` — OPEN_UNRESOLVED: explicit typed emit/yield/return semantics are needed before production lowering.
3. `H-CC-NAMED-CYCLE-020` — OPEN_NOT_JUSTIFIED_AS_LANGUAGE_CHANGE: fix the unreferenced fixture label first; add callable named-cycle syntax only if a real application/FRANK counterexample demands it.

## Highest-information next execution

Do **not** redesign ClayCode again.

1. Build/freeze one grammar-conformant generic control fixture.
2. Parse it with the production-bound frontend.
3. Emit a typed IR that explicitly distinguishes event emission from yield/return/termination.
4. Hash and link every compiler stage.
5. Lower the identical typed IR to the current native reference path and a second backend when feasible.
6. Differentially execute positive, negative, mutation and short-circuit/termination cases.
7. Credit `CC-WP-02/03/06/11` only when the source-to-execution ancestry is reproducible.
8. Reuse that chain format for H1→H2 FRANK differential replay.

If an existing admitted universal-core artifact already defines generic return/yield semantics, bind and test it rather than inventing another construct.

## Completion boundary

Completed:

- canonical boot and re-read;
- current trigger/protocol routing;
- current G9/grammar/prior-fixture/prior-lowering inspection;
- deep ClayGraph V2 and UnifiedDB V9 input;
- concurrent ClayCode worker assimilation;
- bounded executable header discriminator;
- 20,000-case emit-vs-return semantic materiality test;
- 10,000-label semantic-vs-contract identity discriminator;
- primary-source external compiler triangulation;
- Goodman review;
- nine-branch feedback manifest;
- negative results, hypotheses, tool/interconnect manifests and final report.

Not completed and not falsely claimed:

- production parser implementation;
- target Andreas Ubuntu execution;
- fresh E2B execution;
- official repo-local interconnect/goodman validator PASS;
- APP-01..10 PASS;
- any CC work-package PASS;
- BASE / GENERAL_PURPOSE gate PASS;
- canonical ClayCode promotion.
