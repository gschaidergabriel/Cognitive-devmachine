# Topic Packet Delta — Causal Transition Kernel / BASE Semantic Convergence

Run: `clayresearch-20260809T1653p0700-chatgpt-secondary-ctk`

## Topic

**Compiler-internal semantic convergence for ClayCode BASE without premature surface-language redesign.**

The current G9 surface already contains most required semantic families: Delta/incremental state, provenance algebra, capability-bearing effects, dialect contracts, ViewDelta/UnifiedDB, GraphDelta/ClayGraph, GWT selection/causal-credit axes, EffectIntent/Needle lowering, bounded equality saturation, context rent, usage observations and native cognition tasks.

The new integrated candidate is therefore not another language generation. It is a compiler architecture hypothesis:

`existing G9 surface -> canonical typed Causal Transition Kernel (CTK) -> evaluator / verifier / lowerings / instrumentation`

Candidate CTK dimensions:

- semantic identity + runtime resource identity;
- source/output epoch;
- typed value/state including UNKNOWN/CONFLICT/REVOKED;
- Delta/change set;
- typed relation/role/n-ary identity;
- cause/dependency refs;
- provenance/evidence expression;
- effect intent;
- capability scope;
- protected information-flow class;
- resource budget;
- recoverability/rollback witness;
- intervention/measurement specification;
- execution/verification receipt;
- cost shadow.

## Why this matters now

`BASE_CLAYCODE_RELEASE` is the active gate and all 14 current work packages remain OPEN. The highest-information question is no longer whether Clay needs a rich semantics; it is whether the existing rich semantics can be compiled into one coherent executable pipeline without introducing unnecessary new surface constructs.

## Evidence added by this run

1. **GWT re-entry toy support:** truthful re-entry strongly outperformed shuffled/no re-entry in the local noisy tracking model; target replication remains mandatory.
2. **N-ary representation negative result:** unlabeled pairwise clique reduction cannot preserve role-labelled ternary identity; typed pairwise reduction remains an open simpler alternative.
3. **Incrementalism qualifier:** dependency-directed recomputation is highly sensitive to graph density; a runtime crossover to batch/full recomputation should be benchmarked.
4. **Safe-Effect composition counterexample:** individually valid read/send capabilities can compose into forbidden data flow; effect/capability safety needs flow-sensitive composition checks or an independently proven equivalent architecture.
5. **Epoch-coherence toy support:** atomic old-or-new publication prevented mixed-state reads in a minimal coupled-state model.

## External evidence alignment

- row-polymorphic effect systems support making effects statically visible;
- capability systems support least/explicit authority at resource boundaries;
- information-flow-control systems support end-to-end data-flow policy beyond simple access control;
- WAL/snapshot systems support coherent historical/snapshot reads;
- incremental view-maintenance research supports delta-derived recomputation but does not imply it always wins;
- equality-saturation research supports bounded alternative-preserving compiler optimization and highlights explosion/cost risks;
- GWT/PEID literature provides relevant architecture/measurement ideas but does not validate FRANK's complete coupling architecture.

## Open contradictions preserved

- CTK unification may simplify lowering, or may create a giant tagged IR with worse compiler complexity.
- Native hyperrelations may preserve semantics efficiently, or typed pairwise/state-machine reductions may be cheaper and equally expressive.
- Incremental Delta propagation may dominate sparse workloads but lose badly in dense dependency closure.
- Capability-only security may prove sufficient under a stricter adapter architecture; information-flow labels are not pre-promoted as mandatory until the comparative test runs.
- Whole-system recurrence may explain FRANK better than a conventional event pipeline, but no target-run evidence in this run decides that question.

## Current-stage decision

**NO ClayCode surface change is justified by this run.**

Instead, prioritize an executable cross-branch semantic conformance suite. A new syntax/semantic primitive should be admitted only if a minimal witness from a registered branch cannot be represented and lowered with current G9 semantics without an opaque host escape hatch.

## Required next executable artifact

`BASE_CROSS_BRANCH_SEMANTIC_CONFORMANCE_SUITE`

At minimum include witnesses for:

- FRANK multiscale recurrent transition + recovery;
- GWT episode through re-entry receipt;
- Emergence intervention/readout with null control;
- Hyperposition role-labelled n-ary relation + reduction test;
- ClayGraph Delta/projection/activation boundary;
- UnifiedDB snapshot/ViewDelta/replay;
- Safe-Effect capability + protected-flow + budget + rollback commit;
- adaptive visual prototype/version/provenance/promotion rollback;
- Harness deterministic fixture + frozen-output intervention.

Pipeline under test:

`parse -> canonicalize -> semantic hash -> typed IR -> type/effect/flow check -> evaluator -> lowering -> runtime receipt -> replay`.

This packet is an OPEN research synthesis, not a release gate or scientific generation promotion.
