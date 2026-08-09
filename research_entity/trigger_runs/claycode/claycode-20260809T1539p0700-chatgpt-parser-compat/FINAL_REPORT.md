# ClayCode Trigger Run — G9 Parser / Grammar Compatibility

Run: `claycode-20260809T1539p0700-chatgpt-parser-compat`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **none**

## Executive result

This run found a concrete BASE-stage executable blocker without finding a reason to redesign ClayCode semantics.

The admitted `CLAYCODE_G9_FUSION_SPEC_V3.clay` and `DIALECT_REGISTRY_V3.clay` already use source constructs that the admitted `grammar.ebnf` does not correctly describe. A local executable parser probe found five current constructs that the baseline grammar rejected or semantically misparsed: union types, comparison operators, interface method signatures, relation-word operations and explicit `if` control. A minimal compatibility candidate accepted all five while continuing to reject the malformed generic negative control.

Therefore the current best action follows the project law **less change, more compile**:

`repair/freeze parser + canonicalizer -> full admitted G9 corpus -> typed canonical IR -> semantic resolver/type-effect -> evaluator/lowering -> application proofs`

No G9 semantic concept is promoted or refuted by this result.

## Fusion 1 — current internal state

The current program is in `BASE_CLAYCODE_RELEASE`. The release workspace still has all fourteen CC-WP packages OPEN and no accepted application proof. Current G9 semantics already distinguish semantic/provenance identity, effect intent from execution authority, UnifiedDB semantic state from physical layout, and ClayGraph activation from truth/authority.

The mandatory adaptive-visual-learning directive adds a concrete BASE requirement: ClayCode must express versioned classifier/prototype state, trusted example provenance/tier, calibrated known/unknown/conflict outputs, candidate promotion/rollback, resource budgets and replay hooks. This run found no missing semantic primitive specific to those requirements; parser/toolchain compatibility is the earlier blocker.

## Executable experiment — grammar compatibility

Experiment: `EXP-CC-G9-GRAMMAR-COMPAT-20260809`.

Observed current-source failures/misparses under the published grammar:

1. `POS|NEG` union type — rejected.
2. `diff>0` comparison — rejected.
3. `projection(reader:ReaderId)->Ref` interface method — rejected.
4. `Delta never_implies epistemic_upgrade` relation-word form — rejected.
5. `if residual.effect {...}` — syntactically accepted by the baseline approximation but with the wrong structure: `if` became an ordinary identifier/action and the block could be interpreted as set syntax.

Minimal candidate parser-surface repair accepted all five and still rejected `record Broken {x:Set<Ref}`.

Classification: `EXECUTABLE_COUNTEREXAMPLE_PARSER_SURFACE`.

Interpretation boundary: this proves an exact compatibility defect in the checked grammar surface. It does **not** prove no richer production parser exists elsewhere and does not justify semantic redesign.

## Canonicalization probe

A second local test normalized the patched parse tree and SHA-256 hashed it. Three comment/whitespace variants produced the same probe hash; changing the tested union from `POS|NEG` to `POS|UNKNOWN` changed the hash.

This is evidence that a deterministic surface-normalization route is feasible for the tested subset. It is **not** the final ClayCode `semantic_hash` and must not be conflated with the provenance-bound contract-instance identity.

## ClayGraph finding

Current ClayGraph schemas already preserve graph epochs, typed relations/hyperrelations, activation, assemblies, projection/selection/receiver receipts, provenance/admissibility and explicit authority classes. Current G9 already contains `GraphDelta`, typed hyperrelation roles and the rule that derived relations cannot authorize effects.

This run found **no executable ClayGraph counterexample requiring a new ClayCode semantic primitive**. The actionable requirement is to prove these existing concepts survive parser -> canonical IR -> type/effect -> runtime lowering. Until then, conceptual alignment is not executable coverage.

## UnifiedDB finding

Current UnifiedDB exposes semantic transactions, transaction operations, state epochs, semantic records, query receipts, evidence/claim references and snapshots. G9 already models `ViewDelta`, semantic-vs-physical unification and bounded cognitive views.

This run found **no executable UnifiedDB counterexample requiring semantic redesign**. Future BASE tests should use real transaction/query/replay examples to prove canonical identity, snapshot consistency, store authority and rollback semantics rather than adding database-specific syntax speculatively.

## FRANK / Harness finding

A bounded lookup did not locate a current `FRANK_ARCHITECTURE.claycode.json`; no substitute was fabricated. Current Harness and fixed FRANK v0.1 requirements were used as provisional architecture requirements.

Goodman review result:

- external capability/commit authority boundary: `SUPPORTED` by independent historical safety-failure lineage, with compiler/FFI adversarial testing still required;
- claim that current ClayCode is already executable enough to carry frozen FRANK: `UNRESOLVED` because this run found a parser-surface blocker;
- graph activation vs semantic truth/authority separation: `REFINED` as a retained normative safety invariant, not independent causal/performance proof.

## External research triangulation

Primary external analogues were used only to challenge/shape implementation, not as ClayCode evidence promotion.

- MLIR independently demonstrates an IR architecture where human-readable textual, in-memory and serialized forms describe the same semantic content and where dialects/operations/types can be extended with verification. This supports the architectural direction `surface syntax != canonical semantic IR`.
- Tree-sitter documentation emphasizes explicit grammar conflicts, precedence and contextual lexing. This is directly relevant to avoiding the observed silent `if`-as-identifier structural ambiguity.
- WebAssembly Component Model WIT provides typed interfaces/worlds/resources between components. This is a useful FFI analogue, but WIT resource typing itself does not provide ClayCode execution authority; ClayCode's external capability/commit boundary remains separately required.

## Infrastructure negative result

The mandatory `tools/research_interconnect_preflight.py` is currently inconsistent with the authoritative trigger rename `clay -> clayresearch`. The current registry-derived scientific branch set includes `clayresearch`; the tool's hard-coded priority/alias tables still use `clay`, and its fail-closed set-equality guard would raise.

This run therefore materialized a transparent manual current-registry interconnect manifest and records `NR-RAE-INTERCONNECT-001`. It does not claim the mandatory preflight passed.

## Fusion 2 — architecture/research delta

The highest-information interpretation is not “ClayCode needs more features.” It is:

1. freeze the currently intended G9 semantic concepts unless a real application/FRANK counterexample forces change;
2. make the concrete parser faithfully represent the syntax that admitted G9 already uses;
3. reserve control keywords/structures so a valid-looking program cannot silently acquire the wrong AST;
4. resolve extensible relation/predicate names in the typed semantic layer rather than granting arbitrary identifiers semantics merely because the parser accepts them;
5. compile the entire admitted G9 + dialect corpus to one deterministic typed canonical IR;
6. only then judge missing types/effects/runtime/FFI/stdlib semantics through the mandatory app suite and real FRANK component.

## Hypothesis state

New OPEN hypotheses:

- `H-CC-G9-PARSER-001`: admitted grammar/current-source incompatibility;
- `H-CC-G9-SURFACE-002`: parser repair can restore compatibility without semantic redesign;
- `H-CC-G9-AMBIG-003`: explicit control/relation structure is required to prevent silent misparse;
- `H-CC-G9-IR-004`: extensible typed canonical IR should absorb surface evolution better than direct grammar churn;
- `H-CC-G9-FFI-005`: typed interface/resource FFI can remain general-purpose while authority stays externally gated;
- `H-RAE-PREFLIGHT-006`: current preflight is broken by the trigger rename.

Negative results:

- `NR-CC-G9-GRAMMAR-001` — current grammar is not release-ready for tested admitted source constructs;
- `NR-RAE-INTERCONNECT-001` — current mandatory preflight cannot honestly PASS against the renamed registry.

## Recommended implementation handoff

Create/revise a BASE work item for a local build executor to:

- locate/declare the actual normative parser implementation;
- update grammar/parser tests for every admitted G9 construct;
- parse the complete admitted G9 spec, dialect registry and current candidate corpus;
- build deterministic canonical IR and roundtrip checks;
- reject malformed/ambiguous controls and undeclared semantic operators with precise diagnostics;
- preserve `semantic_hash` vs provenance-bound contract identity;
- run type/effect checker next;
- avoid semantic changes unless this executable corpus yields a genuine semantic counterexample.

## Completion / non-completion

Completed in this run: canonical boot, all-branch bounded interconnect, deep ClayGraph/UnifiedDB input, Goodman review, executable parser counterexample, canonicalization probe, external primary-source triangulation, hypotheses, negative results and durable run report.

Not completed and not falsely claimed: full G9 production parser repair, full-corpus parse, canonical IR implementation, type/effect checker, compiler/lowering, application proof suite, FRANK component compilation, E2B replication, mandatory preflight PASS, BASE gate PASS or canonical ClayCode promotion.
