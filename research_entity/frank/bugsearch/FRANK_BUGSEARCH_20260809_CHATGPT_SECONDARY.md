# FRANK targeted bugsearch — 2026-08-09

Actor: `chatgpt-secondary` (OpenAI, GPT-5.6 Sol)  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Request: user message `frank bugserch`  
Trigger semantics: NOT an exact registered `frank` trigger; treated as targeted FRANK/Harness bug search.  
Authority: Research Entity researches/tests Frank; Frank self-Harness authority remains `PROPOSAL_ONLY`.

## Scope and evidence class

Inspected current canonical/program state, active Frank repository commits, FRANK loop-dynamics probe, H1 reference loop semantics, exact `bug` feedback capture, Clay bug ingest, systemd deployment template, and current ClayCode BASE path. Findings below distinguish checked-in code contradictions from target-host verification still required.

## BUG-FRANK-LOOP-001 — P1 — H1 loop decision semantic divergence

Status: `CONFIRMED_BY_CHECKED_IN_CODE_DIFFERENTIAL`; Ubuntu/live integration verification still required.

Frank file: `gschaidergabriel/Dr.-Unterweger:harness/loop_dynamics_probe.py` at/after commit `acf487ceb06575ae04166b8b2226957a2c38d16e`.
Reference: `research_entity/harness/reference/loop_dynamics_reference.py`.

The Frank probe states that it is an adapter in front of the typed H1 reference semantics but reimplements materially different thresholds and decision rules instead of invoking/version-binding the reference contract.

Concrete discriminators, using constant short trajectories so the tail summary equals the stated values:

- `delta=.07, pressure=.10, net=0, budget>0`: Frank probe => `CONVERGING_FIXED_POINT / HALT_CANDIDATE_CONVERGED`; H1 reference => `CHAOTIC_OR_UNCLASSIFIED / ROUTE`.
- `delta=.05, pressure=.20, net=-.05, budget>0`: Frank probe => `CHAOTIC_OR_UNCLASSIFIED / ROUTE`; H1 reference => `STALLED / ESCALATE_STALLED`.
- `delta=.90, pressure=.20, net=0, budget>0`: Frank probe => `CHAOTIC_OR_UNCLASSIFIED / ROUTE`; H1 reference => `DIVERGING_OR_OVERTHINKING / ABORT_DIVERGING` when no rollback ref exists.
- `delta=.20, pressure=.05, net=.02, budget>0`: Frank probe => `CHAOTIC_OR_UNCLASSIFIED / CONTINUE`; H1 reference => `CHAOTIC_OR_UNCLASSIFIED / ROUTE` because the reference utility margin threshold is `.04`.

Impact: recurrent-loop control can halt, continue, route, or abort differently from the claimed H1 reference. This can directly distort Frank's loop-of-loops behavior.

Required repair/test: one semantic authority implementation or explicit versioned adapter contract; add exhaustive/boundary differential tests between trajectory projection and `decide_recurrence`, including the four cases above. Do not merely tune fixtures until green.

## BUG-FRANK-REPO-002 — P1 — stale/nonexistent FRANK baseline repository identity

Status: `CONFIRMED_REMOTE_PATH_DRIFT`.

Current Research Entity bootstrap names the Frank repo `gschaidergabriel/Dr.-Unterweger`, and that repository contains current Frank/Harness commits. In contrast, `PROGRAM_STATE.json` H1 `reference_baseline`, Clay bug-ingest constant, bug-ingest env template, and queued Ubuntu deployment work refer to `gschaidergabriel/frankv0.1`. GitHub lookup of `gschaidergabriel/frankv0.1` returned 404 during this run.

Impact: deployment, provenance, H1 baseline accounting, and bug evidence can point to a nonexistent/wrong repository even while current code evolves elsewhere.

Required repair/test: resolve one authoritative Frank repository identity through a single config/registry source; update H1 baseline/deployment/ingest references through approved state mechanisms; prove checkout HEAD and provenance receipts refer to the same repository before deployment.

## BUG-FRANK-INGEST-003 — P1 — malformed valid-hash bug export can restart-loop the Clay watcher

Status: `STATIC_REPRODUCIBLE_FROM_CONTROL_FLOW`; service-level test required.

File: `research_entity/runtime/ingest_frank_bug_feedback.py`.

`ingest_one()` catches JSON parse errors and hash mismatch, but after a valid self-hash/kind/trigger it directly indexes/uses fields such as `p['bug_id']` without complete schema/type validation. `ingest()` does not isolate exceptions per file, and `watch()` has no exception containment. The systemd service is configured `Restart=on-failure`.

A hash-valid payload with `kind=FRANK_RESEARCH_BUG_REPORT`, `trigger=bug`, but missing or malformed `bug_id` can therefore abort the batch/watcher. If the malformed file remains in the watched directory, systemd can repeatedly restart into the same failure and prevent later valid reports from being processed.

Required repair/test: strict schema validation, per-file exception isolation/quarantine, continue-after-invalid behavior, payload size limits, and restart regression with malformed file preceding a valid report.

## BUG-FRANK-CAPTURE-004 — P1/P2 — export/database crash-consistency gap

Status: `CONFIRMED_FROM_WRITE_ORDER`; fault-injection verification required.

File: `gschaidergabriel/Dr.-Unterweger:runtime/bridge/frank_bug_feedback.py`.

`capture_pair()` writes the export JSON before beginning/committing the Frank DB transaction. A DB failure after file creation can leave an orphan export that Clay may ingest although Frank has no corresponding committed bug row.

Required repair/test: staged temp export + DB state transition + atomic finalize/receipt, or equivalent recoverable two-phase protocol; inject failure between filesystem write and DB commit and prove no orphan can become READY research work without reconciliation.

## BUG-FRANK-REDACT-005 — P1 security — secret redaction is narrower than its contract implies

Status: `CONFIRMED_PATTERN_COVERAGE_GAP`; secret-class threat model required.

Current regexes cover simple unquoted `api_key|token|secret|password` assignments, OpenAI-style `sk-*`, and GitHub token prefixes. Existing tests cover only simple unquoted forms. Common quoted JSON key/value forms and other credential classes are not comprehensively covered.

Impact: exact `bug` capture deliberately preserves the previous Andreas/Frank exchange and exports it to another repository boundary; incomplete redaction can persist credentials in Frank DB/export and then Clay research state.

Required repair/test: structured redaction where possible plus broad credential detectors, negative/positive corpus, quoted JSON/header/cookie/JWT/private-key cases, and fail-closed handling for high-risk secret uncertainty.

## Additional medium-priority findings

- Frank bug capture keeps one pending input per `session_ref` via `INSERT OR REPLACE`; concurrent/overlapping turns can overwrite pairing state unless strict serial-turn behavior is guaranteed and enforced.
- `remember_output()` records the output caller's node id but does not preserve the pending input node id, weakening cross-node handoff provenance.
- Frank loop threshold validation rejects negatives but does not reject non-finite threshold values; NaN/Infinity can distort comparisons.
- Loop slopes are computed over ordinal sample index rather than actual `step` spacing although nonuniform strictly increasing steps are accepted.
- The latest checked Frank loop commit exposed no GitHub combined CI statuses in this run, so the claimed H1 alignment had no visible remote differential check at that commit.

## Related ClayCode risk surfaced during Frank dependency audit

Not promoted here as a Frank Harness bug, but the current BASE compiler deserves targeted differential tests before FRANK handoff: integer reference division converts through Python float (`int(left/right)`) while C uses `int64_t` division; large integers above exact float range can diverge. Python integer behavior also differs from C `int64_t` overflow. String equality in the interpreter is value equality while emitted C `const char * ==` is pointer equality if that path becomes reachable. These belong to the BASE compiler blocker stream.

## Priority order

1. Fix/lock H1 loop semantic differential before allowing loop-control output to steer more FRANK recurrence.
2. Resolve authoritative Frank repository identity before Ubuntu deployment/provenance promotion.
3. Harden bug ingest against malformed exports so the feedback channel itself cannot block research intake.
4. Repair capture/export atomicity and redaction before treating exact `bug` as reliable operational telemetry.
5. Add regression and target-host receipts; only then promote statuses.

## Promotion guard

No finding here claims that the real Andreas Ubuntu runtime has already exhibited the failure. `BUG-FRANK-LOOP-001` is a checked-in semantic contradiction with explicit discriminators; repository-path drift is remotely observed; intake/capture findings are deterministic control-flow/write-order defects requiring integration/fault-injection receipts before live-runtime claims.
