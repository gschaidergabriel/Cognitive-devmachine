# UnifiedDB / Database Pulse — V1→V4 Iterative Build, Falsification and Fusion

Date: 2026-08-10 +07:00  
Origin actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`  
Status: `ACTIVE_RESEARCH / BUILT / TEST_LANES_QUEUED / NO_CANONICAL_PROMOTION`

## Executive synthesis

The current evidence supports a narrower and stronger interpretation of the owner-fixed
Database Pulse idea than “replace the database with a novel database engine”.

**UnifiedDB / StateLedger remains the authoritative transactional, provenance and replay
state plane. Database Pulse is an endogenous bounded state/cognition cycle above that plane.
The model-facing data path is becoming an adaptive possibility/context preprocessor whose
physical access mechanism is selected from conventional and Clay-specific primitives by
correctness, epoch coherence, evidence sufficiency and measured amortized cost.**

The current strongest direction is therefore:

```text
authoritative state/event transaction
-> endogenous Database Pulse
-> bounded correct candidate generation BEFORE budget truncation
-> coherent possibility/context assembly
-> cheapest validated read primitive
-> optional model organ as UNKNOWN candidate only
-> GWT/use/outcome/causal re-entry
-> Pulse telemetry feeds future read/build/maintenance economics
```

This cycle produced one concrete correctness bug, two successive repairs, a simpler
counterbaseline, and a further control improvement:

1. Pulse V1 had a pre-ranking truncation bug.
2. ActiveField V2 repaired it but added a second derived candidate table.
3. Authoritative RankIndex V3 expresses the same score ordering directly over canonical
   `state` with a partial SQLite expression index, eliminating that second table.
4. Adaptive Rank Path V4 preserves exactly the same correct score-before-LIMIT semantics
   even when no index exists, and admits the physical index only when Pulse lifetime plus U16
   compile economics says the cold build is amortized. Sparse history, churn shock or build
   failure stays/falls back to the correct online path.

No V3/V4 promotion is authorized until Ubuntu receipts, write-amplification/resource results,
replay/fault tests and fair matched baselines are complete.

## Source and owner-contract reconstruction

The owner-fixed `FRANK_DATABASE_PULSE_CONTRACT.md` defines Pulse as an endogenous state and
cognition cycle rather than a continuous language-model loop. It explicitly separates
`pulse_count`, `state_transition_count`, `model_call_count`, tool/effect counts, requires a
zero-model path, pause/resume/restart/replay, bounded work and fail-closed stale/corrupt
handling. Optional model inference is an organ call inside the cycle, not Frank's identity.

The current H1 StateLedger already supplies an authoritative append-only event stream plus
current state with epistemic/status classes, semantic root, trace root, replay and
transactional update semantics. That makes a second Pulse delta log unnecessary as semantic
authority.

## Iteration A — U12 transactional Pulse ingress experiment

Built:

- `research_entity/runtime/RAE_UNIFIEDDB_V12_DATABASE_PULSE.sql`
- `research_entity/runtime/database_pulse_v0.py`
- `research_entity/runtime/test_database_pulse_v0.py`
- `tools/database_pulse_benchmark.py`

This branch tested useful mechanisms:

- bounded unapplied-delta queue;
- separate Pulse/state/model/tool/effect observables;
- state/payload hashing;
- U10 possibility invalidation bridge;
- semantic-generation epoch coherence;
- one-transaction delta acknowledgement + state + receipt + checkpoint;
- injected mid-transaction rollback;
- last-known-good checkpoint recovery;
- zero-model pulse;
- crash/restart and deterministic replay.

**Fusion result:** keep this as mechanism evidence, not as a second semantic truth plane.
StateLedger events already provide the authoritative source change stream. Duplicating them
into a second mandatory delta authority would increase synchronization and recovery surface.

## Iteration B — semantic Pulse V1 and discovered correctness defect

A concurrent worker built `database_pulse_candidate_v1.py` directly on StateLedger with:

- explicit scheduler;
- bounded census and focus;
- signal score:
  `1 + .40*priority + .25*urgency + .20*salience + .15*novelty`, numeric inputs clamped 0..1;
- truthful/no-reentry/shuffled/provenance-broken controls;
- optional model candidate persisted `UNKNOWN`;
- no effect authority.

Adversarial review found a correctness defect: `UnifiedDBQueryPlane` bounded the census in
lexicographic `domain,key` order before Pulse applied salience ranking. A high-salience item
outside the first N lexical rows therefore had probability zero of entering the workspace.

`tools/database_pulse_candidate_v1_falsifier.py` materializes the counterexample:

- 180 low-salience `memory:k....` rows;
- one maximal `memory:zzzz-critical` row sorted after them;
- bounded V1 census = 64;
- wide matched control sees the critical state;
- bounded V1 can miss it.

This is not merely a performance issue. It is a candidate-selection correctness error.

## Iteration C — PulseActiveField V2

Built:

- `research_entity/runtime/database_pulse_active_field_v2.py`
- `research_entity/runtime/test_database_pulse_active_field_v2.py`
- `tools/database_pulse_active_field_benchmark.py`
- `research_entity/runtime/database_pulse_runtime_v2.py`
- `research_entity/runtime/test_database_pulse_runtime_v2.py`
- `tools/database_pulse_runtime_v2_benchmark.py`

V2 materializes salience in a rebuildable/non-authoritative projection before applying the
candidate budget. Initial build scans current StateLedger; later refreshes consume only keys
touched by new authoritative events. Differential verification compares projection state and
score against StateLedger.

Tests cover:

- the exact V1 truncation counterexample;
- single-ref incremental refresh;
- retract;
- replay determinism;
- semantic roots unchanged by projection;
- truthful re-entry reserve;
- zero-model/tool/effect path;
- optional model remains UNKNOWN;
- idempotent Pulse IDs.

Two further review results matter:

1. Receipt metadata was repaired so `candidate_universe_count`, candidate budget and actual
   truncation are explicit rather than falsely claiming `query_truncated=false`.
2. A separate worker found that V2's initial `state_transition_count=2+model_hypothesis`
   counted Pulse bookkeeping and UNKNOWN model hypotheses as substantive state transitions.
   The correct observable semantics treat those as Pulse/hypothesis bookkeeping, not admitted
   world/self semantic transition. V3 already carries `state_transition_count=0` for this path.

V2 is therefore a **known correctness repair and baseline**, not the selected final mechanism.

## Iteration D — simpler Authoritative RankIndex V3

Hypothesis:

> For this narrow deterministic scalar ranking, a normal SQLite physical index directly on
> authoritative StateLedger may preserve the V2 correctness repair with less duplicated state,
> less repair logic and atomic maintenance by the existing transaction.

Built:

- `research_entity/runtime/database_pulse_rank_index_v3.py`
- `research_entity/runtime/test_database_pulse_rank_index_v3.py`
- `tools/database_pulse_rank_index_v3_benchmark.py`
- `tools/database_pulse_rank_index_v3_randomized_falsifier.py`

A concurrent worker then fused it into:

- `research_entity/runtime/database_pulse_runtime_v3.py`
- `research_entity/runtime/test_database_pulse_runtime_v3.py`

V3 uses a **partial SQLite expression index on the authoritative `state` table**:

```text
score DESC, domain, key, semantic_hash
WHERE status='CURRENT' AND epistemic='KNOWN'
```

The exact same score expression is reused in `ORDER BY` before `LIMIT`. Boolean JSON values
are deliberately excluded from numeric scoring to match Python V1/V2 semantics; numeric
signals are clamped to 0..1. UNKNOWN/CONFLICT remain observability counts, not default KNOWN
candidates.

The index is physical/rebuildable only. Creating/dropping it does not alter StateLedger epoch,
semantic root or trace root. StateLedger writes maintain the index in the same SQLite
transaction; there is no `pulse_active_field` candidate table.

Unit falsifiers cover:

- exact V1 lexical miss repair;
- query-plan index use;
- no second ActiveField table;
- score type/clamp equivalence;
- atomic rank change after authoritative update;
- retract;
- truthful re-entry;
- malformed JSON fail-closed;
- Runtime V3 zero-model path;
- `state_transition_count=0` for bookkeeping;
- model candidate UNKNOWN/no effect;
- pause/reopen/resume;
- stale epoch;
- re-entry lesion;
- Pulse ID idempotency.

A local independent SQL micro-falsifier executed outside the repo runtime with the exact V3
expression mechanics over 1,000 randomized updates and observed zero Top-64 divergences from
a Python reference; its median raw SQLite update was roughly 0.048 ms in that local process.
This is **SQL-mechanism evidence only**, not a StateLedger benchmark and not Hostinger/Andreas
target evidence.

The durable randomized repo falsifier additionally runs multiple deterministic seeds, mixed
numeric/bool/string/scalar/missing signal values, SET/RETRACT/SUPERSEDE, differential top-k
after every transaction, then full event replay and re-verification.

## Iteration E — Adaptive Rank Path V4 removes hidden cold-build work

Adversarial review found one remaining architectural problem in V3: `select()` may call
`CREATE INDEX` on the first Pulse. Even if correct, an O(N) schema/index build is undesirable
as hidden work inside an ostensibly bounded cognition cycle.

The key observation is that the semantic repair does **not** require the physical index.
SQLite can execute the same authoritative `ORDER BY SCORE_EXPR ... LIMIT N` online without an
index. The index changes cost, not meaning.

Built:

- `research_entity/runtime/database_pulse_rank_path_v4.py`
- `research_entity/runtime/test_database_pulse_rank_path_v4.py`
- `tools/database_pulse_rank_path_v4_benchmark.py`
- `.github/workflows/database-pulse-v4-adaptive-rank-probe.yml`

V4 separates two layers:

### Semantic layer — invariant

Always rank authoritative StateLedger CURRENT/KNOWN rows with the same deterministic score
**before** the candidate limit. This remains correct with or without a physical expression
index.

### Physical layer — adaptive optimization

Reuse:

- `semantic_compile_amortization_gate_v16.py` for measured build/read/quality economics;
- `semantic_compile_horizon_estimator_v16.py` for conservative completed-Pulse read lifetime.

Policy:

- insufficient completed Pulse history -> `ONLINE`, no hidden index build;
- compiled quality worse -> `ONLINE`;
- no positive read saving -> `ONLINE`;
- conservative horizon below guarded break-even -> `ONLINE`;
- churn shock -> recent floor can cancel compile;
- horizon amortizes build -> create/use physical index;
- index build failure -> correct online fallback, not cognition failure.

Tests preserve truthful re-entry equivalence across online and compiled modes and assert the
physical route never mutates semantic StateLedger roots.

The V4 benchmark measures matched:

1. V3 forced cold index build + select;
2. V4 sparse-history online select with no build;
3. measured standalone index build and compiled read cost;
4. V4 stable-history admission using those measured economics;
5. post-admission hot reads.

No numeric V4 repository benchmark result is claimed until an execution receipt exists.

## Fusion with the broader UnifiedDB possibility-preprocessor program

Concurrent branches materially strengthen the same architecture rather than compete with it.

Current fused stack:

```text
UnifiedDB / StateLedger authoritative transaction + provenance
-> Database Pulse endogenous cycle
-> narrow scalar candidate ranking:
     V4 correct online expression sort
     OR cost-admitted V3 physical expression index
-> U12 fail-closed semantic entity resolution
-> U13 one-cycle/one-generation pin
-> U14 cheapest validated read primitive
     exact resolved key -> ordinary B-tree/index
     sufficient compiled semantic field -> STOP
     compositional route -> possibility frontier
     unresolved/gap -> resolver / bounded deepening / fallback
-> U15 typed evidence-gap control
-> U16 compile economics + Pulse lifetime estimate
-> when compiled, maintenance economics chooses full generation vs SPM-S1 only if locality pays
-> provenance-bearing ActiveAssembly/PossibilityCapsule
-> GWT/model organ
-> verified outcome / causal credit / re-entry
-> next Pulse telemetry updates horizon/locality forecasts
```

The `CLAY_POSSIBILITY_FIELD_COMPILER_FUSION_CANDIDATE` was updated independently with the same
special-case law: when ordering is an authoritative deterministic scalar expression, prefer
an index inside the authoritative state table over a second materialized candidate table if
matched tests show equal semantics and lower total cost.

The broader maintenance fusion measured SPM-S1 local copy-on-write semantic-field maintenance
as promising for locality-friendly derived fields but materially worse at bootstrap than full
generation. That branch is cost/locality gated, not universal.

This reinforces the governing design law:

> **Use the cheapest validated primitive that preserves the required semantic contract. Clay
> semantics choose and verify mechanisms; they do not require every physical mechanism to be
> novel.**

## External primary-source research integrated this cycle

Current primary/official evidence supports the mechanism class, not a Clay superiority claim:

- Timely Dataflow / differential-style systems motivate propagating changes through stateful
  iterative computations rather than recomputing the full world for every update.
- DBSP formalizes incremental view maintenance over rich queries.
- SQLite officially supports partial indexes, expression indexes, transactional isolation/WAL
  and query-planner use of indexes for ordering/searching. Expression-index matching requires
  query expressions that correspond syntactically to the indexed expression, which is why V3
  reuses one exact `SCORE_EXPR` string for CREATE INDEX and ORDER BY.
- Current industrial incremental-view systems such as Enzyme reinforce cost-based refresh
  strategy rather than unconditional materialization.

External sources do not establish Frank cognitive quality; only project tests can do that.

## Strongest counterhypotheses retained

1. **Conventional matched implementation wins.** A conventional SQLite/PostgreSQL/search/graph
   stack implementing the same epochs, epistemic gates, sufficiency stop, provenance and
   adaptive materialization may equal or beat Clay-specific mechanisms. This is a valid result.
2. **V3 write amplification dominates.** Direct expression-index maintenance may be too costly
   under real Frank churn even if read latency is excellent.
3. **V4 horizon predictor has regret.** Conservative q20/recent-floor policy may still lose to
   simple ALWAYS_ONLINE or ALWAYS_COMPILE under regime shift.
4. **SPM locality vanishes live.** Real dependency fan-out may make segmented maintenance lose.
5. **Retrieval improvement is not cognition improvement.** Better context ranking may fail to
   improve downstream answer/tool-route/calibration/token/resource outcomes.
6. **Rank score is too static.** Fixed priority/urgency/salience/novelty weights may prove
   inferior to another lesionable controller; V3/V4 optimize the current semantics, they do not
   prove those semantics ideal.
7. **Cold/portable SQLite capability differs.** JSON expression behavior, query planning and
   index cost must be verified on exact target versions/hardware.

## Fair comparison boundary

The cross-engine contract now explicitly forbids handicapping conventional databases. Any
strong UnifiedDB claim must let SQLite/PostgreSQL/graph baselines use their normal indexes,
transactions, generated/materialized structures and equivalent application-side receipts.

Current admissible claim:

> UnifiedDB/Pulse is evolving into a workload-specific semantic/context-control architecture
> that may choose conventional or Clay-derived physical mechanisms adaptively.

Current inadmissible claim:

> UnifiedDB is universally a faster/better physical database engine than normal databases.

## Execution and evidence status at report write

**Committed source/tests:** yes for U12 experiment, V1 falsifier, ActiveField/Runtime V2,
RankIndex/Runtime V3, randomized V3 falsifier, Adaptive Rank Path V4 and its benchmark/tests.

**Independent local SQL mechanics:** V3 expression ordering survived 1,000 randomized updates
in a local micro-falsifier; scope limited as described above.

**GitHub-hosted auxiliary Ubuntu:** workflows committed/triggered for V3 stack and V4; no
persisted receipt observed yet at this report timestamp. Treat as `PENDING/UNKNOWN`.

**Hostinger self-hosted Ubuntu:** V2/V3/V4 workflows committed/triggered; no persisted receipt
observed yet at this report timestamp. Treat as `PENDING/UNKNOWN`, never PASS by assumption.

**Andreas final Ubuntu target:** not executed in this cycle; release acceptance remains open.

## Promotion status

- Database Pulse owner contract: **ACTIVE ARCHITECTURAL CONTRACT**.
- V1 lexical pre-limit candidate generation: **REFUTED**.
- ActiveField V2: **SUPPORTED CORRECTNESS REPAIR / NOT PROMOTED**.
- Runtime V2 original state-transition observable: **DEFECT IDENTIFIED / SUPERSEDED IN V3**.
- RankIndex V3: **STRONG SIMPLER COUNTERBASELINE / TESTING / NOT PROMOTED**.
- Runtime V3: **BUILT / ADVERSARIAL TESTING / NOT PROMOTED**.
- Adaptive Rank Path V4: **ARCHITECTURE CANDIDATE / TESTING / NOT YET FUSED INTO RUNTIME**.
- Universal novel physical DB replacement: **REFUTED/UNSUPPORTED**.
- Adaptive possibility/context preprocessor over conventional authoritative storage: **CURRENT
  STRONGEST FUSED DIRECTION**.

## Next discriminating work

1. Consume actual V3/V4 GitHub-hosted and Hostinger receipts; fix any failure before promotion.
2. Measure V3/V4 p50/p95/p99, cold build, write amplification, RSS, WAL/file bytes and recovery.
3. Run concurrent writer/reader, crash/restart, index corruption/drop/rebuild and malformed-state
   fault matrix.
4. Run V4 policy regret against ALWAYS_ONLINE, ALWAYS_COMPILE and oracle under regime shifts.
5. Fuse V4 physical route into Runtime V3 only if it beats hidden-build V3 without semantic loss.
6. Execute the fair cross-engine SQLite/PostgreSQL lanes under matched semantics.
7. Feed real Frank Pulse read/update/invalidation telemetry into U16/SPM horizon controllers.
8. Measure downstream cognition/tool routing/calibration/context/token effects, not only retrieval.
9. Re-run on Hostinger exact Ubuntu lane and finally Andreas target Ubuntu before release claims.

## Architecture delta candidate

```text
CANDIDATE
Database Pulse candidate generation is semantic; acceleration is physical.

Invariant:
  authoritative StateLedger CURRENT/KNOWN candidates
  -> deterministic score/order before candidate LIMIT
  -> bounded focus

Physical routing:
  insufficient/short/churned horizon -> ONLINE authoritative ordered query
  sufficiently amortized stable horizon -> physical expression index
  compile failure -> ONLINE fallback

Separate higher-order semantic path:
  exact-key / semantic-field / frontier / resolver / EAP / SPM chosen by U14-U16 evidence,
  not by identity or metaphor.

No candidate/preprocessor/model output receives semantic truth or effect authority.
```

This delta should remain `TESTING` until the pending Ubuntu receipts and matched conventional
baselines are available.
