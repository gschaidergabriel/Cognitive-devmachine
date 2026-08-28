# TRIGGERWORT 4 — Full Internal Latency Tracing Addendum

Status: OWNER-DIRECTED MANDATORY OPERATIONS LAW
Date: 2026-08-28

## Purpose

Frankenstein 2.0 must measure not only end-to-end latency but every material latency inside the system so bottlenecks, queueing, contention and hidden coordination delays can be attributed to exact components and transitions.

`END_TO_END_LATENCY != LATENCY_ROOT_CAUSE`
`WALL_TIME != QUEUE_TIME != COMPUTE_TIME != IO_TIME != MODEL_TIME`

All material test runs must support causal latency reconstruction.

## Trace identity

Every instrumented latency interval should carry, where applicable:

- `run_id`, `series_id`, `workpackage_id`, `generation`;
- `trace_id` for one causal end-to-end flow;
- `span_id` for one timed interval;
- `parent_span_id` for nesting;
- UTC wall-clock start/end;
- monotonic start/end in nanoseconds;
- `component`, `subsystem`, `operation`;
- host/process/thread/worker IDs;
- session/turn/causal IDs;
- agent/child/task/invocation/effect/prediction/hypothesis IDs;
- system state and nested state;
- queue name/resource if waiting occurred;
- status/error classification;
- payload/work-unit metadata;
- source/build commit.

Duration must be derived primarily from monotonic clocks. UTC timestamps are for cross-source correlation and human analysis.

## Required latency classes

Measure every applicable boundary, including at least:

### Perception / embodiment
- sensor capture -> frame available;
- frame available -> Retina L0/L1 result;
- Retina delta -> PerceptEvent;
- PerceptEvent -> UnifiedDB/State update;
- perception/state change -> Pulse admission decision;
- Voice input audio -> VAD detection;
- VAD -> STT partial/final;
- STT final -> cognitive input accepted;
- GRID speech decision -> Realtime/TTS request;
- TTS request -> first audio byte/frame;
- first audio -> playback start;
- barge-in audio -> detection -> truncate/stop;
- user utterance end -> Frankenstein first useful response audio.

### Persistent pulse / state
- event arrival -> StateFingerprint update;
- fingerprint update -> salience score;
- salience -> Pulse admission;
- admitted pulse -> SituationFrame compile start/end;
- checkpoint write/read;
- HOLD wake trigger -> active cognition start;
- restart detection -> state restored -> useful work resumed.

### GRID10 / GWT
- SituationFrame ready -> GRID cycle start;
- each GRID logical function start/end;
- candidate generation latency per slot/function;
- candidate ready -> arbitration/selection;
- winner selection -> GWT broadcast;
- broadcast -> reception per consumer;
- reception -> demonstrated uptake;
- uptake -> downstream candidate/decision change;
- Hyperposition branch creation/update/collapse/discriminator timing;
- GRID cycle start -> first decision candidate;
- GRID cycle start -> final action/WAIT/HOLD decision;
- outcome arrival -> re-entry -> next cognition update.

### Retrieval / memory / context
- query construction;
- exact/FTS/vector/graph/activation retrieval separately;
- DB query execution;
- vector search;
- rerank/filter;
- memory materialization/decompression;
- ContextHandle -> ContextView construction;
- ContextView -> model-ready context compile;
- cold archive lookup/reactivation;
- memory write/consolidation/compression.

### World model / Micro-Lab
- WorldNeed -> projection request;
- vector/causal projection;
- QUBO construction;
- QUBO solve;
- NeRD setup/simulation/result extraction;
- generic Micro-Lab setup/execute/validate;
- cross-view comparison/disagreement calculation;
- prediction contract creation -> real outcome -> residual calculation.

### Model / provider / recursive harness
- request queued -> dispatch;
- network connect/TLS where observable;
- request sent -> first token/event (TTFT);
- first token -> final token;
- total model call;
- retry/backoff;
- context preparation/tokenization where observable;
- R1 recursive child-call spawn/wait/fusion;
- R2 full child-harness spawn;
- child ready time;
- parent handoff -> child first useful action;
- child result -> parent result availability;
- multi-child fan-out -> first result / quorum / all results;
- harness fusion/verification time.

### Workpackage / native child
- workpackage created -> claimed;
- claim -> native child spawn requested;
- spawn request -> process/actor started;
- actor start -> task acknowledged;
- task acknowledged -> first tool/action;
- tool invocation queue -> execution start;
- execution -> receipt;
- child says done -> evidence available;
- evidence available -> CompletionGate decision;
- completion decision -> canonical checkpoint.

### UnifiedDB / persistence / IPC
- SQLite query/transaction duration;
- transaction begin -> commit;
- lock wait / busy retry;
- WAL/fsync/checkpoint cost where observable;
- serialization/deserialization;
- IPC/message enqueue -> dequeue;
- event bus publish -> subscriber receive;
- Room/delivery send -> ACK;
- queue waiting by queue name;
- filesystem read/write;
- artifact hashing/compression;
- git add/commit/push where relevant to build-worker telemetry.

### Effects / completion
- action proposal -> invocation;
- invocation -> external effect start;
- external effect start -> external completion;
- external completion -> observed world verification;
- observation -> ResultReentry;
- ResultReentry -> CompletionEvidence;
- CompletionEvidence -> goal/workpackage state update.

### Whole-loop traces
At minimum preserve complete traces for:

- user input -> understood state -> GRID decision -> response;
- visual change -> cognition -> action/voice;
- workpackage request -> child result -> verified completion;
- unknown-world observation -> hypothesis -> discriminating experiment -> model update;
- error observed -> bug record -> root-cause discrimination -> fix -> regression acceptance;
- HOLD wake -> useful resumed activity;
- perception -> world projection -> Micro-Lab -> GRID -> outcome -> residual.

## Latency database

`performance.sqlite` must include a trace/span layer with at least:

- `traces`;
- `latency_spans`;
- `span_links` for non-tree causal relations/fan-in/fan-out;
- `queue_waits`;
- `latency_aggregates`;
- `state_intervals`.

Recommended `latency_spans` fields:

```text
span_id PRIMARY KEY
trace_id
parent_span_id
run_id
series_id
workpackage_id
component
subsystem
operation
start_utc
end_utc
start_monotonic_ns
end_monotonic_ns
duration_ns
queue_wait_ns
compute_ns
io_wait_ns
network_wait_ns
model_wait_ns
db_wait_ns
child_wait_ns
status
system_state
host
pid
tid
worker_id
agent_id
child_agent_id
task_id
invocation_id
causal_id
metadata_json
```

Do not force all duration subcomponents when they cannot be measured independently; unknown attribution must remain `NULL/UNKNOWN`, not estimated as fact.

## Clock / cross-host handling

For same-process durations use monotonic clocks. For cross-process/cross-host chains, preserve both local monotonic spans and UTC synchronization metadata. Never subtract unrelated monotonic clocks across hosts.

Record clock source/synchronization quality in the run environment. Cross-host wall-clock latency claims must include uncertainty when synchronization is imperfect.

## Aggregates

For every important operation and state calculate, when sample count permits:

- count;
- min/max;
- mean/median;
- p50/p90/p95/p99/p99.9;
- standard deviation / robust spread;
- cold vs warm;
- success vs failure;
- cache hit vs miss;
- single-child vs multi-child;
- idle vs load/stress;
- before/after architecture change.

Tail latency is first-class. An architecture with good median and pathological p99 must not be described as simply fast.

## Critical-path analysis

Each end-to-end trace should support reconstruction of:

- critical path;
- parallel branches not on the critical path;
- queueing contribution;
- compute contribution;
- model/provider contribution;
- DB/lock contribution;
- IPC/network contribution;
- child/harness contribution;
- unattributed time.

`END_TO_END = CRITICAL_PATH`, not the sum of parallel child durations.

## Performance acceptance

Every material latency claim must name:

- operation / end-to-end trace;
- system state;
- workload;
- source commit;
- environment;
- sample count;
- percentile/statistic;
- warm/cold condition;
- instrumentation completeness.

No promotion based only on one stopwatch measurement.

## Required analyses after build

The archived data must make it possible to answer:

- Where does every millisecond in a cognitive loop go?
- Which GRID function creates the longest median/tail delay?
- Is GWT broadcast cheap but uptake slow?
- Does QUBO/Micro-Lab add more delay than the external actions it saves?
- Is latency caused by model inference or context assembly?
- How much delay comes from DB locking?
- What is child spawn overhead and when is delegation still worthwhile?
- Which operating state has the worst p99 latency?
- Which component creates jitter rather than average slowdown?
- How quickly does Frankenstein wake from HOLD and become useful?
- What is user speech -> useful spoken response latency and its internal breakdown?
- What is perception change -> correct action latency?
- What is bug observation -> root-cause confirmation -> verified-fix latency during development?

## Final laws

`ALL_MATERIAL_INTERNAL_BOUNDARIES -> LATENCY_SPANS`

`TRACE_ID + SPAN_ID + MONOTONIC_TIME -> CAUSAL_LATENCY_RECONSTRUCTION`

`MEDIAN_ONLY != PERFORMANCE_CHARACTERIZATION`

`UNKNOWN_LATENCY_ATTRIBUTION stays UNKNOWN`

`EVERY_END_TO_END_LATENCY -> INTERNAL_CRITICAL_PATH_BREAKDOWN`
