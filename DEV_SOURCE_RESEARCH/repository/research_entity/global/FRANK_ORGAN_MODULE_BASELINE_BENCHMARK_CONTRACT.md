# FRANK Original Organ / Module Baseline Benchmark Contract

**Status:** PROJECT_OWNER_FIXED_GLOBAL_FRANK_RESEARCH_AND_BUILD_GATE  
**Effective:** 2026-08-09  
**Scope:** every historical Frank organ, module, service, recurrent subloop and materially distinct cognitive/runtime function before `RETAIN`, `FUSE`, `EMERGENT_DISTRIBUTE` or `CLAY_REDESIGN_CANDIDATE` decisions.  
**Target semantics:** Ubuntu Linux developer system. The verified Hostinger GitHub self-hosted runner may be used for reproducible remote Ubuntu build/test evidence when a compatible authorized workflow exists; final release evidence still requires Andreas' actual target system.

## 1. Absolute baseline law

No historical Frank organ/module/function may be fused, emergently distributed, replaced, redesigned in Clay/ClayCode, removed as an explicit boundary, or claimed improved until its **Original Baseline** has been reconstructed and measured as far as surviving evidence/runtime permits.

The baseline is not prose. It is a versioned, machine-comparable measurement package with complete provenance and environment metadata.

If the exact historical executable can no longer be run, record `BASELINE_PARTIAL_ARCHAEOLOGY` and reconstruct the strongest possible executable/traceable surrogate from source, historical logs, fixtures, databases and documented behavior. Missing values remain `UNKNOWN`; they must never be silently invented.

## 2. Baseline package identity

Every organ/module receives a stable `baseline_id` and one or more immutable benchmark runs.

Required identity fields:

- `baseline_id`;
- `organ_or_module_id`;
- canonical/historical name;
- historical path/service/process/container/unit;
- source repository;
- branch/tag/commit/blob hashes;
- code/config/schema version;
- historical architecture generation;
- successor/lineage references;
- baseline class: `LIVE_ORIGINAL | REBUILT_ORIGINAL | TRACE_REPLAY | BASELINE_PARTIAL_ARCHAEOLOGY`;
- evidence confidence;
- known missing evidence;
- created/reconstructed/tested timestamps;
- benchmark owner/worker/provenance;
- immutable artifact/checksum references.

## 3. Mandatory functional lineage metadata

For every organ/module/function record:

- intended historical role;
- observed historical role where different;
- inputs and input schemas;
- outputs and output schemas;
- internal state variables;
- persistent state and storage surfaces;
- update equations/rules where known;
- initialization/default state;
- boot/start order dependencies;
- shutdown/recovery behavior;
- cadence/timescale;
- sync/async/event-driven mode;
- upstream dependencies;
- downstream consumers;
- feedback/re-entry participation;
- GWT/attention participation;
- Needle/tool/effect participation;
- memory/retrieval participation;
- self/world/personality/reward/control participation;
- authority boundary;
- error/fallback behavior;
- historical failure modes/bugs/negative results;
- known safety constraints;
- known resource constraints;
- known coupling strength/delay/inhibition/gain controls;
- lesion/rescue handles where possible.

## 4. Mandatory performance metrics

Every baseline run must measure or explicitly mark `NOT_APPLICABLE` / `UNKNOWN`.

### 4.1 Latency

- end-to-end latency;
- internal compute latency;
- queue/wait latency;
- dependency/I/O latency;
- median;
- p50;
- p90;
- p95;
- p99 where sample count supports it;
- minimum/maximum;
- cold-start latency;
- warm-start latency;
- steady-state latency;
- first-token / first-result latency where applicable;
- completion latency;
- timeout rate;
- jitter / variance;
- contribution to total Frank cycle latency.

### 4.2 Accuracy / functional correctness

`accuracy` is task-appropriate correctness, never blindly a single classification percentage.

Record the full applicable error surface, for example:

- classification: accuracy, balanced accuracy, precision, recall, F1, confusion matrix, calibration, Brier/ECE, open-set UNKNOWN/AMBIGUOUS/CONFLICT rejection;
- Needle/routing: correct route, false route, missed route, unnecessary escalation, abstention quality, tool-choice correctness, route confidence calibration;
- retrieval/memory: hit@k, recall@k, precision@k, MRR/nDCG where meaningful, provenance correctness, stale retrieval rate, false association rate;
- GWT/attention: candidate admission/selectivity, missed relevant candidate, false ignition, receiver delivery/reconstruction/use/causal-use closure, focus stability;
- controller/homeostasis: intervention correctness, false intervention, stabilization success, overshoot, oscillation, stagnation, divergence, overcoupling, false halt;
- state/persistence: transition correctness, stale-state rate, lost-update rate, duplicate-update rate, replay equivalence, migration correctness;
- effects/tools: intended-effect success, incorrect effect, duplicate effect, missed verification, false success receipt, rollback correctness;
- generative/cognitive functions: frozen-episode task success, calibrated uncertainty, contradiction/error taxonomy, correction success and outcome quality.

### 4.3 Reliability

- successful-run rate;
- failure rate;
- crash rate;
- timeout rate;
- hang/deadlock rate;
- retry rate;
- retry success rate;
- transient versus deterministic failure split;
- recovery success rate;
- restart success rate;
- state corruption rate;
- stale-state rate;
- duplicate processing/effect rate;
- idempotency failure rate;
- data-loss rate;
- long-run drift;
- degradation under load;
- failure-mode distribution;
- mean time between failures where sample duration supports it;
- mean time to recovery;
- last-known-good rollback success.

## 5. Mandatory resource metrics

Where measurable:

- CPU model and utilization;
- per-core utilization where useful;
- user/system CPU time;
- RAM RSS/PSS/heap;
- peak RAM;
- swap;
- GPU model;
- GPU utilization;
- VRAM usage/peak;
- accelerator kernel time;
- storage reads/writes/IOPS/bytes;
- network bytes/requests/round trips;
- DB/query count and query latency;
- filesystem calls where relevant;
- context/token input/output/cache usage;
- model inference calls;
- external API calls;
- tool calls;
- energy/power where measurable;
- temperature/throttling where measurable;
- process/thread/task count;
- queue depth;
- lock contention;
- cache hit/miss behavior;
- artifact/state amplification.

## 6. Exhaustive run metadata

Every raw measurement row/run MUST bind all metadata that can materially affect interpretation. Unknown metadata is explicit `UNKNOWN`.

### 6.1 Machine / hardware

- machine/node identity;
- physical/VM/container classification;
- cloud/VPS provider and instance identity/class where applicable;
- CPU vendor/model/microarchitecture;
- CPU sockets/cores/threads;
- CPU governor/frequency/turbo state where visible;
- RAM total/type/speed where visible;
- NUMA topology where applicable;
- GPU/accelerator vendor/model/count;
- GPU driver/runtime versions;
- VRAM;
- storage device/filesystem/mount type;
- network interface/path characteristics where relevant;
- virtualization/container runtime;
- thermal/power state where visible;
- concurrent machine load/background jobs.

### 6.2 OS / runtime environment

- OS/distribution/version;
- kernel version;
- architecture/ISA;
- libc/runtime versions;
- container image/digest;
- Python/Node/Rust/C/C++/Java/other runtime/compiler versions as applicable;
- CUDA/ROCm/OpenCL/BLAS/backend versions;
- package/dependency lock hashes;
- environment profile;
- process limits/ulimits;
- scheduler/cgroup/container resource limits;
- locale/timezone if behavior-relevant;
- enabled services/dependencies;
- network availability state.

### 6.3 Build metadata

- Git repository/branch/commit;
- dirty-tree state;
- file/blob hashes for tested component;
- build system/version;
- compiler and linker versions;
- compile flags;
- optimization level;
- CPU/GPU target flags;
- feature flags;
- debug/release mode;
- static/dynamic linking information;
- binary hash;
- package/artifact hash;
- ClayCode/compiler/runtime semantic version where applicable;
- schema/migration version;
- generated-code provenance.

### 6.4 Model metadata

Where an ML/LLM component participates:

- model family/name;
- exact model revision/hash;
- parameter count/class;
- tokenizer/version;
- quantization type/parameters;
- dtype;
- context length;
- inference backend/version;
- batch size;
- KV-cache policy;
- sampling/decoding parameters;
- system/prompt/capsule version/hash;
- LoRA/adapter names, revisions and merge state;
- embedding/reranker/classifier versions;
- feature extractor/backbone version;
- calibration version;
- model routing decision;
- model warm/cold state.

### 6.5 Frank cognitive-state metadata

Capture the complete applicable state at episode start/end and important internal checkpoints:

- semantic epoch;
- graph epoch;
- memory epoch;
- state/basis epoch;
- cycle/episode/signal identity;
- boot/restart sequence;
- current self/world/goal/task state refs;
- workspace candidate universe;
- selected coalition/focus;
- GWT ignition state/threshold/hysteresis;
- receiver delivery/reconstruction/use/local-effect receipts;
- recurrence count/budget;
- re-entry class/identity/delay/accepted state;
- loop-regime readout;
- cross-loop gain/coupling/delay/inhibition;
- residual pressure/error/uncertainty;
- state delta norm;
- novelty/reseed state;
- historical E-PQ values;
- Thalamus channel gains/habituation;
- NAcc phasic/tonic state;
- Amygdala category/urgency;
- ACC/conflict state where available;
- experience-vector identity/novelty annotation;
- active memory/retrieval set;
- active Hyperposition alternatives;
- Needle route/confidence/abstention/tool candidate state;
- current effect/authority state;
- current control intervention/damping/rescue state.

### 6.6 Workload / test metadata

- suite/test/fixture ID;
- benchmark protocol version;
- workload/domain/task class;
- input identity/hash;
- input length/size/complexity;
- expected output/ground truth provenance;
- train/dev/held-out/OOD class;
- source dataset/version;
- randomized seed(s);
- warmup count;
- repetition count;
- concurrency level;
- arrival/request rate;
- timeout/retry policy;
- order/randomization;
- perturbation/intervention identity;
- lesion/rescue identity;
- truthful/shuffled/no-reentry control identity;
- baseline/candidate pairing identity;
- cache state;
- DB/state snapshot identity;
- network condition where relevant;
- external provider/model/API version and response receipt where applicable.

### 6.7 Time metadata

- UTC timestamp;
- local timestamp/timezone;
- monotonic start/end clocks where available;
- duration;
- sequence number;
- run order;
- cold/warm/restart phase;
- time since boot;
- time since model/component load;
- time since state migration;
- time since last failure/recovery;
- benchmark window identity.

### 6.8 Provenance / evidence metadata

- worker/organ/provider/model/session/node provenance;
- tool/action identity;
- exact command/workflow/job ID;
- GitHub Actions run/job/runner identity when used;
- log/artifact references;
- raw trace references;
- DB snapshot/checkpoint references;
- source citation/URL/repo/paper refs when external evidence is involved;
- evidence class;
- verification class;
- confidence;
- known confounders;
- exclusions;
- data-quality flags;
- missing-field reasons;
- checksum/content hash.

## 7. Sampling and statistical rules

- Never compare one lucky run against one unlucky run when repeated measurement is feasible.
- Preserve raw per-run rows, not only aggregates.
- Report sample count.
- Report distribution/quantiles, not only mean.
- Use matched inputs/seeds/snapshots when comparing original versus successor.
- Randomize or counterbalance execution order when order/cache/thermal effects may bias results.
- Separate cold-start and steady-state results.
- Separate deterministic fixture performance from live/noisy workloads.
- Report confidence intervals or uncertainty bands when sample size permits.
- Preserve outliers with annotations; do not silently trim them.
- Record benchmark failures as data.

## 8. Baseline comparison gate

Every proposed successor must be compared against the exact applicable Original Baseline under matched conditions.

Required comparison classes:

- `ORIGINAL -> RETAIN`;
- `ORIGINAL -> FUSE`;
- `ORIGINAL -> EMERGENT_DISTRIBUTE`;
- `ORIGINAL -> CLAY_REDESIGN_CANDIDATE`;
- simpler baseline where meaningful;
- lesion/no-component control;
- rescue control;
- held-out/OOD transfer.

For every comparison produce delta vectors for at least:

`latency, functional_correctness, reliability, recovery, resource_cost, causal_signature, GWT/reentry_behavior, integration_cost`.

No successor is called better from one scalar alone.

## 9. Promotion law

A historical organ/module boundary may disappear only when the successor:

1. preserves or intentionally improves the required function;
2. is no worse beyond accepted tolerances on critical accuracy/correctness;
3. is no worse beyond accepted tolerances on reliability/recovery;
4. has measured latency/resource tradeoffs;
5. preserves required causal/GWT/re-entry signatures or demonstrates a better validated replacement;
6. survives matched lesion/rescue and replay;
7. survives held-out/OOD tests where applicable;
8. has complete lineage and metadata sufficient to reproduce the conclusion.

If a candidate is faster but materially less reliable/correct, or more accurate but catastrophically slower/less recoverable, preserve it as a tradeoff candidate rather than silently promote it.

## 10. Binary-freeze linkage

The final one-module/binary FRANK configuration may only freeze from organ/module successors whose baseline comparison packages are complete enough for the selected architecture. `BinaryFreezeCandidate` must reference every relevant Original Baseline and successor comparison receipt.

Binary compilation itself must be benchmarked again because changed timing, memory layout, scheduling, inlining or coupling can alter the measured regime.

## 11. Storage and replay

Persist:

- immutable raw run records;
- normalized benchmark rows;
- aggregate summaries;
- environment/build/model metadata;
- traces/logs/artifacts;
- state snapshots/checkpoints;
- baseline/successor pairing identities;
- comparison reports;
- negative results;
- promotion/rejection decision receipts.

UnifiedDB is the semantic/query authority; ClayGraph may project causal/dependency/topology relations. Physical storage may remain specialized where justified.

## 12. Hard invariants

- `NO_ORIGINAL_BASELINE -> NO_REPLACEMENT_CLAIM`.
- `UNKNOWN != ZERO`.
- `NOT_MEASURED != NO_DIFFERENCE`.
- `ONE_RUN != RELIABILITY`.
- `MEAN_LATENCY != TAIL_LATENCY`.
- `OUTPUT_EXISTS != FUNCTIONAL_EQUIVALENCE`.
- `SERVICE_UP != LEARNER_HEALTH`.
- `ACTIVITY != CLOSED_LOOP_REENTRY`.
- `SHARED_ANCESTRY != INDEPENDENT_REPLICATION`.
- every material metric retains complete available metadata and provenance.
