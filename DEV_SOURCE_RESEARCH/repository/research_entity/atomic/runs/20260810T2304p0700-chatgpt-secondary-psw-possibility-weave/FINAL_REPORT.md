# ATOMIC — PSW-001 Possibility State Weave

## Executive result

This cycle searched the current Frank v0.1 frontier for a non-duplicated high-leverage problem after the SPL, CMX, V16, Q23 and ClayCode/effect work had moved. The selected problem was not a new truth semantics for Hyperposition; current Hyperposition remains intentionally NO_CHANGE. The question was physical and computational:

> How can self.root preserve many unresolved alternatives exactly without paying for N complete copies of mostly-identical cognitive state and N repeats of identical pure computation?

The candidate `Possibility State Weave (PSW-001)` represented alternatives as an immutable common base plus sparse branch deltas and proposed exact-read-signature lifting of pure transitions across branches.

The candidate was built and measured, but **failed its architecture-level acceptance condition**.

A simpler conventional baseline — immutable base + sparse per-branch overlays + exact branch metadata + memoization keyed by transition identity and exact material read signature — reproduced PSW's defining state and computation sharing. Across 168 scaling cells it required exactly the same number of pure transition evaluations. PSW's median local time was 1.00937x the conventional baseline and its serialization proxy was 1.01518x the ordinary overlay representation.

Final decision:

`REFUTED_AS_DISTINCT_ARCHITECTURE / USEFUL_IMPLEMENTATION_ENVELOPE`

No PSW organ is promoted.

A durable target issue was created instead: `gschaidergabriel/Dr.-Unterweger#194`.

## 1. Freshness and nonduplication

The run began after several recent frontiers moved materially:

- SPL-001 had already refuted a separate Semantic Parity Lattice and routed translator validation into issue #162.
- CMX-001 had just refuted market-like procedural memory selection against a stronger newest-valid/supersession baseline.
- V16 execution continuity and explicit idle-handoff work had reached target-side evidence.
- Q23 was actively closing multimodal representation/cache/epoch work.
- current ClayCode WP03/WP04 and effect-generation fencing were under active parallel work.
- autotelic/proactive agency already had owner-fixed InterestTrace/Goal/Heartbeat semantics and therefore was not a free invention surface.

The current Hyperposition branch itself remained NO_CHANGE and explicitly required an executable counterexample before changing unresolved-alternative semantics. Its consumer constraint was that alternatives preserve entity/version/provenance distinctions and do not fabricate cognitive states across downtime.

Therefore this run intentionally treated Hyperposition semantics as fixed and asked only about physical representation and pure computation reuse.

## 2. GRT search, not GWT enclosure

The current owner correction defines Generative Reality Theory (GRT) as the outer ATOMIC thinkspace. GWT is one possible mechanism family, not the boundary of thinkability.

Accordingly the hypothesis population included conventional and alien geometries: log-only worlds, sparse overlays, content-addressed DAGs, guarded fields, lazy fork, causal slicing, observational quotienting, adaptive representation, genomic-reference encoding, deferred-measurement/symbolic encoding, particles, SIMD-over-worlds, branch-epoch braids and factorized possibility graphs.

The candidate was selected for falsifiability and cross-module leverage rather than narrative novelty.

## 3. Hypothesis field

Fourteen hypotheses from eight families were generated.

The selected H2/PSW proposed:

`shared immutable base + sparse branch deltas + exact branch guard/identity + pure transition lifting over equal exact read signatures`.

The strongest initial counterhypothesis was present before implementation:

> Ordinary sparse overlays plus memoization probably reproduce the same useful sharing with less architecture.

This counterhypothesis became the decisive test.

## 4. External prior-art collision

Fresh technical research sharply limited novelty.

Persistent data structures already preserve access to multiple versions using structural-sharing techniques. Variational execution explicitly executes many configurations together, tracks alternative concrete values, and shares similarities/redundant execution across configurations. Faceted execution already provides guarded/conditional alternative values. Self-adjusting computation tracks dependencies and propagates only the computation affected by changes.

Therefore none of the broad claims — persistent alternative state, guarded values, shared many-world computation, lazy divergence, dependency-driven recomputation — can support a world-first or general mechanism novelty claim.

The highest surviving novelty class was:

`PROJECT_SPECIFIC_COMBINATION_ONLY`.

The project-specific part is the composition with Frank's epistemic/authority laws:

- unresolved branch != truth;
- unresolved branch != SELF;
- unresolved branch != user intent;
- unresolved branch != effect authority;
- branch identity includes exact self/entity/version/epoch/revision/hypothesis/provenance;
- physical deduplication never implies epistemic identity merge;
- shared execution is restricted to exact PURE transitions with complete current material-read semantics;
- effects are proposals only until the single-current normal authority path executes them;
- downtime does not invent unpersisted branch evolution.

## 5. ClayCode-first candidate

The candidate artifact defines `BranchIdentity`, `SparseDelta`, `PossibilityBranch`, `PossibilityStateWeave`, `PureTransitionContract`, `ReadSignature`, `LiftWitness` and `CollapseWitness`.

The critical rule is not a new truth operator. It is a runtime admissibility law:

`branches may share one PURE evaluation only when their exact current transition ReadSignature is equal`.

A ReadSignature is bound to transition identity/implementation, exact read values, base state epoch and semantic epoch.

Unknown/dynamic read set disables lifting.

External/effectful/security-sensitive operations cannot be unresolved multi-branch executed.

The candidate also makes an explicit distinction between physical equality and epistemic identity: two branches can share identical immutable payload storage and still remain distinct branches because their hypothesis identity or provenance differs.

## 6. Benchmark design

The deterministic local Python reference used controlled integer-valued state fields. This was not intended as a cognitive-quality benchmark. It isolates representation and computation-sharing mechanics.

Main scaling dimensions:

- state fields F: 64, 256, 1024;
- branch counts N: 4, 16, 64, 256, with 1024-branch cells for F=256/1024;
- divergence density: 0%, 1%, 5%, 10%, 25%, 50%;
- pure transition material read-set sizes: 4 and 16;
- total scaling cells: 168.

The full-copy ground truth materialized every branch. Sparse overlay stored one base and override map per branch. Overlay+memo keyed the deterministic pure transition by its exact read tuple. PSW explicitly grouped branches by that same exact signature and evaluated once per group.

The benchmark asserted exact equality of reconstructed state and pure outputs.

## 7. Main scaling result

All exact reconstruction and pure-output checks passed.

Across the 168 cells:

- median ordinary overlay serialization / FULL_COPY: 0.177876;
- median PSW serialization / FULL_COPY: 0.184566;
- median PSW / ordinary overlay serialization: 1.015177;
- median OVERLAY_MEMO time / FULL_COPY: 0.717381;
- median PSW time / FULL_COPY: 0.720328;
- median PSW / OVERLAY_MEMO time: 1.009366;
- OVERLAY_MEMO faster: 103 cells;
- PSW faster: 65 cells.

Most importantly:

`overlay-memo unique evaluation count == PSW group evaluation count`

for every scaling cell.

This is the architecture refutation. PSW did not discover a new computation-sharing equivalence. It explicitly materialized the same equivalence class that a normal memoization key obtains from the exact material read signature.

## 8. Low-divergence regime

Sparse sharing itself is unquestionably useful in the synthetic state model.

A six-seed representative series used F=1024, N=256, read-set=16.

At 0% divergence:

- 1 unique read signature;
- sharing factor 256x;
- overlay serialization ~0.784% of FULL_COPY;
- overlay-memo time ~23.85% of FULL_COPY;
- PSW time ~24.68% of FULL_COPY.

At 1% divergence:

- median 37.5 unique signatures;
- ~6.83x sharing;
- overlay serialization ~1.755% of FULL_COPY;
- overlay-memo ~40.33% of FULL_COPY time;
- PSW ~40.65%.

At 5% divergence:

- ~145.5 unique signatures;
- ~1.76x sharing;
- overlay-memo ~75.07% of FULL_COPY;
- PSW ~74.01%.

This establishes a real low-divergence benefit, but not a PSW-specific one.

## 9. Crossover and high-divergence regime

At 10% divergence in the representative read16 workload:

- ~213 unique signatures out of 256;
- only ~1.20x compute sharing remained;
- overlay memo was already ~97.86% of FULL_COPY time.

At 25% divergence:

- ~253 unique signatures;
- ~1.01x sharing;
- overlay memo became ~1.169x FULL_COPY time.

At 50% divergence:

- all 256 signatures were unique;
- no compute sharing remained;
- overlay memo was ~1.194x FULL_COPY.

The useful physical state compression can persist after compute-sharing benefit disappears. This distinction is important: state divergence and transition read-signature divergence are related but not identical.

A branch may differ strongly in fields irrelevant to a particular transition and still share computation. A globally low-divergence branch may still destroy sharing if its few changed fields lie exactly in a transition's read set.

Therefore the production control signal should be read-signature diversity and measured transition cost, not only a global 'branch divergence percentage'.

## 10. 1024-branch stress examples

For F=1024, N=1024, read-set=16:

At 0% divergence:

- FULL_COPY wire proxy: 14,474,241 bytes;
- ordinary overlay: 71,414 bytes;
- PSW: 79,535 bytes;
- one unique signature;
- 1024x sharing;
- overlay memo ~0.214x FULL_COPY execution time;
- PSW ~0.221x.

At 1% divergence:

- 152 unique signatures;
- sharing factor ~6.74x;
- FULL_COPY ~14.48 MB;
- overlay ~211.7 KB;
- PSW ~219.8 KB;
- overlay memo ~0.388x FULL_COPY;
- PSW ~0.391x.

At 50% divergence/read16:

- all 1024 signatures unique;
- no computation sharing;
- overlay memo ~1.355x FULL_COPY;
- PSW ~1.422x.

This reinforces the crossover rather than a universal shared-state win.

## 11. Guarded-value control

A field-wise guarded-value proxy was also tested in the representative series. It can compress storage, but in this Python implementation its per-field indirection was slower than the simpler branch overlay path.

This is not a claim against production faceted/BDD implementations; it is only evidence that adding a more elaborate guard representation is not automatically beneficial for Frank's workload.

## 12. Critical read-set lesion

This is the most important safety result of the run.

Two branches were built:

- same value for `a`;
- different value for `b`.

The pure transition actually read both `a` and `b`.

An intentionally wrong memo contract declared only `a` as the material read set. The two branches therefore received the same cache key. One evaluation was reused for both.

Result:

- incomplete read-set: 1 concrete incorrect branch output;
- exact `{a,b}` read-set: 0 incorrect outputs.

Therefore cross-branch computation sharing is only sound if ClayCode/runtime can provide a sound exact or conservative material read/effect summary. `PURE` by itself is not enough.

This is a durable compiler/runtime obligation independent of PSW.

## 13. Epistemic merge lesion

Two branches were constructed with equal materialized payload but different:

- `hypothesis_id`;
- `provenance_root`.

A payload-only merge considered them identical.

Strict branch identity did not.

This establishes a clean separation:

`physical data equality` may permit storage deduplication;

`epistemic branch identity equality` requires stronger identity/provenance conditions.

Frank may store a shared immutable value once while keeping two distinct references/evidence histories. That is compression, not semantic collapse.

## 14. Epoch/self controls

The reference safety boundary rejected:

- stale base epoch;
- native identity `Frank` instead of `self.root`.

The current exact `self.root`/epoch passed.

The human surface name therefore remains irrelevant to internal branch identity.

## 15. Effect controls

Positive lifting control:

`PURE + exact known read set -> may lift`.

Negative controls:

- PURE with unknown read set -> no lift;
- EXTERNAL_READ -> no unresolved multi-branch lift;
- EXTERNAL_WRITE -> no lift;
- SECURITY_CHANGE -> no lift.

The conservative EXTERNAL_READ rule is deliberate for this candidate: even a read can be time-varying, side-channel-bearing, rate-limited or observationally non-repeatable. A later capability-specific rule could prove a read replay-safe, but PSW is not allowed to infer that.

## 16. Adaptive representation result

Because low and high divergence regimes cross, H8 — an adaptive representation selector — became more useful than PSW itself.

A simple diagnostic policy was tested:

`if unique_read_signatures / active_branches <= threshold -> OVERLAY_MEMO else FULL_COPY/separate`.

On the main 168-cell grid, threshold 0.8 had mean measured time regret ~0.1556% versus an oracle that chooses the faster measured path per cell, with ~96.4% exact winner selection. Because this threshold was inspected on the main grid, that is not held-out evidence.

A separate 48-cell grid with a different seed family was then generated across F=256/1024, N=64/256, all six divergence values and read sets 4/16.

The same 0.8 probe had:

- mean regret ~0.0829%;
- p95 regret 0 in the sampled timing table;
- exact measured winner fraction ~95.8%.

The numeric threshold is not portable. It is a synthetic signal that **representation should be a measured physical policy**, not a permanent semantic organ.

## 17. Why PSW still fails despite the positive adaptive result

Adaptive selection is not unique to PSW. It can choose between normal representations.

The durable design therefore becomes simpler:

- semantic Hyperposition/ACEF branch model remains authoritative;
- physical representation is replaceable;
- conventional sparse deltas are preferred when beneficial;
- exact read-signature memoization is enabled only for sound PURE transitions;
- branch materialization/separate execution is selected when signature diversity or bookkeeping cost makes sharing unprofitable.

That is an implementation envelope, not a new cognitive organ.

## 18. Concurrent ACEF collision

During PSW execution, another ATOMIC worker published ACEF — Atomic Causal Epoch Fabric.

ACEF already introduces `HypothesisBranch` and branch-scoped `SemanticDelta` inside execution/lease/state/schema/identity-bound cognitive transactions. It distinguishes monotone, non-monotone and effect-coupled deltas and controls canonical commit through commit certificates.

ACEF itself is still a non-promoted testing candidate and its strongest simpler task-/belief-transaction counterhypothesis remains unresolved.

Nevertheless its existence raises the duplication penalty for PSW dramatically. A second branch-state substrate would be unjustified.

The correct interconnection is one-directional:

if ACEF later survives and becomes the semantic branch/transaction substrate, then the sparse representation and exact PURE read-signature policies discovered here may be tested underneath it as a physical runtime strategy.

PSW does not alter ACEF's commit semantics.

## 19. New AI-native architecture freedom directive

A new owner-fixed directive arrived during final refresh stating that Frank's internal representation may be machine-native, distributed, learned, dynamic, high-dimensional, nonlinguistic or nonhuman-readable. Human intuitiveness is not a promotion gate.

Crucially, the same directive requires measurable outcomes, falsification survival and comparison against simpler baselines; a candidate should be rejected/held if novelty lacks benefit or a simpler candidate dominates.

PSW's rejection is therefore fully aligned with the new directive. PSW is **not** rejected because it is unusual. It is rejected because a simpler conventional baseline reproduced its measured benefit.

## 20. Target re-entry

Target issue `gschaidergabriel/Dr.-Unterweger#194` was created.

The issue requires future real Hyperposition/ACEF branch implementation to compare:

1. independent materialized states/execution;
2. sparse branch delta/overlay;
3. sparse branch delta/overlay + exact read-signature memoization;
4. the actually admitted branch substrate existing at that future head.

It requires exact reconstruction, false-merge controls, stale/replay rejection, CPU, RSS, serialization, latency, signature overhead, conversion cost and held-out representation-policy evaluation on the accepted target VPS.

The synthetic 0.8 threshold is explicitly forbidden from becoming an unmeasured production constant.

## 21. What was not measured

No target-VPS PSW benchmark was claimed because there is no current admitted target Hyperposition/ACEF physical runtime corresponding to this synthetic structure. Inventing target code solely to create a 'VPS PASS' would test the new benchmark harness, not current Frank.

Unmeasured:

- real Frank branch traces;
- production Clay value sizes;
- actual model context/token savings;
- target-VPS RSS/CPU;
- production persistent HAMT/BDD implementations;
- compiler-generated sound material read sets;
- representation-conversion cost in real UnifiedDB;
- final ACEF physical semantics because ACEF is still a candidate.

These remain the correct next falsifiers.

## 22. Scientific result

The cycle began with a candidate that looked like a new 'many-world cognitive state weave'. External research and strong baselines progressively removed almost all novelty.

What remains is more precise and more useful:

### Supported implementation facts in the tested proxy

- Sparse branch deltas can reduce physical state serialization enormously when branches mostly agree.
- Exact read-signature memoization can reduce pure computation enormously when branches are observationally identical for that transition.
- Sharing benefit collapses as read-signature diversity approaches branch count.
- One missing material read makes cross-branch reuse unsound.
- Physical payload equality cannot replace epistemic/provenance branch identity.
- A simple adaptive representation policy can closely track a regime crossover in held-out synthetic cells.

### Refuted claim

- PSW is not a distinct architecture mechanism required to obtain those gains.

### Durable architecture direction

`semantic branch substrate` and `physical branch representation` should be separate concerns.

The semantic substrate preserves truth/uncertainty/provenance/epoch/authority laws.

The physical layer may adaptively use materialization, sparse deltas, structural sharing and exact pure computation reuse according to measured workload, with machine-verifiable conversion/identity receipts.

That conclusion is now encoded in the run artifacts and target issue #194.

## 23. Authority statement

This run:

- did not promote PSW;
- did not change Hyperposition truth semantics;
- did not mint effect authority;
- did not authorize final training;
- did not mutate a target Harness;
- did not claim synthetic results as target-live results;
- did produce a reproducible reference discriminator, negative controls, a measured resource envelope, an adaptive policy proxy, a target issue and whole-mesh re-entry.
