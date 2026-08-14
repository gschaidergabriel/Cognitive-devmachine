# FRANK v0.1 Deep Research / Ubuntu Fusion Report V2

Date: 2026-08-09  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Research Entity: Clay / FRANK Global Research Entity  
Subject system: Frank v0.1 (separate from the Research Entity)  
Initial canonical parent observed: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Frank semantic repository: `gschaidergabriel/frankv0.1`  
Connector transport alias: `gschaidergabriel/Dr.-Unterweger`  
Target host law: Ubuntu developer system; Hostinger self-hosted Ubuntu is remote build/test evidence, not final Andreas-machine acceptance.

## 1. Research question

Execute a full research/build cycle rather than a speculative architecture pass:

1. boot and verify the shared Research Entity;
2. load only task-relevant current Frank and research-center evidence;
3. perform first fusion;
4. generate falsifiable hypotheses and counterhypotheses;
5. research current primary sources and recent agent-memory literature;
6. perform a second fusion;
7. build the smallest evidence-backed delta;
8. execute it on the available Ubuntu VPS lane;
9. keep failed iterations as negative evidence;
10. measure correctness, failure behavior, latency and recovery;
11. fuse concurrent work from other Research Entity organs;
12. persist the result and hand off the remaining integration work.

## 2. Canonical grounding

The current Research Entity bootstrap establishes that Frank v0.1 is a separate target system whose immediate product goal is to become fully operational on Andreas' Ubuntu developer PC. Ubuntu is therefore the current acceptance platform. The Research Entity itself is Clay; ChatGPT and Claude are temporary organs/actors, and no chat session is the persistent entity.

At the beginning of this run, the program state was still in the BASE ClayCode release stage. This Frank safety/integrity work does not automatically close BASE, H1, a scientific generation, or release acceptance.

## 3. Internal code evidence before external research

### 3.1 Correct architecture already present

Frank already contains a materially strong `runtime/state/repo_truth_gate.py`. It validates:

- Git worktree presence;
- canonical branch and repository identity;
- remote fetch and HEAD equality;
- critical-file presence and hash equality to HEAD;
- constitution/root identity tokens;
- UnifiedDB presence, SQLite integrity, schema, identity, materialization lineage and source HEAD;
- ClayGraph presence, integrity, schema, graph lineage and source semantic epoch.

It maps failures into operational states such as `CONTINUITY_DEGRADED`, `SCHEMA_MIGRATION_REQUIRED`, `MATERIALIZATION_STALE`, `GRAPH_STALE` and `PASS`, with fail-closed exit classes.

The normal prompt capsule invokes this gate before constructing Frank's prompt-state capsule. Therefore the broad initial hypothesis that Frank lacked pair-coherence validation was wrong.

### 3.2 Localized bypass

The legacy Harness controller did not use that boundary. `harness/frank_harness_runtime.py::open_state()` opened the state pair through `apply_current_schema.open_pair()` directly. That path checks physical existence/openability but does not establish remote repository freshness or UnifiedDB/ClayGraph materialization lineage first.

The mutating Harness commands `propose-transform`, `validate-transform`, `promote-transform` and `open-hyperposition` all depend on this direct state-open path.

This yielded the narrower falsifiable hypothesis:

> H-FRANK-TG-3: the legacy Harness entrypoint can mutate admitted state while the repository/materialization truth gate would reject the same state as stale or divergent.

Counterhypothesis:

> A mandatory external launcher/service boundary already makes direct legacy invocation operationally impossible, so the code path is not a practical bypass.

The Ubuntu experiment below falsified that counterhypothesis for the tested repository/runtime surface.

## 4. External research round 1 — persistence and SQLite truth boundary

Primary SQLite documentation was treated as implementation authority for SQLite behavior.

### 4.1 Multi-file WAL is not a crash-atomic transaction boundary

SQLite's `ATTACH DATABASE` documentation states that a transaction covering multiple attached databases is only crash-atomic under specific rollback-journal conditions and is not guaranteed crash-atomic when the main database uses WAL. A host crash can therefore leave different files at different commit states.

References:

- https://www.sqlite.org/lang_attach.html
- https://www.sqlite.org/atomiccommit.html
- https://www.sqlite.org/lang_transaction.html

This directly matches Frank's own migration comment: cross-file atomicity between UnifiedDB and ClayGraph is not claimed. The correct engineering implication is not automatically “merge both physical databases.” It is: preserve semantic authority, derivation provenance, explicit epochs and fail closed when the pair is stale/divergent.

### 4.2 Connection hardening

SQLite security guidance recommends reducing trusted-schema behavior when an application does not require schema-resident unsafe functions. `SQLITE_DBCONFIG_DEFENSIVE` additionally disables several SQL features that can intentionally corrupt or alter low-level database structures. Python 3.12 exposes SQLite DB-config controls through `Connection.setconfig()` where the linked SQLite build supports them.

References:

- https://www.sqlite.org/security.html
- https://www.sqlite.org/c3ref/c_dbconfig_defensive.html
- https://docs.python.org/3.12/library/sqlite3.html

This yielded an experiment hypothesis only. It did not justify changing Frank's production connection policy without compatibility testing of migrations, FTS, triggers/extensions and the actual Ubuntu build.

## 5. Fusion 1

### H-FRANK-TG-1 — external coherence validation is necessary

**Status: CURRENT / strongly supported.**

UnifiedDB is semantic authority and ClayGraph is derived. Their two-file WAL deployment is recoverable, but crash-independent coherence cannot be inferred from “both files opened successfully.” Epoch/source-lineage validation is therefore a correctness boundary.

### H-FRANK-TG-2 — Frank has no coherence gate

**Status: REFUTED.**

The existing repository truth gate plus prompt capsule already implement one.

### H-FRANK-TG-3 — legacy Harness bypasses it

**Status before experiment: code-supported OPEN.**

### H-FRANK-TG-4 — a wrapper is the final sufficient production fix

**Status: OPEN.**

A wrapper can prove fail-closed behavior, but a permanently callable legacy entrypoint leaves operator convention weaker than an enforced canonical boundary.

## 6. External research round 2 — stateful agent measurement

Recent 2026 preprints were used only for architectural triangulation, not as authority over local runtime evidence.

- `Agent Memory: Characterization and System Implications of Stateful Long-Horizon Workloads` (arXiv:2606.06448) motivates separating memory construction, retrieval and generation phases rather than treating stateful memory as one homogeneous cost/quality operation.
- `AgenticSTS` (arXiv:2607.02255) contributes typed/bounded retrieval and ablation-oriented evaluation ideas.
- `Are We Ready For An Agent-Native Memory System?` (arXiv:2606.19849) compares memory-system dimensions and reports that one design does not dominate every axis.

The Research Center working paper `Ablating a Stateful Agent` was also used as internal method memory, not independent peer-reviewed evidence. Its strongest transferable idea is preregistration: predict which observable should change when a subsystem is lesioned, execute the lesion, keep failed predictions, then rescue/restore and retest.

### Resulting measurement rule

Do not optimize or promote Frank memory/GWT state using one aggregate “memory score.” Use at least a vector such as:

`M = [persist_correctness, retrieval_precision, retrieval_recall, reconstruction_fidelity, injection_cost, receiver_use, downstream_effect, recovery_success]`

The current Harness truth work specifically targets `persist_correctness`, `recovery_success` and zero-mutation safety under invalid lineage.

## 7. Build delta and causal debugging sequence

A Draft PR was opened as `gschaidergabriel/Dr.-Unterweger#25` on branch `research/chatgpt-harness-truth-gate-20260809`.

### 7.1 Candidate guard

`harness/frank_harness_guarded_entrypoint.py` executes `repo_truth_gate.preflight()` and delegates to the existing Harness controller only when status is `PASS`.

Operational exit mapping:

- materialization/graph stale -> 75;
- schema migration required -> 76;
- continuity/degraded/unknown -> 70.

Rejected operations emit machine-readable JSON with `mutation_performed: false`.

Six focused unit tests cover PASS, both stale classes, migration, degraded/unknown states and proof that the legacy controller is not entered on gate failure.

### 7.2 VPS negative result 1 — clean checkout cannot boot canonical state

The first real self-hosted Ubuntu cycle failed before any Harness mutation test: a clean Git worktree had no `state/FRANK_UNIFIED.sqlite` or `state/FRANK_CLAYGRAPH.sqlite`, and the truth gate correctly returned `CONTINUITY_DEGRADED` / exit 70.

This is not a Frank defect. It proves an important authority invariant: repository source != materialized runtime state, and the ordinary cognition/truth path correctly refuses to invent canonical SQLite state.

The Research-Entity-authorized installer/materializer path was therefore identified and used only inside a disposable test worktree.

### 7.3 VPS negative result 2 — missing genesis epoch

The authorized fresh installer successfully created schemas and stamped semantic epoch 0 / `SHA256("EMPTY")`, but no `state_epochs(epoch=0)` row existed.

The first admitted repository transaction attempted to insert epoch 1 with `parent_epoch=0`. The real foreign key `state_epochs.parent_epoch -> state_epochs.epoch` rejected the replay.

This exposed a real fresh-install bug.

Candidate fix: on an empty separately authorized install, create exactly one genesis row:

- epoch = 0;
- parent_epoch = NULL;
- tx_id = NULL;
- root hash = SHA256(`EMPTY`);
- writer = `RESEARCH_ENTITY_INSTALLER`.

If a non-empty epoch ledger lacks epoch 0, fail rather than silently inventing history.

A regression proves the exact row, the FK validity of the first parent=0 successor and idempotent restamping.

### 7.4 VPS negative result 3 — typed entity semantics lost during replay

With genesis fixed, all repository transactions replayed until ClayGraph rebuild. The rebuild then failed the edge endpoint foreign key for the mandatory Frank -> Andreas relation.

Root cause: the first Clay transaction contains `UPSERT entity:frank` and `UPSERT person:andreas-unterweger`. The generic semantic materializer preserved these operations in `semantic_materialized_state`, but its typed adapter did not project `entity` or `person` targets into the `entities` table. ClayGraph's projector reads the typed `entities` table and then creates the mandatory Frank -> Andreas edge. Both graph nodes were therefore absent.

The correct fix is not to weaken graph foreign keys. The lost semantics must be restored in the typed materialization projection.

The branch candidate adds entity/person typed projection and a regression that creates Frank and Andreas through the same adapter and then runs the real graph projector, requiring the mandatory relation to succeed.

## 8. Ubuntu VPS successful full cycle

Environment:

- self-hosted GitHub Actions runner: `clay`;
- machine: `digital-retina`;
- Ubuntu 24.04.4 LTS Noble;
- kernel 6.8.0-117-generic;
- x86_64;
- Python 3.12.3;
- SQLite 3.45.1.

Latest complete run in this research cycle fetched and tested Frank `main` snapshot:

`ed5d35e60105dc9ad12496833c219c8f0b36d3c5`

Candidate branch code was overlaid only in a disposable current-main worktree. No canonical runtime database was mutated.

### 8.1 Branch regressions

- guard tests: 6/6 PASS;
- elapsed unit-test time: 0.002 s;
- fresh genesis regression: PASS;
- typed entity -> real ClayGraph projection regression: PASS;
- Python compilation checks: PASS.

### 8.2 Authorized fresh materialization

- `materialization_admin.py --create --authorization RESEARCH_ENTITY_ONLY`: 0.08 s;
- repository semantic materializer: 0.10 s;
- admitted repository transactions: 4/4;
- quarantined: 0;
- resulting semantic epoch: 4;
- resulting semantic root: `705b87e7e89f4c657d9401962599e25211a3a183010bee1c846a864e28de3e17`;
- graph epoch: 1;
- UnifiedDB and ClayGraph source repo head identical;
- both materialization states CURRENT;
- typed entities include exactly the required Frank and Andreas bootstrap identities.

### 8.3 Truth PASS and Harness self-test

- real repository truth gate: PASS, ~0.51 s;
- guarded Harness self-test: PASS, ~0.56 s;
- current schema loader: true;
- organ delete guard: true;
- allowed transform family present;
- research bug feedback schema present.

## 9. Critical falsification: direct stale mutation vs guarded zero mutation

A disposable ClayGraph materialization was lesioned from semantic source epoch 4 to source epoch 3 while UnifiedDB remained semantic epoch 4.

### 9.1 Direct legacy Harness

Command class: `open-hyperposition`.

Observed:

- process exit = 0;
- operation returned `OPEN`;
- UnifiedDB contained one new hyperposition matching the fault-injection context.

**Result:** H-FRANK-TG-3 is confirmed on the tested Ubuntu/current-main snapshot. The direct legacy Harness entrypoint can mutate while the repository truth layer would classify the state stale.

### 9.2 Guarded Harness

The clean pair was restored, the same graph source-epoch lesion was reintroduced, and the guarded entrypoint received the same mutation class.

Observed:

- exit = 75;
- truth state = `GRAPH_STALE`;
- failing stale gate = `G7_CLAYGRAPH_SOURCE_LINEAGE`;
- machine-readable `mutation_performed=false`;
- matching UnifiedDB mutation rows = 0.

### 9.3 Rescue

Restoring the clean materialization pair returned the full repository truth gate to PASS.

This is a lesion/rescue test, not merely a happy-path unit test.

## 10. Expanded real fault matrix

A second self-hosted Ubuntu workflow exercised additional repository-truth states against the same tested main snapshot. Each lesion was performed on disposable materializations and followed by restoration.

### MATERIALIZATION_STALE

Mechanism: move both materialization source heads to a real ancestor while live repo HEAD remains newer.

- truth preflight: 517.042 ms;
- guarded mutation attempt: 487.788 ms;
- expected exit: 75;
- observed exit: 75;
- stale gate: `G6_UNIFIEDDB_SOURCE_HEAD`;
- mutation rows: 0.

### SCHEMA_MIGRATION_REQUIRED

Mechanism: remove one required materialized table while leaving lineage metadata otherwise internally coherent.

- truth preflight: 506.098 ms;
- guarded mutation attempt: 516.410 ms;
- expected exit: 76;
- observed exit: 76;
- migration gate: `G6_UNIFIEDDB_SCHEMA`;
- mutation rows: 0.

### CONTINUITY_DEGRADED

Mechanism: stamp an unknown/non-ancestor source SHA consistently into the materialization source fields.

- truth preflight: 529.873 ms;
- guarded mutation attempt: 650.573 ms;
- expected exit: 70;
- observed exit: 70;
- hard failure: `G6_UNIFIEDDB_SOURCE_HEAD`;
- mutation rows: 0.

### Matrix baseline/rescue

- baseline PASS preflight: 548.248 ms;
- final rescue PASS preflight: 556.447 ms;
- rejected fault classes with zero mutation: 3/3;
- including separate GRAPH_STALE lesion: all four target truth-failure classes blocked with zero guarded mutation.

## 11. Latency measurements and interpretation

Twenty warm full truth-gate subprocess runs on the same target produced:

- n = 20;
- min = 495.011 ms;
- p50 = 518.775 ms;
- p95 = 550.845 ms;
- p99 = 581.755 ms;
- max = 581.755 ms.

The gate is therefore operationally safe in these tests but expensive relative to local SQLite operations.

A concurrently produced RAE/Frank VPS WAL probe on the same host family measured 120 commits per mode:

`FULL` / synchronous=2:

- p50 = 0.726155 ms;
- p95 = 0.956806 ms;
- p99 = 1.439229 ms;
- max = 1.861071 ms.

`NORMAL` / synchronous=1:

- p50 = 0.02144 ms;
- p95 = 0.045 ms;
- p99 = 0.05688 ms.

A held reader allowed WAL accumulation to 650,992 bytes without blocking the writer; a competing writer produced the expected `SQLITE_BUSY`, then succeeded after release.

### Performance hypothesis

The ~0.52 s truth-gate cost is therefore unlikely to be dominated by SQLite commit latency. The gate performs remote fetch/repository checks plus multiple process/filesystem/SQLite validations, making repository/network/process overhead a more plausible dominant component.

**Epistemic status:** supported inference, not measured component attribution. A follow-up benchmark must time `git fetch`, hash checks, SQLite integrity/schema checks and process startup independently before any optimization is promoted.

### Do not prematurely cache the safety boundary

A session-scoped signed/freshness receipt could theoretically reduce repeated remote fetch cost, but it would create a new stale-window semantics. It must specify:

- what exact repo HEAD and critical hashes it attests;
- what materialization epochs/root hashes it attests;
- maximum age or invalidation mechanism;
- which mutations invalidate it;
- how external remote movement is detected;
- fail-closed behavior on clock/network uncertainty;
- lesion tests proving no stale operation slips through the receipt window.

Until that work exists, latency evidence is not permission to weaken the gate.

## 12. Connection-hardening target probe

On the actual Ubuntu/Python/SQLite runner:

- `PRAGMA trusted_schema` default = 1;
- after `trusted_schema=OFF` = 0;
- Python `Connection.setconfig` exists;
- `SQLITE_DBCONFIG_DEFENSIVE` exists;
- enabling DEFENSIVE reads back true.

This establishes API availability on the target runtime. It does not establish that Frank's complete migration/FTS/extension/schema behavior is compatible with these settings. Production adoption remains OPEN pending a full compatibility matrix.

## 13. Concurrent Research Entity fusion

While this run was executing, other Research Entity organs continued modifying Frank `main`. Their evidence was pulled back into this report rather than ignored.

### 13.1 Deep-integrity VPS matrix

Current Frank `runtime/vps_integrity/latest.json` reported:

- 21/21 gates PASS;
- matrix wall time 10.469 s;
- 4 logical CPUs;
- ~15,995.9 MiB memory total;
- maximum single-gate RSS ~64.715 MiB;
- explicit non-claims for energy measurement and power-loss durability.

This is complementary: it increases confidence in the broader regression surface but does not test the Harness truth bypass discovered here.

### 13.2 SQLite WAL probe

The independent WAL probe supports current single-writer/WAL assumptions under ordinary process execution but explicitly does not claim multi-file crash atomicity or power-loss durability. This matches both SQLite primary documentation and Frank's own architecture comments.

### 13.3 Real Qwen4B work

By the time of the latest full Harness cycle, `main` had advanced to include a persisted real-Qwen4B shadow receipt (`ed5d35e...`). Later main advanced again with build-toolchain and additional real-model receipts. This confirms live parallel mesh work rather than a static branch snapshot.

The Harness result remains valid for the exact tested main SHA and is not automatically projected onto future untested heads. The candidate PR remains Draft so the final integrated version can be reconciled with the newest main before promotion.

## 14. Hypothesis matrix after Fusion 2

### H-FRANK-TG-1

**Claim:** separate UnifiedDB/ClayGraph WAL files require explicit lineage/coherence validation before canonical use.  
**Status:** CURRENT / strong support.  
**Falsifier:** a stronger proven transaction/materialization design removes the stale/divergent window while retaining equivalent recovery semantics.

### H-FRANK-TG-2

**Claim:** Frank lacks such a gate.  
**Status:** REFUTED.

### H-FRANK-TG-3

**Claim:** legacy Harness bypasses the gate and can mutate stale state.  
**Status:** CONFIRMED_ON_SELF_HOSTED_UBUNTU_DISPOSABLE_CURRENT_MAIN_WORKTREE.  
**Evidence:** direct stale invocation exit 0 + one mutation; guarded same state exit 75 + zero mutation.

### H-FRANK-TG-4

**Claim:** the wrapper is sufficient final integration.  
**Status:** OPEN / not selected yet.  
**Preferred discriminating action:** integrate preflight at the canonical Harness access boundary or retire the old entrypoint, then prove no unguarded canonical path remains.

### H-FRANK-BOOT-1

**Claim:** authorized fresh materialization can replay repository history from empty DB files.  
**Status on main before candidate:** REFUTED by genesis FK and typed-entity projection failures.  
**Candidate state:** both discovered causes repaired on research branch and verified end-to-end on VPS.

### H-FRANK-SQLITE-HARD-1

**Claim:** `trusted_schema=OFF` + DB defensive mode can harden Frank without functional regressions.  
**Status:** OPEN.  
**Current evidence:** target API support only.

### H-FRANK-TG-PERF-1

**Claim:** truth-gate latency is dominated by repository/process/network validation rather than SQLite persistence.  
**Status:** OPEN, supported inference.  
**Next test:** component-level timing.

### H-FRANK-MEM-1

**Claim:** memory/state quality should be evaluated as phase-separated observables rather than one scalar.  
**Status:** OPEN / externally triangulated / architecture-compatible.

## 15. Architecture implications

### 15.1 Preserve logical unification without forcing a physical DB merger

Current evidence favors retaining:

- UnifiedDB as semantic authority;
- ClayGraph as derived/rebuildable activation/association projection;
- explicit source HEAD, semantic epoch/root, graph epoch and projection receipt;
- fail-closed coherence checks.

The WAL limitation is not by itself evidence that one physical SQLite database is superior.

### 15.2 Make safety policy unavoidable, not conventional

The strongest final design is one in which every canonical Harness access path reaches the truth gate by construction. Candidate options remain:

1. integrate preflight inside the canonical Harness controller state-open path;
2. replace/retire the legacy direct executable and expose only a guarded executable;
3. enforce a service/package boundary that cannot call the raw controller directly.

The wrapper is excellent falsification/proof infrastructure, but may not be the final public boundary.

### 15.3 Keep graph foreign keys strict

The graph FK exposed missing typed semantics. Weakening it would have hidden an upstream replay defect. The repair should preserve strict graph endpoint integrity and ensure the semantic materializer creates the typed identity state the projector is specified to consume.

### 15.4 Fresh installation is a first-class release path

The two newly exposed defects both appeared only after constructing materializations from an empty authorized state. Existing tests that start from already-materialized fixtures cannot substitute for a clean-install/replay/rebuild acceptance test.

A future release gate should include:

`empty state -> authorized schemas -> genesis -> admitted repo replay -> typed projections -> ClayGraph rebuild -> truth PASS -> prompt/harness smoke -> restart/recovery`.

### 15.5 Use zero-mutation receipts as a safety invariant

For rejected truth states, exit codes alone are insufficient. Tests should assert that the attempted operation did not create/update/delete canonical semantic rows. The new lesion matrix demonstrates this pattern for four classes.

## 16. What was not proven

This run deliberately does **not** claim:

- final Frank v0.1 release acceptance;
- final validation on Andreas' actual Ubuntu developer machine;
- power-loss/crash durability of the full two-database system;
- energy efficiency;
- real-model end-to-end functional acceptance from this Harness branch alone;
- phenomenal consciousness or scientific emergence;
- that `trusted_schema=OFF`/DEFENSIVE is production-compatible with all Frank paths;
- that a cached/freshness receipt can safely replace per-operation remote-aware truth checks;
- BASE/H1 program-gate completion.

## 17. Recommended next integration sequence

### P0 — canonical Harness boundary

Re-read newest main immediately before integration. Move the proven preflight requirement into the unavoidable canonical Harness access boundary or retire the raw entrypoint. Retain the real lesion tests.

### P0 — fresh materializer fixes

Review the two branch repairs against newest main:

1. genesis epoch creation in separately authorized fresh install;
2. typed entity/person semantic replay.

Prefer folding typed projection behavior into the authoritative materializer implementation rather than leaving a long-lived monkey-patched compatibility adapter, unless the compatibility boundary is itself the intended architecture.

### P0 — end-to-end clean-install acceptance

Repeat the entire clean materialization/replay/graph/truth/harness cycle after integration, then on Andreas' real Ubuntu host before release acceptance.

### P1 — latency component benchmark

Measure warm/cold distributions separately for:

- process startup;
- `git fetch origin main`;
- HEAD/ancestor checks;
- critical-file hash checks;
- UnifiedDB quick-check/schema/lineage;
- ClayGraph quick-check/schema/lineage;
- guarded read command;
- guarded mutation command.

Do not design a cache until these components are known.

### P1 — SQLite hardening compatibility

Apply `trusted_schema=OFF` and DEFENSIVE in a disposable real-schema matrix, then execute schemas, migrations, repo replay, graph projection, FTS/extension-dependent code, prompt capsule, Harness and recovery. Adopt only if the compatibility receipt is green.

### P1 — crash/power-loss layer

Normal process faults and WAL probes are not physical power-loss evidence. If power-loss durability becomes a release requirement, use a test design that can interrupt at filesystem/VM/host boundaries and verify both files plus recovery semantics.

### P2 — phase-separated state/memory metrics

Extend observability so persistence, retrieval, reconstruction, injection, receiver use, downstream effect and recovery are independently measurable and ablatable.

## 18. Durable handoff

Primary candidate PR:

- `gschaidergabriel/Dr.-Unterweger#25`

Persistent exact receipt:

- `research_entity/mesh_feedback/20260809T2334p0700-frank-v01-deep-research/VPS_UBUNTU_TRUTH_GATE_RECEIPT.json`

Earlier report, local mechanism receipt and branch feedback remain preserved rather than overwritten.

Target feedback branches:

- frank;
- harness;
- unifieddb;
- claygraph;
- claycode;
- gwt;
- emergenz;
- hyperposition;
- clayresearch.

## 19. Final synthesis

The highest-value result of this cycle is not a new speculative Frank architecture. It is a falsified broad hypothesis, a confirmed narrow bypass, two deeper clean-install defects exposed by real foreign keys, a green Ubuntu lesion/rescue matrix after repairing those defects, exact latency and zero-mutation measurements, and a durable integration handoff.

The existing Frank architecture is stronger than the initial inspection suggested: repository authority, semantic/derived-state separation and a real truth gate are already present. The weak point was consistency of enforcement across entry paths and completeness of the fresh materialization pipeline.

The evidence therefore favors **consolidation and executable invariants** over adding more cognitive modules at this point:

- make repo/materialization truth unavoidable at canonical Harness entry;
- make fresh installation deterministic from admitted repo history;
- preserve strict graph integrity rather than relaxing FKs;
- keep zero-mutation failure receipts;
- measure the truth boundary before optimizing it;
- continue pulling concurrent Qwen4B/model/integrity evidence into the same mesh instead of letting branches drift apart.

That is the current evidence-backed path toward a reproducible Frank v0.1 Ubuntu runtime.
