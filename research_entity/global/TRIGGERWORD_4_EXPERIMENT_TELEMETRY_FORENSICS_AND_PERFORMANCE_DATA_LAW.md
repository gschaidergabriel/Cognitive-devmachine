# TRIGGERWORT 4 — Experiment Telemetry, Forensics + Performance Data Law

Status: OWNER-DIRECTED MANDATORY OPERATIONS LAW
Date: 2026-08-28

## 1. Purpose

Frankenstein 2.0 is to be built as an experimentally inspectable system. Every material test series must leave enough structured evidence to reconstruct what the whole system and each participating subsystem did, communicated, hypothesized, consumed, failed on and learned.

The canonical repository is `gschaidergabriel/frankenstein-2.0`.

`TEST_RAN != TEST_IS_ANALYZABLE`
`NO_LOG_SOURCE != NO_EVENT`
`SYMPTOM_GONE != ROOT_CAUSE_FIXED`
`TOTAL_CPU != COMPONENT_COST`

## 2. Required project databases

The canonical repository must contain and maintain at least these SQLite databases under `data/`:

1. `system_telemetry.sqlite` — structured system/test events from every instrumented Frankenstein-2.0 component and every declared external/supporting process participating in a test.
2. `communications.sqlite` — all Frankenstein-2.0-produced communications with timestamps, direction, channel and causal/actor/task/invocation metadata.
3. `hypotheses.sqlite` — hypotheses and counterhypotheses, evidence, falsifiers, planned discriminators, status and test linkage.
4. `bugs.sqlite` — all bugs, symptoms, reproductions, root-cause hypotheses, confirmed root cause, fix commit, regression evidence and reopen history.
5. `grid10_telemetry.sqlite` — GRID cycles, slots/functions, candidates, broadcast, uptake, re-entry, Hyperposition branches, world projections, Micro-Lab calls, decisions and budgets.
6. `performance.sqlite` — per-component and whole-system resource/performance samples, phase/state transitions, derived aggregates and benchmark summaries.

These databases are project-level longitudinal stores. Tests also create immutable run packages containing run-specific database snapshots/slices.

## 3. Test-series package law

Every discriminating test/benchmark/failure injection/held-out cognitive experiment must create:

`runs/<WP-ID>/<series-id>/<run-id>/`

Minimum package:

- `manifest.json`
- `receipt.json`
- `sources.json`
- `environment.json`
- `system_telemetry.sqlite` — run-local slice/snapshot
- `communications.sqlite` — run-local slice/snapshot where communications occurred
- `hypotheses.sqlite` — run-local relevant hypotheses/evidence/tests
- `bugs.sqlite` — run-local relevant defects/evidence
- `grid10_telemetry.sqlite` — required when GRID participates
- `performance.sqlite` — run-local resource samples and derived metrics
- `metrics.json`
- raw logs or compressed raw-log bundle when material
- artifact hashes/index
- exact next action / unresolved uncertainty

The run package must be timestamped and independently analyzable after the test.

## 4. Instrumentation completeness

`ALL LOGS` means all logs/events from every Frankenstein-2.0 component and every other system/process declared in the test manifest as participating in the test.

Before a run starts, `manifest.json` must enumerate expected sources. Every source must have a collector/instrumentation entry or be explicitly marked `NOT_INSTRUMENTABLE` with reason.

A test cannot claim `FULL_TELEMETRY` if an expected participating source has no collected events/health receipt.

Required common event metadata where applicable:

- UTC timestamp;
- monotonic timestamp;
- run/series/workpackage/generation;
- component/subsystem;
- host/process/thread/worker;
- session/turn/causal identity;
- agent/child/task identity;
- invocation/effect/prediction/hypothesis/bug identity;
- event type/severity;
- payload/artifact reference;
- source commit/build identity.

## 5. Communication log law

Every Frankenstein-2.0-produced communication event must be recordable in `communications.sqlite` with:

- exact timestamp;
- direction;
- channel/type;
- producer and intended/actual consumer where known;
- session/turn/causal IDs;
- agent/child/task/invocation/effect linkage;
- content or content hash/artifact reference as appropriate;
- metadata such as model/provider, latency, interruption/cancellation, result/completion linkage.

Channels may include voice transcript/events, user text, child-agent handoff/result, tool/model request/response, internal structured messages, room/delivery events and other explicit communications.

## 6. Hypothesis / counterhypothesis work queue

Every material engineering or cognitive hypothesis formed during build/test must enter `hypotheses.sqlite` rather than remain only in chat or worker memory.

Each hypothesis stores:

- `HYPOTHESIS` or `COUNTERHYPOTHESIS`;
- parent/opponent relation;
- claim and rationale;
- confidence/priority;
- falsification criterion;
- discriminator / next test;
- linked workpackage/run/component;
- evidence supporting/refuting/neutral;
- state: OPEN / TEST_PLANNED / TESTING / SUPPORTED / REFUTED / INCONCLUSIVE / SUPERSEDED / RETIRED.

Triggerword 4 must periodically select high-value open hypothesis pairs for direct discrimination when they affect the current frontier.

`HYPOTHESIS_RECORDED -> DISCRIMINATOR -> EVIDENCE -> UPDATE`

## 7. Bug + root-cause law

Every observed defect enters `bugs.sqlite`.

Required lifecycle:

`OPEN -> REPRODUCED -> ROOT_CAUSE_HYPOTHESIZED -> ROOT_CAUSE_CONFIRMED -> FIX_CANDIDATE -> REGRESSION_PENDING -> FIXED`

Alternative states include `REOPENED` and `WONT_FIX`.

`FIXED` is valid only if all are present:

- confirmed root cause;
- evidence that distinguishes the root cause from competing explanations;
- source/configuration fix identity;
- regression test ID;
- regression receipt proving the original defect no longer reproduces under the relevant conditions;
- no known equivalent manifestation through the same root cause.

A symptom disappearing is not a fix. A workaround is not a root-cause fix unless the causal defect itself is removed or deliberately neutralized at its source with evidence.

Project goal: drive the set of unresolved confirmed root causes to zero at whole-system acceptance scope.

## 8. GRID10 telemetry law

GRID10 gets an independent structured telemetry database because its cognition must be analyzable without reconstructing it from generic stdout.

Record at minimum:

- pulse/situation-frame identity;
- GRID cycle start/end;
- active functions/slots;
- each candidate and provenance;
- salience/confidence/utility/EIG/cost estimates;
- Hyperposition branches and weights/status;
- GWT winner/broadcast;
- uptake by other functions;
- whether uptake affected later candidate/decision;
- re-entry of outcome/prediction residual;
- world projections used (observation/vector/QUBO/NeRD/Micro-Lab);
- projection disagreement;
- Micro-Lab call identity/cost/result;
- chosen ACT/ASK/OBSERVE/SPEAK/DELEGATE/WAIT/HOLD result;
- token/time/branch/resource budgets;
- recursion/harness route selected;
- rumination/reset/hold events.

This is required for causal GWT and GRID ablations.

## 9. Performance/resource telemetry law

Every relevant component and the whole system must be profiled across representative operating states.

### 9.1 Per-component samples

Where measurable, capture:

- wall-clock latency;
- CPU user/system time and utilization;
- process/thread CPU time;
- RSS, PSS where available, VMS and peak memory;
- major/minor faults;
- disk bytes/ops/read/write latency;
- network bytes/packets/connections;
- file-descriptor/process/thread counts;
- queue depth and wait time;
- SQLite/query/transaction time and lock wait;
- subprocess/child spawn time;
- model-call latency, time-to-first-token, tokens in/out, context size, retries;
- GPU utilization, VRAM, kernel/inference timing where available;
- accelerator/model residency/load time;
- power/energy/temperature/frequency where the platform exposes trustworthy sensors;
- component-specific work units such as frames, GRID cycles, retrieval candidates, simulations or tool calls.

### 9.2 Whole-system samples

Capture the same applicable host-level totals simultaneously so component attribution can be reconciled against total system cost.

`SUM_MEASURED_COMPONENTS <= WHOLE_SYSTEM_TOTAL + MEASUREMENT_ERROR`

Unattributed resource cost should be reported, not silently ignored.

### 9.3 Explicit system-state labeling

Every performance sample/interval must be associated where possible with a typed system state. Minimum representative states:

- `BOOT/INITIALIZE`;
- `IDLE_HOLD`;
- `PULSE_ONLY`;
- `RETINA_IDLE` / `RETINA_ACTIVE`;
- `GRID_BURST`;
- `WORLD_PROJECTION`;
- `MICROLAB`;
- `NERD_PHYSICS`;
- `RETRIEVAL`;
- `VOICE_SESSION`;
- `DIRECT_SMALL`;
- `CHILD_BUILD`;
- `MULTI_CHILD`;
- `RECURSIVE_HARNESS`;
- `COMPLETION_REENTRY`;
- `RECOVERY_RESTART`;
- `WHOLE_LOOP`;
- `STRESS/SATURATION` where intentionally tested.

Nested states are permitted. A run should make it possible to compare cost distributions per state and transitions between states.

### 9.4 Derived performance products

Store derived summaries such as:

- p50/p95/p99 latency;
- CPU-seconds per work unit;
- MB/GB memory peak and steady-state;
- tokens and model cost per cognitive decision;
- resource cost per GRID cycle;
- resource cost per successful workpackage/test;
- spawn overhead per child;
- Micro-Lab simulation cost vs external-action savings;
- retrieval cost vs useful-hit rate;
- action efficiency / information gain;
- idle baseline vs active delta;
- component share of total CPU/RAM/I/O/GPU;
- performance regressions against previous accepted baseline.

A component cannot be called `cheap`, `expensive`, `faster`, `lighter` or `efficient` without an archived measurement at the relevant state/scope.

## 10. Automatic collectors

Triggerword 4 must build reusable instrumentation helpers rather than hand-copy logs after each test. Expected primitives include:

- run start/stop wrapper;
- source registration;
- structured event emitter;
- communication emitter;
- hypothesis/counterhypothesis recorder;
- bug/root-cause recorder;
- GRID telemetry emitter;
- resource sampler;
- run finalizer that snapshots/slices project databases into the run package;
- manifest completeness checker;
- artifact hash/index generator.

Tests should use the same collectors whenever possible so cross-test analysis remains comparable.

## 11. Data retention and repository practicality

SQLite DBs and structured receipts are canonical. Large raw logs may be compressed and chunked. Extremely large binary artifacts may be stored externally only when repository limits make direct storage unreasonable; in that case the canonical repo must contain immutable hash, provenance, retrieval location and a compact structured summary.

Do not discard raw material merely because a summary exists until the relevant analysis/retention decision is explicitly made.

## 12. Analysis-after-build target

By the end of the build, this data spine must support questions such as:

- Which component consumes the most CPU/RAM/GPU in each operating state?
- Which GRID functions actually influence decisions after broadcast?
- Which hypotheses repeatedly fail and why?
- Which root causes remain open or have been reopened?
- Which subsystem causes latency spikes?
- What does Micro-Lab cost and how often does it prevent expensive external actions?
- Does memory degradation reduce retrieval cost without harming recall?
- Does R2 child delegation improve context hygiene enough to justify spawn overhead?
- Which world projection adds independent predictive value?
- Which cognitive improvements survive held-out tests and at what resource cost?

## 13. Final laws

`EVERY_TEST -> MANIFEST + TELEMETRY + PERFORMANCE + RECEIPT + RUN_PACKAGE`

`EVERY_GRID_TEST -> GRID10_STRUCTURED_TELEMETRY`

`EVERY_MATERIAL_HYPOTHESIS -> HYPOTHESIS_DB`

`EVERY_BUG -> BUG_DB -> CONFIRMED_ROOT_CAUSE -> REGRESSION_BEFORE_FIXED`

`EVERY_PERFORMANCE_CLAIM -> COMPONENT + WHOLE_SYSTEM MEASUREMENT AT NAMED STATE`
