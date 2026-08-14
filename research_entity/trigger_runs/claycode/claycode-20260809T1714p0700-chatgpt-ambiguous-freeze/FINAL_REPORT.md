# ClayCode Trigger Run — Ambiguous Legacy Rule Semantic-Freeze Gate

Run: `claycode-20260809T1714p0700-chatgpt-ambiguous-freeze`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**  
Gate advancement: **NONE**

## Executive result

This run fused the newest concurrent ClayCode evidence rather than repeating already-running parser work.

The live rule-surface partition had already shown that the current G9 rule surface is not best repaired by continuously enlarging a flat operator set: a closed expression proxy plus registered declarative PredicateIR/ConstraintIR deterministically covered 50/53 current G9 rule lines, while three legacy clauses remained semantically ambiguous.

This run targeted only those three residual clauses:

1. `Needle.lowers EffectIntent -> concrete_adapter_plan`
2. `Claude_only consumes latest stack + writes task receipts`
3. `training_data personalizes_for_Andreas_when_FRANK_target && preserves_general_transfer_variants`

For each clause, at least two materially different plausible ASTs were constructed and produced distinct semantic hashes. Therefore automatic normalization is unsafe: syntax alone does not establish one intended meaning.

A registry-gated typed n-ary PredicateIR test then showed that, **after** an explicit semantic freeze chooses an intended representation, deterministic identity and strong fail-closed validation are feasible:

- explicit candidate IR validated: 3/3;
- unknown relation mutations rejected: 10000/10000;
- wrong-arity mutations rejected: 10000/10000;
- semantic hash remained stable under 10000/10000 surface-whitespace variants.

The candidate IR trees used in the experiment are test fixtures only. They are not evidence of the intended meaning of the original three lines and are not authorized source rewrites.

## Current-state grounding

Verified canonical state at run start and again before durable write:

- entity: RAE-8.8 / Clay research entity;
- revision: 2;
- state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`;
- stage: `BASE_CLAYCODE_RELEASE`;
- BASE rule: `less change, more compile`;
- Frank v0.1 target: Ubuntu Linux developer system only.

The durable ClayCode workspace still reports all 14 BASE work packages as OPEN, while fresh concurrent run receipts show significant experimental progress. No work package is marked complete by this run.

## Fusion with current live research

### Existing self-conformance evidence

Current G9 V3 uses constructs not represented by the current `grammar.ebnf`, including relational operators and `if`. A previous minimal repair improved sampled parsing but did not close self-conformance. Additional evidence showed:

- flat expression parsing leaves precedence/associativity underdetermined;
- `receipt? or residual` has unresolved fallback semantics;
- sampled current rule and interface corpora remain incomplete under the minimal patch.

### Live rule-surface partition

The immediately preceding concurrent run measured 53 current G9 rule lines:

- current expression proxy: 29/53;
- minimal relational-operator patch: 33/53;
- registered PredicateIR normalization: +17;
- deterministic total: 50/53 (94.3%);
- residual ambiguous lines: 3.

It also showed why a fail-open arbitrary-relation grammar is unsafe: generated nonsense relation names were accepted by the permissive arm, while a registry-gated arm rejected unknown relations.

### Relation and resource evidence

Recent ClayCode relation-IR work supports keeping semantic relation identity distinct from capability/effect authority. Recent resource-lifetime work independently supports typed resource handles, lifetime/freshness checks and external authority boundaries rather than inventing domain-specific syntax.

These findings converge on implementation discipline, not broad semantic expansion.

## External evidence

Primary technical documentation was used only as independent engineering evidence, not as proof of ClayCode correctness.

- Tree-sitter grammar documentation treats flat binary expression grammars as ambiguous unless precedence and associativity are made explicit. This supports separating executable expression precedence from domain semantic interpretation.
- MLIR's declarative operation/constraint model provides an independent analogue for explicit typed operation definitions, traits and constraints rather than unconstrained relation words.
- Rust's language reference provides an independent example of specified lazy short-circuit boolean operators, reinforcing that boolean/fallback evaluation order belongs in executable semantics and cannot be left implicit.

None of these external systems establishes the intended meaning of ClayCode's three legacy clauses.

## Executable experiment

Artifact: `ambiguous_semantic_freeze_probe.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`

The probe defined a small relation-signature registry with fixed n-ary arity and canonical JSON semantic hashing. For each ambiguous source clause, two distinct plausible ASTs were represented. Distinct semantic hashes confirmed that choosing one interpretation is a semantic decision, not harmless formatting normalization.

The test then selected one candidate tree per clause solely as a fixture for the post-freeze validator. The validator required:

- registered relation identity;
- exact declared arity;
- recursively valid typed relation nodes or atomic references;
- canonical serialization before semantic hashing.

Adversarial mutations verified fail-closed behavior for unknown relation names and wrong arity.

## Hypotheses

`H-CC-AF-01` — supported for the local proxy: automatic normalization of the three residual rules is unsafe before an authoritative semantic freeze; post-freeze typed n-ary PredicateIR can preserve deterministic identity.

`H-CC-AF-02` — supported adversarially for the local proxy: a fixed relation-signature registry provides a safer BASE boundary than arbitrary bare relation identifiers.

`H-CC-AF-03` — open/refined: executable operator precedence and declarative predicate identity should likely be separate typed frontend/IR layers. A production compiler can still falsify this if one grammar proves equally precise, safe and simpler.

## Negative results

`NR-CC-AF-01`: the three residual legacy clauses cannot be safely auto-normalized from source syntax alone.

`NR-CC-AF-02`: a fail-open arbitrary relation surface is not justified for BASE by current evidence.

These results are preserved rather than silently repaired away.

## Goodman anti-echo review

FRANK and ClayCode share project ancestry, so their agreement is not independent evidence.

Verdict: **REFINED**.

Supported/refined engineering boundary:

1. executable expressions require explicit precedence/associativity and evaluation semantics;
2. declarative relations should resolve through typed relation signatures/PredicateIR;
3. legacy source that admits multiple materially different ASTs should enter a fail-closed `SEMANTIC_FREEZE_REQUIRED` state until authoritative semantics are bound;
4. representation and semantic identity remain separate from capability/effect authority.

Not supported:

- the exact intended AST of any ambiguous legacy line;
- automatic rewrite of current G9 source;
- production parser completeness;
- Ubuntu target equivalence;
- any BASE gate advancement.

## Cross-branch implications

### ClayGraph

Typed n-ary relation identity and arity/role signatures should be resolved before graph mutation or projection. Ambiguous legacy text must not silently create graph relations or truth. Activation and selection remain non-authoritative.

### UnifiedDB

A frozen semantic relation identity/hash can be persisted separately from source text, work identity and effect authority. Nothing in this result implies a physical monolithic database.

### FRANK / Harness

FRANK-specific syntax is not justified. Harness/compiler fixtures should reject the three ambiguous rules until an authoritative expected IR is bound. After freeze, differential tests should verify roundtrip semantic identity and that the representation does not expand authority.

### GWT / Emergenz

No change: parser determinism is not broadcast/use/effect/re-entry evidence and is not evidence of causal emergence.

### Hyperposition

Until semantic freeze, multiple plausible interpretations are genuine alternatives and should not be collapsed by arbitrary precedence rules.

## BASE architecture delta

The highest-value frontend sequence is now more specific:

1. implement a real parser with explicit executable precedence/associativity and evaluation rules;
2. lower executable expressions into typed executable IR;
3. add registry-gated typed `PredicateIR/ConstraintIR` for declarative relations with declared identity, arity and role/type constraints;
4. add a fail-closed `SEMANTIC_FREEZE_REQUIRED` diagnostic/state for legacy clauses that map to multiple materially different ASTs;
5. bind authoritative expected IR for the three current ambiguous clauses before source rewrite;
6. make current G9 V3 a mandatory self-conformance fixture;
7. prove parse -> canonical IR -> semantic hash -> print/roundtrip stability;
8. run the same fixtures through type/effect checking and Ubuntu-target lowering;
9. only then expand toward general-purpose application proofs.

This delta reduces ambiguity around `CC-WP-01-SPEC-FREEZE`, `CC-WP-02-PARSER-CANON`, `CC-WP-03-IR-TYPES` and `CC-WP-04-TYPE-EFFECT`, but completes none of them.

## Tool/runtime limits

- E2B was not exposed to this hosted worker.
- Andreas' exact Ubuntu developer host was not exposed.
- Repository-local preflight/Goodman scripts could not be executed without a repository checkout; equivalent manifests/review were written from verified remote state, but script execution is not claimed.
- One first GitHub write attempt hit an HTTP 409 because concurrent workers advanced `main`; the conflict was detected, no false commit was claimed, the remote head was refreshed, and the unique run path was successfully written on retry.

## Next discriminating test

Build the production frontend gate and run:

`current G9 source -> parser with explicit precedence + relation registry -> typed executable IR / PredicateIR partition -> SEMANTIC_FREEZE_REQUIRED for the 3 residual clauses -> authoritative expected-IR binding -> canonical semantic hash -> roundtrip -> type/effect -> Ubuntu execution receipt`

A semantic rewrite should occur only when the intended IR is established by authoritative lineage or an explicit evidence-bearing freeze decision.

## Provenance

Origin actor: `chatgpt-secondary`  
Provider/model: OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Executable evidence class: local hosted Linux proxy  
External evidence class: primary technical documentation  
Canonical promotion: none
