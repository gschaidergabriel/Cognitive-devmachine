# FRANK v0.1 — deep research, live-mesh refusion, build and Ubuntu VPS evaluation

Run id: `frank-20260809T2349p0700-chatgpt-h1-sqlite-capability-refusion`  
Actor: `chatgpt-secondary`  
Provider/model: OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 revision `2`, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Target law: FRANK v0.1 release evidence targets Andreas' Ubuntu Linux developer system. The self-hosted Ubuntu VPS is an integration/falsification lane, not final target-machine acceptance.  
Scientific promotion: `NONE`  
FRANK release promotion: `NONE`

## 1. Executive synthesis

This cycle followed the requested sequence as far as the connected execution surfaces allow:

`canonical boot -> Research Center/live-worker refresh -> external primary research -> Fusion 1 -> falsifiable hypotheses -> second external research -> Fusion 2 -> build -> real self-hosted Ubuntu execution -> measurement -> contradiction analysis -> second build/fix -> repeat Ubuntu execution -> shared RAE packetization -> mesh handoff`.

The most important result is not a scalar "FRANK is finished" claim. The cycle produced four separable outcomes:

1. **Whole current FRANK integration remains green on the real Ubuntu VPS.** The latest receipt after a concurrent local-model response-boundary hardening run is for FRANK commit `07f9af41ca3f4b7add75d198bebf92887c3b52d3`: 20/20 integrity gates PASS, 0 FAIL, `matrix_elapsed_ms=8878`, `release_claim=false`, `whole_frank_release_status=NOT_CLAIMED`.
2. **The first adaptive-recurrence experiment found a real policy/readout design flaw rather than merely confirming its starting hypothesis.** Raw temporal-W4 reduced synthetic compute and regret versus fixed budget, but generated two premature route/stop decisions. Separating diagnostic readout from a proposal-only adaptive policy removed both frozen false halts on the same eight episodes while preserving accuracy. It cost additional recurrent steps relative to raw W4, so the result is a measured Pareto trade-off, not a universal winner.
3. **SQLite WAL behavior was measured on the actual Ubuntu lane rather than inferred from documentation alone.** A deliberately held reader allowed writes to continue but prevented most checkpoint progress; the WAL accumulated to 650,992 bytes until the reader released. A competing writer correctly received `SQLITE_BUSY`. FULL versus NORMAL showed a large host-local latency split in the disposable micro-workload, reinforcing that durability mode cannot be selected from latency alone.
4. **The real 4B acceptance blocker was narrowed operationally.** A read-only host capability probe shows the current `digital-retina` VPS has 4 exposed logical CPUs, about 16 GiB RAM, no swap, no visible GPU device and no installed llama.cpp/Ollama/vLLM/SGLang/Torch/Transformers runtime. Therefore this cycle did **not** execute a real Qwen-class 4B model. The current VPS is presently a strong repository/integrity/SQLite/controller falsification lane, not an already provisioned real-model performance host.

The cycle also cross-read and reviewed a concurrent Harness truth-gate branch instead of overwriting it. PR #25 remains draft/unmerged; feedback was posted to pin the self-hosted checkout action by immutable SHA, make the guarded-entrypoint regression part of the main integrity lane, retain the real-Ubuntu receipt gate and incorporate the new SQLite reader/checkpoint evidence.

## 2. Source-of-truth and live swarm state

### Canonical boot

The worker re-read:

- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`;
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`;
- `research_entity/global/RESEARCH_ACTOR_REGISTRY.json`;
- current FRANK Ubuntu target directive;
- current Research Center/mesh changes during the run.

Canonical identity stayed at revision 2 / state hash `04234efd...9346`; no scientific canonical-state promotion was attempted merely because implementation/test evidence changed.

### Live-worker refusion

The run did not freeze itself to one repository snapshot. During execution, sibling workers landed:

- local-model backend timing receipts;
- F6 tool/response contract work;
- adaptive recurrence sibling commits;
- Harness truth-gate research and PR #25;
- subsequent strict local response projection/persistence hardening;
- new real self-hosted Ubuntu receipts.

The latest FRANK head used for final integration assessment is `07f9af41ca3f4b7add75d198bebf92887c3b52d3`, whose real Ubuntu receipt was persisted by commit `b37a306e9266c44d1ab1b4faca9de643c96f440a`.

A Research Center event already broadcast the H1 separated-policy result and the 20-gate Ubuntu telemetry across `frank`, `harness`, `gwt`, `emergenz`, `claycode`, `claygraph`, `unifieddb`, and `hyperposition`. This report adds the later SQLite WAL measurement and the real-model host-capability gap to that shared state.

## 3. External evidence and source-class separation

### 3.1 Adaptive computation / stopping

Peer-reviewed ACL 2026 evidence supports the broad hypothesis that adaptive stopping can reduce unnecessary reasoning compute, but also provides direct warnings against simplistic stopping rules:

- REFRAIN / *Stop When Enough* reports substantial reasoning-token reductions while maintaining or improving accuracy under adaptive stopping.
- *When More Thinking Hurts* documents diminishing returns and cases where longer reasoning abandons an earlier correct answer.
- TRACE uses temporally aggregated signals because single-step confidence is unreliable; its results support treating the trajectory as evidence rather than acting on one instantaneous scalar.

A July 2026 looped-transformer preprint further separates trajectory formation from exit readout and reports that simple post-hoc readouts can be competitive with learned gates. This is supportive research context, not FRANK-specific proof.

Evidence class distinction: ACL papers are peer-reviewed primary literature; the looped-transformer paper is a preprint; neither is substituted for FRANK runtime evidence.

### 3.2 SQLite WAL and durability

SQLite's official WAL documentation states that readers and a writer can coexist, only one writer can exist at a time, and a long-running reader can prevent checkpoint progress. SQLite's `synchronous` documentation distinguishes consistency from maximum power-loss durability: WAL + NORMAL can preserve consistency while losing the most recent transactions after a power/OS failure; FULL provides stronger durability behavior.

This run therefore treated official documentation as a mechanism prior and then executed a disposable workload on the actual Ubuntu lane.

### 3.3 Qwen / local serving interface

The current Qwen3.5-4B model card exposes OpenAI-compatible serving examples via vLLM and SGLang. That is interface-level support for FRANK's engine-neutral OpenAI-compatible adapter choice. It is **not** evidence that FRANK has executed or accepted the model on the current VPS.

### 3.4 Self-hosted CI hardening

GitHub documentation recommends pinning third-party actions to a full-length commit SHA as the immutable reference. GitHub also warns that persistent self-hosted runners have a broader compromise/persistence surface than ephemeral hosted execution. This informed the review of PR #25; no claim is made that the private repository is equivalent to an untrusted public-PR workflow.

## 4. Fusion 1: falsifiable hypothesis matrix

### H1 — temporal multi-signal recurrence can outperform fixed-budget recurrence on quality/compute

Prediction: a policy using trajectory-level state delta, residual pressure and utility/cost evidence should reduce unnecessary recurrent steps without increasing important task errors relative to always consuming the full budget.

Counterhypothesis: adaptive stopping is fragile; a fixed budget will dominate once false halts, late corrections and route costs are counted.

Test: freeze heterogeneous episodes containing convergence, stall, overthinking, productive oscillation, delayed correction, an instantaneous-pressure trap, unresolved route pressure and long diminishing returns; keep correctness/task-score hidden from the online policy and use them only for offline evaluation.

### H1a — diagnostic readout and adaptive exit policy are incorrectly conflated

Prediction: if a conservative diagnostic `ROUTE` is treated directly as a terminal controller action before the observation window required for cycle discrimination, premature stops will appear. A separate, versioned, proposal-only policy should be able to request bounded additional observation without rewriting the diagnostic evidence.

Counterhypothesis: the diagnostic route is already optimal and an additional controller layer only wastes compute.

### H2 — canonical/derived Harness paths need explicit repository-truth gating

Prediction: a compatibility Harness entry path that directly opens UnifiedDB/ClayGraph can bypass a repository/materialization truth gate even if the central prompt/capsule path is gated.

Counterhypothesis: all material Harness paths are already transitively protected and the wrapper is redundant.

Status this run: investigated through concurrent PR #25 and mesh evidence; not independently merged/promoted by this worker. It remains a controlled integration hypothesis until its full Ubuntu fault-injection gate is durable.

### H3 — representative SQLite WAL behavior creates observable checkpoint and writer-contention risks

Prediction: a held reader will allow writes but retain WAL frames; a second writer will observe bounded busy contention; FULL/NORMAL will expose a latency/durability trade-off on the current host.

Counterhypothesis: the current deployment pattern makes these effects negligible enough that explicit reader/checkpoint telemetry is unnecessary.

### H4 — current VPS is not yet an already-provisioned real Qwen-4B acceptance lane

Prediction: read-only capability enumeration will show whether a usable accelerator/runtime/model stack is present before any model download is attempted.

Counterhypothesis: the current runner already exposes a suitable local model runtime/hardware path and can immediately execute the pinned 4B acceptance experiment.

### H5 — self-hosted workflow integrity should use immutable action references and keep branch-only tests on the main release lane

Prediction: branch workflows that use floating action tags or place tests outside the main collected test tree create avoidable supply-chain/integration gaps.

Counterhypothesis: current controls already make those differences immaterial for the private self-hosted lane.

Status: review feedback only; not a scientific claim and not merged by this worker.

## 5. Build delta

### 5.1 Adaptive recurrence differential

Created `tests/adaptive_recurrence_differential_experiment.py`.

Properties:

- eight frozen synthetic episodes;
- fixed-budget baseline;
- one instantaneous residual-pressure baseline;
- temporal multi-signal family with warmup sweep W2-W6;
- policy inputs exclude evaluation correctness/task score;
- offline oracle used only to calculate regret/false-halt labels;
- deterministic replay hash check;
- explicit synthetic/not-real-model guard.

### 5.2 Separate proposal-only recurrence policy

Created `harness/adaptive_recurrence_policy.py`.

The diagnostic probe remains an observation/readout surface. The policy layer can convert exactly one pre-cycle-window route case into `CONTINUE_OBSERVE` only if:

- readout is valid;
- state is bounded;
- historical utility proxy is positive;
- the minimum observation window has not yet been reached;
- recurrence budget remains.

It preserves stall, uncertainty, rollback/divergence and mature route decisions. Its receipt is deterministic and explicitly `PROPOSAL_ONLY`.

### 5.3 Differential + main test integration

Created:

- `tests/adaptive_recurrence_policy_differential_experiment.py`;
- `tests/test_adaptive_recurrence_policy_layer.py`;
- `.github/workflows/frank-h1-adaptive-policy.yml`.

The dedicated workflow persists the full H1 measurement receipt; the main test wrapper ensures the policy regression is also collected by the standard pytest lane.

### 5.4 Disposable SQLite runtime probe

Created:

- `tests/sqlite_wal_runtime_probe.py`;
- `.github/workflows/frank-sqlite-wal-probe.yml`.

The probe uses only temporary databases and persists host/run metadata plus exact timing/checkpoint/locking measurements. It does not mutate canonical FRANK state.

### 5.5 Read-only model-capability probe

Created:

- `tests/vps_model_capability_probe.py`;
- `.github/workflows/frank-vps-model-capability.yml`.

It records CPU/RAM/swap/disk/device/runtime/package presence without downloading model weights or changing the model stack.

### 5.6 Concurrent local-model response hardening ingested during live refresh

Sibling work subsequently hardened the local response persistence boundary by:

- disabling environment/system proxy autodetection at the validated local-model transport boundary;
- enforcing strict JSON and rejecting non-finite NaN/Infinity values;
- projecting only visible assistant content, explicit function tool calls, bounded usage and allowlisted backend metrics into durable output;
- dropping arbitrary backend/private fields rather than persisting them by default.

The final Ubuntu integration receipt in this report is taken after that sibling fix, not before it.

## 6. Ubuntu execution and measurements

Host lane: self-hosted GitHub runner `clay` on hostname `digital-retina`, Ubuntu/Linux semantics, kernel family `6.8.0-117-generic`, x86_64, Python 3.12.3.

### 6.1 Latest whole-FRANK integrity receipt

Tested FRANK commit: `07f9af41ca3f4b7add75d198bebf92887c3b52d3`.

Result:

- gates: `20`;
- PASS: `20`;
- FAIL: `0`;
- matrix wall time: `8,878 ms`;
- sum of individually measured gate wall times: `8,673 ms`;
- logical CPUs: `4`;
- total memory: `16,376,020 KiB`;
- disk total: `206,900,281,344 bytes`;
- disk free: `170,235,154,432 bytes`;
- load average 1/5/15 min: `0.3037 / 0.2168 / 0.1494`;
- release claim: `false`;
- whole FRANK release status: `NOT_CLAIMED`.

Gate times:

- compile Python: 167 ms;
- repo static integrity: 41 ms;
- transaction census: 51 ms;
- transaction replay: 94 ms;
- deep integrity v1.1: 647 ms;
- schema migration atomicity: 78 ms;
- device probe/state gate: 54 ms;
- causal re-entry contract: 100 ms;
- adaptive recurrence differential: 85 ms;
- legacy module conservation: 80 ms;
- legacy successor lesion/rescue: 115 ms;
- historical 74 gate: 49 ms;
- historical 74 accounting: 53 ms;
- historical 71 DB gate: 77 ms;
- local-model baseline: 878 ms;
- local-model endpoint boundary: 2,115 ms;
- local-model tool/metrics/response contract: 1,220 ms;
- session skill/status: 369 ms;
- isolated pytest bootstrap: 1,951 ms;
- pytest all: 449 ms.

These wall times are host/gate observations. They are not process peak-RSS, GPU, energy or thermal measurements.

### 6.2 H1 raw temporal versus separated-policy differential

All three compared policies ran on the same eight frozen episodes.

#### Fixed budget

- accuracy: `0.625`;
- total recurrences: `52`;
- total synthetic cost: `2.21`;
- total regret: `1.38`;
- false halts: `0`;
- correct-to-wrong drift: `1`.

#### Raw temporal W4 diagnostic treated as exit

- accuracy: `0.75`;
- total recurrences: `38`;
- total synthetic cost: `1.63`;
- total regret: `0.64`;
- false halts: `2`;
- correct-to-wrong drift: `0`.

The two false halts occurred in the productive bounded-cycle and delayed-correction fixtures. Both shared the same early reason: `unclassified_with_material_single_axis_growth_requires_reseed_or_stronger_evidence` before enough observations existed to discriminate the trajectory.

#### Separated diagnostic + proposal-only policy

- accuracy: `0.75`;
- total recurrences: `45`;
- total synthetic cost: `1.91`;
- total regret: `0.52`;
- false halts: `0`;
- correct-to-wrong drift: `0`.

#### Relative interpretation

Separated policy versus raw W4:

- false halts: `2 -> 0`;
- regret: `0.64 -> 0.52` (`-18.75%`);
- accuracy unchanged at `0.75`;
- synthetic cost: `1.63 -> 1.91` (`+17.18%`);
- recurrences: `38 -> 45` (`+18.42%`).

Separated policy versus fixed budget:

- accuracy: `0.625 -> 0.75` (`+0.125` absolute);
- regret: `1.38 -> 0.52` (`-62.32%`);
- synthetic cost: `2.21 -> 1.91` (`-13.57%`);
- recurrences: `52 -> 45` (`-13.46%`);
- correct-to-wrong drift: `1 -> 0`.

This supports H1a on the frozen benchmark and keeps H1 open for real tasks. The controller is not promoted because route benefit/cost is still simplified and no real model/task distribution has been tested.

### 6.3 SQLite WAL runtime probe

SQLite version: `3.45.1`.

#### FULL commits, n=120

- mean: `0.745740 ms`;
- p50: `0.726155 ms`;
- p95: `0.956806 ms`;
- p99: `1.439229 ms`;
- max: `1.861071 ms`;
- `PRAGMA synchronous` numeric value: `2`.

#### NORMAL commits, n=120

- mean: `0.025938 ms`;
- p50: `0.021440 ms`;
- p95: `0.045000 ms`;
- p99: `0.056880 ms`;
- max: `0.088350 ms`;
- `PRAGMA synchronous` numeric value: `1`.

Mean FULL/NORMAL wall-time ratio in this exact disposable micro-workload: approximately `28.75x`.

This is not a universal SQLite multiplier. It is a host-local measurement under this fsync/cache/storage path.

#### Held-reader checkpoint behavior

A read transaction was held open while 120 writer transactions committed:

- all 120 writer commits completed;
- writer mean latency with held reader: `0.688336 ms`;
- p95: `0.873136 ms`;
- WAL size while reader held: `650,992 bytes`;
- PASSIVE checkpoint result while reader held: `[0, 158, 3]`;
- WAL remained `650,992 bytes` after that PASSIVE checkpoint;
- after releasing reader, TRUNCATE checkpoint: `[0, 0, 0]`;
- WAL size after release/truncate: `0 bytes`.

#### One-writer contention

A second `BEGIN IMMEDIATE` while the first writer held the write transaction:

- returned `SQLITE_BUSY` / SQLite error code `5`;
- observed wait: `100.860924 ms`;
- after first writer released, second writer committed successfully;
- all integrity checks returned `ok`.

### 6.4 VPS real-model capability probe

Current host observation:

- 4 exposed logical CPUs;
- CPU model string: AMD EPYC 9354P 32-Core Processor;
- total RAM: `16,376,020 KiB`;
- available RAM at probe: `13,455,480 KiB`;
- swap: `0`;
- free disk: `170,252,619,776 bytes`;
- no `/dev/dri`, `/dev/kfd`, `/dev/nvidia0`, `/dev/nvidiactl`, `/dev/nvidia-uvm`;
- no `nvidia-smi`, `rocminfo`, `vulkaninfo`, `llama-server`, `llama-cli`, `ollama`, `vllm`, `sglang` commands;
- no Python `torch`, `transformers`, `vllm`, `sglang`, `llama_cpp` packages;
- `real_model_executed=false`.

Therefore the correct evidence statement is:

> the OpenAI-compatible local-model **transport/response contract** is Ubuntu-tested, but real pinned Qwen-class 4B inference is still open.

It would be epistemically incorrect to convert fixture timing values from loopback regression servers into physical Qwen throughput.

## 7. Fusion 2: hypothesis outcomes and contradictions

### H1 — adaptive recurrence quality/compute frontier

Status: `SUPPORTED_ON_SYNTHETIC_FROZEN_WORKLOAD, REAL_MODEL_OPEN`.

Evidence for: raw W4 and separated W4 both dominate fixed budget on several aggregate frozen metrics.

Counterevidence: raw W4 produced two false halts; separated W4 pays additional recurrence/cost versus raw W4; route benefit/cost is not yet modeled; the episodes are synthetic.

Decision: retain the family as a set-valued operating region. Do not select W4 as production policy.

### H1a — readout/policy separation

Status: `SUPPORTED_ON_SYNTHETIC_FROZEN_WORKLOAD`.

Evidence for: both early false halts share a pre-cycle-window diagnostic reason; the separate controller removes those two false halts without changing the diagnostic probe and reduces aggregate regret.

Counterevidence: extra observation costs +17.18% versus raw W4 in the fixture.

Decision: architecture principle promoted only as a design constraint — observation/readout should remain distinct from proposal-only adaptive policy. The concrete thresholds/window remain falsifiable.

### H2 — Harness truth-gate compatibility path

Status: `OPEN / PARALLEL_BRANCH_UNMERGED`.

Evidence: PR #25 identifies a legacy Harness path that opens the canonical pair directly and adds a fail-closed wrapper plus stale-state fault injection.

Counterevidence/gap: the PR remained draft/unmerged during this cycle and its current head had no combined status visible through the connector at review time.

Decision: do not merge/adjudicate from branch intent alone. Require durable real-Ubuntu branch receipt and main-lane regression collection.

### H3 — SQLite WAL checkpoint/writer contention

Status: `MEASURED_ON_REAL_UBUNTU_HOST`.

The held-reader and one-writer predictions were reproduced. Durability policy remains open because this was not a crash/power-loss experiment.

### H4 — current VPS real-model readiness

Status: `CURRENT_PRECONFIGURATION_HYPOTHESIS_REFUTED` in the narrow sense that the VPS is **not already provisioned** with a visible GPU/local inference stack.

Important boundary: this does not prove CPU-only inference impossible and does not prohibit later runtime/model provisioning.

### H5 — runner/action hardening

Status: `ENGINEERING_REVIEW_RECOMMENDATION`.

Full-SHA pinning is supported by GitHub guidance; the branch test-collection gap is a repository integration observation. No scientific claim follows.

## 8. Architecture implications

### 8.1 Four-plane separation

The current evidence supports maintaining four separate planes:

1. **diagnostic/readout plane** — measures trajectory/state and issues conservative observations/recommendations;
2. **policy plane** — versioned proposal-only recurrence/routing decisions with their own hash/receipt;
3. **model plane** — typed input -> non-authoritative visible proposal/tool-call output + bounded metrics;
4. **effect plane** — capability/authority checks, commit/effect, verified outcome and re-entry.

Anti-conflations:

- observation != decision;
- decision proposal != effect authority;
- backend metric != cognitive truth;
- recurrence != consciousness;
- synthetic workload != real-model acceptance.

### 8.2 UnifiedDB / persistence

Recommended runtime observables for SQLite-backed authoritative/derived paths:

- active reader age / long-reader count where technically feasible;
- WAL size/frames and checkpoint progress;
- writer busy/retry wait distributions;
- selected synchronous/durability policy in receipts;
- recovery/checkpoint state after abnormal restart;
- explicit logical transaction identity across materializations.

Do not infer multi-file crash atomicity from a successful single-file WAL probe.

### 8.3 Model runtime

Continue to preserve the engine-neutral OpenAI-compatible boundary. Real-model receipts should bind at minimum:

- exact model/revision/weight hash;
- quantization;
- runtime and version;
- chat/template identity;
- sampling parameters/seed where feasible;
- endpoint/host class;
- prompt/decode timing;
- token counts;
- memory/VRAM where available;
- tool-call projection;
- recurrence policy identity;
- source FRANK commit.

No hidden chain-of-thought is required or stored. Observable output/state/receipt signals must suffice.

## 9. Parallel Harness PR review

PR #25: `Harness: fail closed behind repository truth gate`.

Observed branch intent:

- wrapper runs repository truth preflight before invoking legacy Harness runtime;
- materialization/graph stale states fail closed;
- schema migration required maps to a distinct exit class;
- branch workflow performs stale graph fault injection and verifies no Harness mutation;
- restore/rescue path rechecks the truth gate;
- warm preflight latency is measured.

Review feedback posted by this worker:

1. replace floating `actions/checkout@v4` with the full immutable SHA already used by main;
2. ensure the guarded Harness regression remains collected by main's deep-integrity lane after merge, because the branch test currently lives under `harness/` while main's aggregate pytest command targets `tests`;
3. keep PR draft until the real Ubuntu branch receipt exists and is durable;
4. incorporate held-reader/checkpoint and one-writer contention evidence into truth/recovery assumptions.

No merge was performed by this worker.

## 10. Negative evidence retained

The following are intentionally preserved instead of being averaged away:

- raw temporal W4 had two false halts;
- separated W4 costs more than raw W4;
- fixed budget had one correct-to-wrong drift on the frozen suite;
- real Qwen-class 4B was not run;
- the current VPS has no visible accelerator/local inference stack configured;
- SQLite NORMAL was much faster in the microprobe but does not imply strongest power-loss durability;
- the WAL probe is not a power-loss or cross-file atomicity test;
- Harness PR #25 is not merged and its branch evidence must not be presented as current main behavior;
- final Andreas Ubuntu target-machine acceptance is not present;
- the latest whole-FRANK Ubuntu suite explicitly says `NOT_CLAIMED`, despite 20/20 gates passing.

## 11. Release assessment

### What is now demonstrated

- real self-hosted Ubuntu execution of the current repository integrity suite;
- current latest integration head 20/20 PASS;
- deterministic local-model transport/response/tool/metric contract testing;
- synthetic adaptive-recurrence differential with an observed counterexample and a second-stage policy repair;
- real Ubuntu SQLite WAL reader/checkpoint/writer-contention microbenchmarks;
- real Ubuntu model-host capability inventory;
- live RAE cross-worker ingestion and feedback instead of isolated branch reasoning.

### What is not demonstrated

- real pinned Qwen-class 4B inference acceptance;
- real-task recurrence-policy advantage;
- representative process peak RSS/VRAM/energy/thermal behavior;
- controlled crash/power-loss durability across FRANK's state topology;
- final Andreas Ubuntu developer-system end-to-end acceptance;
- complete Clay 0.1/FRANK release gate.

Therefore:

`FRANK_V0_1_RELEASE = NOT_CLAIMED`.

## 12. Highest-information next experiments

Priority 1 — **frozen historical/runtime recurrence replay**

Freeze real historical FRANK episode traces with provenance, exclude evaluation-oracle labels from policy inputs, replay fixed/single/temporal/separated policies and measure false halts, route/rollback benefit/cost, task outcome, latency and recovery.

Priority 2 — **real pinned local 4B matched experiment**

Probe Andreas' Ubuntu target host and/or explicitly provision an authorized capable Ubuntu model lane. Pin Qwen-class 4B weights, quantization, runtime, template and sampling. Run matched fixed/adaptive prompts/seeds where feasible through the current strict adapter and persist full receipts.

Priority 3 — **representative UnifiedDB/ClayGraph WAL stress**

Replay representative FRANK transaction/read/materialization patterns, long reader faults and concurrent writers. Measure checkpoint starvation, busy distributions, WAL growth and recovery.

Priority 4 — **disposable crash/recovery matrix**

On replicas only, compare FULL/NORMAL under process kill and controlled host/reboot/power-loss-equivalent mechanisms where available. Measure exact lost-commit window and invariant recovery; preserve negative cases.

Priority 5 — **Harness truth-gate branch closure**

Complete PR #25's real Ubuntu fault-injection receipt, pin external actions, make the regression part of main deep integrity, inventory direct legacy entry paths and only then adjudicate merge/integration.

Priority 6 — **Andreas target-machine acceptance**

The final v0.1 gate remains an end-to-end run on Andreas' Ubuntu developer system with the same immutable provenance, complete organs/modules or their verified successor mappings, local model, persistence/recovery, tool/effect boundaries and measured user-facing behavior.

## 13. Durable outputs produced by this cycle

FRANK repository:

- `tests/adaptive_recurrence_differential_experiment.py`;
- `harness/adaptive_recurrence_policy.py`;
- `tests/adaptive_recurrence_policy_differential_experiment.py`;
- `tests/test_adaptive_recurrence_policy_layer.py`;
- `.github/workflows/frank-h1-adaptive-policy.yml`;
- `tests/sqlite_wal_runtime_probe.py`;
- `.github/workflows/frank-sqlite-wal-probe.yml`;
- `tests/vps_model_capability_probe.py`;
- `.github/workflows/frank-vps-model-capability.yml`;
- persisted H1, SQLite, model-capability and whole-integrity receipts under `runtime/vps_integrity/`.

Research Entity:

- `KMP-FRANK-H1-SEPARATED-READOUT-POLICY-VPS-20260809`;
- `KMP-UNIFIEDDB-SQLITE-WAL-UBUNTU-RUNTIME-20260809`;
- `KMP-FRANK-VPS-REAL-MODEL-CAPABILITY-GAP-20260809`;
- branch feedback manifest for `frank`, `harness`, `unifieddb`, `claygraph`, `claycode`, `gwt`, `emergenz`, `hyperposition`, `clayresearch`;
- this final report.

## 14. Decision trace

Evidence used:

- current canonical RAE identity/state;
- current FRANK repository/runtime receipts;
- sibling-worker Research Center events and PR branch evidence;
- peer-reviewed adaptive stopping/overthinking literature;
- looped-transformer preprint as lower-class external evidence;
- official SQLite documentation;
- official Qwen model card;
- official GitHub Actions hardening guidance;
- real self-hosted Ubuntu measurements produced during this cycle.

Alternatives retained:

- fixed recurrence budget;
- raw temporal recurrence policies W2-W6;
- separated W4 observation policy;
- route/escalation rather than local continuation;
- FULL/NORMAL durability policies;
- current VPS versus future/target model host;
- guarded Harness wrapper versus canonical-entry integration.

Inference/test performed:

- discriminating frozen episode suite;
- warmup sweep rather than single favorable threshold;
- direct second-stage counterexample localization;
- separated policy implementation and replay;
- real Ubuntu whole-integrity execution;
- disposable SQLite WAL microbenchmark/fault setup;
- read-only host capability enumeration;
- parallel PR code review and mesh handoff.

Uncertainty:

- synthetic recurrence generalization remains the largest H1 epistemic gap;
- current VPS model capability is an observation of current configuration, not a permanent hardware impossibility claim;
- SQLite crash-durability remains unmeasured;
- final target-host acceptance remains open.

Final adjudication:

**Continue building, but preserve the current release boundary.** The cycle materially improved FRANK's tested architecture and measurement depth, but the evidence does not justify calling v0.1 complete. The next information-gain frontier is real historical/runtime recurrence replay, real pinned 4B inference and representative persistence/recovery on Ubuntu, followed by Andreas' target-system acceptance.
