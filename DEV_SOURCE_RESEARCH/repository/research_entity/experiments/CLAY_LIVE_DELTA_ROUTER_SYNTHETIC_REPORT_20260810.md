# Clay Live Delta Router v1 — synthetic discriminating experiment

Status: SYNTHETIC_ONLY / NOT RUNTIME EVIDENCE  
Actor: chatgpt-secondary (OpenAI GPT-5.6 Sol), temporary Clay research worker  
Time: 2026-08-10T14:21:00+07:00  
Canonical parent: revision 2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346

## Question

Can dependency-aware targeted delivery preserve invalidation coverage while avoiding full-broadcast amplification, with explicit duplicate and stale-event guards?

## Hypothesis

A semantic router that sends a delta to explicitly affected work plus the transitive dependent closure can preserve required delivery while substantially reducing delivery amplification relative to broadcasting every delta to every work item.

## Strongest counterhypothesis

The apparent gain is an artifact of sparse synthetic dependency graphs. Real Clay branch/work dependencies may be denser, stale, or incompletely materialized, making targeted routing unsafe or yielding little amplification reduction.

## Method

Pure-Python deterministic synthetic test, no external network broker and no Frank runtime mutation.

- 200 random acyclic work graphs
- 120 work nodes per graph
- max 3 direct prerequisites per node
- 100 events per graph
- 20,000 total events
- each event directly affects 1 or 2 work nodes
- invalidation delivery target = affected node(s) plus transitive dependent closure
- duplicate deliveries injected probabilistically and deduplicated by event identity
- stale epoch replay checked by fail-closed epoch guard

This experiment tests router semantics only. It does NOT establish real network latency, real project topology sparsity, NATS reliability, Git polling latency, or production benefit.

## Results

- total events: 20,000
- full-broadcast deliveries: 2,400,000
- dependency-aware deliveries: 199,199
- modeled delivery reduction: 91.7000%
- mean fanout fraction: 8.3000%
- median fanout fraction: 2.5000%
- p95 fanout fraction: 42.5000%
- dependency misses: 0
- duplicate effects after dedup guard: 0
- stale accepts after epoch guard: 0

## Interpretation

The candidate is worth a real A/B test because the algorithmic invariant held in the synthetic model and the amplification gap was large. The heavy p95 fanout tail is important: some invalidations naturally propagate widely, so the design must support deliberate broad delivery when dependency closure requires it.

No runtime promotion is justified. The next discriminating test is a matched Hostinger/Ubuntu replay against current Git-event polling using current Clay work/dependency data.

## External primary-source fusion

- CloudEvents specification: event context standardization; `source + id` identifies duplicates and `type`/`subject` support routing metadata.
- W3C Trace Context: portable trace identity/context propagation across distributed components.
- OpenTelemetry messaging semantic conventions: message processing can use span links, including batch/multiple causal inputs.
- NATS subject model: interest-based hierarchical subject routing and wildcard subscriptions.
- NATS JetStream: durable consumers, explicit acknowledgements/redelivery, server-side filtering, replay and deduplication/exactly-once mechanisms.

## Promotion gate

Candidate remains `RESEARCH_CANDIDATE_NOT_PROMOTED` until real Ubuntu/Hostinger evidence shows:
1. zero missed required recipients;
2. zero duplicate/stale effects under injected faults;
3. exact Git/UnifiedDB fallback replay equivalence;
4. materially better propagation latency and/or lower transport amplification;
5. acceptable CPU/RSS/network overhead and restart recovery.
