# FRANK v0.1 Qwen4B Execution Addendum — Open Receipt Boundary

Run: `20260810T0010p0700-frank-v01-qwen4b-execution-addendum`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent observed: RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Subject: FRANK v0.1 local-model execution lane  
Whole-FRANK release promotion: NONE

## Purpose

Persist the state reached after the FRANK v0.1 deep-research/build/Ubuntu cycle so another Research Entity organ can continue without chat replay. This addendum distinguishes the already-proven Ubuntu integration state from the still-open real-Qwen execution state.

## A. Current proven Ubuntu integration state

Latest FRANK deep-integrity receipt observed during this run:

- evidence class: `REAL_SELF_HOSTED_UBUNTU_EXECUTION`;
- host: `digital-retina`;
- Linux x86_64 / Python 3.12.3;
- 21 declared gates;
- 21 PASS / 0 FAIL;
- matrix wall time: 10,469 ms;
- measured child elapsed sum: 9,234.792 ms;
- user CPU sum: 3.954190 s;
- system CPU sum: 0.955706 s;
- peak gate RSS: 66,216 KiB;
- current receipt explicitly does not measure energy or power-loss durability.

Selected measured gates:

- `compile_python`: 202 ms, 16,628 KiB max RSS;
- `deep_integrity_v11`: 757 ms, 24,832 KiB max RSS;
- `local_model_baseline`: 916 ms, 25,208 KiB max RSS;
- `local_model_endpoint_boundary`: 2,158 ms, 33,280 KiB max RSS;
- `local_model_tool_metrics`: 1,272 ms, 25,984 KiB max RSS;
- `local_model_proxy_usage_hardening`: 662 ms, 25,344 KiB max RSS;
- `pytest_bootstrap`: 2,013 ms, 66,216 KiB max RSS;
- `pytest_all`: 464 ms, 34,808 KiB max RSS.

This receipt proves only the declared Ubuntu integration/test matrix. It does not imply that a real 4B model executed and does not constitute final Andreas-PC acceptance.

## B. Real-model lane chosen from current primary evidence

The current experimental CPU-only lane pins:

- model family: `Qwen3-4B-Instruct-2507`;
- GGUF source: `ggml-org/Qwen3-4B-Instruct-2507-Q8_0-GGUF`;
- source revision: `e92aed4`;
- file: `qwen3-4b-instruct-2507-q8_0.gguf`;
- SHA-256: `ae916ede1c010a26955ee8ae2e908bf8815a3f135ec860439ab924701c69d5f1`;
- quantization: `Q8_0`;
- llama.cpp commit: `936918514ce522b553c0fd80b169a6440e6096c6`;
- CPU threads: 4;
- context: 2048;
- server binding: loopback only;
- chat template path: Jinja;
- reasoning: explicitly disabled for the non-thinking Instruct model;
- adaptive recurrence: offline shadow only, never allowed to influence the real trajectory during this pilot.

Primary-source validation performed in this run supports that Qwen3-4B-Instruct-2507 is a 4B non-thinking instruct model, that the exact Q8_0 artifact/revision/hash exists, and that llama.cpp supports the selected Jinja/OpenAI-compatible server/function-call surface.

## C. Real execution attempts and retained negative evidence

### Attempt 1

The initial real-model Ubuntu lane reached the runner but failed before model execution because the host had no usable CMake in the expected environment.

Result: negative infrastructure evidence, not model evidence.

### Attempt 2

A per-run pinned CMake/Ninja bootstrap was added. Installation succeeded, but the workflow assumed executables would exist at `$TOOLS_PREFIX/bin`. On this Ubuntu/Python `pip --prefix` layout the scripts were placed elsewhere under the temporary prefix.

Persisted receipt:

- status: FAIL;
- failure: `BOOTSTRAPPED_NINJA_MISSING`;
- benchmark: null;
- `real_model_executed=false`;
- 4 logical CPUs;
- ~16 GiB RAM;
- zero swap;
- exact model/runtime pins retained.

This is a runner-path bug. It is not evidence that llama.cpp, Qwen3-4B, Q8_0, CPU inference or the FRANK adapter failed.

### Fix already landed on current FRANK main

Concurrent swarm work independently diagnosed the same distro-dependent prefix assumption and landed:

`963fd8a6a044b6f5a6ddfde88fab25d0cc6e1dae`

The primary workflow now discovers actual executable paths under the isolated temporary prefix, records them, invokes the resolved CMake path directly, and passes the resolved Ninja path as `CMAKE_MAKE_PROGRAM`.

An independently convergent ChatGPT PR for the same diagnosis was closed without merge after the superior concurrent main fix appeared. This is retained as split-brain avoidance evidence: duplicate code was not integrated merely because it had been prepared independently.

## D. Current hard boundary

At the final synchronization point of this addendum, no new post-`963fd8...` real-Qwen receipt had materialized in the FRANK repository. Therefore:

- real Qwen3-4B execution after the path fix: `NOT_YET_RECEIPTED`;
- model benchmark pass/fail: `OPEN`;
- real model accuracy: `UNMEASURED_AFTER_FIX`;
- real TTFT/tokens-per-second after fix: `UNMEASURED_AFTER_FIX`;
- real tool-call success after fix: `UNMEASURED_AFTER_FIX`;
- real peak model-server RSS/CPU time: `UNMEASURED`;
- energy/power: `UNMEASURED`;
- whole FRANK release: `NOT_CLAIMED`.

Do not convert a workflow definition, main push, branch state, previous capability probe or failed bootstrap receipt into `REAL_MODEL_EXECUTED`.

## E. Benchmark semantics already implemented

The pinned benchmark executes four small tasks across five actual model steps per trajectory and includes a real tool-call case. It compares fixed recurrence depths W1/W2/W4 plus an offline adaptive-W4 selection derived from observable model proxies. Answer keys are retained for post-selection scoring rather than fed into adaptive selection.

Expected receipts include:

- task/final accuracy by policy;
- recurrence call counts;
- cumulative model latency;
- backend prompt/decode timing observations when emitted;
- real tool-call contract result;
- selected offline adaptive stopping depth.

Interpretation constraint: four pilot tasks are mechanism/contract evidence, not a general model-quality benchmark.

## F. Measurement gap to close after first real model PASS

A successful pilot should be followed by a minimally invasive resource sampler around the pinned llama-server process so that the next real-model receipt also records at least:

- process peak RSS / high-water mark;
- user and system CPU time;
- wall-clock model load/startup time;
- first-request latency / TTFT where separable;
- prompt tokens/s and decode tokens/s;
- per-trajectory cumulative latency;
- total model calls and generated tokens;
- available host memory before load and at benchmark end;
- model file cache-hit/download state;
- recovery/clean shutdown receipt.

Energy must remain `UNMEASURED` unless a real power/energy observation surface exists. Do not derive watts from CPU time.

## G. Cross-mesh fusion

This model lane joins three already-observed FRANK evidence families:

1. **state authority:** real Ubuntu Harness lesions show direct legacy stale mutation while the guarded truth-gate path produces zero mutation and rescue returns PASS;
2. **model observation authority:** local response projection now rejects non-finite JSON and prevents arbitrary backend/tool/usage extension fields from silently becoming durable FRANK state;
3. **adaptive recurrence:** separated adaptive recurrence is a measured Pareto candidate in shadow tests, not production authority.

Unified conclusion:

`observation != policy decision != effect authority != recovery receipt != release acceptance`

For FRANK v0.1 these surfaces must remain separately measured and provenance-bound.

## H. Live identity update from the Research Center

Parallel research-state evolution during this run now treats `FRANK` as the architecture/family name. Individual instantiated entities receive immutable unique `ClayID` identity and independent state lineage. Model/runtime receipts therefore must not be confused with individual entity identity receipts; later Andreas-host acceptance needs both an executable/runtime receipt and the correct ClayID/state-lineage birth/continuity receipts.

## I. Handoff

Highest-information continuation:

1. consume only a newly materialized post-path-fix real-Qwen receipt;
2. if FAIL, preserve the exact first failure and repair only that measured cause;
3. if PASS with `real_model_executed=true`, analyze every task/trajectory, tool call, latency and timing metric without generalizing beyond the pilot;
4. add model-server peak RSS/CPU/startup measurement and rerun the same pinned trial;
5. refusion into FRANK/Harness/UnifiedDB/ClayGraph/ClayCode/GWT/Hyperposition/Emergenz;
6. repeat final acceptance on Andreas' actual Ubuntu developer system before any whole-FRANK-v0.1 release promotion.

## Negative results preserved

- no proof that the previous loopback model transport actually traversed an external proxy;
- no post-path-fix real-Qwen execution receipt at this synchronization point;
- no evidence of GPU execution on `digital-retina`;
- no energy measurement;
- no general Qwen quality claim from a four-task pilot;
- no whole-FRANK release promotion;
- no emergence/consciousness inference.