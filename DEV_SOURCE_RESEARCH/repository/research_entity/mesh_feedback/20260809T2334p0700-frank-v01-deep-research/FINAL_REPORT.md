# FRANK v0.1 Deep Research / Fusion Report — 2026-08-09 23:34 +07

Actor: `chatgpt-secondary` (ChatGPT organ of Clay)  
Subject: separate target system `Frank v0.1`  
Canonical parent observed before durable write: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
User goal: research -> fusion -> hypotheses/counterhypotheses -> live external research -> second fusion -> build -> test/measure -> feed results to the shared Research Center.  
Target host law: Ubuntu Linux developer system only for Frank v0.1.

## Executive result

The run found one concrete Harness integration gap and produced a reversible code candidate rather than widening architecture speculatively.

The initial hypothesis was too broad: Frank already has a strong repository/materialization truth gate in `runtime/state/repo_truth_gate.py`, and `runtime/state/frank_prompt_capsule.py` invokes it before normal prompt-state construction. Therefore the hypothesis **"Frank lacks UnifiedDB/ClayGraph coherence validation" is REFUTED**.

The narrower hypothesis remains supported by direct code evidence: `harness/frank_harness_runtime.py` opens the canonical state through `open_pair()` without first invoking `repo_truth_gate.preflight()`. `open_pair()` verifies existence/openability but does not itself establish repository-head/materialization lineage. That creates a compatibility entry path in which Harness operations can reach state without the same fail-closed preflight used by the prompt path.

A draft implementation was created in Frank transport repo branch `research/chatgpt-harness-truth-gate-20260809`, PR #25. It adds a guarded Harness entrypoint and six regression tests. An isolated local test reproduction passed 6/6 tests in 0.005 s and both files passed Python byte-code compilation. This is **LOCAL/ISOLATED evidence only**, not an Ubuntu developer-host or VPS receipt. PR #25 remains draft and must not be promoted on this evidence alone.

A READY dynamic work event was issued to the local/Ubuntu-capable execution organ: `WORK-FRANK-HARNESS-TRUTH-GATE-UBUNTU-20260809`.

## Internal evidence used

### Current Clay/Research Center

- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`: RAE-8.8 r2, state hash `04234efd...f489346` at read time.
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`: mission is Frank v0.1 fully operational on Andreas' PC; current staged program and live-refresh laws.
- `research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay`: Ubuntu developer system is the active v0.1 target; Frank remains a separate research subject.
- `research_entity/rooms/PROGRAM_STATE.json`: current stage `BASE_CLAYCODE_RELEASE`; H1 is blocked by BASE.
- `research_entity/claycode/CLAYCODE_RELEASE_WORKSPACE.json`: only `CC-WP-01-SPEC-FREEZE` is PASS; CC-WP-02..14 remain OPEN at the observation point.

### Current Frank repo

- `README.md`: UnifiedDB is semantic authority, ClayGraph is a derived association/activation graph; repository architecture/CI alone is explicitly not v0.1 release completion.
- `runtime/state/apply_current_schema.py`: two SQLite materializations use WAL and explicit ordered migrations; cross-file atomicity is explicitly not claimed; an interrupted/divergent pair is expected to fail closed at the repository/materialization truth gate.
- `runtime/state/repo_truth_gate.py`: validates repo identity/head, critical files, UnifiedDB integrity/schema/lineage/source head, ClayGraph integrity/schema/source epoch and stale/divergent states.
- `runtime/state/frank_prompt_capsule.py`: executes the truth gate before standalone prompt injection and additionally validates current materialization lineage inside `open_central()`.
- `harness/frank_harness_runtime.py`: its `open_state()` directly returns `open_pair(STATE, test_mode=False)` and mutating Harness commands use that path.

### Institute archive

`Ablating a Stateful Agent — Institute for Agentic Research` was treated as an internal working paper, not peer-reviewed independent evidence. Its useful methodological contribution is the preregistered subsystem-ablation pattern: predict an operational target, lesion the subsystem, measure selective effects, preserve failed predictions and unexpected dependencies. It reports four selective hits out of five pre-registered ablations in one Frank.ink case study and explicitly warns against class-level generalization.

## External live research

Source classes were preserved.

### SQLite official documentation — primary implementation evidence

1. SQLite `ATTACH DATABASE` documentation states that transactions spanning multiple attached databases are atomic across files only under specific conditions and **not when the main database uses WAL**. In WAL mode, a host crash during commit can leave some files changed and others unchanged.
2. SQLite atomic-commit documentation explains the rollback-journal mechanism used for multi-file atomic commit and its dependence on a super-journal; this does not provide the same cross-file guarantee for WAL.
3. SQLite transaction documentation confirms `BEGIN IMMEDIATE` obtains a write transaction immediately but does not turn separate connections/files into one crash-atomic transaction.
4. SQLite security guidance recommends defensive connection settings for hostile/untrusted database/SQL contexts. `SQLITE_DBCONFIG_DEFENSIVE` disables several database-corrupting SQL features. Current SQLite documentation also encourages `trusted_schema=OFF` for applications that do not require trusted schema features.
5. Python 3.12 `sqlite3` exposes `Connection.setconfig()` and SQLite DB-config constants where supported. This is a candidate hardening surface, not yet a Frank production change.

Primary references:
- https://www.sqlite.org/lang_attach.html
- https://www.sqlite.org/atomiccommit.html
- https://www.sqlite.org/lang_transaction.html
- https://www.sqlite.org/security.html
- https://www.sqlite.org/c3ref/c_dbconfig_defensive.html
- https://docs.python.org/3.12/library/sqlite3.html

### Current agent-memory research — external research/preprint evidence

Recent 2026 work was used only for architectural triangulation, not as authority over local runtime evidence:

- `Agent Memory: Characterization and System Implications of Stateful Long-Horizon Workloads` (arXiv:2606.06448) argues for phase-aware profiling of memory construction, retrieval and generation rather than treating stateful-agent memory as one undifferentiated operation.
- `AgenticSTS` (arXiv:2607.02255) studies typed/bounded retrieval and layer ablation in a stateful agent context.
- `Are We Ready For An Agent-Native Memory System?` (arXiv:2606.19849) evaluates multiple memory systems across representation/storage/extraction/retrieval/maintenance and reports no single design dominating all dimensions.

These sources support a measurement design in which Frank separately measures persistence, retrieval, reconstruction/injection and downstream causal use instead of optimizing a single aggregate memory score.

## Fusion 1

### H-FRANK-TG-1 — multi-file coherence must be externally validated

**Hypothesis:** Because UnifiedDB and ClayGraph are physically separate WAL databases, correctness requires a fail-closed lineage gate before canonical use; file-open success is insufficient.

**Support:** Frank's own migrator says cross-file atomicity is not claimed; SQLite primary documentation confirms WAL does not provide crash-atomic multi-file transactions.

**Counterhypothesis:** Derived ClayGraph can always be rebuilt, so an explicit coherence gate is unnecessary.

**Evaluation:** Rebuildability reduces recovery cost but does not make a stale graph safe to use before detection. Counterhypothesis NOT_SELECTED for canonical read/mutation paths.

### H-FRANK-TG-2 — Frank lacks such a gate

**Status:** REFUTED.

`repo_truth_gate.py` already implements materially stronger validation than the first inspection suggested, and the prompt capsule executes it.

## Fusion 2

### H-FRANK-TG-3 — Harness compatibility entry bypasses the gate

**Status:** CURRENT / code-supported / needs Ubuntu reproduction.

Evidence path:

`harness/frank_harness_runtime.py::open_state()` -> `apply_current_schema.open_pair()`

No truth-gate invocation is present on that path in the observed main revision, whereas `frank_prompt_capsule.py::hook_main()` explicitly runs `repo_truth_gate.py` first.

**Falsifier:** current target checkout shows an external mandatory launcher/hook that makes direct invocation impossible or a newer main integrates preflight before any Harness-backed canonical operation.

### H-FRANK-TG-4 — guarded wrapper is sufficient final fix

**Status:** OPEN / deliberately not promoted.

The wrapper removes the bypass for operators who use it, but operator convention is weaker than enforcing the gate at the canonical Harness boundary. Ubuntu integration should decide whether to fold preflight into the legacy controller, retire the old entry path, or enforce a single launcher at packaging/service level.

### H-FRANK-SQLITE-5 — defensive/trusted-schema hardening improves safety without breaking Frank

**Status:** OPEN.

Primary documentation supports the safety mechanism, but compatibility with Frank's schema, migrations, FTS/extensions/triggers and actual Python/SQLite build must be measured on Ubuntu before adoption.

### H-FRANK-MEM-6 — memory quality must be phase-separated

**Status:** OPEN but externally triangulated.

Proposed readout vector:

`M = [persist_correctness, retrieval_precision, retrieval_recall, reconstruction_fidelity, injection_cost, receiver_use, downstream_effect, recovery_success]`

Do not collapse this to one scalar for promotion decisions. Use task- and failure-specific shadows plus lesion/rescue tests.

## Build delta

Frank draft PR #25 (`Harness: fail closed behind repository truth gate`) contains:

- `harness/frank_harness_guarded_entrypoint.py`
  - requires `repo_truth_gate.preflight()` status `PASS` before delegating to the existing Harness controller;
  - maps materialization/graph stale -> exit 75, schema migration required -> 76, degraded/unknown -> 70;
  - emits machine-readable failure JSON including `mutation_performed: false`.
- `harness/test_frank_harness_guarded_entrypoint.py`
  - PASS path;
  - materialization stale;
  - graph stale;
  - schema migration required;
  - degraded/unknown states;
  - proof that the legacy target is never entered when the gate fails.

## Measurements completed in this ChatGPT execution surface

Environment class: isolated local sandbox, not Frank repo checkout, not Andreas Ubuntu host, not VPS.

- unit tests: 6 passed / 6 run;
- observed test elapsed: 0.005 s;
- Python compilation check: 2/2 new files compiled successfully;
- GitHub PR CI for head `9d3bd18b21e33b681657c55795d6381ec586b6b1`: no workflow runs observed immediately after PR creation;
- production/VPS acceptance: NOT RUN because this ChatGPT session exposes no SSH/terminal/VPS execution capability.

These measurements may not be promoted to Ubuntu acceptance.

## Mandatory Ubuntu/VPS experiment matrix

The queued local-execution work must measure at least:

1. **Truth PASS:** current main + current admitted databases; execute each guarded Harness command; record outputs and mutation hashes.
2. **UnifiedDB stale source head:** induce a controlled stale materialization; expect exit 75 and zero state mutation.
3. **ClayGraph stale source epoch:** expect exit 75 and zero state mutation.
4. **Schema migration required:** expect exit 76 and zero state mutation.
5. **Continuity/divergence hard fail:** expect exit 70 and zero state mutation.
6. **Recovery/rescue:** rebuild/materialize from admitted repo state, then require PASS and successful command execution.
7. **Latency:** >=100 warm and >=20 cold runs if practical; record p50/p95/p99 for total preflight, git fetch, DB checks, guarded no-op/read command and representative mutation command.
8. **Crash/fault injection:** interrupt between derived-graph and UnifiedDB migration/materialization phases; verify next canonical entry fails closed until recovery.
9. **Connection hardening experiment:** test `trusted_schema=OFF` and, where Python/SQLite supports it, `SQLITE_DBCONFIG_DEFENSIVE`; run migrations/self-tests/FTS/extensions and report compatibility before any production change.
10. **Ablation/rescue:** bypass or lesion the gate only in an isolated test root, demonstrate the stale-pair failure mode, restore guard and demonstrate recovery. Never disable the guard on canonical state for convenience.

## Architecture implications

1. **Keep logical unification, not forced physical merge.** The current semantic split can remain if epoch/provenance coherence is enforced and recovery is explicit. SQLite's WAL limitation is an argument for the gate, not automatically for merging everything into one physical DB.
2. **Make safety boundaries executable at the lowest practical entry boundary.** A wrapper is a candidate; a canonical controller/service boundary is stronger.
3. **Treat derived ClayGraph as rebuildable but not disposable evidence.** Its source epoch, projection receipt and derivation lineage are necessary for safe use.
4. **Retain the existing repo-first authority model.** The discovered bypass is localized; the broader architecture already contains strong lineage controls.
5. **Use lesion/rescue + zero-mutation receipts for Harness safety changes.** Happy-path tests alone are insufficient.
6. **Do not widen current work to Android/mobile/edge.** Ubuntu remains the explicit v0.1 acceptance target.

## Negative results / corrections preserved

- N1: "No pair-coherence gate exists" -> REFUTED by `repo_truth_gate.py` and prompt capsule integration.
- N2: "Cross-file WAL is crash-atomic" -> REFUTED by SQLite official documentation and by Frank's own migration contract.
- N3: "Draft wrapper is a production fix" -> NOT ESTABLISHED; local tests are not Ubuntu acceptance.
- N4: "No CI run means tests failed" -> false inference; no workflow run was observed, which is absence of CI evidence, not a test failure.
- N5: Institute ablation results generalize to stateful agents as a class -> NOT SUPPORTED; the source itself states n=1 and working-paper limitations.

## Shared-center handoff

Dynamic work event:
`research_entity/state/work/events/20260809T2334p0700_chatgpt_secondary_frank_harness_truth_gate_ubuntu.json`

Frank draft PR:
`gschaidergabriel/Dr.-Unterweger#25` (semantic repo: `gschaidergabriel/frankv0.1`).

Expected feedback targets: `frank`, `harness`, `unifieddb`, `claygraph`, `claycode`, `gwt`, `emergenz`, `hyperposition`, `clayresearch`.

No stage gate, scientific generation, H1 PASS, BASE PASS, Ubuntu acceptance or VPS execution is claimed by this report.
