# TRIGGERWORT 4 — Canonical Frankenstein 2.0 Repository + Worker Archive Law

Status: OWNER-DIRECTED MANDATORY OPERATIONS LAW
Date: 2026-08-28

## 1. Canonical repository

The target build/evidence repository is:

`gschaidergabriel/frankenstein-2.0`

Once initialized, this repository is the canonical home of Frankenstein 2.0 implementation, architecture, workpackages, measurements, runtime receipts, negative results, checkpoints and complete build history.

The current `clay-global-research-entity` repository remains a research/control/forensics source, not the final artifact home.

## 2. Repository-first Triggerword-4 law

Every Triggerword-4 worker must, before substantive Frankenstein-2.0 mutation:

1. resolve whether `gschaidergabriel/frankenstein-2.0` exists and is initialized;
2. fetch its current `main`;
3. read `README.md`, `WORKPACKAGES.md`, `WORKER_PROTOCOL.md`, `workpackages/STATE.json`, `checkpoints/CURRENT.json` and relevant workpackage receipts;
4. resume the current accepted frontier rather than reconstructing a new plan from chat;
5. use the stable F2 workpackage ID as the primary dedupe key;
6. archive all accepted work and evidence in the canonical repository.

If the repository is not yet initialized, use the authorized bootstrap route in `gschaidergabriel/Dr.-Unterweger` and do not invent a second artifact repository.

## 3. Every coherent step becomes durable history

A Triggerword-4 worker must commit every meaningful coherent engineering step that changes the Frankenstein-2.0 state. The repository history is part of the experimental record.

Commit message convention:

`<F2-WP-ID>: <coherent step>`

Examples:

`F2-WP-200: add pulse admission score skeleton`
`F2-WP-200: add novelty residual unit tests`
`F2-WP-200: archive hold/wake benchmark receipt`

Do not make one giant end-of-session dump when multiple independently meaningful steps occurred.

Trivial temporary debugging noise does not need its own commit, but any source change, contract change, test fixture, measurement, result, accepted negative result, checkpoint or workpackage transition that matters to reproducibility must become durable.

## 4. Workpackage checklist law

`WORKPACKAGES.md` is the human-readable canonical checklist.

Machine-readable state lives under `workpackages/` and `checkpoints/`.

Statuses:

- `[ ]` NOT_STARTED
- `[-]` IN_PROGRESS / HOLD
- `[x]` ACCEPTED_AT_SCOPE

A workpackage may only become `[x]` when its declared evidence exists in the repository and the acceptance receipt names the exact source/test/measurement identity.

`WORKER_SAYS_DONE != WORKPACKAGE_ACCEPTED`

## 5. Required run archive

Every discriminating test, benchmark, failure injection, target-environment run or cognitive experiment must produce a durable run directory:

`runs/<F2-WP-ID>/<run-id>/`

Minimum:

- `receipt.json`
- exact source commit(s)
- environment identity/scope
- commands or executable test identity
- pass/fail/partial/blocked result
- relevant measurements
- evidence paths
- negative-result references
- exact next action

Raw logs may be compressed when large, but the structured receipt must remain human-readable and searchable.

## 6. Measurement law

All material measurements used to justify an architectural decision must live in the canonical repository or be copied there with immutable external provenance.

Examples:

- accuracy / score;
- latency;
- tokens / context size;
- RAM / CPU / GPU;
- action count / information gain;
- retrieval precision;
- world-model prediction residual;
- false completion rate;
- transfer / negative-transfer rate;
- child spawn / recovery / concurrency evidence;
- lesion and ablation results.

A claim such as `better`, `faster`, `more intelligent`, `more robust` or `cheaper` earns no promotion without archived measurement appropriate to the claim.

## 7. Negative-results law

Failed hypotheses and non-improving changes are first-class artifacts.

Store them under `negative_results/` and link them from the responsible workpackage/run.

Do not erase failed experiments merely because a later path succeeds. This prevents future workers from repeating disproven approaches and is part of Method Memory for the engineering process itself.

## 8. Checkpoint law

Before a worker stops, it must update a durable checkpoint containing at minimum:

- current workpackage;
- generation/claim identity;
- source commit after work;
- strongest current evidence;
- unresolved defect or uncertainty;
- exact next action;
- any blocked external condition.

The next Triggerword-4 worker resumes from this checkpoint.

## 9. Parallel worker / anti-stampede law

Multiple Triggerword-4 workers may run concurrently, but they must not become parallel authorities over the same workpackage generation.

Required behavior:

- refresh `main` before claim and before push;
- claim stable workpackage/subpackage identity;
- prefer independent workpackages when parallelizing;
- stale generations cannot overwrite newer accepted state;
- if the frontier has already moved, validate/fuse instead of duplicating;
- rebase/CAS-style update before shared checklist/state changes;
- preserve conflicting experimental results rather than silently overwriting them.

## 10. External research / Triggerword-5 ingestion

Triggerword 5 still disassembles the current donor `gschaidergabriel/frankenstein` and feeds evidence into Triggerword 4.

When Triggerword 4 adopts a Triggerword-5 result, the relevant distilled packet/contract/provenance must be copied or summarized into the Frankenstein-2.0 repository under `research/` or `architecture/` so the final artifact does not depend on chat history or hidden worker state.

Historical sources are allowed only when needed to resolve the provenance of a concrete current-donor mechanism; they are not the primary Triggerword-5 target.

## 11. Repository completeness target

By whole-system acceptance, the canonical repository must contain or immutably index all material artifacts needed to understand and reproduce the final system:

- source;
- architecture contracts;
- tests;
- workpackages;
- run receipts;
- measurements;
- accepted and rejected experiments;
- benchmarks / cognitive-unit-test results;
- build/runtime instructions;
- checkpoints;
- migration/provenance history;
- final artifact/package manifests.

`CHAT_ONLY_RESULT != ARCHIVED_PROJECT_RESULT`
`TEMPORARY_WORKER_STATE != PROJECT_MEMORY`
`EXTERNAL_RESEARCH_RESULT != INTEGRATED_EVIDENCE` until archived with provenance.

## 12. Security phase

Dedicated security/hardening systems are deferred until Frankenstein 2.0 functional architecture is sufficiently complete to know the real attack surface. Their historical evidence may be archived for later use, but they do not preempt current functional/cognitive build work.

Engineering isolation, exact identity, provenance and reproducible measurement remain required because they are necessary for valid evidence, not because they are the final security architecture.

## 13. Full experimental data spine is mandatory

Every Triggerword-4 worker must also obey these two current telemetry contracts before running or accepting material tests:

- `research_entity/global/TRIGGERWORD_4_EXPERIMENT_TELEMETRY_FORENSICS_AND_PERFORMANCE_DATA_LAW.md`
- `research_entity/global/TRIGGERWORD_4_FULL_INTERNAL_LATENCY_TRACING_ADDENDUM.md`

The canonical Frankenstein-2.0 repository must maintain project-level longitudinal SQLite stores under `data/` for at least:

- `system_telemetry.sqlite`
- `communications.sqlite`
- `hypotheses.sqlite`
- `bugs.sqlite`
- `grid10_telemetry.sqlite`
- `performance.sqlite`

Every material test series must additionally archive a timestamped, independently analyzable run package containing the relevant run-local database snapshots/slices, source/environment identity, metrics, raw logs when material, artifact hashes and the exact test receipt.

`ALL_LOGS` means every Frankenstein-2.0 component and every other process/system declared as participating in that test must have an instrumentation/collector record or an explicit `NOT_INSTRUMENTABLE` reason. A run with missing expected sources cannot claim `FULL_TELEMETRY`.

### 13.1 Hypothesis and counterhypothesis queue

Every material hypothesis/counterhypothesis that affects current engineering or cognition must enter the project hypothesis database with falsification criterion, priority, planned discriminator and evidence linkage. High-value unresolved opposing hypotheses are active test work, not chat notes.

### 13.2 Root-cause bug ledger

Every material defect enters the project bug database. `FIXED` means the root cause itself is confirmed, a fix commit/config identity exists and a regression test receipt proves the original failure path no longer reproduces at the declared scope.

`SYMPTOM_GONE != FIXED`
`WORKAROUND != ROOT_CAUSE_FIXED`

Whole-system acceptance targets zero unresolved confirmed root causes at the declared acceptance scope.

### 13.3 GRID10 telemetry

When GRID participates in a test, structured GRID telemetry is mandatory: cycles, functions/slots, candidates, provenance, salience/confidence/utility/EIG/cost, Hyperposition branches, GWT winner/broadcast, consumer uptake and downstream effect, re-entry, world projections, projection disagreement, Micro-Lab calls, decisions, budgets and HOLD/reset/rumination behavior.

### 13.4 Component and whole-system performance

Every relevant component and the whole system must be measured across representative named operating states. Capture applicable CPU, memory, I/O, network, GPU/VRAM, model/token usage, queueing, DB time, spawn overhead, power/temperature and component-specific work units.

Representative states include at minimum `IDLE_HOLD`, `PULSE_ONLY`, `RETINA_ACTIVE`, `GRID_BURST`, `WORLD_PROJECTION`, `MICROLAB`, `NERD_PHYSICS`, `RETRIEVAL`, `VOICE_SESSION`, `CHILD_BUILD`, `MULTI_CHILD`, `RECURSIVE_HARNESS`, `COMPLETION_REENTRY`, `RECOVERY_RESTART`, `WHOLE_LOOP` and intentional `STRESS/SATURATION` tests.

### 13.5 All internal latencies

All material internal boundaries must be latency-instrumented with causal traces/spans, not only one end-to-end stopwatch. Use `trace_id`, `span_id`, `parent_span_id`, UTC timestamps for correlation and monotonic nanosecond timestamps for local duration.

Instrument applicable latency through perception, Retina, Pulse, SituationFrame, every GRID logical function, candidate arbitration, GWT broadcast/uptake, retrieval, context compilation, UnifiedDB/SQLite/lock waits, vector/QUBO/NeRD/Micro-Lab projections, model/provider TTFT and completion, recursive harnesses, workpackage/child spawn/ack/result, IPC/queues, effects, CompletionGate, ResultReentry, Voice/VAD/STT/TTS/barge-in and restart/HOLD-WAKE recovery.

The run data must support critical-path analysis and decomposition into queue/compute/I/O/network/model/DB/child wait where those contributions are directly measurable. Unknown attribution remains `UNKNOWN`; it is not guessed.

Store latency distributions, not just averages: count, min/max, p50/p90/p95/p99 and p99.9 where sample counts justify them, plus cold/warm and state/workload labels.

`EVERY_END_TO_END_LATENCY -> INTERNAL_CRITICAL_PATH_BREAKDOWN`

## 14. Final law

`TRIGGERWORT_4 = BUILD + TEST + MEASURE + TRACE + COMMIT + ARCHIVE + CHECK_OFF + CHECKPOINT + CONTINUE`

A successful Triggerword-4 step is not finished until its durable source, evidence, telemetry, performance/latency traces and required run artifacts are in `gschaidergabriel/frankenstein-2.0`.