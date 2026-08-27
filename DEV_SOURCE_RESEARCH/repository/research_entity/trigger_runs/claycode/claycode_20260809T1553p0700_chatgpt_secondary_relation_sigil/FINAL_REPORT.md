# ClayCode Trigger Run — Relation Surface Disambiguation

Run: `claycode_20260809T1553p0700_chatgpt_secondary_relation_sigil`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (IN_PROGRESS)  
Promotion: **none**

## Executive result

This run attacked the remaining open relation-surface problem behind the current G9 parser drift: bare semantic relation words such as `never_implies`, `may_reference`, `includes` and `4B_emits` collide with ordinary identifier/operator classification unless the language defines an explicit lexical and semantic-resolution policy.

A minimal candidate was tested:

- compact relation identity: `@relation_name`
- arbitrary/reserved/Unicode relation identity: `@"quoted relation identity"`
- semantic rule: parse acceptance does not mint meaning; every relation must resolve through a typed relation registry/symbol table
- authority rule: relation recognition/resolution never grants execution authority

Examples:

- `Delta @never_implies epistemic_upgrade`
- `effect.Intent @may_reference capability_id`
- `graph.derived_relation @cannot_authorize effect`
- `NativeCognitionTask.forbidden_burden @includes [...]`
- `@4B_emits EffectIntent`

No ClayCode semantic primitive is added by this candidate. It is a surface/lexical encoding proposal only.

## Executable experiment A — current G9 relation sample

Experiment: `EXP-CC-G9-RELATION-SIGIL-003`.

Eight CURRENT-G9 relation families were tested with a Lark LALR proxy parser plus declared-relation resolver:

`never_implies`, `may_reference`, `never_confers`, `returns`, `cannot_authorize`, `distinct_from`, `includes`, `4B_emits`.

Observed:

- parsed + resolved: **8/8**
- intended canonical relation tuple preserved: **8/8**
- mean/max character overhead over the original sampled infix source: **+1 / +1**
- mutation/adversarial forms rejected by parser or resolver: **12/12**
- false accepts in that mutation set: **0**

The mutation set included missing sigils, undeclared relation typos, missing operands, doubled sigils and stray trailing identifiers.

## Executable experiment B — quoted fallback + fuzz

The candidate was extended so identifier-like relation names use `@name`, while arbitrary names use `@"..."`.

Deterministic seed: `20260809`.

Observed over **20,000** generated relation cases:

- parse failures: **0**
- relation identity failures: **0**
- relation-name mutation semantic-hash collisions: **0**
- operand-swap semantic-hash collisions: **0**
- adversarial relation-ID roundtrip: **18/18**
- mean surface byte overhead vs bare infix: **1.30415 bytes**
- min/max overhead: **1 / 7 bytes**

Adversarial identities included reserved words, digit-leading names, spaces, quotes, backslashes, Unicode, dashes and dots.

Evidence boundary: this is local parser/resolver proxy evidence, not the production parser and not full admitted-corpus proof.

## Concurrent discriminating evidence

A concurrent ClayCode worker independently tested a different strict candidate:

`relation("quoted_relation_id", lhs, rhs)`

That candidate achieved:

- CURRENT-G9 sampled relation preservation: **10/10**
- deterministic fuzz parse + relation identity preservation: **20,000/20,000**
- relation-name mutation hash sensitivity: **20,000/20,000**
- operand-swap hash sensitivity: **20,000/20,000**
- adversarial quoted relation-ID roundtrip: **10/10**
- mean surface byte overhead vs infix: **12 bytes**

Therefore the current evidence does **not** select a final syntax winner. It establishes two viable strict lexical families:

1. generic quoted relation call — simplest universally explicit canonical surface, higher source cost;
2. sigil hybrid — explicit lexical category with compact common case and quoted fallback, lower measured surface cost.

A declared contextual bare-infix registry remains the third counterhypothesis and must be tested rather than assumed inferior.

## External primary-source triangulation

External sources were used as independent architecture analogues only.

- Tree-sitter's official grammar documentation distinguishes lexical conflicts, contextual lexing and lexical precedence, including keyword-vs-identifier cases. This supports treating relation-vs-identifier classification as an explicit grammar concern.
- MLIR's official Symbols/SymbolTables documentation separates symbolic references from lookup and verification. This supports resolving extensible ClayCode relation identities after parsing rather than granting arbitrary parsed words semantics.
- MLIR Dialect Conversion and ODS separate operation/surface definition, verification and legality-constrained progressive lowering. This supports `surface -> typed canonical IR -> verified lowering`, not any specific ClayCode sigil.

No external analogue proves the final ClayCode syntax.

## Hypothesis delta

### `H-CC-RELATION-SIGIL-003` — OPEN_SUPPORTED_BY_LOCAL_PROXY_AND_FUZZ

A hybrid sigil relation surface can remove the tested lexical ambiguity, preserve arbitrary relation identity and stay close to current source cost without semantic redesign.

### `H-CC-DECLARED-RELATION-RESOLVER-004` — OPEN_SUPPORTED_BY_LOCAL_PROXY

Open relation names should be resolved in a typed symbol/semantic layer after lexical disambiguation. Unknown relation names must not acquire semantics merely because the parser accepted their text.

### `H-CC-GENERIC-INFIX-NULL-002` — OPEN_WEAKENED_NOT_REFUTED

Bare identifier-like infix relations remain weakened by prior E2B lexer ambiguity, but a properly declared contextual-infix implementation has not yet been benchmarked head-to-head.

### `H-CC-RELATION-THREEWAY-005` — OPEN_NEXT_DISCRIMINATING_TEST

Production selection should be evidence-driven across three candidates: sigil-hybrid, strict generic quoted-call and declared contextual bare-infix.

## Negative results

- `NR-CC-BARE-OPEN-RELATION-LEXICAL-003`: bare open relation words are not safe to freeze without an explicit lexical + semantic-resolution policy; prior E2B replication already exposed a relation-word lexer ambiguity.
- `NR-CC-RELATION-SYNTAX-WINNER-004`: no relation-syntax winner is justified yet. Local parser/fuzz success is insufficient for language promotion.

## Goodman anti-echo

Shared FRANK/ClayCode ancestry was collapsed. The proposal was not accepted because FRANK already uses relation-like prose.

Independent support comes from new executable parser/resolver discrimination plus external parser/compiler architecture analogues. Verdict: `REFINED`, not final `SUPPORTED` syntax.

The external effect boundary is unchanged: relation recognition, graph association, model output or semantic resolution never authorizes effects.

## Cross-branch feedback

- **FRANK:** NO semantic architecture change. Any chosen relation surface must preserve causal/admission/effect distinctions.
- **Clay / staged program:** NO stage advancement; this is BASE parser research only.
- **Harness:** future H1/H2 source fixtures should enter parser-conformance tests; Harness semantics must not be simplified to fit parser weaknesses.
- **ClayGraph:** NO truth/activation/authority change. Typed resolved relation identities are compatible with graph relation/hyperrelation lowering.
- **UnifiedDB:** NO physical/logical storage decision change. Relation declaration/version/provenance should remain persistable/replayable if adopted.
- **GWT:** NO_CHANGE; relation syntax carries no ignition/use/causal-credit semantics.
- **Hyperposition:** NO_CHANGE; alternatives/conflicts remain explicit independently of surface syntax.
- **Emergenz:** NO_CHANGE; parser success is not emergence evidence.

## BASE implication

Do **not** patch CURRENT grammar directly from this run.

Highest-information next experiment:

1. freeze the complete admitted G9 V3 + dialect + current candidate corpus;
2. implement production-parser candidate A: sigil hybrid;
3. implement candidate B: strict generic quoted relation call;
4. implement candidate C: declared contextual bare-infix relation registry;
5. run complete parse + roundtrip + semantic-hash stability;
6. run malformed/mutation/fuzz diagnostics;
7. measure real source tokens, Qwen-class reader accuracy/repair cost and compiler diagnostics;
8. select only after those measurements;
9. then continue into typed canonical IR and type/effect checking.

This directly advances `CC-WP-02-PARSER-CANON` while preserving the project rule: **less change, more compile**.

## Protocol limitations

The current ChatGPT execution surface exposes GitHub but no repository checkout, so repo-local `research_interconnect_preflight.py` and Goodman validator execution were unavailable. A fail-closed manual interconnect manifest and explicit Goodman artifact were committed; official validator PASS is not claimed.

E2B is not exposed as an invokable tool in this session. Prior E2B parser counterevidence was consumed as existing evidence only; this run does not claim fresh E2B execution.

A concurrent repository write caused the first `FINAL_REPORT.md` create attempt to fail with GitHub 409 rather than overwrite new work. The concurrent relation experiment was then re-read and incorporated before this final write.

## Durable delta

Committed artifacts:

- `RELATION_SIGIL_CANDIDATE.ebnf`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `HYPOTHESES.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `INTERCONNECT_MANIFEST.json`
- `TOOL_EXECUTION_MANIFEST.json`
- `FINAL_REPORT.md`

No CURRENT-stack, canonical-state, BASE-stage, application-acceptance or language promotion is requested.
