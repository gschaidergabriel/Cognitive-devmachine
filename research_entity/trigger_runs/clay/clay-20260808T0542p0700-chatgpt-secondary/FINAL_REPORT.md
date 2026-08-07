# CLAY FULL RESEARCH RUN — G7 Hierarchical Semantic Causal Kernel

**run_id:** `clay-20260808T0542p0700-chatgpt-secondary`  
**trigger:** `clay`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**boundary:** all G7 experiments are synthetic/analytic proxies. External sources are literature/implementation evidence. No live-FRANK, production-security, or consciousness claim is promoted.

## Executive synthesis

G7 retains the Semantic Causal Kernel but transforms four G6 mechanisms.

1. **Typed change propagation:** scalar `R_delta` is insufficient for heterogeneous dependencies. Model propagation as `M_delta[i,j] = E[consequential type-j invalidations | changed type-i state]`; use spectral radius `rho(M_delta)` as an amplification diagnostic and eigenstructure to locate dominant propagation types. `rho>1` is amplification, not emergence.
2. **Hierarchical Causal Governor:** G6's flat resource vector becomes a hierarchy: a slower semantic utility allocator plus fast safety loops for thermal state, freshness, authority, cascade risk and deadlines. The vector remains, but dimensions are coupled through constraints/shadow prices and protected by hysteresis/switching costs.
3. **Asymmetric coordination compiler:** G6 invariant-aware closure becomes pair/path-sensitive. ClayCode supplies typed read/write/effect/dependency summaries; declared invariants and authority rules compile to local, escrow/idempotent, pair-ordered or globally closed execution. Unknown invariant coverage fails closed.
4. **Multi-resolution memory:** active Clay/LLM memory should support exact hot detail, coarse summaries and on-demand exact zoom rather than binary retain/evict. Importance recurrence and future causal contribution are candidate retention signals.

The integrated candidate is the **Hierarchical Semantic Causal Kernel (HSCK-G7)**:

`canonical events/provenance -> conflict-preserving hyperposition -> typed incremental projections/M_delta -> multi-resolution active memory -> hierarchical causal governor -> receipt-defined GWT + independent latent probes -> root/dependency-bound ClayCode -> semantic proof/constraint layer -> asymmetric coordination compiler -> external capability/effect gateway -> outcome/re-entry`.

Cross-cutting principle: **resolution, coordination and compute should be paid in proportion to causal necessity.**

## Fusion 1 retained constraints

- canonical truth/history and activation remain separate lifecycles;
- hyperposition is semantic conflict/context preservation, not a mandatory physical graph product;
- GWT claims require causal episode linkage and interventions, not stage labels or self-report;
- activation/salience is not truth;
- model output/ClayCode is proposal, never execution authority;
- universal fixed coupling and universal scalar budget assumptions have failed synthetic counterexamples;
- effectfulness alone is not a sufficient coordination classifier;
- stale state-aware grammar can emit current-invalid proposals;
- pairwise information can miss higher-order causal structure;
- all prior toy/proxy results remain non-live until target replication.

## External research synthesis

### Workspace / interpretability

Gurnee et al. 2026 report a small latent `J-space` with reportability, directed modulation, internal reasoning and flexible downstream use. The 2026 Ignition Index separately operationalizes abrupt activation transitions and reports model/recurrence differences. G7 treats these as distinct functional markers. Neuronpedia is an open-source implementation surface for activations, steering, circuit/graph tooling and Jacobian Lens-style analysis. None establishes phenomenal consciousness. The research implication is a **workspace measurement vector** with selectivity, reportability, ignition, causal receipts, lesion, rescue and re-entry rather than one score.

### Distributed invariants

Invariant Confluence establishes that coordination avoidance depends on preservation of application invariants, not simply internal/external operation labels. CIDR 2026 work on Semi-Linearizability/Event Horizon adds asymmetric dependencies: operation ordering needs can be directional and pair/path-sensitive. G7 therefore replaces G6's coarse risky-class closure with a coordination compiler over declared invariants plus asymmetric dependencies.

### ClayCode semantic constraints

Decode-Time Grammars use an environment-indexed grammar `Gamma` to constrain currently valid names/APIs; ChopChop demonstrates programmable semantic constrained decoding for properties such as type safety/program equivalence. Separate 2026 work shows grammar-constrained decoding itself can be an attack surface. G7 therefore binds Gamma to root/epoch and dependency sets, but keeps capability/authority semantics outside model-controlled grammar.

### KV / active memory

SeKV proposes resolution-adaptive semantic KV with coarse summaries and zoom-in reconstruction; LazyEviction exploits recurrence in token importance; HiKV, K-VEC and ForesightKV add hierarchical, coverage-aware and future-contribution signals. These converge on a G7 hypothesis: memory should be **resolution-adaptive and temporally predictive**, not only current-attention retain/evict.

### Edge runtime

Current edge/mobile LLM work and Qualcomm GenieX support heterogeneous CPU/GPU/NPU deployment, while sustained-load studies and practitioner reports show device-, context- and thermal-dependent reversals. G7 therefore treats backend selection as an online contextual-control problem optimizing sustained useful work, latency, energy and reliability rather than peak tok/s.

### Higher-order emergence

Current PID/PEID work supports higher-order unique/synergistic causal decompositions but also documents multivariate PID inconsistencies. G7 keeps these as complementary intervention tools, never a single canonical emergence scalar.

## Empirical work

### EXP-G7-MULTITYPE-RDELTA-001
Five two-type branching systems were constructed with the same scalar average row-sum `0.8` but different matrices. `safe_uniform` had `rho=.8`, mean cascade `4.97`, P(size>=100)=`.0014`; `hidden_A/B` had `rho=1.2`, mean cascades ~816/~780 and P>=100 ~`.163/.156`; `cross_damped` had `rho=.693` and no >=100 events. Across 80 randomized matrices, correlation with tail risk was `.636` for scalar average row-sum versus `.811` for spectral radius. Synthetic support for typed `M_delta/rho`, not live FRANK proof.

### EXP-G7-HIERARCHICAL-GOV-002
Across 80 seeded six-resource nonstationary simulations: mean normalized loss scalar `.45988`, flat vector `.29379`, hierarchical `.25716`; hierarchy improved 12.47% over flat and eliminated constructed thermal violations, but switching events/step rose from `.0672` flat to `.3324` hierarchical. Conclusion: hierarchy is plausible but requires explicit chatter/switching-cost control.

### EXP-G7-PAIRWISE-CLOSURE-003
In 300k constructed ordered operation pairs with exact asymmetric dependency semantics: strict-global coordination rate `1.0`, G6 class-risk `.81510`, G7 pair-sensitive `.06281`; all had zero misses of the constructed dependency set. This demonstrates possible overcoordination reduction only when dependency/invariant specification is correct and complete.

### EXP-G7-RESOLUTION-MEMORY-004
Equal 20-unit toy memory under shifting relevance: flat detail-only accuracy `.8476`, latency `3.8078`; summary+zoom accuracy `.97765`, latency `2.2914`. Strongly assumption-dependent proxy supporting multi-resolution memory as a testable design.

### EXP-G7-RECURRENCE-MEMORY-005
On recurrence-structured synthetic importance traces: exact period recovery `.74`; future-query hit@40 current salience `.3852`, recurrence model `.7638`, oracle `.7960`. Validates recurrence-sensitive test design, not universal recurrence in real KV/state.

### EXP-G7-DEPENDENCY-GAMMA-006
5000 symbols, 120 rules, 4000 roots: dependency-scoped Gamma rebuilt only `9.58%` of rule masks, produced zero current-invalid references under an exact dependency map, and reduced modeled rebuild work by `10.23x` versus full rebuild. A deliberately stale grammar produced `47.875%` invalid references. G7 implication: root-bound **and dependency-scoped** Gamma.

### EXP-G7-WORKSPACE-VECTOR-007
Constructed causal-mechanism labels with common-cause confounding: ignition-only AUC `.6018`, mean non-intervention metrics `.7319`, intervention-weighted vector `.9385`. Measurement-design sanity check only; supports intervention-heavy workspace evaluation.

### EXP-G7-MATERIALIZATION-008
80 nonstationary query families under explicit query/update/storage/build costs: never-materialize cost `1,718,320`; always `1,049,394`; adaptive `677,615` with 3299 rebuilds. Adaptive saved `60.57%` vs never and `35.43%` vs always; rebuild churn is therefore a required shadow metric.

### EXP-G7-EDGE-CONTEXTUAL-009
Four constructed device classes x four regimes x CPU/GPU/NPU: best universal backend CPU mean utility `.6706`; context oracle `.80875`; epsilon-greedy contextual controller reached `.80294` over last 5000 samples vs oracle `.80769`. This is synthetic table evidence only, motivating physical device measurement.

## Fusion 2 / transformed model

The strongest common pattern is **adaptive semantic resolution**. The same architectural move appears in state propagation, coordination, memory, grammar and hardware routing:
- propagate only consequential typed deltas;
- coordinate only dependency/invariant-critical pairs/paths;
- keep coarse memory when exact detail is not currently worth its cost and zoom when needed;
- invalidate only Gamma masks touched by relevant state dependencies;
- materialize only query families whose reuse outweighs update/storage/rebuild cost;
- route model execution by device x thermal x memory x deadline state.

This is more precise than G6's flat vector because it places fast safety constraints below a slower semantic allocator and allows each subsystem to change resolution independently.

## Negative results / revisions

- `N-G7-001`: scalar `R_delta` is not a sufficient universal heterogeneous-propagation diagnostic.
- `N-G7-002`: a flat independent vector governor is not established as universally sufficient; hierarchy won this proxy but with substantially more switching.
- `N-G7-003`: operation-class closure is not minimally coordinating under exact asymmetric pair dependencies.
- `N-G7-004`: binary retain/evict is not established as universally sufficient under shifting relevance.
- `N-G7-005`: instantaneous salience is insufficient in the recurrence-structured memory toy.
- `N-G7-006`: all Gamma masks need not rebuild after every root change when exact dependency sets are available.
- `N-G7-007`: ignition alone was a weak discriminator in the constructed workspace-measurement toy.
- `N-G7-008`: no single backend was optimal across all constructed device/regime cells.
- `N-G7-009`: always/never materialization were both dominated by an adaptive policy under the defined nonstationary cost model.

All nine are bounded synthetic negatives, not universal empirical truths.

## Highest-information next tests

1. `EXP-LIVE-GWT-LESION`: truthful vs shuffled vs delayed vs removed re-entry on real/read-only FRANK traces with matched compute/time, downstream state hashes and task outcomes.
2. Instrument real FRANK typed invalidation transitions, estimate `M_delta`, and compare scalar `R_delta` vs `rho(M_delta)` for cascade/crossover prediction.
3. Partition/twin replay: strict-global vs G6 class-invariant vs G7 asymmetric dependency compiler, including deliberately incomplete invariant specs to verify fail-closed behavior.
4. Pinned Qwen3-4B ClayCode factorial: grammar-only, fresh Gamma, Gamma+root, dependency-scoped Gamma, semantic constraints/proofs; measure tokens, retries, latency, current-invalid and authority rejects.
5. Open-model dual-workspace cross-lesion using instrumentable latent representations plus FRANK receipt-defined episodes.
6. Physical Android sustained Qwen-class benchmark across CPU/GPU/NPU, KV modes, thermal state, energy, TTFT/tok/s and speculative-decoding acceptance.

## Promotion decision

**NOT PERFORMED.** G7 contains strong architecture-level synthetic counterexamples and current external convergence, but no live FRANK/device replication. Canonical revision/generation therefore remains unchanged.