# HYPERPOSITION RESEARCH RUN — H2 Three-Topology Scoped Delta Hyperposition

**run_id:** `hyperposition-20260808T0550p0700-chatgpt-secondary`  
**trigger:** `hyperposition`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**predecessor run:** `hyperposition-20260808T0526p0700-chatgpt-secondary`  
**boundary:** no quantum-mechanical claim; no live-FRANK promotion.

## Executive synthesis

H2 changes the H1 architecture in one important way: **semantic non-monotonicity and synchronization are not the same property**.

DBSP/Feldera is direct implementation evidence that inserts, updates, deletes and even rich non-monotonic recursive computations can be represented and maintained as signed changes without providing concurrency control itself. LoRe independently shows that coordination can be selected from the interactions that actually threaten safety invariants. The resulting FRANK candidate is:

## HYP-RC2 — Three-Topology Scoped Delta Hyperposition

`canonical events/provenance`
`→ role-aware relation-instance ABI`
`→ signed/typed delta algebra`
`→ semantic dependency topology S`
`→ invariant-interference / coordination topology C`
`→ incremental projection compiler + rebuild controller`
`→ physical execution/locality topology P`
`→ scoped closure only where C requires it`
`→ external capability/effect authority`
`→ receipts + deterministic replay`

The three topologies must not be conflated:

1. **Semantic topology S** — what facts, relations, roles and derivations depend on what.
2. **Coordination topology C** — which concurrent transitions can jointly violate an invariant and therefore require a shared closure domain.
3. **Physical topology P** — which state should be colocated, shared, copied, batched or isolated given cores, cache lines, NUMA/shared memory and process boundaries.

A semantic relation can be close in S without requiring synchronous coordination in C. Two operations can be far apart in S but coupled by a uniqueness/security invariant in C. Two strongly coupled semantic records can still be physically separated in P if cache-coherence or contention costs dominate.

## Internal grounding / Fusion 1

Canonical r2 remains unchanged and still exposes `EXP-LIVE-HYPERPOSITION-BACKEND`, backend-neutral set-valued hyperposition, adaptive selective coupling and an external capability gateway.

H1 established four useful candidates:
- role-aware relation-instance identity rather than destructive pairwise flattening;
- monotonicity as a useful coordination clue;
- `R_delta` tail observability rather than a mean-only coupling metric;
- zero-copy as a boundary optimization rather than a semantic architecture.

H2 asked whether H1's monotonicity gate was too coarse. The answer from cross-domain evidence is yes: monotonicity is a sufficient route to broad coordination avoidance in CALM-like reasoning, but non-monotonicity does not imply that every such operation must globally synchronize. The actual closure requirement depends on invariant interference, execution model and authority scope.

## External research

### 1. Signed deltas are computational semantics, not concurrency policy

DBSP (`arXiv:2203.16684`) provides automatic incremental view maintenance for rich query languages including non-monotonic recursion. Current Feldera documentation describes streams of inserts, updates and deletes; internal Z-set-like changes use positive and negative weights. The same documentation explicitly states that DBSP itself provides no transactions or concurrency control.

**Transfer:** FRANK should represent change polarity (`ADD`, `RETRACT`, `REPLACE`, `COMPENSATE`) separately from the decision to coordinate.

The 2026 paper *The Role of Semirings in Incremental View Maintenance* (`arXiv:2606.07795`) further shows that update complexity depends on the algebra and query structure; there is no single universal incremental cost law.

### 2. Invariant interference determines coordination scope

LoRe (`arXiv:2304.07133`) uses static analysis/verification to identify concurrent interactions that violate application safety properties and selectively employs strong consistency only where required. The LLM-transaction work `arXiv:2412.12493` applies I-Confluence ideas to removable/compensating LLM-generated transactions and coordinates dependency-sensitive histories rather than treating every operation identically.

**Transfer:** H1's `MONOTONE_LOCAL / CAUSAL_DELTA / CONFLICT_CLOSURE` classes should be compiled from two independent axes:
- delta semantics;
- invariant-interference scope.

External effects remain a third independent authority axis.

### 3. N-ary event identity remains the portable semantic ABI

The 2025 n-ary representation taxonomy (`arXiv:2506.05626`) distinguishes role-aware from role-oblivious n-ary modelling. HyperPatch (`arXiv:2606.03179`) reports that sequential updates can fracture n-ary atomicity under ordinary binary expansion.

H2's executable test sharpens the boundary: **naive pairwise flattening** loses event identity, while **reified relation-instance nodes with explicit roles** preserve the original n-ary event exactly. Therefore the negative result targets pairwise flattening, not all graph reification.

### 4. Incremental maintenance needs a rebuild crossover

Feldera/DBSP and Differential Dataflow support update-driven maintenance, including negative changes. Yet both theory and H2's revocation benchmark show that incremental propagation is not automatically cheaper when a large fraction of the dependency structure changes.

**Transfer:** active hyperposition projections need a runtime controller that predicts whether to propagate a delta or rebuild the affected projection.

### 5. Physical locality is a third topology

Current systems evidence strengthens the distinction between semantic and physical coupling:
- OSDI'26 **SBB** removes a centralized userspace networking bottleneck and reports 1.7×–5.2× throughput gains at 48 cores under its workloads.
- OSDI'26 **Soul/GCP** moves synchronization closer to the coherence layer and reports 1–2 orders of magnitude improvement over compared locks on disaggregated memory.
- OSDI'26 **FORGE** reduces synchronization amplification with grouping and lazy synchronization, reporting up to 4.5× throughput and 7.5× lower P99 latency versus its baselines.
- OSDI'26 **DirectKV** removes KV-cache copy/buffering costs but reports up to ~1.2× end-to-end improvement, illustrating that copy elimination can be useful without dominating the whole path.
- OSDI'25 **Tigon** uses CXL atomics instead of network message exchanges for cross-host synchronization and reports large workload-specific throughput gains, while still facing CXL latency/coherence constraints.

These are different systems and are not directly comparable. The common mechanism is that **centralization, synchronization amplification and coherence traffic can dominate after serialization/copy costs are reduced**.

Practitioner ring-buffer discussions on Reddit in 2026 independently emphasize cache-line movement, batching atomics and worst-case latency. These remain anecdotal implementation evidence only.

## Empirical work

### EXP-HYP-H2-SCOPE-001 — global vs invariant-scoped closure

Synthetic queueing model: 100k operations, 64 conflict domains, 120 requests/s, mean closure service 20 ms. Only a fraction `q` of operations require non-monotone closure.

Across 10 seeds:
- `q=0.35`: global mean ~59.4 ms, global P99 ~479 ms; scoped mean ~20.7 ms, scoped P99 ~96 ms.
- `q=0.40`: global mean ~249 ms, global P99 ~2.13 s; scoped mean ~20.9 ms, scoped P99 ~97.6 ms.
- `q=0.42`: global mean ~2.93 s, global P99 ~13.22 s; scoped mean ~21.0 ms, scoped P99 ~98.2 ms.

The global lock approaches/surpasses its queue capacity while per-domain closure remains stable under this workload.

**Scope-soundness subtest:** 50k operations, 64 domains, 15% two-domain interactions, 5 ms mean service. Exact multi-domain scopes produced **0 invariant-overlap violations** across ten runs. A deliberately mis-scoped implementation locking only the first domain produced **~974 violations per 50k operations** while being slightly faster (~5.32 vs ~5.44 ms mean latency).

**Interpretation:** scoped coordination can remove artificial global bottlenecks, but a wrong conflict scope Goodharts latency while breaking correctness. Scope soundness is therefore a hard tripwire.

### EXP-HYP-H2-REVOKE-002 — incremental invalidation vs rebuild

Synthetic 50k-node clustered DAG: 100 clusters × 500 nodes, three parents per derived node, AND-style dependencies. One source was revoked in each selected cluster. Exact incremental invalidation was compared with full recomputation; both outputs were checked equal.

Representative mean speedups:
- 1 cluster touched: ~35.6× incremental advantage.
- 20 clusters: ~3.54×.
- 40 clusters: ~1.79×.
- 60 clusters: ~1.09×.
- 80 clusters: incremental ~0.71× rebuild (rebuild wins).
- 100 clusters: incremental ~0.62× rebuild.

The crossover occurs around 60–80% cluster coverage in this specific Python proxy.

**Interpretation:** `incremental` and `rebuild` are regimes, not ideologies. FRANK should predict touched scope / cascade tail and switch.

### EXP-HYP-H2-RELATION-003 — pairwise flattening vs relation-instance identity

Random ternary event set: 5,000 true relation instances over 60 values per role.

For a representative seed, the three pairwise projections joined back to **92,690 candidate triples**, of which only 5,000 were true: ~5.39% precision. Across ten seeds the mean precision was ~5.31% with very low variation. A reified relation-instance representation retaining event identity and role bindings round-tripped exactly (100% by construction).

**Interpretation:** pairwise edges are useful projections, not a safe canonical representation of general n-ary event identity.

## Fusion 2 — revised architecture

### A. Delta algebra plane

Every state change should carry explicit operation semantics:
- `ADD`
- `RETRACT`
- `REPLACE(old,new)`
- `COMPENSATE(causal_ref)`
- optionally confidence/status deltas distinct from factual deletion.

Negative deltas must preserve provenance and causal ancestry rather than silently erasing old truth.

### B. Invariant-interference topology C

Compile safety/correctness constraints into explicit interference scopes. A scope may be a single relation instance, entity, capability, resource, branch, episode, projection or higher-order set. Coordination is paid only when concurrent operations overlap a scope in a way that can violate the invariant.

This topology is itself n-ary: an invariant can couple several otherwise separate semantic regions.

### C. Semantic topology S

Keep relation-instance identity, role bindings, bitemporal context, branch/conflict identity, provenance and revocation. Pairwise edges and native hyperedges are derived/index forms.

### D. Physical topology P

Map hot projections onto in-process state, SoA/ECS layouts, shared-memory rings or zero-copy IPC only after profiling. Physical colocation must be changed when cache-line bouncing, NUMA, contention or recovery costs rise.

### E. Adaptive projection controller

For each delta, estimate:
- touched-state fraction;
- q95/q99 cascade tail;
- affected invariant scopes;
- current queue/load saturation;
- incremental work vs rebuild work;
- cache/coherence cost;
- recovery cost.

Select incremental propagation, partial rebuild or full projection rebuild dynamically.

### F. Authority remains external

No amount of semantic correctness, incremental exactness, CRDT convergence or scoped locking grants execution authority. External effects still require capability scope, root freshness, nonce/expiry, invariants, rollback and effect receipts.

## Negative results / supersessions

- **N-HYP-H2-001:** H1's monotonicity-only gate is too coarse as an architecture rule. Monotonicity remains informative, but coordination must be derived from invariant interference and authority as separate axes.
- **N-HYP-H2-002:** scoped closure without sound scope inference is unsafe; the synthetic mis-scope test preserved/improved latency while generating invariant violations.
- **N-HYP-H2-003:** incremental propagation does not always beat rebuild; H2 measured a crossover under wide revocation.
- **N-HYP-H2-004:** pairwise flattening and relation-instance reification are not equivalent. Event identity is the decisive distinction.
- **N-HYP-H2-005:** removing copies alone is not a universal latency solution; centralization, synchronization amplification and coherence can become the dominant boundary costs.
- Native hypergraph storage remains optional.
- No quantum entanglement claim.
- No live-FRANK performance claim.

## Transformed hypotheses

1. **HYP-H2-A:** replace a one-dimensional monotonicity gate with a three-axis classifier: delta semantics × invariant interference × effect authority.
2. **HYP-H2-B:** maintain separate semantic, coordination and physical topologies and allow each to reconfigure independently.
3. **HYP-H2-C:** represent coordination scopes themselves as n-ary invariant hyperedges with explicit provenance and falsifiers.
4. **HYP-H2-D:** use relation-instance identity as canonical n-ary ABI; pairwise/native-hyperedge forms are compiled indexes.
5. **HYP-H2-E:** negative deltas/revocations are first-class events, not destructive erasures.
6. **HYP-H2-F:** choose incremental propagation versus rebuild from measured impact/tail estimates.
7. **HYP-H2-G:** queue saturation of centralized closure is an overcoupling signal independent of semantic graph density.
8. **HYP-H2-H:** physical topology should react to coherence/cache-line telemetry independently of semantic relevance.

## Highest-information next experiments

1. **EXP-LIVE-HYPERPOSITION-BACKEND:** equal semantic corpus across temporal relational log, role-aware reified graph and optional native hypergraph; include revocation storms and deterministic rebuild.
2. **EXP-HYP-LIVE-SCOPE:** derive real FRANK invariant scopes from capability, uniqueness, branch and effect constraints; inject reorder/concurrency and measure violation/latency tradeoffs.
3. **EXP-HYP-LIVE-DELTA:** classify real state transitions as ADD/RETRACT/REPLACE/COMPENSATE and measure propagation/rebuild crossover.
4. **EXP-HYP-ZC-IPC:** benchmark socket/serialization vs shared-memory ring vs iceoryx2 with p50/p95/p99, CPU, cache misses, context switches and producer-death recovery.
5. **EXP-HYP-TOPOLOGY-REMAP:** dynamically remap hot assemblies across cores/processes based on contention/coherence telemetry and compare to static placement.
6. **EXP-HYP-SCOPE-FUZZ:** property/stateful fuzz the inferred coordination scopes; any invariant violation blocks selective-closure promotion.

## Tool / evidence boundary

The canonical provider registry/router were re-read. Provider-specific OpenAlex/arXiv/Tavily/Exa adapters are registered remotely but are not exposed as invokable ChatGPT connector surfaces in this session, so their direct MUST_ATTEMPT calls could not be executed here. Native web, primary literature/docs, GitHub and local sandbox were used as fallbacks and recorded in the tool manifest. E2B remains credential-unavailable in the current registry.

## Promotion decision

`canonical_promotion = NOT_PERFORMED`.

HYP-RC2 is a stronger architecture candidate than HYP-RC1 because it separates three concepts H1 partially conflated: change polarity, coordination necessity and physical sharing. The decisive transfer still requires live FRANK traces and scope-fuzzing before any canonical promotion.