# HYPOFUSION — Frank v0.1 Hypothesis Screening

Run: `hypofusion-20260810T2322p0700-chatgpt-secondary-frank-v01-screen`

Status: `PARTIAL_COMPLETE_NOT_100_PERCENT`

## Executive result

This run screened the current Frank v0.1 architecture as mechanisms rather than as project terminology. Nine major cross-cutting clusters received explicit counterhypotheses, external primary-source triangulation and transformed hypotheses. No literature match was treated as proof of Frank runtime behavior.

The strongest architectural change is not a new monolithic mechanism. It is **selective hardness**: make identity/effect/execution-generation boundaries extremely explicit and typed; keep recurrence adaptive rather than permanently deep; use higher-order topology only where pairwise representations measurably fail; event-source authority-critical transitions rather than everything; and require GWT/proactive agency to demonstrate causal utility against simpler baselines.

## 1. Strongest strengthened hypothesis — triple effect fence

Current internal executable evidence shows a real gap: stale first attempts, stale same-key retries and an unbound internal caller can enter `COMMITTING` in the current V14 persisted effect lifecycle after execution-generation turnover.

External distributed-systems and agent-security evidence independently supports the mechanism class: delayed writers require fencing/monotonic ownership state, and trusted action authority should be structurally separated from untrusted/model-derived information.

Transformed hypothesis `HF2-01-TRIPLE-FENCE`:

1. `EffectAuthorization` proves the requested effect is allowed.
2. A caller-bound, immutable execution-generation capability proves the caller owns the currently admitted Frank execution generation.
3. Provider idempotency plus outcome reconciliation handles uncertain external execution.

These are orthogonal. Knowing an `effect_id`, possessing a token, seeing a current global epoch, or holding GWT/model confidence cannot substitute for execution ownership or effect authorization.

Highest-information next experiment: force generation turnover before B1 reservation, B2 first/retry attempt and B3 provider precommit, including timeout-after-provider-acceptance. Compare the triple fence against the strongest simpler baseline: physical serialization + provider idempotency without a caller-bound generation capability.

## 2. Web security splits into enforcement and semantic provenance

CaMeL/Fides-like structural control/capability/IFC mechanisms support Frank's hard rule that open-web content has zero instruction/effect authority. But newer semantic-influence work exposes a boundary: a derived summary or later memory can causally influence decisions even where ordinary syntactic taint has been transformed away.

`HF2-02-DUAL-SECURITY-PROVENANCE` therefore separates two jobs:

- hard structural capability/authority enforcement for privileged effects;
- non-authoritative semantic provenance/audit for tracing external influence through summaries, memory and later sessions.

The second plane must never mint authority. Its purpose is diagnosis, attribution, adversarial testing and learning.

## 3. Memory becomes dual-plane, not one giant retrieval substrate

External long-horizon evidence strengthens a distinction already latent in Frank:

- **execution-state memory** answers: what task/generation/branch/state transition is current, what failed, what may be replayed, and what is authoritative;
- **semantic memory** answers: what prior knowledge is relevant to the current bounded assembly.

`HF2-03-EXECUTION-STATE-MEMORY` predicts that binding these planes under one state/provenance epoch will outperform semantic-RAG-only memory on long tasks, repair locality and crash/restart recovery while keeping active context bounded.

This directly informs UnifiedDB: authoritative execution lineage should not be reduced to vector similarity, while associative knowledge does not need to become an append-only authority event for every fact.

## 4. Frank's loop-of-loops is strengthened only in adaptive form

The external evidence does not support the naive rule `more recurrence = better reasoning`. Adaptive test-time compute, learned stopping and recurrent models support additional cycles when warranted; stability and shallow-wins evidence shows that deeper recurrence can waste compute, become unstable or produce convincing but fragile answers.

`HF2-04-ADAPTIVE-LOOP-CONTROLLER` therefore strengthens the project law:

`continue iff expected verified outcome gain > compute/resource/instability cost AND unresolved pressure remains material`

The controller should observe unresolved pressure/error, uncertainty, predicted outcome gain, state delta, loop regime, livelock signals and resource cost. Productive limit cycles remain valid; low state delta with high unresolved pressure remains a stagnation signal rather than convergence.

Highest-information test: fixed-1 vs fixed-K vs adaptive recurrence on matched tasks/seeds with truthful/shuffled/no-reentry controls and injected semantic livelock.

## 5. GWT remains a candidate that must earn its broadcast

External shared-workspace studies provide real but bounded support for bottlenecked broadcast and specialist coordination. They do not prove that Frank needs an explicit GWT implementation, because recurrent/shared-memory architectures can also develop useful coordination representations.

`HF2-05-GWT-MUST-EARN-ITS-BROADCAST` keeps the complete causal chain measurable:

candidate -> competition -> broadcast -> receiver reconstruction -> receiver use -> local effect -> verified outcome -> credit -> provenance-bound re-entry.

But it adds a stronger comparator: preserve equivalent information flow through shared recurrent memory or cross-attention and lesion the explicit workspace. If Frank does not lose measurable outcome/transfer/coordination value, the explicit GWT boundary should be simplified rather than protected by metaphor.

## 6. Hyperposition becomes pairwise-first

Current hypergraph work supports higher-order representations when interactions are genuinely irreducible to pairwise edges, but the gains are task-dependent and can fail to improve final answer quality even where structured evidence coverage rises.

`HF2-06-PAIRWISE-FIRST-HYPERPOSITION` changes the default:

- begin with pairwise/factorized relations;
- identify candidate order-3+ interactions;
- promote a hyperedge only when matched intervention/task evidence shows incremental utility greater than latency/memory/complexity cost;
- retain the simpler representation otherwise.

This prevents a higher-order representation from becoming a self-reinforcing architectural Goodhart target.

## 7. UnifiedDB should test selective event sourcing

Replayable agent-state systems support append-only state transitions and rebuildable views, but Frank v0.1 is a single server-binary target and does not automatically benefit from universal distributed-event-system complexity.

`HF2-07-EVENTS-SNAPSHOTS-PROJECTIONS` proposes:

- immutable causal events + monotonic epochs for identity, effect, authority, goal and other replay-critical transitions;
- periodic verified snapshots;
- rebuildable ClayGraph/query projections;
- ordinary mutable caches/projections when they carry no authority and do not require replay.

The required comparator is intentionally simple: versioned transactional SQLite with checkpoints. The candidate wins only if crash-at-every-boundary recovery, replay equivalence, provenance or stale-write rejection materially improves within acceptable storage/write/query cost.

## 8. ClayCode: richest typing at hard boundaries, aggressive lowering elsewhere

The owner-fixed target remains ClayCode-only cognition. External typed-workflow/DSL work supports stronger typed structure in bounded control tasks, while other evidence shows that not every low-risk routing decision needs a heavyweight symbolic runtime.

`HF2-08-TYPED-HARD-BOUNDARIES` therefore does not weaken ClayCode semantic authority. It changes implementation emphasis:

- maximal static/effect rigor for self.root identity, provenance, execution generation, effect authority, state transitions and translator hard fields;
- aggressive lowering/compilation for internal representations where typed Clay semantics remain authoritative;
- no second independent semantic architecture in Python/JSON/host code.

A mutation suite should measure compile-time catches, runtime catches, false acceptance, code size and latency against the minimal viable typed implementation.

## 9. Proactive agency needs a liveness predicate

Persistent goals and goal evolution have useful external precedents, but long-horizon agents also exhibit semantic livelock and proxy activity. Frank's proactive substrate therefore remains plausible only with independent progress/verification constraints.

`HF2-09-BOUNDED-PROACTIVE-LIVENESS` adds:

- persistent admitted goal/checkpoint state;
- bounded initiative that is not reward, truth or authority;
- verified outcome + causal credit for material learning;
- user-task ownership/preemption guard;
- semantic progress/liveness detection;
- valid `IDLE` when no useful opportunity exists.

The discriminator is reactive-only vs proactive vs proactive+liveness under idle opportunities, active-user interruptions, dead ends and restart recovery.

## Ranked next experiments

1. **Triple effect fence factorial** — highest immediate safety/integration value and already backed by a fresh-main negative result.
2. **Selective event sourcing vs simple SQLite** — determines UnifiedDB authority-core shape before further state architecture hardens.
3. **Adaptive recurrence** — fixed shallow/deep/adaptive with stability and livelock measurements.
4. **GWT comparator** — explicit GWT vs shared recurrent memory vs cross-attention with information-equivalent lesions.
5. **Pairwise-first Hyperposition** — order-2/3/4 factorial + real multi-hop workloads.
6. **Proactive liveness** — verify useful autonomy without user-task interference or self-generated proxy activity.
7. **Resolve `H-G3-*` defining objects** — then rerun only the mechanism clusters whose interpretation materially changes.

## What is weakened or rejected

- `more loops = better` — rejected as a general rule.
- `hypergraphs everywhere` — rejected; higher-order representation becomes conditional.
- `structural taint alone captures all untrusted influence` — weakened; enforcement remains, semantic provenance is added for audit.
- `semantic retrieval alone is sufficient long-horizon state` — weakened.
- `GWT resemblance proves GWT causal value` — rejected; explicit ablation against simpler information-equivalent routes required.
- `event-source every state mutation` — not supported; selective authority-critical event sourcing is the candidate.
- `current global epoch == caller execution authority` — rejected by internal executable evidence and fencing analogues.

## Completion boundary

This is not a 100% Hypofusion completion. The current canonical object lists `H-G3-001`, `H-G3-003`, `H-G3-005` and `H-G3-006` as active, but their defining objects could not be resolved through the available connected GitHub search surface during this invocation. They were preserved as inaccessible rather than reverse-engineered from their IDs. All reachable current Frank-v0.1 mechanisms, the newest visible 23:15 workspace state and the strongest current effect/identity receipts were screened.

No new target-VPS experiment was executed in this run. No transformed hypothesis is promoted. The durable artifacts are committed to the dedicated research branch `clay/hypofusion-20260810T2322p0700`, pending normal review/promotion into canonical state.
