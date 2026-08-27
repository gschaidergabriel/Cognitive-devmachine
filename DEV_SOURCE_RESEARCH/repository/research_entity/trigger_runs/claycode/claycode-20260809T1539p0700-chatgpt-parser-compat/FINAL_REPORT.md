# ClayCode Trigger Run — G9 Parser / Grammar Compatibility

Run: `claycode-20260809T1539p0700-chatgpt-parser-compat`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **none**

## Executive result

This run found a concrete BASE-stage executable blocker without finding a reason to redesign ClayCode semantics.

The admitted `CLAYCODE_G9_FUSION_SPEC_V3.clay` and `DIALECT_REGISTRY_V3.clay` use source constructs that the admitted `grammar.ebnf` does not correctly describe. The baseline incompatibility was tested locally and then independently replicated in the runtime-verified E2B sandbox: **5/5 tested current constructs failed or semantically misparsed under the baseline grammar surface**.

A first minimal compatibility patch improved the situation but is **not release-ready**. Local testing accepted all five tested constructs; independent E2B replication accepted four and exposed one remaining lexical/grammar ambiguity in open-ended relation-word syntax (`never_implies` vs generic identifier lexing). The malformed generic negative control remained rejected in both environments.

Therefore the current best action remains the project law **less change, more compile**, refined to:

`freeze intended semantics -> repair/freeze unambiguous parser -> full admitted G9 corpus -> deterministic typed canonical IR -> semantic symbol resolver -> type/effect -> evaluator/lowering -> application proofs`

No G9 semantic concept is promoted or refuted by this result.

## Fusion 1 — internal state

The current program is in `BASE_CLAYCODE_RELEASE`. The release workspace still has all fourteen CC-WP packages OPEN and no accepted application proof. Current G9 semantics already distinguish semantic/provenance identity, effect intent from execution authority, UnifiedDB semantic state from physical layout, and ClayGraph activation from truth/authority.

The mandatory adaptive-visual-learning directive adds a concrete BASE requirement: ClayCode must express versioned classifier/prototype state, trusted example provenance/tier, calibrated known/unknown/conflict outputs, candidate promotion/rollback, resource budgets and replay hooks. This run found no missing semantic primitive specific to those requirements; parser/toolchain compatibility is the earlier blocker.

## Executable experiment A — local grammar compatibility

Experiment: `EXP-CC-G9-GRAMMAR-COMPAT-20260809`.

Baseline failures/misparses:

1. `POS|NEG` union type — rejected.
2. `diff>0` comparison — rejected.
3. `projection(reader:ReaderId)->Ref` interface method — rejected.
4. `Delta never_implies epistemic_upgrade` relation-word form — rejected.
5. `if residual.effect {...}` — syntactically accepted by the baseline approximation but structurally wrong: `if` became an ordinary identifier/action and the block could be interpreted as set syntax.

The local compatibility candidate accepted all five and still rejected `record Broken {x:Set<Ref}`.

Classification: `EXECUTABLE_COUNTEREXAMPLE_PARSER_SURFACE`.

## Executable experiment B — E2B independent replication

Experiment: `EXP-CC-G9-GRAMMAR-E2B-REPLICATION-20260809` through the repo-native research-tool bridge.

E2B result:

- baseline union: fail;
- baseline comparison: fail;
- baseline method: fail;
- baseline relation word: fail;
- baseline `if`: parsed but semantically wrong;
- first candidate patch: union/comparison/method/`if` pass;
- first candidate patch: relation-word case still fails;
- malformed generic negative: rejected under baseline and candidate;
- process exit code: 0.

This independently replicates the baseline defect while falsifying the stronger claim that the first minimal parser patch is already sufficient. The remaining relation failure strengthens the requirement for an explicit declared relation/predicate surface plus typed symbol resolution. Simply treating arbitrary identifiers as operators would trade one grammar failure for accidental semantics.

## Canonicalization probe

A separate local probe normalized the compatibility parse tree and SHA-256 hashed it. Three comment/whitespace variants produced the same probe hash; changing the tested union from `POS|NEG` to `POS|UNKNOWN` changed the hash.

This supports feasibility of deterministic surface normalization for the tested subset. It is **not** the final ClayCode `semantic_hash` and must not be conflated with provenance-bound contract-instance identity.

## ClayGraph finding

Current ClayGraph schemas preserve graph epochs, typed relations/hyperrelations, activation, assemblies, projection/selection/receiver receipts, provenance/admissibility and explicit authority classes. Current G9 already contains `GraphDelta`, typed hyperrelation roles and the rule that derived relations cannot authorize effects.

This run found **no executable ClayGraph counterexample requiring a new ClayCode semantic primitive**. The actionable requirement is to prove these existing concepts survive parser -> canonical IR -> type/effect -> runtime lowering. Conceptual alignment is not executable coverage.

## UnifiedDB finding

Current UnifiedDB exposes semantic transactions, transaction operations, state epochs, semantic records, query receipts, evidence/claim references and snapshots. G9 already models `ViewDelta`, semantic-vs-physical unification and bounded cognitive views.

This run found **no executable UnifiedDB counterexample requiring semantic redesign**. Future BASE tests should use real transaction/query/replay examples to prove canonical identity, snapshot consistency, store authority and rollback semantics rather than adding database-specific syntax speculatively.

## FRANK / Harness and Goodman review

A bounded lookup did not locate a current `FRANK_ARCHITECTURE.claycode.json`; no substitute was fabricated. Current Harness and fixed FRANK v0.1 requirements were used as provisional architecture requirements.

Goodman verdicts:

- external capability/commit authority boundary: `SUPPORTED` by independent historical safety-failure lineage, with compiler/FFI adversarial testing still required;
- claim that current ClayCode is already executable enough to carry frozen FRANK: `UNRESOLVED` because this run found a parser-surface blocker;
- graph activation vs semantic truth/authority separation: `REFINED` as a retained normative safety invariant, not independent causal/performance proof.

## External primary-source triangulation

External sources were used only as independent implementation analogues, not ClayCode evidence promotion.

- MLIR demonstrates an IR architecture where textual, in-memory and serialized forms can represent the same semantic content and where dialect operations/types are extensible with verification. This supports `surface syntax != canonical semantic IR`.
- Tree-sitter documents grammar conflicts, precedence and contextual lexing. That is directly relevant to both the baseline `if` structural ambiguity and the E2B relation-word lexer conflict.
- WebAssembly Component Model WIT provides typed interfaces/worlds/resources between components. It is a useful FFI analogue, while ClayCode's capability/commit gateway remains separately necessary because resource typing does not itself confer authority safety.

## Infrastructure negative result

The mandatory `tools/research_interconnect_preflight.py` is inconsistent with the authoritative trigger rename `clay -> clayresearch`. The current registry-derived scientific branch set includes `clayresearch`; the tool's hard-coded priority/alias tables still use `clay`, and its fail-closed set-equality guard would raise.

This run materialized a transparent manual current-registry interconnect manifest and records `NR-RAE-INTERCONNECT-001`. It does not claim the mandatory preflight passed.

## Fusion 2 — architecture/research delta

The strongest current interpretation is **not** “ClayCode needs more features.” It is:

1. freeze intended G9 semantic concepts unless a real application/FRANK counterexample forces change;
2. make the concrete parser faithfully represent the syntax admitted G9 actually uses;
3. reserve structural control forms so valid-looking programs cannot silently acquire the wrong AST;
4. do not make arbitrary identifiers semantic operators merely to keep the grammar open-ended;
5. introduce an explicit relation/predicate declaration or otherwise unambiguous surface, then resolve/type-check symbols in canonical IR;
6. compile the complete admitted G9 + dialect corpus to one deterministic typed canonical IR;
7. only then judge missing types/effects/runtime/FFI/stdlib semantics through the mandatory application suite and a real FRANK component.

## Hypothesis / negative-result delta

OPEN hypotheses include:

- `H-CC-G9-PARSER-001`: admitted grammar/current-source incompatibility, now independently E2B-replicated at exact tested scope;
- `H-CC-G9-SURFACE-002`: parser repair can restore compatibility without semantic redesign, but the first patch is incomplete;
- `H-CC-G9-AMBIG-003`: explicit structural controls and semantic relation resolution are required;
- `H-CC-G9-IR-004`: extensible typed canonical IR should absorb surface evolution better than direct grammar churn;
- `H-CC-G9-FFI-005`: typed interface/resource FFI may remain general-purpose while authority stays externally gated;
- `H-RAE-PREFLIGHT-006`: current interconnect preflight is broken by the trigger rename;
- `H-CC-G9-RELATION-007`: generic relation tokens beside generic identifiers are insufficient without unambiguous declaration/resolution.

Negative results:

- `NR-CC-G9-GRAMMAR-001` — current grammar is not release-ready for tested admitted source constructs;
- independent counterevidence — the first parser repair is also not release-ready because the relation-word case did not replicate;
- `NR-RAE-INTERCONNECT-001` — current mandatory preflight cannot honestly PASS against the renamed registry.

## Implementation handoff

A proposed BASE work item was emitted to the work fabric: `WORK-CC-BASE-G9-PARSER-FREEZE-001`.

Completion should require:

- locate/declare the actual normative parser implementation;
- parse complete admitted G9 spec, dialect registry and current candidate corpus;
- explicit/unambiguous control and relation/predicate surfaces;
- deterministic typed canonical IR and roundtrip checks;
- precise rejection of malformed/ambiguous/undeclared semantics;
- stable semantic identity distinct from provenance-bound contract identity;
- then type/effect checker and lowering;
- no semantic change unless linked to an executable counterexample.

## Completion / non-completion

Completed: canonical boot, bounded all-branch interconnect, deep ClayGraph/UnifiedDB input, Goodman review, local executable parser counterexample, deterministic canonicalization probe, runtime-verified E2B independent replication, external primary-source triangulation, hypotheses, negative results, Micro-Packet, cross-room delta, work handoff and durable run report.

Not completed and not falsely claimed: production parser repair, full-corpus parse, canonical IR implementation, type/effect checker, compiler/lowering, application proof suite, FRANK component compilation, mandatory interconnect-preflight PASS, BASE gate PASS or canonical ClayCode promotion.
