# ClayCode — Topology Read-Effect / Scoped Certificate Cycle

Run: `claycode-20260810T2358p0700-chatgpt-secondary-topology-scope`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Target: `FRANK_V0_1 / F-V01-02-CLAYCODE-COMPILER-RUNTIME`  
Direct predecessor: `hyperposition-20260810T2357p0700-chatgpt-secondary-topology-scope`  
Promotion: `NONE`

## Sequential handoff consumed

The Hyperposition run identified a bounded compiler/cache validity gap: `HYPERMATH-GRF-PCIR-V1.1` carries semantic root plus state/execution/delivery generations, but does not explicitly bind the particular active/coordination/physical topology planes a rewrite/cache result materially reads. The local 100,000-case discriminator showed the V1.1-like key can stale-reuse under intentionally same-generation non-semantic topology mutation, while binding all four planes to every read over-invalidates.

The Hyperposition handoff explicitly required a compiler-visible proof obligation and prohibited changing truth/effect authority.

## Current ClayCode constraints preserved

This run also consumes the fresh exact-current WP03/WP04 adjudication:

- executable-selected V18 remains frozen;
- current Frank procedural source has a separate `FRANK_STRUCTURED_V1` frontend candidate rather than silently widening V18;
- constructor-spelling compatibility and WP03/WP04 semantics remain independently open;
- unresolved external calls/effects remain fail-closed;
- no package PASS may inherit from adjacent successful diagnostics.

Therefore the topology-scope change is implemented only as an additive TypedIR/type-effect/compiler candidate.

## Candidate

`CC-TOPOLOGY-READ-EFFECT-V1` introduces:

- `TopologyPlane = SEMANTIC|ACTIVE|COORDINATION|PHYSICAL`;
- `TopologyReadEffect` with plane set, material reads, closure class and evidence;
- `CompiledTopologyScope` carrying plane fingerprints plus existing state/execution/delivery generations, compiler/law/provenance identity;
- static/observed dependency closure check;
- conservative all-plane binding for unresolved dynamic reads;
- fail-closed rejection of hidden topology reads;
- semantic hash normalization for typed set semantics;
- distinct provenance-sensitive contract hash;
- no speculative cross-alternative execution for external/security-sensitive/unknown effects.

No source syntax or V18 grammar change was made.

## Executable artifact

`claycode_topology_scope_checker.py` was executed locally under Python 3.13.5 / Linux x86_64.

Result: **7/7 deterministic selftests PASS**.

Verified behaviors:

1. ACTIVE-dependent certificate invalidates after active topology mutation.
2. Semantic-only certificate survives an unbound ACTIVE mutation.
3. COORDINATION-dependent certificate invalidates after coordination mutation.
4. Observed ACTIVE read absent from declared exact scope is rejected.
5. Incomplete read closure binds all four planes and cannot claim exact rewrite admissibility.
6. Typed read-set order/duplicates do not change semantic hash.
7. Raw/provenance contract differences change contract hash.

This is local mechanism evidence only. The prototype receives `observed_reads` explicitly; production dependency extraction still has to be implemented and falsified in the actual frontend -> TypedIR -> WP04 path.

## External mechanism check

Fresh primary research supports the design direction but not this implementation as truth:

- Peixoto et al. 2026 (arXiv:2602.16937) strengthens the counterhypothesis that multivariate/higher-order semantics do not require a physically native hypergraph runtime.
- Anderson et al. 2021 (arXiv:2105.06712) tracks control/data dependencies for selective change propagation in self-adjusting computation.
- DBSP (arXiv:2203.16684 / PVLDB) provides general incrementalization for rich computations.
- Egglog (arXiv:2304.04332 / PACMPL) combines incremental execution with equality-saturation rewriting.

The papers validate mechanism classes, not Clay-specific semantics, Frank target behavior or authority.

## Goodman anti-echo result

The review collapses shared Clay/Frank/Hyperposition/ClayCode ancestry and preserves four decisions:

- native n-ary physical runtime requirement: `REFINED`, not universal;
- topology-scoped invalidation: `SUPPORTED` as a bounded candidate, target relevance unresolved;
- rewrite proof without read closure: `REFINED` to require closure/topology scope;
- need to change V18 for this feature: `REFUTED_FOR_CURRENT_CANDIDATE`, preserved as a negative result.

The repository checker schema was validated locally over the validation-significant manifest/review fields with `ok=true` and zero violations. This is schema/governance validation only.

## Architecture / work delta

### F-V01-02 ClayCode

Add candidate obligations to WP03/WP04/WP06/WP11 without marking them PASS:

- WP03 TypedIR: materialize topology read effects and preserve semantic-vs-contract identity split.
- WP04 type/effect: reject undeclared reads; conservative fallback for unresolved dynamic dependency closure; preserve external-effect fence.
- WP06 lowering/runtime: include compiled topology scope in rewrite/cache identity and stale validation.
- WP11 fuzz/conformance: mutate each topology plane independently; compare current key, one coarse generation, all-plane binding and scoped binding.

### F-V01-05 Hyperposition/GWT topology

Consume compiled certificates only as validity/invalidation evidence. Topology fingerprints never become truth, semantic equivalence, GWT causal credit or effect authority.

### ClayGraph

Expose stable fingerprints for derived active/coordination/physical topology snapshots with rebuild/projection receipts. A fingerprint mismatch invalidates dependent derived work; a fingerprint match does not establish causal use.

### UnifiedDB

Persist/read certificate identity, epoch/generation, material read signature and bound plane roots in the proof-carrying receipt/cache layer. Derived topology remains rebuildable and non-authoritative.

## Hypothesis and strongest counterhypothesis

Hypothesis: compiler-visible topology read effects eliminate a class of stale rewrite/cache reuse while preserving unaffected cache hits better than universal all-plane invalidation.

Strongest counterhypothesis: real Frank already advances one existing generation for every topology mutation that can change a result. If so, a per-plane scope is unnecessary complexity.

## Exact next falsifier

On the accepted Hostinger Ubuntu target, using exact current frontend/grammar/TypedIR/compiler identities and frozen real Frank episodes:

1. implement dependency extraction in the actual structured/declarative frontend -> TypedIR chain;
2. record semantic/active/coordination/physical roots per episode;
3. independently mutate active gating, coordination lease/invariant topology and physical placement without changing semantic topology where valid;
4. compare current V1.1-like fence, a single topology-generation counter, bind-all-four and typed scoped certificates;
5. measure semantic mismatch, GWT selection/use/outcome/re-entry divergence, cache hit rate, invalidation amplification, p50/p95/p99 latency, CPU/RSS, crash/restart/replay/recovery;
6. preserve all stale reuse, false invalidation and no-benefit results;
7. promote only if scoped certificates catch real target failures or materially improve target cost/recovery without a simpler dominating mechanism.

## Final status

This ClayCode cycle produced a new executable candidate and direct Frank v0.1 test obligations. It did not alter the frozen V18 grammar, production compiler, Frank Harness, effect authority, work-package PASS state or training authorization.
