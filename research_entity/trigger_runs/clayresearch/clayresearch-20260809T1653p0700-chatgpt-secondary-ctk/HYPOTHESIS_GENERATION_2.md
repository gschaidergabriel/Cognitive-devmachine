# ClayResearch — Hypothesis Generation 2

Run: `clayresearch-20260809T1653p0700-chatgpt-secondary-ctk`

These hypotheses are materially transformed after external research + five synthetic experiments. They are not promoted by being second-generation.

## H2-CR-001 — CTK should be a normalized header + typed payload, not a giant universal record

**Mechanism:** Common transition invariants (`semantic_id`, `source_epoch`, `output_epoch`, causes, provenance root, cost, receipt identity) form a small canonical header. Domain payloads remain typed (`StateDelta`, `GraphDelta`, `EffectTransition`, `WorkspaceTransition`, `MeasurementTransition`).

**Why transformed:** H-CR-001's universal CTK risks a giant tagged-union compiler anti-pattern. The strongest version is semantic convergence where invariants are genuinely shared while payload distinctions remain explicit.

**Prediction:** Less duplicated validation/replay code than fully separate IRs, but lower tag/branch overhead and clearer typing than one monolithic transition record.

**Counterhypothesis:** Either fully separate IRs or one universal record is simpler in practice.

**Test:** Implement three micro-compiler variants and compare code size, invalid-state representability, compile latency, runtime overhead and mutation-bug detection.

## H2-CR-002 — Re-entry benefit may be temporal sufficient-statistic reuse, not GWT-specific causality

**Mechanism:** The toy truthful-reentry gain can arise because the prior estimate is a useful sufficient statistic in an autocorrelated process.

**Why transformed:** The toy test strongly separates truthful vs shuffled context but cannot attribute the gain specifically to a GWT workspace mechanism.

**Prediction:** A conventional Kalman/Bayesian recurrent estimator with the same sufficient statistic can match the toy gain.

**Counterhypothesis:** GWT-specific selection/broadcast/receiver dynamics add measurable value beyond recurrent estimation.

**Test:** H1 compare workspace re-entry against a simpler matched recurrent-state baseline under frozen model output.

## H2-CR-003 — N-ary semantics should be admitted by role/intervention irreducibility, not member count

**Mechanism:** A relation becomes n-ary-semantic when no simpler typed reduction preserves role identity plus intervention/replay behavior under matched cost—not merely because it has >2 members.

**Why transformed:** Unlabeled pairwise reduction is constructively refuted, but typed pairwise reduction remains viable.

**Prediction:** Some 3+-member relations compile losslessly to typed pairwise/state machines; others require native n-ary identity.

**Test:** Automated reduction search + counterexample generator over role-labelled relation corpus.

## H2-CR-004 — Incremental runtime strategy should be selected by online affected-closure cost estimation

**Mechanism:** Estimate affected closure and operator costs before committing to delta propagation; switch to batch/full recomputation when expected incremental cost exceeds batch cost.

**Why transformed:** Synthetic closure moved from ~9% to ~92% touched as graph density increased.

**Prediction:** Adaptive strategy dominates fixed incremental/batch in p95 latency over mixed workloads.

**Counterhypothesis:** Estimation overhead/uncertainty erases the benefit.

**Test:** Real ClayGraph/UDB operator benchmark with oracle, heuristic and fixed strategies.

## H2-CR-005 — Safe composition may be best represented as authority x information-flow product policy

**Mechanism:** Commit admissibility depends on both what resource/action is authorized and what provenance/label class of data is flowing to what sink. Neither dimension is collapsed into the other.

**Why transformed:** Capability composition counterexample shows local authorization can coexist with forbidden global flow; IFC prior work shows flow policy catches a distinct class.

**Prediction:** Product policy catches leaks missed by capability-only while rejecting fewer useful programs than globally secret/no-network policies.

**Counterhypothesis:** Adapter-level capability partitioning can make the product policy redundant.

**Test:** Realistic capability-only vs adapter-partition vs capability×IFC benchmarks.

## H2-CR-006 — Semantic epochs should be operation-scoped coherence domains, not a universal global barrier

**Mechanism:** Only state that must be jointly observed for a specific operation shares an atomic publication epoch; unrelated domains advance independently.

**Why transformed:** Atomic publication fixes mixed-read correctness in the toy, but universal barriers can harm latency and legitimate asynchrony.

**Prediction:** Operation-scoped epochs preserve invariants with less contention than one global epoch.

**Counterhypothesis:** Global epoch simplicity outweighs coordination cost at v0.1 scale.

**Test:** Cross-plane snapshot benchmark with global, per-domain and operation-scoped epochs.

## H2-CR-007 — GWT/Hyperposition measurement should compile as read-only observer effects with explicit non-authority type

**Mechanism:** Measurement/intervention declarations share transition identity/epochs but observers receive no capability-bearing commit path unless an independent intervention authority is supplied.

**Prediction:** Instrumentation can be optimized/replayed without allowing readout values to mutate truth or effect authority.

**Counterhypothesis:** Separate measurement runtime is safer and simpler.

**Test:** Mutation/fuzz suite attempts observer-to-effect escalation.

## H2-CR-008 — Persistent equality state should be scoped to semantic-stable regions, not compiler-global

**Mechanism:** Preserve e-graph equivalences only across stages whose semantic hashes prove compatibility; invalidate at effect/resource/authority-sensitive boundaries.

**Why transformed:** External persistent-egraph work supports cross-stage reuse, while G9 authority/resource semantics make unrestricted equality carryover risky.

**Prediction:** Better optimization reuse than stage-local e-graphs without stale effect equivalence.

**Counterhypothesis:** Stage-local e-graphs are safer with negligible lost optimization.

**Test:** Rewrite workloads containing pure and effectful/resource-sensitive transformations.

## H2-CR-009 — BASE freeze should be witness-driven: 'no unresolved executable semantic counterexample' rather than 'all downstream design resolved'

**Mechanism:** Each branch contributes minimal executable witnesses; BASE freezes when current G9 can parse/type/check/evaluate/lower all required witnesses and all known counterexamples are classified.

**Prediction:** H1 exposes fewer genuine semantic reopenings while avoiding endless architecture memo churn.

**Counterhypothesis:** Downstream uncertainty still hides semantic requirements that witness selection misses.

**Test:** Build cross-branch conformance suite and track semantic reopen rate through H1.

## H2-CR-010 — Safe-Effect backend defense should be layered: Clay semantic checks + capability sandbox + OS receipts

**Mechanism:** Clay checker establishes semantic/effect/flow intent; WASI or equivalent restricts concrete resource reachability; host broker verifies commit/recovery/budget and records receipt.

**Prediction:** Layered design catches more adversarial cases than any single layer with acceptable utility cost.

**Counterhypothesis:** Complexity creates confused-deputy bugs and one strong capability layer is safer.

**Test:** Generated-code escape and delegation suite across one-layer vs layered implementations.

## H2-CR-011 — Dynamic Binding Lattice promotion should depend on counterfactual contribution per cost, not raw multi-axis richness

**Mechanism:** A binding/hyperbinding is retained as active semantic structure only when lesion/rescue or held-out intervention gain exceeds its retrieval/latency/false-binding cost.

**Prediction:** Prevents overcoupled high-dimensional lattices from becoming self-justifying complexity.

**Counterhypothesis:** Multi-axis state improves enough tasks that explicit cost gating is unnecessary.

**Test:** DBL_E1-E8 plus cost-adjusted promotion threshold sweep.

## H2-CR-012 — The most reusable BASE primitive is a proof/receipt-bearing state transition, not a neuroscience-labelled organ primitive

**Mechanism:** GWT, goals, Retina familiarity, graph activation, UDB updates and effect execution are domain semantics compiled through generic typed transition/receipt machinery; neuroscience-inspired labels remain library/domain types.

**Prediction:** Compiler core stays small while FRANK-specific expressivity remains intact.

**Counterhypothesis:** Domain primitives need bespoke compiler semantics for performance/correctness.

**Test:** Attempt to express/compile one witness from each domain using generic transition machinery; record where bespoke semantics are truly required.

## Generation-2 synthesis

The second generation shifts the architecture away from two extremes:

- not a giant universal 'everything is one record/database/graph' abstraction;
- not a fragmented collection of unrelated special-case organs.

The candidate center is **shared semantic invariants + typed domain payloads + explicit authority boundaries + measured adaptive runtime strategies**.

This is a research direction for BASE compiler convergence, not a release decision.
