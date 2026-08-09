# ClayCode Trigger Run — Declared Relation Resolver Discriminator

Run: `claycode-20260809T155804p0700-chatgpt-declared-relations`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (`IN_PROGRESS`)  
Promotion: **none**

## Executive result

This run did not duplicate the concurrent production-parser or strict-normalization work. It joined the new mandatory ClayCode worker federation, detected overlap, and partitioned into a discriminating question:

> Can selected readable word-relations remain in ClayCode if they are admitted only through a finite declared semantic resolver, rather than either (a) normalizing every prose-like relation to punctuation/calls or (b) treating arbitrary identifiers as operators?

A local executable micro-oracle produced a useful third candidate.

- 8/8 sampled current relation/surface forms were accepted by the declared resolver.
- 50,000/50,000 generated unknown relation words were accepted by a naive arbitrary-identifier infix parser, while the declared resolver accepted 0/50,000.
- 20,000/20,000 digit-prefixed semantic symbols were distinguishable from numbers; 20,000 pure-number controls produced zero symbol overlap.
- 10,000/10,000 whitespace variants preserved the canonical AST hash.
- Changing a declared relation changed the semantic hash.

This is **not** a production parser result and does not prove lexical closure. It does show that readable relation names do not require arbitrary implicit semantics: parseability can remain separate from typed semantic admission.

## Current concurrent state assimilated

Before final synthesis the run re-read the Research Center state and incorporated three important concurrent changes:

1. `grammar.ebnf` now includes union types; that specific gap has begun to close.
2. The strict-syntax worker broadened the parser counterexample set and found a strict-normalization proxy that passed 10/10 representative cases while keeping `CC-WP-02` open.
3. A relation-sigil worker produced an executable `@relation` candidate: 8/8 valid sampled relation families parsed/resolved and 12/12 mutation cases rejected, with one-character mean/max overhead. That worker explicitly named a declared-infix alternative as the next comparator.

Therefore the active surface decision is no longer a binary choice. There are now three live implementation policies:

- **N — strict normalization:** rewrite prose-like forms to closed punctuation/calls/qualified fields;
- **S — relation sigil:** use lexically explicit `@relation` / `@"quoted relation"` plus typed resolution;
- **D — declared bare relation:** retain selected bare word-relations, but semantic admission occurs only through a finite declared typed registry.

No candidate is promoted.

## Executable experiment

Experiment: `EXP-CC-G9-DECLARED-RELATION-RESOLVER-20260809`.

Artifact: `STRICT_SURFACE_RESOLVER_PROBE.py`.

Tested representative forms:

- `Delta never_implies epistemic_upgrade`
- `effect.Intent may_reference capability_id`
- `NativeCognitionTask.forbidden_burden includes [...]`
- `delegation returns narrower_or_equal`
- `4B_emits EffectIntent`
- `external_effect lifecycle=[...]`
- `diff>0 => ADD_OR_STRENGTHEN`
- `model_output!=authority`

The micro-oracle separates:

- closed punctuation operators;
- finite declared infix relations;
- finite declared prefix relations;
- finite declared property forms;
- ordinary symbols/numbers/lists/calls.

Unknown relation words fail semantic admission. This directly falsifies the strongest unsafe version of generic infix: **parser acceptance alone cannot be allowed to mint operator meaning**.

## Negative result

`NR-CC-GENERIC-INFIX-NORESOLVER-20260809`

A naive arbitrary identifier-infix parser accepted all 50,000 generated unknown relation words. That is a negative result for *generic infix without a typed semantic resolver*, not for generic infix plus a later strict resolver.

The stronger counterhypothesis remains open: a generic parser plus typed symbol resolution might be equivalent to the finite declared relation surface and could still win on grammar simplicity or extensibility.

## Fusion 1 / ClayGraph

ClayGraph already distinguishes graph state, typed hyperrelations, roles, projection receipts, selection receipts, receiver receipts, activation and provenance/admissibility. The language surface must therefore not convert an arbitrary readable word into graph relation identity merely because it parses.

This run refines the ClayGraph interface requirement:

`surface token -> declared semantic relation identity -> typed canonical IR -> graph mutation/projection`

Activation/relevance remains non-authoritative.

No ClayGraph semantic primitive was added or changed.

## Fusion 1 / UnifiedDB

UnifiedDB V9 separates dynamic work specifications, capability observations, scheduler receipts, leases and execution receipts. That reinforces the same boundary: a word in source text must not mint store role, capability identity, work authority or execution authority.

This run refines the persistence/interface requirement:

- relation/predicate identity must be versionable and resolvable;
- parser convenience must not bypass typed semantic identity;
- exact authority still comes from external capability/effect state, never a relation name.

No physical database consolidation decision changed.

## FRANK / Harness / Goodman

No current `FRANK_ARCHITECTURE.claycode.json` was established by this worker; it was not fabricated. Current fused FRANK overlays and owner-fixed v0.1 requirements were used as provisional requirements only.

Goodman review:

- representation must preserve FRANK distinctions without accidental parser semantic promotion: `REFINED`;
- full adaptive visual learner sufficiency without new primitives: `UNRESOLVED` in this run, because no full learner compile/replay was executed.

No FRANK or Harness gate advanced.

## External triangulation

Independent primary implementation analogues support the architectural separation being tested:

- Tree-sitter explicitly distinguishes lexical token conflicts, contextual lexing, keyword extraction and parser ambiguity rather than assuming arbitrary identifier words have operator meaning.
- MLIR ODS centralizes operation definitions, constraints, parsing/printing and verification; MLIR symbol tables require named symbols to resolve within explicit symbol-table semantics.

These sources support explicit declaration/resolution as a compiler architecture pattern. They do not prove D, S or N is the best ClayCode surface.

## Fusion 2 — new architecture/research delta

The strongest current synthesis is:

1. Keep the existing G9 semantic concepts frozen unless a real application/FRANK counterexample forces change.
2. Keep `CC-WP-02-PARSER-CANON` OPEN.
3. Do not allow parser acceptance to confer semantic relation/operator identity.
4. Do not choose between strict normalization, `@relation`, and declared bare relations from aesthetics.
5. Run a matched full-current-G9+dialects benchmark over N/S/D with the same typed canonical IR oracle.
6. Measure at minimum:
   - full-corpus parse closure;
   - exact AST intent;
   - roundtrip and semantic-hash stability;
   - malformed/typo mutation survival;
   - diagnostics quality;
   - migration edit count;
   - character/token/context cost;
   - target-reader/model repair cost;
   - compiler complexity and latency.
7. Choose the surface policy only after that comparison; semantic IR can remain independent of the winning source spelling.

## Hypotheses

- `H-CC-DECLREL-001` — finite declared relation registry can preserve selected readable word-relations while failing closed.
- `H-CC-RELREG-COST-002` — relation identity belongs in typed semantic registration, not lexer-only keyword accretion.
- `H-CC-NORMALIZE-003` — strict normalization remains a live competitor and may still be cheaper/better.
- Concurrent `@relation` sigil remains a live competitor and is now a required arm of the same falsifier.

## Research Center / federation result

The worker joined and claimed through the Research Center, reused prior parser/E2B/canonicalization evidence, detected concurrent strict-syntax and relation-sigil work, and did not claim those results as independent support. Its material delta was routed back to the center as a **discriminating alternative**, not a duplicate production parser effort.

## Completion / non-completion

Completed in this run:

- canonical re-verification;
- federated join/claim/pulse;
- current grammar/center reread;
- deep ClayGraph and UnifiedDB grounding;
- executable declared-relation micro-oracle;
- 50k unknown-relation fuzz;
- 20k digit-symbol / 20k numeric separation fuzz;
- 10k semantic-hash whitespace fuzz;
- primary-source external triangulation;
- Goodman review;
- hypothesis and negative-result preservation;
- all-branch feedback and final report.

Not completed and not falsely claimed:

- official interconnect-preflight PASS;
- production parser repair;
- full G9+dialect corpus parse;
- N/S/D matched benchmark;
- canonical typed IR implementation;
- type/effect checker;
- evaluator/compiler/lowering/runtime;
- application proof suite;
- full FRANK learner compile/replay;
- `CC-WP-02` PASS;
- BASE gate PASS;
- canonical ClayCode promotion.
