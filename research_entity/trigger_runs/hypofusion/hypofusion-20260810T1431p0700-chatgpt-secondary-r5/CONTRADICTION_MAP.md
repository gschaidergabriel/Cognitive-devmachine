# Hypofusion R5 — Contradiction Map

## C1 — Targeted routing vs complete invalidation delivery

- Supporting side: dependency-aware synthetic routing reduced full-payload fanout and greatly outperformed tag-only recall.
- Contradiction: with 8% missing observed dependency edges it still missed 603 required deliveries. A later dual-view ClayGraph+UnifiedDB candidate plus reconciliation reached synthetic eventual recall 1.0, but needed 8.034 send attempts/event versus 9.0 broadcast, shrinking modeled send-attempt savings to ~10.7%.
- Resolution state: **OPEN, narrowed**.
- Current rule: targeted routing is conditional. Uncertain completeness triggers second-view reconciliation, anti-entropy, dense fallback or explicit degraded coordination.
- Discriminator: real-repo replay/fault matrix with permanent-miss, repair-latency, control/payload bytes and total-resource measurements.

## C2 — Semantic/hash equality vs release-evidence identity

- Supporting side: V18 candidate passed strict construction, 85/85 current statements and production/standalone AST byte parity in a bounded Hostinger candidate run.
- Contradiction: the exact current committed bytes were not durably replayed on the required Ubuntu lane; candidate evidence cannot be relabeled current release evidence.
- External analogue: SLSA provenance binds output digest together with build/process/input provenance.
- Resolution state: **OPEN, transformed to H-HF5-01**.
- Discriminator: exact-current-byte content-addressed Ubuntu replay plus stale/equivalent-surface canaries.

## C3 — Named reward architecture vs measured historical reward function

- Supporting side: original NAcc source defines 16 channel names despite documentation saying 9, suggesting a richer design surface.
- Contradiction: exact static search found only a narrow runtime call candidate surface for several channels and many labels with no confirmed external runtime caller; indirect/dynamic calls remain UNKNOWN.
- External analogue: recent dopamine work argues against one homogeneous scalar account, but does not validate Frank's specific channel taxonomy.
- Resolution state: **OPEN, transformed to H-HF5-02**.
- Discriminator: H1 runtime invocation/effect/reentry instrumentation before successor equivalence claims.

## C4 — Fast live reentry vs observer backaction

- Supporting side: near-live raw-event reentry can shorten stale knowledge windows.
- Contradiction: putting observer receipts/checkpoints on the authoritative SQLite writer/WAL path can change the workload being observed.
- External analogue: SQLite documents one WAL writer, checkpoint-reader interactions and `SQLITE_BUSY` paths.
- Resolution state: **OPEN, transformed to H-HF5-04**.
- Discriminator: no-observer vs same-file vs isolated observer matched tests with tail latency/retry/WAL/checkpoint and recovery metrics.

## C5 — Broker exactly-once semantics vs exactly-once external effects

- Supporting side: JetStream offers publication de-duplication and double-acknowledged consumption modes.
- Contradiction: transport acknowledgement does not independently prove that an arbitrary downstream external effect executed once, with current Clay authority and causal provenance.
- Resolution state: **CONTRACT STRENGTHENED, H-HF4-10 retained**.
- Discriminator: crash after external effect but before semantic effect receipt, then replay; duplicate effect count must remain zero.

## C6 — Stronger networking vs overcoupling

- Supporting side: live dependency routing can reduce stale isolated work and surfaced actual concurrent duplicate-lane collisions that were fused instead of completed twice.
- Contradiction: stronger coupling can amplify stale premises, false interruptions or synchronization collapse if dependency state is wrong.
- Resolution state: **OPEN FAILURE MODE**.
- Discriminator: lesion anti-entropy/dependency views independently and inject stale/false edges while measuring useful interruption, false interruption, recovery and diversity.

## C7 — Strict durable receipts vs coordination cost

- Supporting side: immediate durable causal receipts simplify audit/recovery semantics.
- Contradiction: a local candidate microbenchmark measured strict locked per-record fsync mean cost ~111.84x buffered append. A selective-sync shadow was ~2.714x faster than strict-all-receipts and replayed all modeled deltas/deliveries, but was correctly NOT_SELECTED because replay equivalence alone does not prove immediate receipt durability or power-loss safety.
- Resolution state: **OPEN, transformed to H-HF5-05**.
- Current rule: preserve strict durability until a transaction/group-commit design survives crash/torn-tail/power-loss-surrogate/effect-idempotency tests and reproduces the benefit on Ubuntu.
- Discriminator: matched strict-per-record vs transaction/group-commit Hostinger test with full resource/recovery receipts.

## Unresolved synthesis

The conflicts support neither universal broadcast nor universal targeted routing, neither scalar nor typed reward by default, neither same-file nor isolated observation by default, and neither per-record fsync nor batching by ideology. R5 converts each preference into a matched discriminator and keeps candidates rollbackable.
