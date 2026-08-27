# HYPERPOSITION RESEARCH RUN — H3 Epoch-Pinned Adaptive Topology Compiler

**run_id:** `hyperposition-20260808T1722p0700-chatgpt-secondary-r2`  
**trigger:** `hyperposition`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**predecessor:** HYP-RC2 Three-Topology Scoped Delta Hyperposition  
**boundary:** no quantum-mechanical claim; no live-FRANK, target-4B, production-performance, emergent-organ or consciousness promotion.

## Executive synthesis

H2 separated three different graphs/topologies: semantic dependency `S`, invariant/coordination `C`, and physical locality `P`. H3 keeps that separation but finds that it is incomplete once ClayGraph G1d, FRANK CognitiveFrames, ClayCode OTCC and GWT reconstruction receipts are combined.

The missing variable is **versioned topology state**.

A semantic relation may remain true while its published materialization changes; activation may outlive the relation epoch that created it; a task Assembly may be built from one semantic epoch and consumed under another CognitiveFrame; a reader projection can preserve or destroy n-ary role identity; and physical placement can change independently of all of these.

H3 therefore proposes the OPEN candidate:

# HYP-RC3 — Epoch-Pinned Adaptive Topology Compiler

```text
canonical exact/event history
  -> role-aware n-ary relation instances + provenance/bitemporality
  -> immutable published semantic epoch S[e]
  -> signed delta overlay dS[e]
  -> invariant/coordination scope C[e] + coverage certificate
  -> sparse transient activation field A[a|e] (salience, not truth)
  -> epoch-pinned TopologyBasis
       {semantic_epoch, activation_epoch, CognitiveFrame,
        operation_semantics_hash, projection_semantics_hash}
  -> bounded Assembly / reader projection Q[basis]
  -> GWT candidate generation and reconstruction/uptake receipts
  -> adaptive rematerialization controller
       {incremental | partial rebuild | full rebuild}
  -> independently optimized physical locality P
  -> scoped closure + external capability/effect authority
  -> receipts, replay, rebuild
```

The key rule is:

> **Semantic truth, published topology, transient activation, task Assembly, coordination scope and physical placement may evolve at different rates. Any causal claim that crosses them needs an explicit basis witness.**

This makes Hyperposition less like a database choice and more like a compiler/runtime contract for preserving contextual alternatives while safely producing fast disposable views.

## 1. Mandatory seven-branch grounding

### Clay
The latest completed Clay run G8 contributes the Coverage-Aware Stabilized Causal Kernel: scoped fast paths require coverage/stability evidence, `rho(M_delta)` is insufficient without finite-horizon transient gain, and exact state anchors compressed projections. The newer G9 run was IN_PROGRESS at H3 start and named `EPOCH-G9 — Epoched Projection, Orchestration & Causal-Handoff Kernel`; queued/provider artifacts were treated as fresh incomplete context, not completed evidence.

### ClayGraph — mandatory deep substrate
Cycle 4 G1d is a HOLD candidate, not an accepted migration. It introduces immutable semantic graph epochs, adaptive base+delta compaction, sparse latent activation, and Assemblies pinned to graph/activation epochs and CognitiveFrame. Its 30k-node proxy found no tested query mismatches and a workload-dependent overlay/rebuild crossover: at 10% node changes overlay publication was initially cheaper but rebuild amortized after ~974 later queries; at 20% changes rebuild was already cheaper at publication. Lazy touched-node activation had median 0.028 ms versus 1.098 ms for eager dense decay in that proxy. These are implementation proxies only.

### FRANK
Cycle 4 adds `CognitiveFrame`: a workspace can be chronologically fresh yet causally inconsistent if its contributing channels were sampled from incompatible logical moments. `frame_id`, basis root, per-channel revisions, causal parents and dependency-closure state therefore become part of the basis of any workspace episode.

### ClayCode
CC8/OTCC shows that dependency closure is not only existing object IDs: predicates, absent sets, cross-object invariants, temporal/environment values and workspace/regime state can be dependencies. Trusted static envelopes may be narrowed by completely observed runtime traces but never silently widened by model output.

### GWT
Run 3 separates `gate_event` from scientific ignition and separates `transport -> projection -> uptake -> effect`. For H3, latent ClayGraph activation is therefore upstream candidate-generation state, not evidence of ignition or global uptake.

### Emergenz
No newer dedicated completed emergence run was found. The current method boundary remains the Emergence Certificate: prospective recurrence/prediction, lesion, rescue, OOD stability, multiscale/synergistic causal contribution, independent evaluation and cost/robustness shadows. H3 makes no emergence claim.

### Hyperposition prior
H2's S/C/P separation, signed deltas, relation-instance ABI, scope-soundness tripwire and incremental/rebuild crossover remain. H3 changes the object of optimization from a static topology to a family of **epoch-addressed compiled topologies**.

## 2. Fusion 1 — new uncertainty frontier

H3 generated falsifiable questions around six boundaries:

1. Can stale activation create false causal support after semantic revocation?
2. Does pairwise expansion become especially dangerous when used as an activation substrate?
3. Can rematerialization policy learn workload-dependent read/write crossover rather than use a fixed threshold?
4. Does unbounded higher-order diffusion create noise/representation collapse that adaptive inhibition can control?
5. Which state must be pinned together for deterministic replay of one cognitive Assembly?
6. Can scope discovery and physical locality adapt without being confused with semantic truth or execution authority?

## 3. External research fusion

### Evolving/versioned graph systems
GraphOne uses dual versioning to decouple graph updates from analytics. TEGRA combines persistent versioned graph state with incremental computation over arbitrary windows. OSDI 2026 POEGA processes multiple snapshots concurrently and introduces adaptive state compaction for multi-version state. These systems support the feasibility of versioned graph epochs and adaptive materialization; their benchmark numbers are workload-specific and are not FRANK estimates.

### Spreading activation
`SYNAPSE` (arXiv:2601.02744) models agent memory as a dynamic graph and explicitly combines spreading activation with lateral inhibition and temporal decay. This independently supports activation as a useful retrieval mechanism. It does not establish that a persistent latent field improves FRANK or that activation is truth.

### Higher-order diffusion and oversmoothing
`From Diffusion to Reaction-Diffusion` (arXiv:2607.15773) shows theoretically that pure hypergraph diffusion contracts discriminative transverse variation and that strong multi-way mixing can intensify representation collapse. Current Hypergraph Neural Diffusion / Ricci-flow work similarly uses adaptive incidence-level diffusion or geometric regulation. Transfer: maximum spreading is not a rational Hyperposition objective; activation needs damping, inhibition, budget and stability observability.

### Provider bridge
The current GitHub runner bridge was actually used. OpenAlex and arXiv succeeded; Exa succeeded and surfaced 2026 dynamic-graph/hypergraph diffusion work; Semantic Scholar returned HTTP 429 from the shared pool; Tavily returned HTTP 403; Judge0 independently replicated the relation-activation counterexample. Native web/primary-source research covered failed web-discovery providers. No provider output was promoted merely because the provider succeeded.

## 4. Empirical work

All numeric H3 experiments are synthetic or hybrid-proxy experiments.

### EXP-HYP-H3-EPOCH-001 — activation/semantic epoch tearing

Setup: 20,000 relation instances, 100 epochs, lazy activation decay 0.92, 50 seeds/epoch, top-500 active relations, 12 random seeds. Semantic epochs revoke/replace a fraction of relations while activation persists.

Mean stale activated support without epoch validation:

| semantic change/epoch | mean stale | p95 stale |
|---:|---:|---:|
| 0.1% | 0.56% | 1.04% |
| 0.5% | 2.58% | 3.65% |
| 1% | 5.13% | 6.77% |
| 2% | 10.12% | 12.46% |
| 5% | 23.15% | 26.49% |

An epoch-validating path filtered all stale relation IDs in the constructed test, producing 0 stale support by construction, but paid the corresponding drop/rebase cost.

**Inference:** activation needs semantic-epoch witnesses or negative-delta invalidation. A timestamp alone is insufficient.

### EXP-HYP-H3-NARY-ACT-002 — pairwise activation false associations

Synthetic ternary events `(sender, recipient, asset)` were projected into pairwise edges. A query activates sender+asset and asks for recipients. Pairwise candidates are recipients independently connected to both; relation-instance candidates require both role bindings in the same event.

Across eight seeds:

| relations | pairwise precision | mean false recipients |
|---:|---:|---:|
| 3,000 | 83.41% | 0.38 |
| 6,000 | 53.53% | 1.50 |
| 12,000 | 20.59% | 5.62 |
| 24,000 | 7.29% | 20.04 |
| 40,000 | 3.80% | 47.94 |

The relation-instance role-aware lookup remained exact by construction. An independent Judge0/Python 3.8.1 replication of the 12k condition measured mean pairwise precision **0.20656** and relation-instance precision **1.0**.

**Inference:** H2's pairwise information-loss result becomes a runtime activation hazard: pairwise flattening can create false associative paths as relation density grows.

### EXP-HYP-H3-REMAT-003 — adaptive rematerialization

This simulation used the *measured ClayGraph Cycle 4 proxy timing table* as its cost surface and generated 1,500-cycle nonstationary read/write regimes across 30 seeds. The controller knew current change fraction but predicted reads-before-next-update using an EWMA (`alpha=0.15`).

Mean total modeled cost:
- always incremental: **38,352.77 ms** (`1.194x` oracle)
- always rebuild: **48,651.43 ms** (`1.515x` oracle)
- fixed 10% cutoff: **38,538.05 ms** (`1.200x` oracle)
- adaptive EWMA: **33,411.60 ms** (`1.040x` oracle)
- hindsight oracle: **32,117.47 ms**

**Inference:** read-after-update demand belongs in the rematerialization decision. A fixed changed-node fraction cannot encode the crossover.

### EXP-HYP-H3-DIFFUSION-004 — bounded activation sanity check

Constructed 6,000-node planted graph, 20 communities, 10 seeds in one community, 30 propagation steps, restart 0.15. Compare unrestricted diffusion with a top-400 activation budget.

Mean across 10 seeds:
- unrestricted: final seed-community mass **0.4543**, active nodes **6000**, entropy **7.553**;
- budgeted: seed-community mass **0.9093**, active nodes **400**, entropy **5.543**.

This deliberately favors sparsity and is **not** evidence that top-400 is optimal or that this mechanism improves cognition. It is a mechanism sanity check consistent with external oversmoothing/inhibition evidence.

## 5. HYP-RC3 architecture delta

### A. Canonical relation semantics

Canonical state retains relation-instance identity, explicit roles, bitemporal validity/transaction time, provenance, conflict/branch identity, revocation/tombstone and epistemic status. Native hyperedges are optional.

### B. Published semantic epoch

`S[e]` is an immutable validated semantic projection. New facts/revocations arrive as signed delta overlays. Publication is atomic from a reader's perspective; compaction/rebuild creates a new immutable epoch.

### C. Activation epoch

`A[a|e]` is transient relevance state computed against a particular semantic epoch. It contains decay/inhibition/saturation/budget information and is never authority or truth. Semantic retraction must either invalidate dependent activation or force rebase.

### D. TopologyBasis

Every Assembly/cognitive projection should carry at least:

```text
semantic_epoch_id
activation_epoch_id
cognitive_frame_id / basis state witnesses
op_semantics_version_or_hash
projection_semantics_version_or_hash
coverage_certificate_ref
```

The basis is more important than a global timestamp because the component epochs may advance independently.

### E. Assembly compiler

Assemblies are bounded disposable task views compiled from the basis. Reader-specific projection can materialize relation-instance + role-labelled edges even if the canonical representation is n-ary. The Groq 8B proxy already favored explicit role-labelled relation-instance projection (6/8 extracted relations vs 2/8 for raw n-ary in its final labelled test), but target 4B remains open.

### F. Adaptive rematerialization

Choose among delta propagation, partial rebuild and full rebuild from predicted amortized work:

`update_cost + expected_reads * query_tax + memory_tax + cascade_tail + recovery_risk`.

Do not use one global change-percentage threshold.

### G. Coordination and authority remain separate

The semantic epoch does not dictate synchronization. `C[e]` is compiled from invariant interference and coverage evidence. External effect authority remains a separate capability/root/nonce/invariant/receipt boundary.

### H. Physical topology remains an optimization

`P` may choose in-process SoA/ECS, shared memory, ring buffers, mmap, isolated stores or other layouts based on profile/locality/cache/recovery constraints. Physical colocation never changes semantic identity.

## 6. Negative results / corrections

- **N-HYP-H3-001:** H2's S/C/P model is insufficient without explicit epoch/basis identity for transient activation and task projections.
- **N-HYP-H3-002:** activation computed from an older semantic epoch can preserve revoked support; activation timestamp alone is not a validity proof.
- **N-HYP-H3-003:** pairwise flattening can create false associative paths, not merely lossy storage.
- **N-HYP-H3-004:** always-incremental and fixed change-percentage policies are not justified by current crossover evidence.
- **N-HYP-H3-005:** maximum/unbounded higher-order diffusion is not supported; current theory and the toy test favor controlled propagation.
- **N-HYP-H3-006:** an immutable graph epoch is not enough for causal replay unless activation epoch, CognitiveFrame and projection semantics are also identified.
- Native hypergraph storage is still not mandatory.
- Activation remains relevance, not truth.
- G1d remains HOLD; H3 does not promote it.
- Groq 8B is a proxy, not target Qwen-class 4B evidence.
- No emergence or phenomenal-consciousness claim.

## 7. Highest-information next experiments

1. **EXP-LIVE-HYPERPOSITION-EPOCH-AUDIT** — instrument actual FRANK/ClayGraph Assembly generation with `semantic_epoch + activation_epoch + CognitiveFrame`; count mixed-basis candidates and revoked-support leakage.
2. **EXP-LIVE-HYPERPOSITION-BACKEND** — equal semantics across temporal/relational log, relation-node graph and native hypergraph where available; roundtrip/revocation/query/update/crash/replay.
3. **EXP-HYP-ACTIVATION-REVOCATION** — inject truthful vs delayed vs missing negative deltas into the real sparse activation field and measure stale candidate propagation.
4. **EXP-HYP-NARY-ACTIVATION-4B** — actual target 4B: raw n-ary vs role-labelled relation-instance vs deliberately lossy pairwise projection, randomized order and matched information/token budget.
5. **EXP-HYP-REMAT-LIVE** — compare fixed incremental, fixed rebuild and adaptive amortized controller on actual current corpus under measured read/write regimes.
6. **EXP-HYP-FIELD-LESION** — matched `no-field / truthful-field / shuffled-field` next-thought experiment with identical final visible facts/order/token budget.
7. **EXP-HYP-EPOCH-CRASH** — concurrent publish/read/crash/reclamation stress and deterministic reconstruction from canonical exact history.
8. **EXP-HYP-LOCALITY-REMAP** — remap the same logical Assembly across in-process/IPC/shared-memory layouts and verify identical semantics while measuring p50/p95/p99, cache misses, contention and recovery.

## 8. ClayGraph feedback

H3 sends four explicit revisions back to ClayGraph:

1. G1d should make `TopologyBasis` first-class rather than storing only graph/activation epoch IDs independently; include CognitiveFrame and projection semantics.
2. Relation-instance identity should constrain activation propagation where higher-order role structure matters; pairwise expansion may remain a reader/index optimization only when equivalence is proven for that query.
3. Sparse latent-field implementation should expose inhibition/budget/stability metrics and negative-delta/revocation receipts, not only activation strength.
4. Compaction/rebuild policy should optimize predicted amortized cost across update size **and expected reads-before-next-update**, with a safe fallback under regime change.

These are REVISE/NEW_EXPERIMENT feedback, not a request to promote G1d. Its HOLD decision remains appropriate until live epoch/replay and memory-effect tests pass.

## 9. Promotion decision

`canonical_promotion = NOT_PERFORMED`.

H3 produces a stronger systems contract and three useful counterexamples plus one control proxy. The decisive claims remain unverified on the actual FRANK/ClayGraph runtime and target 4B. Canonical r2 remains the authority until those gates are crossed.
