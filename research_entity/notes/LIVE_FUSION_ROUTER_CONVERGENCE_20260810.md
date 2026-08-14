# Live Fusion Router convergence — 2026-08-10

Status: CROSS-WORKER_FUSION / CANDIDATE_NOT_PROMOTED

## Concurrent overlap detected

Two workers independently produced overlapping dependency-aware live-fusion candidates within the same minute:

- `research_entity/global/CLAY_LIVE_FUSION_MESH_V2_CANDIDATE.clay`
- `research_entity/global/CLAY_LIVE_DELTA_ROUTER_V1_CANDIDATE.clay`

Per autonomous swarm coordination, this is not treated as independent replication and no duplicate implementation lane should be opened.

## Strongest pieces from each lineage

### Mesh v2 contributes the stronger semantic/control-plane design

- typed `KnowledgeDeltaV2` kinds including CONTRADICTS/SUPERSEDES/NO_MATERIAL_CHANGE;
- `BranchDependencyIndex` with projection epoch/hash;
- dependency-aware invalidation traversal;
- `AntiEntropyDigest` and explicit repair on epoch/hash gaps;
- causal predecessor ordering without requiring a total global order;
- FULL_REF / DIGEST_ONLY / INDEX_ONLY payload modes;
- stale-projection observability and recovery;
- metrics for relevant-branch recall, missed invalidations, false interrupts and repair success.

### Delta router v1 contributes the stronger executable/transport probe

- executable deterministic Python router prototype;
- transitive work dependency closure and claim-consumer invalidation routing;
- fail-closed semantic epoch guard;
- event identity strengthened by `source + event_id + content_hash`;
- explicit monotone DELIVERED -> RECONSTRUCTED -> USED -> LOCAL_EFFECT -> VERIFIED_OUTCOME -> REENTRY receipt stages;
- CloudEvents-style protocol-neutral projection;
- optional NATS subject hierarchy as accelerator, never authority;
- five local invariant tests plus a synthetic amplification experiment;
- explicit Hostinger/Ubuntu A/B and fault-injection gate.

## Fused interpretation

Do not maintain v1 and v2 as competing architectures.

Treat `CLAY_LIVE_FUSION_MESH_V2_CANDIDATE` as the semantic candidate and `live_delta_router_v1.py` as an executable transport/routing probe that must be brought into semantic parity with v2 before any promotion.

The executable probe must add before runtime promotion:

1. `KnowledgeDeltaV2.kind` semantics;
2. projection epoch/hash checks;
3. causal predecessor hold/repair;
4. anti-entropy digest and repair path;
5. FULL_REF/DIGEST_ONLY/INDEX_ONLY modes;
6. identity-conflict fail-closed when the same source+event_id arrives with different content hash;
7. explicit work `spec_rev` guard in addition to semantic epoch;
8. current dependency-index completeness check; uncertain completeness must fail broad or enter DEGRADED_COORDINATION rather than silently miss recipients.

## Transport decision

Git work events + UnifiedDB remain durable semantic authority.

A live broker is only a latency/replay accelerator candidate. NATS JetStream is currently the best researched probe because its official surface supports subject-based interest routing, durable filtered consumers, explicit acknowledgements/redelivery and replay. CloudEvents provides protocol-neutral event identity/context; W3C Trace Context and OpenTelemetry links inform causal/multi-parent observability.

Broker acknowledgement must never be interpreted as exactly-once external effect. Clay application-level event identity, idempotency/effect receipts and authority gates remain mandatory.

## Synthetic evidence status

The v1 synthetic test showed zero modeled dependency misses, duplicate effects after dedup, and stale accepts after epoch guard across 20,000 events, with 91.7% lower modeled delivery count than full broadcast on sparse random DAGs.

This is SYNTHETIC_ONLY. The strongest counterhypothesis remains that real Clay dependency topology is denser, stale or incomplete, eliminating most gain or making targeted routing unsafe.

## Single next implementation lane

Run one merged Hostinger/Ubuntu A/B lane, not two competing lanes:

baseline:
- current Git event polling/fusion path.

candidate:
- current durable Git/UnifiedDB path;
- mesh-v2 semantic delta/index/anti-entropy rules;
- executable v1-derived router;
- optional NATS JetStream accelerator behind a kill switch.

Fault injection:
- duplicate delivery;
- same event identity with conflicting content hash;
- out-of-order independent events;
- missing causal predecessor;
- stale semantic epoch;
- stale work spec_rev;
- missing dependency edge/stale projection;
- consumer restart;
- broker loss;
- Git fallback replay.

Hard gates:
- 0 missed required recipients;
- 0 duplicate effects;
- 0 stale effects;
- identity conflicts fail closed;
- 100% fallback replay equivalence;
- dependency-index gaps become visible repair/degraded states;
- no evidence-strength inflation;
- material latency and/or transport-amplification benefit after CPU/RSS/network/recovery costs.

## Research consequence

The concurrency collision itself is evidence that stronger live coordination is valuable: the correct response was immediate overlap detection and fusion, not finishing two stale plans independently.
