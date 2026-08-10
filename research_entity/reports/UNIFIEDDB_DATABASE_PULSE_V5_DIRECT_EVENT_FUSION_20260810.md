# UnifiedDB Database Pulse V5 — direct-event fusion delta

Date: 2026-08-10
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol
Research entity: Clay (`frank-project-global-research-entity`)
Research subject: Frank v0.1
Status: CANDIDATE / TESTING, NOT PROMOTED
Current implementation branch: `chatgpt/unifieddb-pulse-v5-direct-event-plane-20260810`
Current PR: #136

## Question

What should an endogenous UnifiedDB-backed Frank Database Pulse be if it must be continuous,
bounded, replayable, restartable, causally useful, zero-model capable, compatible with adaptive
rank compilation, and unable to mutate semantic truth merely by bookkeeping its own heartbeat?

## Internal evidence fused

1. `FRANK_DATABASE_PULSE_CONTRACT.md` defines Pulse as a persistent endogenous state/cognition
   cycle, explicitly distinct from LLM inference. Zero-model Pulses, pause/resume/restart,
   deterministic receipts, fail-closed integrity, bounded resources, and separated observables are
   hard requirements.
2. Database Pulse v1 demonstrated the cognitive control surface: scheduler, rank selection,
   re-entry controls, optional UNKNOWN model context and fail-closed integrity. It also exposed a
   differential defect: every endogenous Pulse wrote `pulse:latest` / `pulse:metrics` through the
   semantic StateLedger, advancing the semantic epoch and invalidating unrelated prepared query
   receipts even when no external semantic fact changed.
3. The v1 narrow-prelimit falsifier demonstrated bounded lexical starvation: a late
   high-salience `memory:zzzz-critical` row could be excluded before salience ranking.
4. U12 demonstrated a useful separate execution-state plane with Pulse/entity epoch, state hash,
   receipts, checkpoints, pause/recovery and atomic last-known-good semantics.
5. ActiveFieldV2 repaired starvation by materializing salience before the candidate budget, but
   created a second rebuildable candidate table.
6. AuthoritativeRankIndexV3 and AdaptiveAuthoritativeRankPathV4 produced a simpler alternative:
   rank directly over authoritative StateLedger rows, optionally compiling a physical expression
   index only when measured economics justify it. No second semantic candidate table is needed.
7. The current integration fusion on main independently concludes that StateLedger events already
   form the authoritative source change stream. A mandatory second StateLedger->Pulse delta log
   adds synchronization/recovery surface.
8. Authenticated focus-use guards provide a local causal-use integrity boundary while explicitly
   not claiming full-database integrity; periodic/full root audits remain separate obligations.

## Fresh external knowledge refresh

The external refresh was used as architecture evidence, not truth authority over local runtime:

- DBSP / incremental view-maintenance work supports delta-driven maintenance instead of repeated
  full recomputation when inputs change incrementally.
- Differential Dataflow / Naiad literature supports explicit logical progress/frontiers and
  reusable indexed arrangements for incremental computation.
- SQLite official documentation confirms expression indexes are physical query accelerators and
  WAL/transaction machinery provides crash-recovery semantics; this supports keeping physical
  acceleration separate from semantic truth.
- Event-sourcing literature and current engineering guidance reinforce preserving the admitted
  event/transaction as the replay/provenance unit rather than fragmenting one semantic commit into
  unrelated acknowledgement units.

Inference used here: these sources make a direct authoritative event stream + derived/rebuildable
physical acceleration a stronger default than a second mandatory semantic/change-stream copy. The
local differential tests remain decisive for Frank.

## Hypotheses and strongest counterhypotheses

### H1 — separate Pulse execution clock

Hypothesis: endogenous Pulse bookkeeping must advance a dedicated execution/entity clock, not the
canonical semantic StateLedger epoch.

Counterhypothesis: Pulse state is semantically meaningful and therefore belongs in canonical
StateLedger.

Discriminator: prepare an unrelated UnifiedDB QueryReceipt, run an otherwise idle Pulse, then
attempt assembly. V1/V4 semantic Pulse is expected to stale the receipt; V5 must preserve it while
still incrementing the Pulse count and producing a receipt/checkpoint.

Current decision: V5 candidate. Pulse outputs may later re-enter semantic StateLedger only through
an explicit admitted semantic delta, not because time passed.

### H2 — direct StateLedger event stream

Hypothesis: StateLedger events should be consumed directly as the Pulse source change stream.

Counterhypothesis: duplicating every StateLedger change into `frank_database_pulse_delta_queue`
provides enough recovery/isolation benefit to justify a second log.

Discriminator: crash/restart, migration, write amplification, duplicate/lost-event tests and
source-epoch coherence under large bursts.

Current decision: V5 does not populate the U12 delta queue for StateLedger changes. Legacy or
non-StateLedger queue entries remain an explicit migration boundary and block direct-event mode
until drained.

### H3 — event-atomic acknowledgement

Hypothesis: one admitted StateLedger event is one source acknowledgement unit regardless of its op
count.

Counterhypothesis: individual ops can be acknowledged independently without semantic damage.

Discriminator: one StateLedger event with 180 SET operations under a source budget of one. V5 must
consume exactly one source event, observe all 180 memory changes, advance source_epoch/hash to that
event boundary, and create zero duplicate Pulse delta rows.

Current decision: event-atomic direct cursor. Earlier per-op U12 mapping was rejected because a
bounded catch-up could otherwise split one semantic transaction while source_epoch already
advanced to the whole event epoch.

### H4 — adaptive authoritative rank path

Hypothesis: rank directly over authoritative state and compile a physical index only when measured
future-read economics justify it.

Counterhypothesis: always materialize ActiveField or always compile the rank index.

Discriminator: semantic equivalence/replay, randomized differential ranking, read horizon, compile
cost, repeated-read amortization and write amplification.

Current decision: reuse current-main AdaptiveAuthoritativeRankPathV4. Safe unmeasured fallback is
ONLINE_STATE_TOPK.

### H5 — layered integrity

Hypothesis: every selected focus ref must be authenticated at causal use; full canonical root audit
runs on first Pulse, whenever new semantic events are consumed, and periodically while idle.

Counterhypothesis: full canonical root recomputation on every Pulse is required for correctness.

Discriminator: selected-row direct SQL tamper between full audits must fail immediately at focus
use; unselected-row tamper must fail at the next scheduled full audit. Measure audit cost separately.

Current decision: V5 layered candidate. Between full audits it explicitly makes no global-integrity
claim.

## V5 implementation delta

`research_entity/runtime/database_pulse_execution_plane_v5.py` implements:

- fresh snapshot bootstrap at current authoritative event-log head;
- migration from lagging U12 source_epoch to the corresponding authoritative event boundary;
- direct event cursor in U12 `state_clay`;
- `source_epoch` plus `source_semantic_state_hash` bound to the last fully acknowledged event;
- bounded whole-event `drain_source_events()` with zero model/tool/effect calls;
- cognition gate when source-event backlog exceeds the budget;
- AdaptiveAuthoritativeRankPathV4 candidate assembly;
- AuthShadowFocusGuard before focus dereference/use;
- optional model output as UNKNOWN/context-only;
- acyclic state/receipt hash graph;
- transactional invocation registry for idempotency;
- U12 Pulse state + receipt + checkpoint in one SQLite transaction;
- fail-closed mixing rule for legacy unapplied U12 delta rows;
- no semantic StateLedger Pulse bookkeeping writes;
- no external effect authority.

## Test obligations materialized

`test_database_pulse_execution_plane_v5.py` and
`test_database_pulse_execution_plane_v5_source_boundaries.py` cover:

- snapshot bootstrap and zero duplicate delta-log rows;
- idle semantic no-churn and prepared QueryReceipt survival;
- 180-op one-event atomicity;
- 75-event bounded catch-up at exact event seq/epoch boundaries;
- partial catch-up source hash cannot claim the future root;
- lagging U12 migration;
- invocation idempotency/registry binding;
- acyclic provenance hashes;
- selected-row tamper through focus-use guard;
- unselected-row tamper through periodic full audit;
- UNKNOWN model / no effect authority;
- legacy delta backlog fail-closed.

`tools/database_pulse_v5_direct_event_benchmark.py` is a matched engineering differential against
the current semantic Pulse V4. It records distributions, semantic epoch advance, QueryReceipt
survival, storage amplification, full-integrity cost, one-big-event behavior and event-boundary
catch-up hashes.

`.github/workflows/database-pulse-v5-direct-event.yml` defines hosted Ubuntu and Hostinger
self-hosted Ubuntu lanes and re-runs inherited rank/auth falsifiers.

## Execution truth at this report write

CODE MATERIALIZED: YES.
TESTS MATERIALIZED: YES.
BENCHMARK MATERIALIZED: YES.
HOSTED/HOSTINGER EXECUTION PASS: UNKNOWN until a job step receipt is observed.
ANDREAS TARGET HARDWARE ACCEPTANCE: NOT RUN.
PROMOTION: BLOCKED pending real execution evidence.

Earlier workflow attempts on preceding Pulse branches showed hosted jobs failing before Step 1 and
the Hostinger lane remaining queued. Those are runner/control-plane observations, not evidence that
the Pulse code passed or failed. V5 must not inherit a fictional PASS from those attempts.

## Exactly measured next falsifiers

1. Execute V5 unit/adversarial suite on hosted Ubuntu and Hostinger Ubuntu; capture Python/SQLite,
   kernel, CPU, memory and runner metadata.
2. Run matched V4-vs-V5 benchmark at 100 / 1,000 / 10,000 rows with raw per-run latency rows,
   p50/p90/p95/p99, storage pages/bytes and full-integrity cost separated.
3. Add a true concurrent two-writer invocation-id stress test; sequential idempotency is already
   covered, concurrency-safe schema/transaction logic is implemented but not yet independently
   executed under racing processes.
4. Crash at every V5 transaction boundary and prove state/receipt/checkpoint/invocation registry
   remain coherent after restart.
5. Long-run idle Pulse test for receipt/checkpoint amplification, VACUUM/WAL behavior and periodic
   full-audit scheduling.
6. Compare ONLINE_STATE_TOPK vs COMPILED_INDEX_TOPK on measured target-like read/write horizons;
   compile only when current-main break-even policy is supported by live measurements.
7. Re-run on Andreas' actual Ubuntu target system before any v0.1 release gate.

## Architecture delta

Status: TESTING.
Affected components: UnifiedDB, Database Pulse, StateLedger event stream, U12 Pulse state plane,
rank path, authenticated focus-use boundary, recovery/checkpointing.
Rollback: current main semantic Pulse V4 remains the last separate candidate; PR #136 is not
promoted automatically.
Negative results preserved: semantic self-churn, lexical pre-limit starvation, per-op source epoch
splitting, duplicate StateLedger->Pulse change-stream surface, cyclic state/receipt hash dependency.

No final claim of superiority is made without the pending execution receipts.
