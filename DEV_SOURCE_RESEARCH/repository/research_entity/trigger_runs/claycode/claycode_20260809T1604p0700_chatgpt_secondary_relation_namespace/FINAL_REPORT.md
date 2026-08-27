# ClayCode Trigger Run — Relation Namespace Discriminator

Run: `claycode_20260809T1604p0700_chatgpt_secondary_relation_namespace`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (`IN_PROGRESS`)  
Target host: Ubuntu Linux developer system

## Executive result

This run found a new executable counterexample after assimilating the concurrent parser workers.

The repository already had three competing approaches for prose-like semantic relations:

1. finite declared relation/predicate words;
2. a generic canonical form such as `relation("depends",x,y)`;
3. a compact `@relation` sigil candidate.

The `@relation` worker reported 8/8 valid relation examples and 12/12 mutation rejection, but its corpus did not combine the new token class with ClayCode's already-existing `@ref` syntax. The current G9 grammar defines references with the same `@` prefix.

A combined executable Lark discriminator therefore tested references and relations together under three parser/lexer modes:

| candidate | LALR contextual | LALR basic | Earley dynamic |
|---|---:|---:|---:|
| current `@relation` candidate | 5/7 | 3/7 | 7/7 |
| lexically disjoint sigil control | 7/7 | 7/7 | 7/7 |
| quoted generic relation call | 7/7 | 7/7 | 7/7 |

The failures include existing standalone refs (`@foo`, `@research_entity/global/x`) and, under basic LALR lexing, relation forms whose operand is an `@ref`.

**Negative result:** the current `@relation` proposal is not established as a separate backend-neutral lexical namespace. Its relation-only success does not prove coexistence with the existing language. Do not promote it as written.

This does **not** justify new cognitive semantics. The stronger architecture candidate is smaller: one typed canonical `Relation` node/IR identity, with compact surface forms permitted only when they deterministically lower to that node and pass full-corpus lexer-overlap, roundtrip, mutation, diagnostic and semantic-hash tests.

## Why this is new information

Earlier same-day ClayCode runs already established:

- checked-in G9 source and EBNF are not surface-closed;
- union+`if` repair is insufficient;
- strict normalization can close a representative 10-case surface proxy;
- type-directed canonicalization is required;
- narrow FRANK RecognitionValidity / AdaptiveStatePromotion / publication gates are expressible without new primitives;
- a prototype admission/promotion/rollback/effect lowering path passed deterministic proxy fixtures.

This run does not count those findings again. It adversarially tests a *new concurrent repair candidate* against an old lexical namespace and preserves the resulting contradiction.

## Executable experiment

Artifacts:

- `RELATION_NAMESPACE_DISCRIMINATOR.py`
- `EXECUTABLE_RESEARCH_RECEIPT.json`

Runtime: Python 3.13.5, Lark 1.3.1, separate process, exit 0.

Probe SHA-256: `53e762864e52768f525619a26dd42d6d1234c9c31f2d8c855c3b23ac4d436ccb`  
Stdout SHA-256: `54a620d2b9c5c74a6594f930513b18550975bd541a6c6654d221a5eabe1ba4db`

The current `@relation` surface has one-byte overhead over bare word infix, but it reuses the exact prefix already occupied by `@ref`. The disjoint-sigil control has the same character cost and no collision in this probe. The generic quoted call is longer but fully explicit.

Interpretation boundary: this is a combined grammar proxy, not the production BASE parser. Parser implementation details can change the result; that possibility is the explicit counterhypothesis and falsifier, not a reason to discard the negative result.

## External triangulation

Independent primary technical sources were used as architecture analogues only:

- **MLIR Language Reference:** distinct identifier classes use distinct sigils, while the generic operation form identifies extensible operations with explicit string names. This supports separating canonical semantic identity from optional custom/pretty surface syntax.
- **WebAssembly Component Model WIT:** defines explicit lexical token classes/identifier forms and performs name resolution after parsing. This supports fail-closed parse-then-resolve separation.

Neither source proves the ClayCode design; both are independent counterweights to FRANK↔ClayCode self-agreement.

## Goodman anti-echo

`FRANK_CLAYCODE_GOODMAN_REVIEW.json` records three material FRANK-derived assumptions.

1. Parser/render transformations must preserve semantics and authority distinctions: **SUPPORTED** by the new namespace-collision experiment plus independent language-design evidence.
2. Semantic relation resolution must not equal effect authority: **REFINED** into an explicit mechanical rule — `RelationId` resolution is semantic/type resolution only; authority remains a separate capability/commit check.
3. Full adaptive learner expressibility with generic ClayCode semantics: **REFINED** — narrow executable evidence exists, but the full Ubuntu-target learner has not yet been production-compiled/replayed.

Shared FRANK/ClayCode ancestry was collapsed and worker agreement was not counted as independent replication.

## Cross-branch feedback

- **FRANK:** preserve `@ref` identity and the sensor/memory/familiarity/activation/authority separations. Parser transformations are now an executable regression class, not only a prose warning.
- **Clay Research:** stay on BASE `less change, more compile`; this result narrows surface design rather than expanding language semantics.
- **Harness:** no H1/H2/H3 promotion. Future acceptance evidence is Ubuntu-only under the current owner-fixed target-host directive.
- **ClayGraph:** typed `relation_type`, `relation_class`, member `role` and receipt separation fit a typed canonical Relation node better than parser-guessed word semantics.
- **UnifiedDB:** capability/work/execution identities remain separate typed objects; relation names cannot mint authority.
- **GWT:** parser/representation success is not emergence evidence and does not collapse delivery/use/outcome/reentry distinctions.
- **Hyperposition:** relation surface must preserve explicit alternatives, conflict and provenance; no syntax shortcut may collapse set-valued state.
- **Emergenz:** no emergence claim is made; the run contributes only representation/parser evidence.
- **ClayCode:** preserve `NR-CC-G9-AT-RELATION-REF-COLLISION-20260809`; compare generic canonical Relation IR, declared relation sugar and only lexically-disjoint sigil candidates in the production parser.

## Hypotheses and counterhypotheses

See `HYPOTHESIS_MATRIX.json`.

Key state:

- `H-CC-REL-CANONICAL-NODE-20260809-01`: OPEN, supported by proxy + independent compiler-language analogy.
- `H-CC-REL-AT-SIGIL-20260809-02`: CHALLENGED by executable combined-namespace counterevidence.
- `H-CC-REL-DECLARED-SUGAR-20260809-03`: OPEN, supported by concurrent finite-resolver proxy but still requires production comparison.
- `H-CC-BASE-BLOCKER-20260809-04`: run-local support remains on parser/canonical-IR closure rather than new FRANK-specific primitives.

## Negative results

See `NEGATIVE_RESULTS.json`.

New durable negative results:

- `NR-CC-G9-AT-RELATION-REF-COLLISION-20260809`
- `NR-CC-G9-RELATION-ONLY-PROXY-SUFFICIENCY-20260809`

These preserve the important distinction between a feature passing its own positive corpus and remaining compatible with the complete language.

## Tool / protocol boundary

- GitHub canonical state was verified and this run's writes were reread successfully.
- E2B remains repository-marked `ADAPTER_READY_CREDENTIAL_UNAVAILABLE`; no credential workaround was attempted.
- Local separate-process Python was used as the permitted fallback.
- The official `research_interconnect_preflight.py` could not be run from this connector-only worker surface because there is no repository checkout; current prior ClayCode work also records a `clay` -> `clayresearch` normalization defect in that preflight. The manual 9/9 branch manifest is therefore fail-closed and **does not count as official preflight PASS**.

## Concurrency assimilation

Before close, current repository activity was reread. Parallel workers had started:

- a full-G9 surface-closure run;
- control-flow precedence work;
- semantic-publication probes;
- an Ubuntu/Linux effect-boundary probe.

No completed result from those in-flight lanes is silently treated as evidence here. Their paths are complementary; they should be assimilated by the next ClayCode turn once complete. This run did not overwrite their artifacts or the CURRENT G9 stack.

## Release implication

- `CC-WP-02-PARSER-CANON` remains OPEN.
- All BASE application acceptance remains unpassed unless the release workspace is explicitly advanced by evidence.
- No CURRENT ClayCode semantic generation is promoted.
- Do not promote the current `@relation` candidate.
- Highest-information next step: real production parser over complete admitted G9+dialects, with a canonical typed Relation node; differential roundtrip of generic relation syntax vs finite declared sugar vs any disjoint compact syntax; then type/effect/lowering/runtime execution on the Ubuntu target.
- Reopen semantics only if the real compiler/runtime demonstrates an inadequacy.

## Durable research delta

Committed by this run:

- executable combined `@ref` / relation namespace discriminator;
- negative result against the current `@relation` candidate as backend-neutral surface;
- negative result against relation-only corpus sufficiency;
- canonical typed Relation-node architecture hypothesis;
- Goodman anti-echo review;
- 9/9 branch interconnect manifest;
- tool execution manifest;
- active ClayCode knowledge micro-packet;
- no canonical/current-stack/BASE promotion.
