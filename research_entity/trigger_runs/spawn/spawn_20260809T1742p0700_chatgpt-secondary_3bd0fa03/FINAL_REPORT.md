# SPAWN Research Report — ClayCode Incremental Delta Equivalence

Run: `spawn_20260809T1742p0700_chatgpt-secondary_3bd0fa03`  
Trigger: `spawn`  
Origin branch: `claycode`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## 1. Selected microdirection

The weighted OS-CSPRNG branch draw selected **ClayCode**. A second OS-CSPRNG draw selected:

> Does ClayCode G9 incremental state maintenance (`Delta -> dependency_closure -> affected recompute`) remain observationally equivalent to full recomputation under signed retractions, duplicate support, non-monotone selectors and logical-time/epoch changes?

A late novelty check was repeated because parallel `spawn` runs appeared during execution. Those fresh runs focused on effect-authority lowering, adaptive visual learner state and Harness lowering preservation. This direction remained distinct. It also does not duplicate `EXP-INCR-001`, which measured favorable locality/performance rather than semantic equivalence.

## 2. Current ClayCode grounding

G9 V3 already contains a strong starting basis:

- `Delta<T>.diff:Int` with positive, negative and zero deltas;
- `IncrementalReceipt` with source/output epochs, affected dependencies and cost;
- `ViewDelta` with `dependency_hash` and `selector_hash`;
- `GraphDelta` with graph epochs;
- the rule `state.write -> Delta -> dependency_closure -> affected_view_recompute`.

The research result is therefore **not** a proposal to redesign ClayCode. It is a correctness/lowering contract for semantics that already exist.

## 3. External mechanism evidence

Primary external work provides a convergent model:

1. **DBSP** formalizes automatic incremental view maintenance for rich relational/dataflow programs, including insertions/deletions and complex query classes.
2. **Differential Dataflow** represents updates as `(data, time, diff)` and maintains signed multiplicity; its progress/frontier model explicitly communicates when earlier logical times can no longer receive changes.
3. **Self-adjusting computation** provides the useful correctness standard: change propagation should be observationally equivalent to reevaluation from scratch.

These are mechanism analogues and formal/system evidence, not Clay runtime evidence.

## 4. Executed experiments

### EXP-SPAWN-DELTA-001 — signed-diff join equivalence

Synthetic Python Z-set/bag model with a derived self-join (`path2`). Randomized 20,000 signed update steps using `-2,-1,+1,+2`. The incremental differential rule included old/new cross terms and was compared after every update with complete from-scratch recomputation.

**Result:** `20,000 / 20,000` steps matched; **0 observed mismatches**.

Interpretation: the current integer `diff` shape is compatible with exact tested differential maintenance when multiplicity and the complete operator differential are preserved.

### EXP-SPAWN-DELTA-002 — duplicate-support retraction counterexample

Initial multiplicity for `x` = 2. Apply `diff=-1`.

- Correct bag/Z-set state: multiplicity = 1, therefore `x` remains present.
- Naive set-only deletion: removes `x` entirely.

**Result:** set-only negative-diff semantics are unsound when multiple supports exist.

### EXP-SPAWN-DELTA-003 — non-monotone selector counterexample

Scores: `a=10`, `b=9`, `c=8`; winner = `a`. Delete `a`.

- Full recomputation: winner becomes `b`.
- Positive-support-only invalidation: retracts `a` but has no dependency path forcing reconsideration of `b`; result becomes missing/stale.

**Result:** argmax/top-k/GWT-like selection requires competitor/domain/partition invalidation or an equivalent maintained index—not only provenance edges from the old winner.

### EXP-SPAWN-DELTA-004 — selector identity counterexample

Data is unchanged. Selector semantics change from `max` to `min`.

**Result:** output changes despite `data_diff=0`.

Therefore `selector_hash`/plan identity is a semantic dependency. A selector change must produce view invalidation/recompute or an equivalent versioned transition; it cannot be treated as ordinary `NO_CHANGE`.

### EXP-SPAWN-DELTA-005 — global-selector operator-state benchmark

Synthetic 100,000-element max selector, 2,000 point updates:

- naive full `max` scan median: ~`1.768707 ms/update`;
- maintained lazy-heap index median: ~`0.000147 ms/update`;
- synthetic ratio: ~`12,032x`.

This is **not** a Frank/Clay target performance claim. It demonstrates only that closure cardinality is not enough to characterize incremental cost: maintained operator/index state can dominate the implementation strategy.

## 5. Main finding

The current G9 delta model should be retained, but `dependency_closure` must be understood as a semantic invalidation closure, not merely a graph walk over positive support.

For correctness it must account for, directly or through equivalent operator-local state:

1. **positive support** dependencies;
2. **negative/competitive/absence** dependencies for anti-joins, thresholds, top-k, argmax, GWT competition and similar non-monotone selectors;
3. **aggregate/recursive/transitive** downstream dependencies;
4. **selector/plan/schema/version** changes as invalidation events;
5. **logical progress / sealed epochs** before an output is published as stable when late/out-of-order updates are possible.

Recommended correctness invariant:

`FULL(Q, S + Δ, sealed_epoch=e) == APPLY(INCR(Q, S, Δ), prior_view, sealed_epoch=e)`

where the comparison includes semantic result, multiplicity/support state where observable, selector/plan identity, authoritative epoch and required provenance/receipt fields.

## 6. Recommended `IncrementalReceipt` realization

Do **not** add language syntax merely from this research. First attempt compiler/runtime realization using existing fields plus lowering metadata.

For executable conformance, receipts should be able to bind or derive:

- source/output semantic epoch;
- progress/frontier or a proof that execution is strictly serialized;
- dependency hash;
- selector/plan hash;
- affected/invalidation partitions;
- operator/index-state hash where stateful maintenance is used;
- derivation hash;
- recompute mode (`incremental`, `partition_rebuild`, `full_rebuild`);
- cost shadows: latency, memory, index/write amplification and recovery cost.

If existing G9 structures cannot encode this without ambiguity, that failure becomes the executable counterexample required by the BASE language-change policy.

## 7. Harness test obligation

Add a differential oracle before treating incremental execution as release-grade:

- same frozen initial state;
- same signed input deltas;
- same logical timestamps;
- same selector/plan versions;
- same deterministic fixtures/seeds;
- run **from-scratch** and **incremental** paths;
- compare every materialized state/view and receipt at sealed epochs.

Mandatory stress classes:

- duplicates/multiple support;
- insertions and retractions;
- joins and aggregates;
- anti-join/absence conditions;
- argmax/top-k/GWT candidate competition;
- recursive/transitive derivations;
- selector/plan version changes;
- late/out-of-order events;
- checkpoint/restart/replay;
- index corruption/rebuild fallback.

Zero unexplained semantic mismatches is the correctness gate. Performance should then compare incremental versus partition-rebuild versus full-rebuild under real BASE/H1 traces.

## 8. Cross-branch implications

- **ClayCode — NEW_CONSTRAINT:** signed deltas remain; formalize semantic invalidation closure and full-recompute equivalence.
- **UnifiedDB — NEW_CONSTRAINT:** persist/replay enough multiplicity, operator/index, selector and epoch state for deterministic reconstruction.
- **ClayGraph — NEW_CONSTRAINT:** retractions and competitive selections require graph-epoch-aware invalidation.
- **GWT — NEW_CONSTRAINT:** winner deletion must reconsider competitors; selection receipts require selector identity + coherent epoch.
- **Harness — NEW_HYPOTHESIS/TEST:** execute differential full-vs-incremental oracle on current-stage traces.
- **Frank — NEW_CONSTRAINT:** published cognitive views should identify the coherent semantic epoch from which they were constructed.
- **Clayresearch — SUPPORTING_EVIDENCE:** preserves the earlier incremental-locality hypothesis but adds correctness/operator-cost guardrails.
- **Hyperposition — NO_CHANGE:** no new independent higher-order mechanism established.
- **Emergenz — NO_CHANGE:** no emergence claim changed; measurement should consume coherent state epochs.

## 9. Negative results / constraints preserved

1. **Support-only invalidation is refuted** for the tested argmax deletion case.
2. **Set-only negative-diff deletion is refuted** for the tested multi-support case.
3. **`data_diff=0 => NO_CHANGE` is refuted** when selector/plan semantics change.
4. The earlier locality result is **not** refuted; it is narrowed: locality is a performance opportunity only after semantic correctness and operator-state costs are validated.

## 10. What this run does not prove

This run does not prove:

- the current ClayCode compiler/runtime implements these rules;
- actual latency/memory gains on Andreas' Ubuntu developer system;
- H1/H2 Harness equivalence;
- live Frank behavior;
- BASE release readiness;
- any causal-emergence or consciousness claim.

`CLAYCODE_RELEASE_GATE` therefore remains unchanged.

## 11. Next discriminating experiment

Highest-information next action:

> Implement a minimal current-G9 incremental view engine plus from-scratch oracle on the Ubuntu BASE toolchain, then run randomized/property traces containing signed multiplicities, argmax/top-k/anti-join, selector-version changes, logical-time reordering and checkpoint/replay. Compare semantic hashes and complete receipts at sealed epochs; benchmark incremental vs partition rebuild vs full rebuild on the first real BASE/H1 dependency traces.

That executable result can determine whether the requirement is fully solvable in compiler/runtime metadata or whether an actual ClayCode semantic change is necessary.

## 12. Final synthesis

**Keep the Delta calculus. Tighten the invalidation contract.**

The useful abstraction is not “recompute everything downstream of changed positive support.” It is:

> recompute exactly the semantic dependency/invalidation region needed to make the sealed-epoch result observationally equivalent to full recomputation, while recording enough plan/operator/progress state to replay and audit that equivalence.

This is a current-stage compiler/runtime constraint and test obligation, not a canonical promotion and not a BASE PASS.
