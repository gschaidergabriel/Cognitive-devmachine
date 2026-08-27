# ClayCode executable frontier — target evidence and promotion boundary

Date: 2026-08-11 16:30Z  
Program: FRANK_V0_1  
Subject: self.root / Frank  
Implementation repo: `gschaidergabriel/Dr.-Unterweger`

## Status

`TARGET_SUPPORTED_FRONTIER / PROMOTION_PENDING_CURRENT_HEAD_GATES`

This report records a real execution frontier for F-V01-02 / ClayCode compiler-runtime work. It does **not** mark WP03, WP04, WP05, WP06, F-V01-02, APP-09 or whole Frank v0.1 PASS.

## Accepted-target evidence already earned

Accepted self-hosted Ubuntu target run:

- workflow run: `31508724635`
- job: `93837809226`
- exact tested implementation head: `1c0a20d3ec412724f79bd444820c526722def8b5`
- runner: `clay`
- machine: `digital-retina`
- Python: `3.12.3`
- parser dependency: `lark==1.3.1`
- conclusion: `SUCCESS`

Measured composed ClayCode frontier:

- package namespace / ModuleSpec binding: `7/7 PASS`
- hostile earlier top-level `syntax.py` / `host.py` / `analyzer.py` did not capture package imports under `python -P`
- legacy intentional CLI compatibility remained available
- `frank.effects::decide_effect`: `200,576` differential requests, `0` mismatches, `6/6 PASS`
- `effect_request_hash`: `56,000` compared, `0` mismatches
- `confirmation_matches`: `16,000` compared, `0` mismatches; overall confirmation/hash gate `9/9 PASS`
- corpus parse coverage: `36/40 = 90.0%`
- ordinary parser `Call` nodes: `677/677` visible to analyzer, `0` missed
- callable MethodChain sites measured separately: `22` = `filter 11`, `map 10`, `sort_desc 1`; typed member/library semantics remain OPEN
- unary/lexical operator survival: `8/8 PASS`, including `!`, word `not`, double negation and Boolean-prefix identifiers
- unresolved ordinary-call snapshot on parsed corpus: `429` unique names / `464` call-site occurrences
- independent census reproduced `429/464`
- `frank.effects` unresolved targets: `0`
- final exact composed-frontier assertion: PASS

Resource shadows on this target run were approximately 31–35 MiB max RSS for the main differential/corpus probes. Observed wall times were approximately 7.14 s for the 200k `decide_effect` differential, 5.72 s for confirmation/hash, 8.78 s for corpus measurement, and 8.4/8.5 s for count/census probes.

## Important negative evidence / repairs

### Confirmation harness composition gap

Earlier target run `31507247802` on head `9e1afc...` passed package binding and the 200,576-request `decide_effect` differential, then failed before confirmation semantic output because the older confirmation harness imported the now-package-bound sibling differential without repository root on its search path.

Classification: `HARNESS_IMPORT_COMPOSITION_BUG`, not ClayCode semantic failure.

The import contract was repaired; accepted target run `31508724635` subsequently passed confirmation/hash and the complete frontier matrix.

### Main-lineage integration gap

A raw merge of the old frontier ancestry into advancing `main` exposed both visible ClayCode conflicts and silent non-Clay regressions: old ancestry would have deleted/reverted current Storage/V17 files without necessarily producing a merge conflict.

The integration branch was reconstructed on a current-main base tree with an explicit ClayCode-only blob overlay. Non-Clay files therefore inherit current `main` by construction. The resulting lineage became a direct current-main descendant, eliminating the Storage/V17 regressions from the branch-vs-main delta.

### Ambiguous nominal variants

A later fail-closed repair preserved analyzer ambiguity diagnostics in evaluator admission and runtime bypass paths. Duplicate sum-type variant owners must never become a semantic type name merely because a caller bypasses `admit()`.

The dedicated target gate for this exact later head remains a promotion requirement; this report does not credit that later head as target-PASS until the exact gate executes successfully.

### Negation side-gate harness drift

A side workflow produced an apparent red result after the actual operator gate returned `8/8 PASS`; the workflow asserted a removed JSON field `go_out_of_box_experiment_added` and raised `KeyError`. This was harness schema drift, not a negation semantic failure. The workflow assertion was updated to current safety fields (`external_effect_performed`, `authority_minted`).

### Generic/relation side-gate infrastructure

The structured generic-vs-relation side workflow first failed at dirty-runner checkout. After isolated checkout repair, it failed during WP03 substrate materialization because a shallow fetch omitted pinned historical commits required by `materialize_v18_local_v2.py` (`c3709c4...` etc.). No parser counterexample executed. Classification remains `INCONCLUSIVE_INFRA/MATERIALIZER_HISTORY_FETCH`, not semantic failure. The workflow was updated to fetch the exact pinned objects explicitly before materialization; fresh execution is still required for semantic credit.

## Current implementation candidate

Integration PR: `Dr.-Unterweger#357`  
Branch: `chatgpt/claycode-frontier-integration-20260811`

The branch continued to receive only bounded fail-closed / CI integrity fixes after the accepted target frontier run. Therefore the accepted run above is strong mechanism evidence but is **not sufficient by itself to merge the current moving head**.

Required before promotion/merge of the current exact head:

1. exact-head ClayCode Frontier Integration VPS PASS;
2. exact-head current-main composition VPS PASS against then-current `main`;
3. exact-head ambiguous-variant fail-closed target PASS;
4. PR remains mergeable and branch-vs-main delta contains no unintended non-Clay regression.

## WP06 successor lane

Stacked Draft PR `Dr.-Unterweger#366` starts a first real compiler/lowering candidate:

`ClayCode source -> parsed/typed syntax -> fail-closed C lowering -> C11 shared object -> native execution -> three-way differential (shipping Python oracle == Clay evaluator == compiled C)`.

Current scope is deliberately only the already-proven PURE closure:

- `decide_effect`
- `destructive_guard_complete`

The candidate rejects currently open semantics rather than inheriting host behavior:

- multi-relation comparison chains;
- cross-nominal Bool/Int equality;
- unresolved calls;
- host intrinsics/effects;
- unsupported generic/member/library constructs.

This is a CC-WP-06 **candidate mechanism**, not WP06 PASS. It must be rebound to the finally merged #357/main frontier and earn exact accepted-target execution evidence before any promotion credit.

## Open semantic / implementation blockers retained

- comparison-chain semantics (#316): OPEN
- Bool/Int equality alias semantics (#350): OPEN
- typed member/library semantics for 22 MethodChain sites: OPEN
- 4/40 current sources intentionally parser-rejected rather than admitted via invented grammar
- broader parsed corpus: 429 unresolved unique ordinary call names / 464 occurrences
- complete TypedIR/type-effect validation: OPEN
- general compiler/lowering breadth: OPEN
- runtime ABI/FFI: OPEN
- stdlib/SDK: OPEN
- concurrency/memory semantics: OPEN
- real general-purpose application suite / APP-09 Frank component acceptance: OPEN

## Research adjudication

The evidence supports a phase change from `ClayCode as specification/front-end only` to `ClayCode with executable, differentially falsifiable semantics on the accepted target`.

The strongest supported claims are currently:

1. a bounded but real semantic source path (`frank.effects::decide_effect`) is executed from ClayCode and matches the shipping reference over a large target-measured differential;
2. the current parser surface covers 90% of the present ClayCode corpus without inventing grammar for the remaining four sources;
3. package/module origin is part of the executable trust boundary rather than an implicit Python path assumption;
4. construct-level/operator, corpus-level and composition-level falsifiers have already found real bugs that a single large request differential did not expose;
5. current promotion discipline must remain exact-head and merge-tree based because advancing `main` demonstrably created both visible and silent integration hazards.

Do not convert this report into whole-package PASS without the remaining stated gates and acceptance receipts.
