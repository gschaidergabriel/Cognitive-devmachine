# Hypofusion R5 — External Evidence Ledger

Retrieved live: 2026-08-10T14:31+07:00
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol

External sources are analogues, implementation precedents, critiques or failure-mode evidence. None directly proves a Clay/Frank mechanism.

## Incremental propagation / live fusion

1. **McSherry, Murray, Isaacs, Isard — Differential dataflow (CIDR 2013), Microsoft Research**  
   URL: https://www.microsoft.com/en-us/research/?p=163907  
   Class: `PARTIAL_ANALOGUE | IMPLEMENTATION_PRECEDENT`  
   Relevance: demonstrates incremental propagation through iterative/nested computations; supports delta-oriented computation but does not establish safe branch routing under incomplete Clay dependencies.

2. **Budiu, McSherry, Ryzhyk, Tannen — DBSP: Automatic Incremental View Maintenance for Rich Query Languages**  
   URL: https://arxiv.org/abs/2203.16684  
   Class: `PARTIAL_ANALOGUE | IMPLEMENTATION_PRECEDENT`  
   Relevance: general incremental view maintenance over rich/recursive query structures; supports treating projections as incrementally maintainable derivatives, not replacing authoritative event identity.

3. **NATS JetStream documentation**  
   URLs: https://docs.nats.io/nats-concepts/jetstream ; https://docs.nats.io/using-nats/developer/develop_jetstream/model_deep_dive  
   Class: `IMPLEMENTATION_PRECEDENT | FAILURE_MODE`  
   Relevance: durable replay, filtered consumers, publication de-duplication and double acknowledgements are useful transport mechanisms. Base stream QoS is at-least-once and failure modes can produce application-observed duplicates/redelivery. Even JetStream's exactly-once transport semantics do not independently verify arbitrary downstream external effects or Clay authority.

4. **nats-io/nats-server implementation repository**  
   URL: https://github.com/nats-io/nats-server  
   Class: `INDEPENDENT_IMPLEMENTATION_EVIDENCE`  
   Relevance: confirms the candidate accelerator has an active production implementation surface; does not justify making it Clay semantic authority.

## Reentry / persistence / observer backaction

5. **SQLite — Write-Ahead Logging**  
   URL: https://www.sqlite.org/wal.html  
   Class: `AUTHORITATIVE_SPECIFICATION | FAILURE_MODE`  
   Relevance: WAL permits concurrent readers and a writer, but there is one writer; checkpoints interact with active readers and can affect latency. This makes same-file observer backaction a real empirical question rather than a purely semantic concern.

6. **SQLite — sqlite3_wal_checkpoint_v2**  
   URL: https://www.sqlite.org/c3ref/wal_checkpoint_v2.html  
   Class: `AUTHORITATIVE_SPECIFICATION | FAILURE_MODE`  
   Relevance: checkpoint modes may acquire checkpoint/writer locks and return `SQLITE_BUSY`; supports measuring writer p50/p95/p99, busy/retry rate and checkpoint latency under observer variants.

## Evidence identity / release provenance

7. **SLSA Build Provenance specification**  
   URL: https://slsa.dev/spec/v1.2-rc2/build-provenance  
   Class: `AUTHORITATIVE_SPECIFICATION | PARTIAL_ANALOGUE`  
   Relevance: output subject digest is paired with build type, external parameters and resolved dependencies. This independently supports separating byte identity from producer/build/input provenance and downstream admission policy; a digest alone is not a complete release-evidence contract.

## Reward representation / counterhypothesis search

8. **Lee et al. — A feature-specific prediction error model explains dopaminergic heterogeneity, Nature Neuroscience (2024)**  
   URL: https://www.nature.com/articles/s41593-024-01689-1  
   Class: `PARTIAL_ANALOGUE`  
   Relevance: challenges a strictly homogeneous scalar RPE account and provides an independent reason to test richer reward representations. It is not evidence that Frank's historical named NAcc channels are all useful or even active.

9. **Gershman et al. — Explaining dopamine through prediction errors and beyond, Nature Neuroscience (2024)**  
   URL: https://www.nature.com/articles/s41593-024-01705-4  
   Class: `THEORY_CRITIQUE | PARTIAL_ANALOGUE`  
   Relevance: argues the classic scalar RPE account is too simple for all observed dopamine functions while also emphasizing generalized prediction-error explanations. This supports a matched scalar-vs-typed test rather than default promotion of typed reward.

## Anti-echo adjudication

- Project commits repeating the same live-fusion or reward direction are shared Clay ancestry and **not independent replication**.
- Scholarly and standards sources above are independent of Clay but mostly test adjacent mechanisms, so they alter hypotheses and tests rather than proving Frank-specific claims.
- Current strongest external effect on R5 is to strengthen **failure-mode gates**: incomplete dependency projections, transport duplication, storage observer backaction and provenance incompleteness.
