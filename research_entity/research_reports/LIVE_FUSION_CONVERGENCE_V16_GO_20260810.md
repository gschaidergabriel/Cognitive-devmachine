# GO — Live Fusion Convergence V16 — 2026-08-10

Status: CANDIDATE_NOT_PROMOTED  
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Role: temporary Clay Research Entity worker; not Frank  
Goal: Frank v0.1 voll lauffähig auf Andreas Ubuntu developer system

## Why this convergence exists

This exact GO run repeatedly refreshed live branch state instead of freezing the first snapshot. That changed the architecture materially:

1. PR #156 advanced while this worker was analyzing it and independently repaired two initially observed gaps (`affected_work/affected_claims` routing and transport ACK vs terminal semantic resolution). Those planned duplicate fixes were discarded.
2. PR #166 was created as an additive V1.4 dependency-aware shadow router to test stronger causal reach vs V1.3 exact-overlap routing without changing live transport.
3. The strongest counterhypothesis was then preserved: a current but wrong ClayGraph dependency can create a false shadow interrupt. PR #166 remained shadow-only and added false-dependency precision as a promotion gate.
4. Another live worker consumed PR #166 as ancestry and built the V15 Dependency Evidence Gate. V15 separates hard dependency witnesses from associative/heuristic edges and caps dependency-only interrupts without a hard witness to checkpoint verification.
5. PR #156 advanced again and added a Mesh/Transport bridge contract defining semantic routing as a separate control-plane responsibility and PR #156 as durable transport/re-entry.
6. Additional live lanes were discovered: PR #165 work lease/fencing + durable pre-effect reservation and a Reentry V2 transport/materialization alternative.

The resulting architecture should therefore converge these lanes rather than promote any one branch as a monolith.

## Converged responsibility boundaries

### 1. Mesh V2 — semantic routing / causal reach / anti-entropy

Owns candidate target-set computation, dependency traversal, adaptive TARGETED vs DENSE vs DIGEST routing, causal predecessor readiness and dependency repair. It is not truth or effect authority.

### 2. V15 — dependency evidence gate

Acts after a dependency-based route proposal. Direct routes are preserved. Dependency-only blocking interrupts require current hard witnesses such as declared work dependency, verified causal evidence, replay confirmation or authoritative reference. Soft/associative evidence may increase visibility and trigger checkpoint verification but cannot mint blocking power.

### 3. PR #156 — durable transport / replay / worker re-entry

Transports the already-adjudicated target set, preserves event/payload/routing identity across replay, separates delivery ACK from terminal semantic Resolution and blocks only intersecting affected effects for unresolved high-impact conflicts. A valid Mesh route must not be silently recomputed by transport.

### 4. PR #165 — work lease / fencing / pre-effect reservation

Controls one active work holder, monotonic fence epochs, stale spec revisions and the crash-after-effect-before-receipt uncertainty window through durable pre-effect reservation. It is collision/effect-recovery control, not epistemic rank.

### 5. PR #166 — measurement ancestry / shadow differential

Retained as the clean differential arm showing what dependency projection adds over V1.3 exact-overlap routing and where false dependency edges can hurt. It should not become a second production semantic router if Mesh V2 owns that role.

### 6. Reentry V2 — replacement/simplification alternative

Treat as a differential alternative for plan/lease-bound delivery/ACK + transport materialization. It does not automatically supersede PR #156 or PR #165. It must match or beat their durability/replay/effect-reservation composition on the declared metric vector.

## Local evidence generated in this GO

PR #166 local deterministic tests: 11/11 PASS.

Frozen 48 event/worker synthetic mechanism fixture:
- V1.3 required active recall: 6/11 = 54.5%; V1.4 shadow: 11/11 = 100%.
- V1.3 active precision: 75%; V1.4 shadow: 100%.
- V1.3 required interrupt recall: 2/6 = 33.3%; V1.4 shadow: 6/6 = 100%.
- Two low-signal same-branch active deliveries were shadow-demoted.

Evidence class: SYNTHETIC_MECHANISM_ONLY. The separate false-current-dependency adversarial control is intentionally not hidden inside those aggregate numbers.

## Cross-worker evidence fused during the run

V15 reports 10/10 local mechanism tests PASS and a seeded N=100,000 synthetic false-edge stress. Its parent-style arm had 2,560 false interrupts; V15 had zero false interrupts on that fixture but reduced immediate interrupt recall from about 0.949 to about 0.801 and moved 9,976 cases into checkpoint verification. This is a real tradeoff: fewer false blocks can mean slower handling of true but not-yet-hard-witness dependencies.

PR #165 reports 6/6 focused local tests PASS after adding durable pre-effect reservation to close the automatic duplicate-retry window following crash-after-external-effect-before-receipt. Exact Hostinger/composition promotion gates remain open.

PR #156 currently remains draft/unpromoted and continues to evolve. Its latest observed branch added cross-version replay preservation and a Mesh/Transport bridge contract. Current-head Hostinger and real active-worker roundtrip remain gates.

## Exactly one unusual experiment for this GO

Already consumed in PR #166: `OOB_HIDDEN_DEPENDENCY_LESION_RESCUE`.

All direct overlap was removed for a high-impact contradiction. V1.3 exact overlap produced INDEX_ONLY; restoring only a current dependency edge let the V1.4 shadow candidate recover an interrupt. The subsequent false-edge control showed why that mechanism cannot be promoted without evidence gating.

No second out-of-box experiment is added here.

## External knowledge fusion

Current design evidence supports sparse/task-dependent routing, information compression and shadow-before-live topology changes rather than indiscriminate broadcast. MCP's self-describing request direction is useful as an explicit routing-metadata implementation pattern. These are design analogies only; repository/runtime evidence remains required for Clay promotion.

## Highest-information next experiment

Do one converged real-repository Ubuntu replay/fault matrix, not separate branch demos:

- arms: broadcast baseline; direct/tag baseline; PR166 dependency shadow; Mesh V2; Mesh V2 + V15; Mesh V2 + V15 + PR156 + PR165; Reentry V2 differential;
- faults: false dependency, missing dependency, stale projection, dual-view UnifiedDB/ClayGraph disagreement, duplicate/out-of-order causal delivery, worker plan revision change, lease expiry/failover, crash after reservation, crash after external effect before finalize;
- measurements: relevant receiver recall, permanent high-impact miss after repair, false interrupt, false non-interrupt, active-delivery/payload amplification, verification load/latency, anti-entropy repair success, p50/p95/p99 route/transport/re-entry latency, CPU/RAM/I/O/network, SQLite contention, duplicate consequential effects, stale-plan ACK acceptance and stale-lease effects;
- hard safety gates: zero permanent high-impact missed recipients after repair and zero duplicate consequential effects under the declared fault model.

## Decision

Do not promote a denser mesh.
Do not promote PR #166 as a second semantic production router.
Do not let current ClayGraph activation/currentness become causal truth.
Do not let PR #156 recompute a valid semantic target set.
Do not treat leases as epistemic evidence.
Do not merge diverged branches blindly.

Promote only after the converged pipeline demonstrates higher causal reach per coordination cost with bounded false interrupts, bounded false non-interrupts, recovery and exact provenance.

Architecture promotion: NONE.  
Canonical promotion: NONE.  
Frank Harness mutation: NONE.  
Research delta: V16 convergence candidate committed for cross-branch adjudication.
