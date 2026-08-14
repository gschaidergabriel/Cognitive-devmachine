# ATOMIC FINAL REPORT — Monotone Causal Membrane (MCM)

## Selected problem
Frank v0.1 still has open cognitive-loop, UnifiedDB, GWT/Hyperposition, agency, memory/reward and recovery obligations. Building each as a conventional mutable subsystem risks recreating a globally sequential state machine in which unrelated evidence updates pay global ordering/broadcast costs.

## Radical candidate
**ATOMIC-MCM-001 / AT-MCM-001-v1 — Monotone Causal Membrane.**

Mechanism: provenance-bound semantic deltas that only add information/alternatives remain monotone and can join without a global workspace barrier. A causally closed MembraneCut is materialized only when a transition is non-monotone: winner selection, alternative elimination, retraction, unique commitment, reward admission, goal activation/deactivation or effect proposal. That seal can become the exact WorkspaceEpisode reconstruction/re-entry identity.

This changes GWT from an always-global broadcast substrate into a potentially event-induced determination surface. It does not delete GWT causal observability: addressable/delivered/reconstructed/used/effect/outcome/re-entry receipts remain required.

## Why structurally different
The current GWT microkernel is select -> ignite -> broadcast -> receiver receipts -> causal outcome -> re-entry. MCM asks whether globality can be derived from semantic non-monotonicity instead of being the default state geometry.

Hyperposition becomes especially natural: adding unresolved alternatives can remain monotone; selecting or eliminating one crosses a membrane. CJC may supply exact local order-risk evidence but cannot prove semantic monotonicity. SCF and ECT remain complementary cross-boundary/contract mechanisms.

## Fresh live evidence that changed the search
The previous CJC run had already shown hidden causal order effects in proxy state. After that cutoff, target-VPS EUDI evidence showed that a naive one-writable-inode design allowed writes into the supposedly immutable prefix while a split root blocked O_RDWR with EACCES. That counterevidence argues against confusing semantic unification with physical one-file unification.

Concurrent ATOMIC workers also produced SCF-001 and ECT-001 during this run. They were inspected before MCM persistence and classified as complementary rather than duplicate.

## External collision
Primary distributed-systems literature destroys any claim that the ingredients are globally new. CALM/Coordination Criterion relate coordination freedom to monotonicity; Chandy-Lamport supplies consistent global cuts; Naiad/timely dataflow uses partial logical time for cyclic incremental computation; invariant confluence and Blazes localize coordination requirements; 2026 determination provenance explicitly models commitments that resolve ambiguity.

Therefore novelty is **NOVEL_COMBINATION_CANDIDATE**, not world-first.

## Executable proxy
Synthetic causal-DAG traces were generated with 80 evidence atoms and 12 determinations per trace, delayed arrival and duplicate delivery. Four implementations were compared over 400 seeds / 4,800 determinations:

- naive arrival-order mutable state;
- strict global total order;
- strong causal event-sourcing/dependency-cut baseline;
- MCM monotone-delta + membrane implementation.

Controls included duplicate delivery, mid-trace crash/replay, stale epoch and determination-rate sweep.

## Measurements
Correctness:
- naive: 408 wrong / 4,800;
- global total order: 0 wrong;
- strong causal event sourcing: 0 wrong;
- MCM: 0 wrong.

Mean logical determination latency:
- global total order: 21.3575 ticks;
- strong causal baseline: 6.6175;
- MCM: 6.73646.

MCM therefore reduced mean logical latency by ~68.46% versus total ordering, but was ~1.80% slower than the strong causal baseline.

Python proxy runtime per trace:
- strong causal mean: 0.231883 ms;
- MCM mean: 0.262330 ms;
- MCM overhead: ~13.13%.

Recovery:
- 0/400 crash-replay result/cut mismatches.

Stale control:
- stale required atom rejected;
- dependent seal not emitted.

Payload model with six receivers:
- full-state snapshot broadcast: 571,050,972 bytes;
- MCM cut receipts: 7,227,744 bytes (~1.27% of snapshot payload);
- strong causal ref receipts: 6,766,944 bytes;
- MCM is ~6.81% larger than the strong causal reference baseline.

Determination-rate sweep (~2% to 25% non-monotone events): both MCM and strong causal baseline remained correct. MCM remained ~1.083x to 1.328x the Python runtime of the strong causal baseline.

## Strongest counterhypothesis
**Not refuted.** Conventional causal event sourcing with dependency-aware cuts reproduces the proxy correctness, reorder tolerance, crash replay and low determination latency with lower Python cost and slightly lower reference payload. If real Frank traces show that most transitions are non-monotone, or if TypedIR monotonicity coverage is low, MCM should be rejected.

## What remains potentially unique
MCM still has a distinct testable architectural claim: a ClayCode compiler could prove/annotate semantic transition polarity and automatically derive where GWT-level determination barriers are required. If that works, it could unify coordination analysis, WorkspaceEpisode identity, Hyperposition collapse, causal-use credit and re-entry without making every state update globally ordered.

Current ClayCode can represent explicit polarity records/rules, but compiler TypedIR does not yet prove semantic monotonicity or emit causal-cut certificates. The smallest proposed language/runtime gap is therefore typed monotonicity/effect classification plus a causal-cut certificate, with every unproven transition treated as UNKNOWN rather than optimistically monotone.

## Decision
**NO ARCHITECTURE PROMOTION.** Status: `TESTED_PROXY_MIXED_RETEST`.

MCM has crossed the ATOMIC threshold from prose to measured possibility, but it has not beaten the strongest conventional baseline.

## Next highest-information falsifier
Take current real Frank v0.1 TypedIR/transitions and perform a semantic census: `MONOTONE | DETERMINATION | UNKNOWN`. Compile two matched implementations: MCM and conventional causal event sourcing. Execute current Frank traces on the accepted Hostinger VPS with exact GWT candidate/selection/delivery/reconstruction/use/outcome/re-entry receipts, stale/replay/crash controls, CPU/RAM/latency/state-amplification measurements and CJC/SCF/ECT integration only where independently justified. Reject MCM if it yields no unique defect coverage, architecture compression, resource improvement or causal-observability gain.

No final/paid training was started. No effect authority was minted. Frank/self.root Harness mutation authority remains proposal-only.
