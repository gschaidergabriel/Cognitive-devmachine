# ClayCode Trigger Run — Strict Surface / Broader Adversarial Parser Gate

Run: `claycode_20260809T1547p0700_chatgpt_secondary_strict_syntax_gate`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE` (`IN_PROGRESS`)

## Executive result

The previous ClayCode parser-alignment work was correct but incomplete. The repository's CURRENT G9 source and CURRENT `grammar.ebnf` were re-read after concurrent writes and remain unchanged by blob SHA. A broader executable Lark proxy tested ten representative CURRENT-G9 surface forms.

- Prior union+`if` repair proxy: **1/10 PASS, 9/10 FAIL** on the broader raw representative set.
- Strict explicit candidate + semantically conservative source normalization: **10/10 PASS**.

This does **not** justify a new cognitive or runtime semantic primitive. It strengthens the BASE conclusion: freeze one explicit parseable surface and typed AST policy before adding language semantics.

## What this run adds beyond the concurrent parser run

A concurrent ClayCode run already proved three additional failures beyond union/`if` (`external_effect lifecycle=...`, digit-prefixed `4B_...`, and `includes`) and separately executed an 8/8 Retina/Unified-Memory gate subset. This run does not duplicate that result.

The new adversarial coverage extends the surface-closure set with additional CURRENT forms, especially:

- numeric comparisons: `diff>0`, `diff<0`, `count(...)>=...`;
- unseparated ownership relation: `Needle.owns [tool_schema,...]`;
- prose chain: `Claude_only consumes latest stack + writes task receipts`;
- postfix/fallback form: `verify(receipt? or residual)`;
- `returns` relation syntax;
- plus independent re-confirmation of `lifecycle`, `4B_...`, `includes`, union and `if` behavior.

## Candidate repair policy

Do **not** solve this by admitting arbitrary identifier-as-infix operators. That would make the surface increasingly prose-like and move meaning into parser guesses.

Candidate policy:

1. retain explicit `if` and union types from the prior patch candidate;
2. add explicit comparison operators `>`, `<`, `>=`, `<=`;
3. normalize prose-like relations to explicit existing forms (`=`, `->`, calls, qualified fields);
4. rename digit-leading symbols such as `4B_emits` to legal identifiers such as `model4B_emits`;
5. normalize fallback syntax to an explicit call such as `coalesce(receipt,residual)`;
6. keep arbitrary identifier-infix syntax as a counterhypothesis until it wins deterministic parse/roundtrip/mutation tests.

Artifacts: `CLAYCODE_G9_GRAMMAR_PATCH_V2.ebnf`, `SOURCE_NORMALIZATION_CANDIDATE.md`.

## Executable evidence

`grammar_alignment_probe_v3.py` uses Lark 1.3.1 with an LALR proxy derived from the current research grammar and the prior union/`if` repair.

Observed summary from `grammar_alignment_probe_v3_results.json`:

```text
raw prior-patch proxy:     PASS 1 / FAIL 9
strict normalized proxy:  PASS 10 / FAIL 0
```

Evidence boundary: this is executable proxy evidence over representative exact CURRENT constructs. It is **not** a generated parser over the full G9 file and does not complete `CC-WP-02-PARSER-CANON`.

## Cross-branch findings

- **FRANK:** the fused target explicitly lists parser/render/context corruption as inherited failure risk and requires semantic/authority distinctions to survive representation changes. Strict surface closure is compatible with that requirement.
- **Clay:** current stage remains BASE ClayCode compiler/runtime; semantic change still requires an executable inadequacy, not aesthetic preference.
- **Harness:** H-WP-03 remains blocked on ClayCode release. The concurrent 8/8 Retina gate probe is retained as the current narrow representability evidence; full MVC compile/replay remains open.
- **ClayGraph:** typed hyperrelation roles and separate projection/selection/receiver receipts increase the cost of ambiguous surface syntax; activation remains non-authoritative.
- **UnifiedDB:** work specifications, capabilities and execution receipts are separate typed objects; parser convenience must not collapse these boundaries.
- **GWT/Emergenz:** selection, delivery, use, outcome and re-entry remain distinct; parser success is not emergence evidence.
- **Hyperposition:** higher-order relation/topology structures remain explicitly typed and do not require prose-like grammar.
- **ClayCode history:** this run confirms and broadens the prior parser negative result rather than superseding its semantics.

## External triangulation

The WebAssembly Component Model WIT specification independently uses explicit lexical token classes, reserved keywords/operators, identifier rules and a pseudo-formal grammar. That is supporting design evidence for keeping an interface/IR language lexically explicit rather than treating arbitrary prose words as implicit operators. It is not proof that this exact ClayCode candidate is optimal.

Primary source: WebAssembly/component-model `design/mvp/WIT.md`.

## Goodman anti-echo

`FRANK_CLAYCODE_GOODMAN_REVIEW.json` passes the repository validator reconstructed from current `tools/goodman_filter_check.py`: **9 registered branches, 0 violations**.

Key verdicts:

- strict parser/surface policy: `REFINED`, supported by independent explicit-grammar practice but still pending full parser/canonical roundtrip evidence;
- adaptive visual learner semantic sufficiency: `UNRESOLVED` for the full component, because the concurrent 8/8 gate subset does not execute the complete versioned learner/promotion/rollback/resource/replay lifecycle.

## Hypotheses and negative result

- `H-CC-STRICT-SYNTAX-002` — OPEN, supported by proxy: deterministic explicit syntax + normalization can close tested surface gaps without semantic redesign.
- `H-CC-GENERIC-INFIX-NULL-002` — OPEN counterhypothesis: generic identifier-infix grammar may be better if it proves deterministic AST/hash stability and lower repair cost.
- `H-CC-MVC-EXISTING-SEMANTICS-003` — OPEN: full adaptive visual learner may still be expressible using current generic typed semantics; requires real compile/runtime evidence.
- `NR-CC-G9-PATCH1-INCOMPLETE-002` — NEGATIVE_RESULT: the prior union+`if` patch is insufficient for the broader representative CURRENT-G9 surface.

## Protocol / tooling limitations

The official `research_interconnect_preflight.py` could not be run because the local execution surface has no repository checkout/network path. This is additionally consistent with the concurrent repo finding that the preflight currently has a `clay` -> `clayresearch` normalization problem. A manual fail-closed interconnect manifest was built from verified GitHub reads; **official preflight PASS is not claimed**.

E2B is not exposed as a callable tool in this session, so the mandated fallback used the local container. The receipt states that evidence class explicitly.

## Release implication

- Keep `CC-WP-02-PARSER-CANON` OPEN.
- Do not promote a new ClayCode semantic generation.
- Next highest-information step remains: generate/use the real repository parser against the complete CURRENT G9 corpus, freeze the typed AST/canonicalizer, and run roundtrip + mutation + semantic-hash tests.
- Then compile the real adaptive visual learner path through parser -> typed IR -> type/effect -> lowering -> runtime. Reopen semantics only on an executable inadequacy.

## Research delta

Durable delta committed by this run:

- broader adversarial parser surface coverage;
- strict explicit-syntax candidate rather than generic prose infix;
- comparison-operator grammar candidate;
- semantically conservative source-normalization map;
- executable 10-case proxy receipt;
- concurrency-aware deduplication against the newer Retina/parser run;
- Goodman validation receipt;
- no canonical/current-stack/BASE promotion.
