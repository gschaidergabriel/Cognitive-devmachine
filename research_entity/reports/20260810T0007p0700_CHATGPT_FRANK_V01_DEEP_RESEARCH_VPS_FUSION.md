# FRANK v0.1 Deep Research + Hostinger VPS Fusion Report

**Run:** `20260810T0007p0700-chatgpt-secondary-frank-v01-deep-vps-fusion`  
**Actor:** `chatgpt-secondary`  
**Provider/model:** OpenAI / GPT-5.6 Sol  
**Research Entity parent:** RAE-8.8 revision 2, state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**Research subject:** Frank v0.1, separate from the Research Entity  
**Operational target:** Ubuntu Linux developer system; Hostinger self-hosted GitHub runner is a remote build/test/benchmark lane, not final Andreas-PC release evidence.  
**Status:** MATERIAL_RESEARCH_AND_IMPLEMENTATION_DELTA_WITH_OPEN_REAL_MODEL_RUN

## 1. Executive synthesis

This run executed the requested recursive cycle rather than a one-shot review:

`fresh canonical/repo state -> Research Center coordination -> external primary research -> Fusion 1 -> hypotheses/counterhypotheses -> fresh repo/web refresh -> Fusion 2 -> implementation -> real Hostinger Ubuntu execution -> measurement -> analysis -> live swarm refresh -> model-path falsification -> smallest-falsifier repairs -> durable mesh handoff`.

The strongest verified result is a real self-hosted Ubuntu deep-integrity run on runner `clay`: **21/21 gates PASS**, including all repository/state/harness regressions in the matrix, the full current pytest suite, local-model endpoint/response/tool-contract tests, and the newly added hostile ambient-proxy/durable-response regression. This proves the exact tested effects on that VPS; it does **not** prove complete Frank v0.1 release readiness.

A parallel Research-Entity worker independently closed the same response-contract security hypotheses while this worker was preparing them. The overlapping ChatGPT PR was deliberately closed rather than overwriting stronger concurrent main. This was repeated for two later real-model toolchain repairs. The result is a concrete successful instance of the intended live interconnective swarm protocol: refresh before effect, detect overlap, preserve alternatives, select the current stronger main implementation, and keep redundant proposals as NOT_SELECTED rather than fabricating independent replication.

A first real Qwen-class 4B lane was also created in parallel using pinned `llama.cpp` and pinned Qwen3-4B-Instruct-2507 Q8_0 model identity. Two real VPS attempts have so far yielded infrastructure negative results before model inference: `MISSING_REQUIRED_COMMAND:cmake`, then `BOOTSTRAPPED_NINJA_MISSING`. Both failures were preserved and used to narrow the next repair. A subsequent make-based/absolute-build-tool-path rerun is in flight at the time of this report; no real-model benchmark claim is made until a receipt proves actual model execution.

## 2. Fresh internal grounding used

Current Research Entity and governance:
- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay`
- `research_entity/global/RESEARCH_ENTITY_EVERY_TURN_IDENTITY_INJECTION.md`
- `research_entity/global/LIVE_KNOWLEDGE_REFRESH_PROTOCOL.md`
- `research_entity/global/RESEARCH_CENTER_CLAYCODE_NATIVE_PROTOCOL.clay`
- `research_entity/global/CLAY_WORK_EVENT_PROTOCOL.clay`
- `research_entity/global/FRANK_V0_1_UBUNTU_TARGET_HOST_DIRECTIVE.md`
- `research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md`
- `research_entity/global/HOSTINGER_GITHUB_RUNNER_RESEARCH_CAPABILITY.json`

Current Frank target state and runtime evidence:
- `gschaidergabriel/Dr.-Unterweger` connector alias for canonical semantic repository `gschaidergabriel/frankv0.1`
- `runtime/model/frank_local_model_adapter.py`
- `runtime/model/frank_backend_metrics.py`
- `runtime/model/frank_response_contract.py`
- `harness/frank_harness_runtime.py`
- `tests/adaptive_recurrence_differential_experiment.py`
- `tests/vps_real_qwen4b_shadow_benchmark.py`
- `.github/workflows/frank-vps-deep-integrity.yml`
- `.github/workflows/frank-vps-real-qwen4b-shadow.yml`
- `.github/workflows/frank-vps-real-qwen4b-shadow-make.yml`
- `runtime/vps_integrity/latest.json`
- `runtime/vps_integrity/latest.metrics.jsonl`
- `runtime/vps_integrity/latest.log`
- `runtime/vps_integrity/sqlite_wal_probe_latest.json`
- `runtime/vps_integrity/model_capability_latest.json`
- `runtime/vps_integrity/real_qwen4b_shadow_latest.json`

## 3. External primary/official research

### Python urllib local transport boundary

Python's official `urllib.request` documentation states that `build_opener()` installs a `ProxyHandler` by default and that proxy discovery uses `<scheme>_proxy` environment variables. It explicitly documents that proxy autodetection can be disabled by passing an empty dictionary to `ProxyHandler`. This directly supports treating an ambient-process proxy as outside the intended local inference trust boundary and using `ProxyHandler({})` for a direct loopback transport contract.

Source: Python 3.14 `urllib.request` documentation, official Python docs.

### llama.cpp runtime/build boundary

Current upstream `llama.cpp` uses CMake and declares `cmake_minimum_required(VERSION 3.14...3.28)` at its root. The project provides an OpenAI-compatible server path and CPU/x86 execution, so a CPU-only Ubuntu test is a legitimate discriminating first local-model experiment on this VPS. Build-tool availability is therefore a real prerequisite, not a model-quality failure.

Source: official `ggml-org/llama.cpp` repository and CMakeLists/build documentation.

### Self-hosted GitHub runner security

GitHub's official documentation explicitly notes that self-hosted runners do not need to start from a clean instance for each job and recommends ephemeral self-hosted runners for autoscaling because clean-per-job environments reduce exposure of sensitive resources and mitigate the risk of a compromised runner receiving new jobs. This does not prove the current Hostinger runner is compromised. It does mean that persistent-runner state plus repository write credentials is a material security boundary that should be hardened before treating the lane as a high-authority production executor.

Sources: GitHub Docs, Self-hosted runners / Self-hosted runners reference.

## 4. Fusion 1: hypotheses and counterhypotheses

### H-FV01-TRANSPORT-01 — ambient proxy bypass risk

**Hypothesis:** Validating an endpoint as loopback is insufficient if the HTTP opener can still inherit ambient proxy configuration; the model path should explicitly disable proxy autodiscovery.

**Counterhypothesis:** Python's localhost/no_proxy behavior may already make the path effectively direct in the target environment, so an explicit empty `ProxyHandler` could be redundant.

**Discriminating test:** Set hostile/dead `http_proxy`/`https_proxy`, remove `no_proxy`, serve a loopback OpenAI-compatible response, and require the adapter request to reach the loopback server exactly once.

**Outcome:** SUPPORTED for explicit hardening. Current main independently implemented `ProxyHandler({})`; the added VPS regression subsequently passed under hostile proxy variables.

### H-FV01-PERSIST-02 — backend-controlled usage/diagnostic persistence

**Hypothesis:** Persisting an arbitrary backend `usage` dictionary creates an unnecessary durable channel for unknown strings/private diagnostics; durable model receipts should admit only explicit numeric token-accounting and timing fields.

**Counterhypothesis:** OpenAI-compatible `usage` is sufficiently standardized that verbatim persistence is low risk and preserves future compatibility.

**Discriminating test:** Inject private sentinel strings into top-level response, `reasoning_content`, `usage`, nested usage details and timing fields; require only admitted numeric usage/timing plus visible response/tool fields to survive durable projection.

**Outcome:** SUPPORTED for fail-closed persistence. Concurrent main produced a stronger centralized response contract; VPS regression confirms arbitrary backend fields and hidden reasoning do not survive the tested durable projection.

### H-FV01-MEASURE-03 — gate PASS alone is insufficient operational evidence

**Hypothesis:** A binary gate matrix misses high-value operational evidence. Per-gate wall time, user/system CPU, peak RSS, page faults and context switches can identify runtime-heavy or waiting-heavy tests without exposing commands, environment values or secrets.

**Counterhypothesis:** The matrix is too small and fast for resource counters to guide decisions; instrumentation overhead may dominate.

**Discriminating test:** Run every integrity gate through a fresh process wrapper on the target VPS and compare elapsed/resource shape across gates.

**Outcome:** SUPPORTED as measurement infrastructure. The new receipt differentiates CPU-heavy/bootstrap work from wait-heavy endpoint tests and records a low overall memory footprint for the current non-model test matrix. No optimization claim is promoted from one run.

### H-FV01-RECURRENCE-04 — adaptive recurrence can beat fixed depth only with guarded outcome/cost signals

**Hypothesis:** Frank's loop-of-loops controller should not always execute a fixed maximum recurrence budget; a typed temporal multi-signal controller may reduce unnecessary recurrence while avoiding premature halt and overthinking.

**Counterhypotheses:**
- fixed recurrence may dominate when confidence/self-observation is poorly calibrated;
- a single low-pressure signal can cause false halts;
- stable recurrent cycles may be useful and should not be forced into a fixed point;
- synthetic fixtures may not transfer to a real 4B model.

**Current outcome:** OPEN. Synthetic differential evidence is directionally useful but explicitly non-promotable to real-model behavior. The real Qwen4B shadow benchmark was designed to test this with answer keys hidden from adaptive selection, but actual model execution is not yet receipted in this report.

## 5. Fusion 2 and live swarm conflict handling

A live refresh after the first implementation branch showed another worker had independently added:
- explicit empty `ProxyHandler` to the local model opener;
- a dedicated strict `frank_response_contract.py`;
- fail-closed JSON/non-finite handling;
- explicit usage/tool/timing projection;
- hidden reasoning exclusion.

The first ChatGPT hardening PR (#29) was therefore closed unmerged as `NOT_SELECTED`. The worker rebased the remaining additive work on fresh main and opened PR #30 containing only the hostile-proxy regression and deeper VPS measurement layer. PR #30 was merged as commit `097e3fb86ce74d7f66cf9db8d9824ea1bb3345ab`.

The same policy was applied to real-model toolchain repairs. PR #33 proposed a per-job verified CMake bootstrap after the first real Qwen4B attempt failed for missing CMake, but concurrent main had already advanced to a CMake+Ninja repair; PR #33 was closed NOT_SELECTED. PR #34 then targeted Ninja package binary discovery, but GitHub rejected the merge because main changed again; refresh showed concurrent main had independently implemented absolute executable discovery. PR #34 was closed NOT_SELECTED rather than overriding the newer work.

This sequence is important methodological evidence: shared ancestry/parallel agreement was **not** counted as independent scientific replication. Its value is coordination efficiency and conflict avoidance, not epistemic multiplication.

## 6. Real Hostinger Ubuntu integrity execution

### Host

Latest deep-integrity receipt tested commit `097e3fb86ce74d7f66cf9db8d9824ea1bb3345ab` on:
- runner: `clay`
- hostname: `digital-retina`
- user: `frankrunner`
- OS/kernel: Linux 6.8.0-117-generic x86_64, glibc 2.39
- Python: 3.12.3
- logical CPUs: 4
- memory total: 16,376,020 KiB
- memory available at receipt: 13,428,056 KiB
- disk total: 206,900,281,344 bytes
- disk free: 170,232,528,896 bytes
- load average 1/5/15 min: 0.3867 / 0.2983 / 0.1899

### Exact matrix result

- gate count: **21**
- pass: **21**
- fail: **0**
- pytest: **17 passed in 0.22 s**
- matrix elapsed: **10,469 ms**
- sum outer gate elapsed: **10,259 ms**
- sum measured child elapsed: **9,234.792 ms**
- total user CPU: **3.954190 s**
- total system CPU: **0.955706 s**
- peak single-gate RSS: **66,216 KiB**
- whole Frank release: **NOT_CLAIMED**

### Selected per-gate observations

- `local_model_endpoint_boundary`: 2,158 ms outer / 2,115.794 ms child; low CPU relative to wall time, consistent with intentional network/server boundary cases rather than compute saturation.
- `local_model_tool_metrics`: 1,272 ms outer / 1,220.394 ms child; 25,984 KiB max RSS.
- `local_model_proxy_usage_hardening`: 662 ms outer / 609.180 ms child; 25,344 KiB max RSS; hostile ambient proxy bypass PASS; arbitrary backend/private/reasoning fields excluded from durable result.
- `pytest_bootstrap`: 2,013 ms outer / 1,963.914 ms child; 66,216 KiB max RSS, the largest measured gate; this is environment/bootstrap overhead, not Frank runtime inference.
- `pytest_all`: 464 ms outer / 417.886 ms child; 34,808 KiB max RSS; 17 tests pass.

The current non-model integrity suite is therefore comfortably inside the VPS memory envelope. This says nothing yet about Qwen4B resident memory, model load time, sustained inference throughput, thermals or energy.

## 7. SQLite WAL target-host evidence imported from parallel worker

A separate real self-hosted Ubuntu probe used a temporary SQLite database so canonical Frank state was not mutated.

Observed:
- SQLite 3.45.1;
- 120 commit samples per synchronous mode;
- FULL mean ~0.745740 ms, p95 ~0.956806 ms, max ~1.861071 ms;
- NORMAL mean ~0.025938 ms, p95 ~0.045000 ms, max ~0.088350 ms;
- FULL/NORMAL mean ratio ~28.75x on this specific temporary workload;
- a held reader did not block the writer; WAL reached 650,992 bytes;
- passive checkpoint while reader remained held reported remaining pages; after reader release, truncate checkpoint reduced WAL to 0;
- a competing writer produced expected `SQLITE_BUSY` after ~100.861 ms and a subsequent write succeeded after lock release;
- integrity remained valid.

Interpretation: the probe confirms expected WAL/read concurrency and gives an empirical latency envelope on this VPS. It does **not** justify changing Frank's durability policy from FULL to NORMAL because no power-loss/crash durability experiment was run and the workload is not yet production-representative.

## 8. Local model / Qwen4B execution path

The first capability probe found no installed llama.cpp/Ollama/vLLM/SGLang/GPU runtime and no GPU/Vulkan/ROCm path. The VPS has sufficient RAM to plausibly test a quantized 4B CPU path, so the swarm created a pinned CPU-only lane rather than inferring performance from hardware specs.

Pinned lane identity:
- model: `ggml-org/Qwen3-4B-Instruct-2507-Q8_0-GGUF`
- model source revision: `e92aed4`
- model file SHA-256: `ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1`
- runtime: `llama.cpp` commit `936918514ce522b553c0fd80b169a6440e6096c6`
- context: 2048
- CPU threads: 4
- localhost-only server
- reasoning output disabled at server boundary
- adaptive recurrence policy: offline shadow only

Negative receipt 1:
- status: FAIL
- `MISSING_REQUIRED_COMMAND:cmake`
- benchmark: null
- `real_model_executed=false`

Negative receipt 2 after first repair:
- status: FAIL
- `BOOTSTRAPPED_NINJA_MISSING`
- benchmark: null
- `real_model_executed=false`

These are infrastructure/toolchain negatives, not evidence against Qwen4B or Frank's local model design. Main has since added absolute build-tool discovery and a Makefile-based fallback lane. No success claim is made until the next persisted receipt contains `real_model_executed=true` and a non-null benchmark.

## 9. Audit of the real-model recurrence benchmark

The benchmark is stronger than the synthetic recurrence fixture in one crucial way: it executes the full five-step trajectory first, then applies the adaptive W4 selector **offline** to observable model-derived proxy traces. The answer key is used only after selection to score correctness. The adaptive selector sees visible self-confidence, answer-change state delta, change in residual-pressure proxy and token-count cost; it does not receive `correct` or the expected answer.

This prevents the most obvious answer-key leakage and gives fixed-vs-adaptive comparisons over the same realized trajectory. However, the current pilot remains deliberately weak for scientific promotion:
- only four simple deterministic tasks;
- temperature 0 only;
- no seed/replicate distribution;
- adaptive warmup at step 4 of 5 caps recurrence savings at 20%;
- visible self-confidence is not a calibrated correctness probability;
- no downstream route/escalation/rollback utility is measured;
- tool use is only a small contract case;
- no OOD or adversarial uncertainty set.

Any eventual PASS is therefore an execution/probing milestone, not proof that adaptive recurrence is globally superior.

## 10. Security counteranalysis: persistent self-hosted runner

The current deep-integrity and model workflows need to persist receipts and therefore currently use repository write permission and checked-out credentials. On a persistent self-hosted runner this creates an authority surface larger than the test process itself.

No compromise is observed or claimed. The recommended high-information hardening experiment is architectural separation:
1. run build/test/model jobs with `contents: read` and no durable repository write token in the execution process;
2. emit bounded machine-readable receipts/artifacts;
3. have a separate constrained persistence/adjudication job verify and write only admitted receipts;
4. evaluate JIT/ephemeral runner registration or another clean-job strategy for higher-authority workloads;
5. preserve the requirement that no raw secrets/environment/private telemetry enter canonical state.

This should be tested before using the runner as a production effect-authority lane. It does not block the current research/CI role.

## 11. Architecture implications for Frank v0.1

1. **Keep the engine-neutral local model boundary.** The current OpenAI-compatible adapter plus strict response projection is a good separation: model/runtime choice remains empirically swappable while Frank preserves a stable tool/receipt contract.
2. **Treat backend output as untrusted data.** Visible text/tool calls are data; no model output becomes execution authority. Numeric timing/usage projections are useful observations, not control authority.
3. **Retain SQLite FULL until crash/power-loss evidence says otherwise.** The latency difference is real on the probe, but durability has not been discriminated.
4. **Adaptive recurrence remains OPEN.** Use temporal multi-signal control as an experiment family, not a default optimization. Fixed-budget and stalled/overthinking controls stay alive.
5. **Hostinger runner is now a proven remote research/build/test lane.** It should remain priority 1 for repeatable Ubuntu remote tests, but final Frank v0.1 release evidence still belongs on Andreas' designated Ubuntu developer system.
6. **Measurement should stay first-class.** Per-gate wall/CPU/RSS/fault/context-switch metrics cost little operationally and expose where time/resources actually go; repeat comparable runs before deriving ETA accelerators.

## 12. Claim-state and negative-result delta

### Supported/current operational claims

- `FRANK-HOSTINGER-BUILDTEST-001`: Hostinger runner `clay` can execute and persist a current Frank Ubuntu integrity workflow; latest measured run is 21/21 PASS. Evidence class: REMOTE_EXECUTION_RECEIPT.
- `FRANK-LOCAL-TRANSPORT-002`: explicit proxy autodiscovery disable is implemented and passes a hostile ambient proxy regression for the tested loopback adapter path. Evidence class: CODE + REMOTE_EXECUTION_RECEIPT + OFFICIAL_DOC_SUPPORT.
- `FRANK-RESPONSE-PERSIST-003`: current tested response contract excludes private backend sentinel fields and hidden reasoning while retaining admitted usage/timing/tool response data. Evidence class: CODE + REMOTE_EXECUTION_RECEIPT.

### Negative results preserved

- `FRANK-QWEN4B-BOOT-NEG-001`: first real-model lane blocked before inference by absent CMake.
- `FRANK-QWEN4B-BOOT-NEG-002`: second lane repaired CMake but failed to locate bootstrapped Ninja under a distro-dependent pip-prefix assumption.
- These do not refute Qwen4B viability; they refute the corresponding runner-toolchain assumptions.

### Open / not promoted

- real Qwen4B inference performance and quality on the VPS;
- adaptive recurrence superiority;
- SQLite NORMAL as a production durability mode;
- whole Frank v0.1 release readiness;
- power-loss durability;
- runner compromise or security breach;
- any consciousness/phenomenal claim.

## 13. Ranked next falsifiers

1. Complete the current pinned Qwen4B Ubuntu run; require `real_model_executed=true`, non-null benchmark, model SHA match, runtime pin, throughput/latency, task results and tool-call behavior.
2. If Qwen4B passes, repeat a larger held-out benchmark with matched fixed/adaptive trajectories, multiple task classes and calibration/OOD cases before promoting recurrence control.
3. Split self-hosted execution authority from receipt-write authority and test read-only execution + constrained persistence.
4. Run production-shaped SQLite state workloads, concurrent readers/writers/checkpoints and explicit process-kill/restart tests; perform power-loss-equivalent durability testing only in a disposable environment with appropriate safety controls.
5. Repeat the 21-gate matrix across several comparable commits to calibrate stable per-gate variance and only then consider an ETA/throughput multiplier.
6. Move final acceptance to Andreas' actual designated Ubuntu developer system once the remote harness/model/database/tool stack is complete; Hostinger PASS remains supporting evidence, not substitute release evidence.

## 14. Decision trace

**Evidence used:** current canonical/stack/contracts, fresh Frank main repeatedly during work, real Hostinger receipts, current code/tests/workflows, official Python/GitHub/llama.cpp documentation, concurrent worker deltas.  
**Alternatives preserved:** verbatim usage persistence, fixed recurrence, SQLite NORMAL, persistent runner with direct write token, multiple build-tool bootstrap approaches.  
**Discriminating actions:** hostile proxy test; durable sentinel filtering; 21-gate real VPS matrix; SQLite WAL lock/checkpoint probe; pinned real Qwen4B attempts.  
**Results:** proxy/persistence hardening supported; integrity matrix PASS; SQLite probe informative but not a durability promotion; real Qwen4B currently blocked by runner build-tool path assumptions and still under active repair.  
**Uncertainty:** real-model performance/quality, recurrence transfer, durability under crash/power loss, security of persistent runner state, final-device integration.  
**Promotion boundary:** measurements outrank architecture preference; no release, consciousness, real-model or security-compromise claim without exact receipts.

## 15. Mesh feedback

Affected branches should ingest this report as follows:
- `frank`: host/runtime/model boundary, adaptive recurrence and final-device implications;
- `harness`: 21-gate receipt, model/toolchain negatives, runner security separation;
- `gwt`: adaptive recurrence remains measurement/control hypothesis only;
- `emergenz`: recurrence is not emergence; no promotion;
- `unifieddb`: SQLite WAL measurements + durability open questions;
- `claygraph`: no new truth-authorizing graph claim; link host/model/runtime evidence and falsifiers;
- `claycode`: Ubuntu execution/toolchain evidence, but no ClayCode semantic change is justified by these results;
- `hyperposition`: preserve fixed/adaptive recurrence and runner-security alternatives until discriminated.

**Whole-system reentry:** The best immediate path toward `Frank v0.1 voll lauffähig auf Andreas Ubuntu developer system` is to finish and measure the real pinned Qwen4B CPU lane, keep the now-green integrity matrix as a regression gate, harden self-hosted runner authority, then carry the validated stack to Andreas' actual Ubuntu system for final acceptance.
