# ClayCode negative results — 20260809T1505p0700

1. **Positional SQL lowering is not semantically safe under column reordering.** In both local SQLite 3.46.1 and isolated E2B SQLite 3.40.1, the statement executed successfully while mapping the three logical fields to the wrong columns. This is more dangerous than an arity error because execution itself does not reveal the semantic corruption.

2. **Named-field lowering is not sufficient by itself.** Adding a new required `NOT NULL` column without a default still requires a source/schema contract update. The compiler/runtime must preflight required target fields rather than treating named columns as universal compatibility.

3. **Additive graph projection is insufficient for complete-snapshot semantics.** Given current `{A-B,A-C}` and a new complete projection `{A-B}`, additive update leaves `A-C` stale-current. Retraction closure removes it. This result does not imply omission means deletion for PATCH semantics.

4. **No evidence currently justifies new first-class `work` or `cap.resolve` grammar keywords.** UnifiedDB V9 already carries stable work IDs, spec revisions, leases, receipts and freshness-aware capability observations; G9 generic records/rules can carry those semantics. Syntax expansion remains unselected until a matched benchmark demonstrates measurable benefit.

5. **Research tooling drift found and repaired.** `research_interconnect_preflight.py` gives ClayCode priority `frank, clay, harness, claygraph, unifieddb, ...`, while `goodman_filter_check.py` required a prefix omitting `harness`. The checker was corrected in commit `77cbe4ddfc924174930f7732833bf356f8500a2b`. This is a Research Entity tooling fix, not FRANK Harness modification and not scientific support for a ClayCode hypothesis.
