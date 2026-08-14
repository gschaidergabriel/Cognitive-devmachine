# Hyperposition — Topology-Scoped Rewrite/Cache Validity

Run: `hyperposition-20260810T2357p0700-chatgpt-secondary-topology-scope`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Target: `FRANK_V0_1` / component `F-V01-05-GWT-HYPERPOSITION-TOPOLOGY`  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Promotion: `NONE`

## Current grounding

This run consumes the current owner-fixed one-program Frank v0.1 state, the Hyperposition readout contract, HyperMath/GRF proof-carrying IR v1.1, the accepted-target H7B anti-context-smuggling validator receipt, the new faceted-backend reduction work, current ClayCode G9 rewrite/GraphDelta semantics, ClayGraph lineage feedback, GWT causal-use distinctions and UnifiedDB proof-carrying receipt work.

The faceted-backend result already separates semantic n-ary identity from physical backend choice. This run addresses a different boundary: validity of a compiled rewrite/cache entry across changes in the four mandated topology planes.

## Observation

`HYPERMATH-GRF-PCIR-V1.1` binds semantic root, state epoch, execution generation, delivery generation and schema version in `HyperFenceKey`; its cache rule additionally binds material read signature and carrier/law version. The project separately mandates distinct semantic, active-propagation, coordination/invariant and physical-execution topologies.

A gap therefore exists unless every material active/coordination/physical topology change is guaranteed to advance one of the existing bound generations: a cached rewrite whose result depends on a non-semantic topology plane can be reused after that plane changes while its V1.1-style key remains unchanged.

## Hypothesis

`H-HP-TS-01`: make topology dependencies compiler-visible. A rewrite/read declares the topology planes it materially reads; a certificate binds exactly those plane fingerprints plus the existing generation fence. Unknown/incomplete read closure binds all four planes conservatively and cannot claim exact rewrite admissibility.

## Strongest counterhypothesis

A single existing epoch/generation may already advance on every topology change that can alter a Frank result. If verified on real traces, per-plane fingerprints add complexity without additional safety and should not be promoted.

## Executable discriminator

A deterministic local Python model generated 100,000 matched cases across six query dependency classes and mutations to the four topology planes.

Results:

- V1.1-like key: `33,368` unsafe reuses; `41,844` correct unaffected hits.
- Bind-all-four key: `0` unsafe reuses, but `41,844` unnecessary invalidations.
- Typed scoped key: `0` unsafe reuses and `0` unnecessary invalidations in the experiment model, while preserving the same `41,844` unaffected hits.

These counts are exact for the synthetic model and seed `8102355`; they are not estimates of production Frank failure rates.

## Architecture delta

Candidate `HP-TOPOLOGY-SCOPE-CERTIFICATE-V1` adds:

- `TopologyPlane = SEMANTIC|ACTIVE|COORDINATION|PHYSICAL`;
- `TopologyReadEffectV1` with declared/observed topology reads, material read set and closure status;
- `TopologyScopeCertificateV1` binding only material topology roots for exact declared reads;
- conservative all-plane binding for incomplete read closure;
- fail-closed rejection of undeclared observed topology reads;
- invalidation of dependent rewrite plans/cache handles on bound-plane changes;
- no truth or effect-authority promotion.

This is designed as a thin compiler/cache proof obligation, not a new runtime organ.

## ClayCode handoff

Do not reopen the frozen V18 surface grammar for this candidate. Implement it first as TypedIR/type-effect metadata plus deterministic validator logic:

1. infer/declare topology read effects;
2. compare observed dependency closure against declarations;
3. canonicalize read sets for semantic identity;
4. keep contract/provenance identity separate;
5. bind exact plane roots in compiled cache/rewrite certificates;
6. make incomplete closure conservative and non-exact;
7. reject stale bound-plane roots before cached result/rewrite reuse;
8. keep external/security-sensitive alternative execution disabled.

## External evidence / counterevidence

Fresh primary literature does not justify a new native hypergraph computer. Peixoto, Peel, Gross and De Domenico (arXiv:2602.16937, 2026) argue that graph models can represent multivariate/higher-order interactions, strengthening the counterhypothesis that semantic higher-order identity need not dictate a native hyperedge physical runtime. Self-adjusting computation (Anderson et al., arXiv:2105.06712) explicitly tracks control/data dependencies to propagate only affected changes. DBSP (Budiu et al., arXiv:2203.16684) provides a general incrementalization framework for rich computations. Egglog (Zhang et al., arXiv:2304.04332) combines incremental execution with equality saturation. These are independent precedents for dependency-scoped incremental invalidation/rewrite machinery, not evidence that the exact Clay candidate is already correct on Frank.

## Supported / challenged / unresolved

- Supported as local candidate: topology-scoped validity is strictly more precise than the two tested alternatives under declared-dependency truth.
- Supported by current architecture: the four topology planes are already semantically distinct and current HyperMath certificates do not explicitly carry a per-plane dependency scope.
- Challenged: native n-ary physical execution remains unnecessary by default; preserve semantics and prove lowering instead.
- Unresolved: whether real Frank has same-state-epoch mutations of active/coordination/physical topology that materially alter Hyperposition/GWT results.
- Unresolved: whether a simpler single topology-generation counter matches scoped safety at lower runtime/implementation cost.

## Required next falsifier

Use frozen real Frank v0.1 episodes and current GWT/Hyperposition readouts. Independently mutate active gating, coordination/invariant topology and physical placement while preserving semantic topology where valid. Compare:

1. current V1.1-like generation/semantic-root key;
2. one coarse topology generation;
3. four-plane bind-all;
4. typed topology-scoped certificates.

Measure semantic mismatch, GWT selection/use/outcome/re-entry divergence, cache hit rate, invalidation amplification, p50/p95/p99 latency, CPU/RSS, restart/replay behavior and recovery time. Promotion requires target-VPS evidence and a lower/equal complexity alternative must not dominate.

## Frank v0.1 re-entry

Direct impact: `F-V01-05` gains a falsifiable topology/cache safety candidate; `F-V01-02` receives an implementation obligation in TypedIR/type-effect/compiler validation. No work-package PASS, architecture promotion, effect-authority change, or training authorization is claimed.
