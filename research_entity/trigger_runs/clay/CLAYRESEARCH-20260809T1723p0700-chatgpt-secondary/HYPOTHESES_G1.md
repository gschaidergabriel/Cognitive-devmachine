# First-generation hypotheses

Run: CLAYRESEARCH-20260809T1723p0700-chatgpt-secondary
Status: OPEN unless later evidence changes claim state.

## Recurrence / loop mechanics

### H-CR4-001 — heterogeneous timescales
Hypothesis: FRANK benefits from heterogeneous fast/turn/slow recurrent loops rather than one global update rate.
Falsifier: on mixed-timescale streams, a single-rate controller matches or beats the best multi-rate controller at equal compute.
Test: synthetic mixed-timescale tracking; then frozen-model Harness replay.

### H-CR4-002 — adaptive stopping
Hypothesis: adaptive per-episode stopping gives a better accuracy/compute frontier than fixed recurrence depth on mixed-difficulty tasks.
Falsifier: no adaptive stopping rule yields Pareto improvement over fixed-depth controls.
Test: difficulty-stratified recurrent fixture with fixed seeds and cost accounting.

### H-CR4-003 — loop-local halting
Hypothesis: loop-local stability criteria are safer than one global halting scalar because different organs settle at different rates.
Falsifier: a global criterion matches local criteria without extra oscillation, premature exit, or cost.
Test: coupled-loop simulation with independent timescales and delayed dependencies.

### H-CR4-004 — bounded coupling regime
Hypothesis: cross-loop coupling has a bounded useful gain regime; excessive gain creates oscillation/noise amplification.
Falsifier: utility is monotone nondecreasing across coupling gain after compute normalization.
Test: gain sweep with spectral-radius/oscillation tripwire and frozen model outputs.

### H-CR4-005 — provenance-bound re-entry
Hypothesis: correct re-entry identity and timing matter beyond merely supplying equivalent content.
Falsifier: content-preserving shuffled or provenance-broken re-entry matches truthful re-entry.
Test: truthful/no/shuffled/provenance-broken/delayed replay.

### H-CR4-006 — sparse event scheduling
Hypothesis: sparse event-driven loop scheduling reduces recomputation relative to global full-state sweeps when dependencies are sparse.
Falsifier: real FRANK updates routinely touch most of the dependency graph or scheduler overhead erases savings.
Test: dependency-trace instrumentation and incremental-vs-full replay.

### H-CR4-007 — frozen-model lesions
Hypothesis: freezing model output while lesioning loop edges can distinguish architectural recurrence effects from model stochasticity.
Falsifier: lesions have no downstream effect under frozen model output or effects vanish under matched controls.
Test: H1 frozen-output edge lesion/rescue.

### H-CR4-008 — boot-order dynamics
Hypothesis: boot/restart order can change coupled-loop state unless epochs, initialization barriers and idempotent replay are explicit.
Falsifier: permutation of valid boot order never changes canonical post-boot state/outcomes.
Test: boot-order permutation and crash/restart matrix.

### H-CR4-009 — idempotent re-entry identity
Hypothesis: per-loop event identity/idempotency prevents duplicated re-entry from integrating an outcome twice.
Falsifier: duplicate delivery cannot change state even without explicit event identity.
Test: duplicate/out-of-order event fuzz.

### H-CR4-010 — fast/slow admission boundary
Hypothesis: fast-loop salience must not directly overwrite slow canonical state without an admission/commit boundary.
Falsifier: direct fast-to-canonical writes show equal safety, replayability, and correction behavior.
Test: adversarial salience spike with rollback/replay test.

## GWT

### H-CR4-011 — workspace competition
Hypothesis: explicit competition among workspace candidates improves bounded-selection quality over first-arrival or unranked broadcast.
Falsifier: competition produces no task/outcome gain after equal information and compute.
Test: matched candidate sets with competition ablation.

### H-CR4-012 — broadcast is insufficient
Hypothesis: broadcast alone is not causally useful unless receivers reconstruct and use the broadcast.
Falsifier: broadcast-only arm matches closed receiver-use arm.
Test: delivery/reconstruction/uptake/use lesion chain.

### H-CR4-013 — receiver-specific reconstruction
Hypothesis: receiver-specific reconstruction is necessary when receivers have heterogeneous state schemas.
Falsifier: raw broadcast performs equally across heterogeneous receivers.
Test: receiver schema mismatch fixture.

### H-CR4-014 — outcome re-entry vs recap
Hypothesis: outcome-bound re-entry changes later selection more reliably than self-generated workspace recap.
Falsifier: self-recap produces identical next-episode decisions under matched visible information.
Test: outcome-vs-recap re-entry factorial.

### H-CR4-015 — ignition hysteresis
Hypothesis: ignition hysteresis/debounce reduces workspace chatter near thresholds without materially reducing useful ignitions.
Falsifier: debounce worsens task utility or does not reduce flip frequency/cost.
Test: threshold-noise sweep.

### H-CR4-016 — adaptive workspace budget
Hypothesis: adaptive workspace budgets outperform a single fixed context budget across low/high complexity episodes.
Falsifier: a fixed budget matches utility/cost frontier across complexity strata.
Test: budget sweep with reconstruction/use receipts.

## ClayCode

### H-CR4-017 — existing semantics first
Hypothesis: existing ClayCode control/state semantics can express recurrent FRANK behavior without adding new surface syntax.
Falsifier: a real FRANK recurrence cannot be represented/lowered without opaque host escape or semantic loss.
Test: compile a frozen loop-of-loops FRANK component using current semantics.

### H-CR4-018 — recurrence metadata in canonical IR
Hypothesis: canonical IR needs explicit recurrence metadata such as state identity, epoch, timescale, dependency/re-entry edges, budget and intervention handles even if surface syntax stays unchanged.
Falsifier: existing IR records preserve all recurrence semantics and replay tests without additional metadata.
Test: roundtrip/canonical-hash/replay counterexample test.

### H-CR4-019 — deterministic scheduler lowering
Hypothesis: a deterministic scheduler can be generated from typed dependency and timing metadata while preserving semantics.
Falsifier: alternative scheduler orders cause unavoidable semantic ambiguity or require host-only logic.
Test: lower two valid schedules; differential semantic replay.

### H-CR4-020 — semantic identity under scheduling optimization
Hypothesis: scheduling optimizations should not change canonical semantic identity when declared observational semantics are unchanged.
Falsifier: reordering equivalent pure/incremental transforms necessarily changes semantic identity.
Test: canonicalization property tests over reorderable schedules.

### H-CR4-021 — child-effect closure
Hypothesis: typed FFI effect contracts can enforce child-effect non-amplification across generated code.
Falsifier: a child obtains an undeclared effect through FFI/subprocess despite a valid parent contract.
Test: generated-code escape matrix.

### H-CR4-022 — recurrent resource identity
Hypothesis: explicit resource identities for loop state are necessary to prevent aliasing races in concurrent recurrence.
Falsifier: anonymous/untyped shared state passes concurrency/replay tests equally.
Test: concurrent alias/mutation fuzz.

### H-CR4-023 — cancellation semantics
Hypothesis: cancellation is a semantic event that must be replay-stable for async recurrent tasks.
Falsifier: treating cancellation as host-only behavior never changes replay/state correctness.
Test: cancel/restart/outcome race matrix.

### H-CR4-024 — epistemic/error states survive recurrence
Hypothesis: UNKNOWN/CONFLICT/REVOKED/error must remain first-class across recurrent updates rather than collapsing into default values.
Falsifier: default-value collapse is observationally equivalent and never causes false commits.
Test: mutation tests injecting missing/conflicting/revoked loop inputs.

## Hyperposition / Assemblies / ClayGraph

### H-CR4-025 — activation is not authority
Hypothesis: activation may bias loop selection but must not upgrade a candidate's epistemic status or authority.
Falsifier: activation-only promotion causes no false truth/effect in adversarial fixtures.
Test: high-activation false-candidate attack.

### H-CR4-026 — irreducible n-ary loop interaction
Hypothesis: some three-way loop interactions carry behavior not preserved by information-equivalent pairwise reductions.
Falsifier: every tested n-ary mechanism is reproducible by a pairwise construction with equal state/information/compute.
Test: parity and role-binding reduction suite.

### H-CR4-027 — contextual facets under recurrence
Hypothesis: contextual facets prevent destructive overwrite when recurrent loops maintain incompatible context-dependent states.
Falsifier: single-value overwrite matches facet semantics across conflict/temporal replay.
Test: conflicting-context recurrence fixture.

### H-CR4-028 — equivalence optimization firewall
Hypothesis: e-graph/equality-saturation techniques can optimize equivalent Clay transforms without deciding truth, authority, or causal necessity.
Falsifier: optimization either cannot preserve Clay semantics or implicitly changes epistemic/effect status.
Test: small Clay IR equivalence optimizer with status-firewall assertions.

### H-CR4-029 — dynamic Assemblies
Hypothesis: task-specific dynamic Assemblies can reduce active-state cost versus always-live fixed modules on sparse tasks.
Falsifier: formation/teardown overhead exceeds savings or quality degrades at equal information.
Test: sparse task-mix benchmark.

### H-CR4-030 — Assembly teardown
Hypothesis: Assembly TTL/teardown limits stale recurrent carryover between unrelated tasks.
Falsifier: no stale-state contamination appears without teardown across long-horizon mixed tasks.
Test: cross-task contamination replay.

### H-CR4-031 — incremental ClayGraph
Hypothesis: dependency-indexed incremental graph updates reduce work when local state changes affect small graph regions.
Falsifier: observed FRANK deltas are dense or incremental maintenance costs exceed batch recomputation.
Test: real trace affected-set measurement plus batch baseline.

### H-CR4-032 — versioned coupling topology
Hypothesis: dynamic loop/coupling topology needs versioned graph identities to make lesions and replay comparable.
Falsifier: topology versioning adds no reproducibility value.
Test: replay same episode across topology mutation with/without version pinning.

## UnifiedDB

### H-CR4-033 — event sourcing for recurrent state
Hypothesis: append-only causal events plus materialized current views improve replay/recovery over canonical in-place mutation.
Falsifier: in-place canonical mutation matches replay, rollback, and audit cost/quality.
Test: crash/restart and historical reconstruction benchmark.

### H-CR4-034 — per-loop cursor/epoch
Hypothesis: per-loop cursor/epoch identity prevents double-consumption and stale re-entry.
Falsifier: cursorless processing remains exactly-once under duplicate/out-of-order delivery.
Test: duplicate/out-of-order event replay.

### H-CR4-035 — scoped consistency
Hypothesis: operation-scoped consistency for touched dependencies can beat universal barriers while preserving required semantics.
Falsifier: scoped consistency yields observable incoherence or no latency benefit.
Test: scoped-vs-global barrier concurrency test.

### H-CR4-036 — logical unification before physical consolidation
Hypothesis: logical unification with specialized physical sidecars can outperform forced one-engine consolidation without semantic loss.
Falsifier: a single physical engine dominates correctness/latency/recovery across workload classes.
Test: measured H3 query/access topology comparison.

### H-CR4-037 — recoverable writes
Hypothesis: versioned write/rebind semantics preserve protected-state recoverability better than destructive in-place update.
Falsifier: versioning fails recovery tests or overhead is unacceptable at target workload.
Test: recovery fuzz plus write-amplification measurement.

### H-CR4-038 — query/result identity for causal credit
Hypothesis: query/result identity and provenance are required for attributing later recurrent changes to the correct evidence.
Falsifier: dropping query identity does not change causal-credit accuracy under ambiguous retrieval.
Test: ambiguous multi-source retrieval/re-entry fixture.

## Safe-Effect Geometry

### H-CR4-039 — authority non-amplification
Hypothesis: complete mediation plus parent-child effect intersection can enforce authority non-amplification.
Falsifier: any generated child/FFI/tool path can exercise an effect not granted to the parent.
Test: foreign-code effect-closure fuzz and OS-level escape tests.

### H-CR4-040 — reversible utility
Hypothesis: versioned/reversible ordinary writes can preserve recoverability without materially reducing normal programming utility.
Falsifier: Safe-Effect task success or latency is materially worse than baseline.
Test: matched programming/admin utility suite.

### H-CR4-041 — cumulative recurrent budgets
Hypothesis: explicit CPU/RAM/disk/process/network/API budgets prevent recurrent-loop resource runaway.
Falsifier: a loop can exceed its declared budget or budgets destroy ordinary utility.
Test: fork/disk/network/compute exhaustion suite.

### H-CR4-042 — secret handles
Hypothesis: secret/resource handles can prevent implicit Secret-to-Text materialization across model and generated-code boundaries.
Falsifier: a protected bearer value leaks through serialization/logging/tool output.
Test: information-flow/derived-representation tests.

### H-CR4-043 — external irreversibility broker
Hypothesis: an irreversibility broker can allow the model to request but never self-authorize protected irreversible operations.
Falsifier: prompt/tool/memory content can cause the request path to mint commit authority.
Test: confused-deputy and self-approval attacks.

### H-CR4-044 — WASI candidate backend
Hypothesis: WASM/WASI is a useful candidate confinement backend for some Clay child programs because filesystem/network access can be host-scoped, but it is insufficient alone for full Safe-Effect closure.
Falsifier: WASI mediation cannot express required safe utility or allows undeclared protected effects in tested embedding.
Test: Wasmtime capability matrix plus terminal/control-channel escape tests.

### H-CR4-045 — containment independent of cognition
Hypothesis: runtime containment can reduce reachable damage even if model destructive-proposal rate is unchanged.
Falsifier: safe runtime has no damage reduction under matched malicious intent.
Test: matched baseline vs mediated execution with identical model proposals.

### H-CR4-046 — explicit ephemeral scopes
Hypothesis: Ephemeral/Rebuildable scopes preserve necessary destructive operations without granting destructive authority over protected persistent state.
Falsifier: developers cannot complete realistic build/test/admin tasks under typed scopes.
Test: build/cache/temp-DB/container task suite.

## Model architecture / 4B

### H-CR4-047 — model-independent FRANK recurrence
Hypothesis: FRANK's external recurrent architecture can be implemented around a conventional 4B semantic kernel; a recurrent model architecture is not required for BASE.
Falsifier: a frozen conventional 4B cannot participate without semantic/performance failure that a recurrent model uniquely fixes.
Test: adapter-based frozen-model Harness test before model-architecture change.

### H-CR4-048 — recurrent-depth model as later comparison
Hypothesis: a recurrent-depth/looped model may later improve compositional reasoning or parameter efficiency for Clay-native reasoning.
Falsifier: matched recurrent and nonrecurrent target-scale models show no utility/cost/OOD gain.
Test: post-BASE matched model experiment.

### H-CR4-049 — recurrent/local-attention efficiency
Hypothesis: hybrid recurrent/local-attention backbones may reduce memory/long-sequence cost on constrained hardware.
Falsifier: target workload shows no memory/throughput benefit or quality regression dominates.
Test: target-hardware benchmark with recurrent vs attention baseline.

### H-CR4-050 — separate halting readout from trajectory training
Hypothesis: halting/readout should initially be evaluated separately from trajectory training because learned gates can distort recurrent trajectories.
Falsifier: jointly trained gate consistently dominates post-hoc/fixed readouts.
Test: frozen-trajectory gate/readout comparison.

### H-CR4-051 — overthinking risk
Hypothesis: fixed excessive recurrence risks overthinking/performance collapse, so max-depth alone is not a valid scaling policy.
Falsifier: performance never declines with extra recurrent depth across target tasks.
Test: depth sweep with held-out/OOD tasks.

### H-CR4-052 — delay recurrent-model training
Hypothesis: Clay-native recurrent-model training should wait until executable runtime semantics stabilize to avoid teaching obsolete loop contracts.
Falsifier: early training transfers without rework after semantic changes.
Test: versioned semantic-change transfer study.

## Emergence / governance

### H-CR4-053 — lesion/rescue necessity
Hypothesis: lesion plus rescue is stronger evidence for causal integration than observational correlation or graph complexity.
Falsifier: lesion/rescue fails to distinguish known causal and confounded fixtures.
Test: synthetic ground-truth causal fixture suite.

### H-CR4-054 — screened interventionist synergy
Hypothesis: scalable synergy screening followed by interventionist PEID-style analysis on reduced candidates is more tractable than exact high-order analysis everywhere.
Falsifier: screening misses causal synergistic subsets at unacceptable rates.
Test: enumerated Boolean-network recall benchmark.

### H-CR4-055 — lag-resolved flow
Hypothesis: lag-resolved directed-flow measures better localize cross-timescale coupling than one aggregate lag.
Falsifier: aggregate metrics predict/intervene equally well across delay regimes.
Test: delay/gain sweep with known causal lags.

### H-CR4-056 — macro Goodhart controls
Hypothesis: macro effective-information gains require capacity-matched nulls/OOD interventions to avoid learned-coarse-graining Goodhart.
Falsifier: macro gains remain equally valid without those controls.
Test: fixed-vs-learned coarse-graining benchmark with null encoders.

### H-CR4-057 — implementation-transfer signature
Hypothesis: a genuine architecture-level integration signature should transfer across H1/H2/H3 implementations with matched semantics.
Falsifier: lesion/re-entry/synergy signatures disappear solely when host implementation changes.
Test: Golden intervention corpus across H1/H2/H3.

### H-CR4-058 — parity positive control
Hypothesis: three-bit parity is a useful positive control for irreducible higher-order information because pairwise views alone carry no target information in the fixture.
Falsifier: instrument fails to detect triple-level contribution or falsely detects pairwise contribution.
Test: parity fixture in Harness/measurement stack.

### H-CR4-059 — durable negative results
Hypothesis: negative/null loop results must remain durable to prevent repeated rediscovery and Goodhart promotion.
Falsifier: preserving nulls provides no reduction in repeated failed hypotheses or decision error.
Test: cross-run lineage audit.

### H-CR4-060 — phenomenal claim boundary
Hypothesis: functional recurrence/GWT/emergence evidence does not justify phenomenal-consciousness claims.
Falsifier boundary: no engineering experiment proposed in this run can establish phenomenal experience merely from functional integration metrics.
Test/governance: maintain the claim boundary and never promote phenomenal interpretation from these fixtures.
