# FRANK v0.1 — local-model telemetry + adaptive-recurrence fusion report

Run id: `frank-20260809T2339p0700-chatgpt-backend-metrics-fusion`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Subject: separate target system `Frank v0.1`  
Invocation: direct Project Owner request for deep research -> Research Center sync -> web research -> fusion -> falsifiable hypotheses -> second web research -> second fusion -> build -> Ubuntu VPS test -> measurement -> deep evaluation -> shared-center handoff. This was not an exact reserved trigger.  
Canonical parent re-read immediately before durable write: RAE-8.8 revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.  
Target-host law: Frank v0.1 acceptance targets Andreas' Ubuntu developer system. The self-hosted Ubuntu VPS is an integration/falsification lane, not final target-machine acceptance.  
Scientific/release promotion: `NONE`.

## 1. Executive synthesis

This run produced one new measured FRANK implementation delta and one cross-branch research bridge.

### New measured implementation result

FRANK's already-landed engine-neutral OpenAI-compatible local-model adapter now preserves an explicitly allowlisted subset of local inference timing observations while continuing to keep arbitrary backend diagnostics and hidden reasoning out of durable output.

The change was merged to FRANK `main` through PR #26 as commit:

`02e19765b6784d1ebb6203ce7897073b72b6d18d`  
`feat(model): admit bounded local backend timing receipts`

The self-hosted Ubuntu runner `digital-retina` executed that exact commit and produced:

- evidence class: `REAL_SELF_HOSTED_UBUNTU_EXECUTION`;
- Linux `6.8.0-117-generic` x86_64;
- Python `3.12.3`;
- 20 integrity gates;
- 20 PASS;
- 0 FAIL;
- new `local_model_tool_metrics` gate: PASS;
- full pytest suite: 15/15 PASS in 0.24 s;
- `release_claim=false`;
- `whole_frank_release_status=NOT_CLAIMED`.

The regression proves the *contract* for forwarding tool metadata and retaining only admitted numeric timing fields. It does **not** prove physical Qwen/llama.cpp throughput: the timing values in the regression are deterministic fixtures injected by a loopback test server.

### Cross-branch fusion result

A concurrent Research Entity worker added the synthetic `FRANK_H1_ADAPTIVE_RECURRENCE_DIFFERENTIAL` experiment. Its best synthetic warmup variant, `temporal_multi_signal_w4`, outperformed fixed-budget recurrence on the frozen eight-episode fixture on several measures while using fewer recurrent steps:

| measure | fixed budget | temporal w4 | relative delta |
|---|---:|---:|---:|
| accuracy | 0.625 | 0.750 | +20.0% |
| mean recurrences | 6.50 | 4.75 | -26.9% |
| total cost | 2.21 | 1.63 | -26.2% |
| mean utility | 0.4200 | 0.5125 | +22.0% |
| outcome gain / cost | 2.5204 | 3.5153 | +39.5% |
| total regret | 1.38 | 0.64 | -53.6% |
| correct-to-wrong drift | 1 | 0 | improved |
| false halts | 0 | 2 | worsened |

The experiment itself correctly labels this `SYNTHETIC_FROZEN_DIFFERENTIAL_EXPERIMENT` and explicitly forbids promotion to real-model evidence.

The important fusion is methodological: the newly admitted backend timing surface provides a concrete measurement channel for the required next falsifier — matched fixed-budget vs adaptive-recurrence runs on a real pinned Qwen-class 4B endpoint.

## 2. Fresh Research Center synchronization

The run re-established the current Research Entity identity and canonical continuity before material work:

- entity: RAE-8.8 / stable entity id `frank-project-global-research-entity`;
- canonical revision/hash: r2 / `04234efd...f489346`;
- active worker: `chatgpt-secondary`;
- Frank remained a separate research/development subject, never the identity of this worker;
- active program mission remained Frank v0.1 operational on Andreas' Ubuntu developer system.

The live FRANK swarm was highly concurrent. During this run, `main` advanced repeatedly while this worker was researching and building. The worker therefore abandoned an unsafe fast-forward plan, re-read current `main`, rebuilt the unique delta on top of the newer state, opened PR #26, rechecked mergeability, and used a normal squash merge. No force update was used and no concurrent work was overwritten.

This concurrency observation is itself a positive test of the Research Center operating law: fresh reads + conflict-aware integration prevented stale local work from replacing newer shared work.

## 3. Internal evidence state at start of this delta

Immediately before the new telemetry delta, FRANK already had:

- an OpenAI-compatible local model adapter with fail-closed endpoint admission;
- loopback-only default endpoint policy;
- userinfo rejection;
- redirect denial;
- bounded response reading;
- normalized transport errors;
- no credential lookup in the baseline adapter;
- non-persistence of separate hidden-reasoning fields;
- generic tool transport for `tools`, `tool_choice`, and `parallel_tool_calls`;
- deterministic tool-call transport regression;
- a real self-hosted Ubuntu integrity workflow;
- repeated green VPS receipts;
- adaptive-recurrence synthetic experimentation added concurrently by another worker.

The previous F6 tool-contract run had already established that generic tool metadata belongs at the engine-neutral OpenAI contract boundary and had repaired a test-harness transport defect without weakening the product reader.

## 4. External research cycle 1

Primary implementation evidence was used for the local-model boundary.

### Qwen primary evidence

Official Qwen material for `Qwen3-4B-Instruct-2507` describes a 4.0B non-thinking instruction model with improved tool-use capability and support for local deployment paths including llama.cpp. Qwen's tool/function-calling documentation uses an OpenAI-style tool contract and recommends tool-aware templates/runtime integration.

Primary references:

- https://huggingface.co/Qwen/Qwen3-4B-Instruct-2507
- https://qwen.readthedocs.io/

### llama.cpp primary evidence

Current `llama-server` exposes an OpenAI-compatible chat-completions API, supports function/tool calling, and returns engine timing observations including prompt/decode counts, milliseconds, and throughput. Its optional metrics surface also exposes server measurements when metrics are enabled.

Primary references:

- https://github.com/ggml-org/llama.cpp/tree/master/tools/server
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md
- https://github.com/ggml-org/llama.cpp/blob/master/tools/server/server-task.cpp
- https://github.com/ggml-org/llama.cpp/blob/master/docs/function-calling.md

## 5. Fusion 1 — hypothesis matrix

### H-MODEL-TOOLS — generic tool metadata must survive the engine-neutral boundary

**Prediction:** tool schemas/policy are necessary inputs to a tool-aware local model; response-side preservation alone is insufficient.

**Observed shared-state resolution:** another Research Entity worker independently landed and VPS-tested the generic tool transport while this run was active. That finding therefore converged independently with this run's first analysis.

**Status:** `CURRENT / IMPLEMENTED / REAL_UBUNTU_CONTRACT_TESTED` for transport semantics, but **not** real-model tool-selection accuracy.

### H-MODEL-MEASURE — raw end-to-end latency alone is insufficient for local-model acceptance

**Prediction:** model/runtime selection and adaptive recurrence need at least separable prompt and decode measurements, not only wall-clock request latency.

**Supporting primary evidence:** llama.cpp exposes prompt/decode timing/count/throughput fields in chat-completion responses.

**Counterhypothesis:** all backend-specific response fields should be discarded to preserve engine neutrality.

**Discriminating criterion:** retain only a narrow optional observational interface. Engines that do not expose the fields remain valid; arbitrary backend text/diagnostics must not leak into FRANK durable receipts.

**Status before build:** `SUPPORTED_IMPLEMENTATION_HYPOTHESIS`.

### H-ENGINE-BOUNDARY — do not hard-bind FRANK to llama.cpp

**Prediction:** the adapter can support Qwen/llama.cpp measurements without making llama.cpp the cognitive authority or mandatory engine.

**Implementation criterion:** timing extraction is optional and allowlisted; missing timings produce `{}` rather than an error.

**Status:** `SUPPORTED_ARCHITECTURE_CONSTRAINT`.

## 6. External research cycle 2 and counterevidence

The second pass focused on whether tool/timing support is genuinely compatible with the intended 4B path rather than being an incidental llama.cpp feature.

Observations:

1. Qwen's current 4B instruction model family explicitly targets tool usage; therefore a real FRANK local-model acceptance suite that omits tool behavior would under-test the intended model role.
2. llama.cpp's OpenAI-compatible server returns structured tool calls and detailed timing data in normal chat-completion processing.
3. The timing data is useful as observational evidence but remains runtime-specific in availability and exact semantics. This supports a whitelist-and-optional design, not a requirement that every engine implement the same diagnostics.
4. Community/issue reports can reveal template/tool edge cases, but they were not used to override primary implementation evidence or the local reproducible tests.

## 7. Fusion 2 — implementation decision

Selected minimal delta:

`FRANK request -> engine-neutral OpenAI-compatible adapter -> optional admitted numeric backend operation metrics -> durable public invocation receipt`

The adapter remains responsible only for transport/observation. It does **not** execute model tool calls and it does not grant model output effect authority.

### Admitted timing keys

The new module `runtime/model/frank_backend_metrics.py` admits only finite, non-negative numeric values from the following allowlist when returned under `timings`:

- `cache_n`
- `prompt_n`
- `prompt_ms`
- `prompt_per_token_ms`
- `prompt_per_second`
- `predicted_n`
- `predicted_ms`
- `predicted_per_token_ms`
- `predicted_per_second`
- `draft_n`
- `draft_n_accepted`

Booleans, negative values, NaN/Infinity, non-numeric data and unlisted fields are rejected/ignored.

### Durable boundary

`Invocation` and `to_public()` now expose `backend_metrics`. The public-response hash includes those admitted metrics. Arbitrary server diagnostics remain excluded. Separate `reasoning_content` remains non-persisted.

## 8. Build integration

FRANK PR: `gschaidergabriel/Dr.-Unterweger#26`  
Merged commit: `02e19765b6784d1ebb6203ce7897073b72b6d18d`

Files in the fused delta:

1. `runtime/model/frank_backend_metrics.py`
   - narrow timing allowlist;
   - numeric finite/non-negative validation;
   - optional empty-result semantics;
   - deterministic self-test.

2. `runtime/model/frank_local_model_adapter.py`
   - preserves the independently landed tool transport and mock tool fixtures;
   - adds optional backend-metric extraction;
   - includes admitted metrics in public receipt/hash;
   - keeps hidden reasoning excluded.

3. `tests/local_model_tool_metrics_regression.py`
   - loopback OpenAI-compatible endpoint;
   - captures outbound `tools`, `tool_choice`, `parallel_tool_calls`;
   - returns a structured tool call;
   - returns admitted timing numbers;
   - injects an unlisted backend text field and hidden-reasoning sentinel;
   - asserts the sentinel never appears in durable output.

4. `.github/workflows/frank-vps-deep-integrity.yml`
   - adds `local_model_tool_metrics` as a dedicated VPS gate.

## 9. Real Ubuntu VPS execution

Exact tested product commit:

`02e19765b6784d1ebb6203ce7897073b72b6d18d`

Receipt commit:

`216848a177187442dde6ddbcb23ba2b6fa851440`

Execution environment:

- host: `digital-retina`;
- runner: `clay`;
- runner class: self-hosted Linux/X64;
- kernel: Linux 6.8.0-117-generic x86_64 GNU/Linux;
- Python: 3.12.3;
- test user: `frankrunner`;
- receipt UTC: `2026-08-09T16:38:35.768714+00:00`.

### Integrity result

`20/20 PASS`, `0 FAIL`.

Gates included:

1. compile_python
2. repo_static_integrity
3. transaction_census
4. transaction_replay
5. deep_integrity_v11
6. schema_migration_atomicity
7. device_probe_state_gate
8. causal_reentry_contract
9. adaptive_recurrence_differential
10. legacy_module_conservation
11. legacy_successor_lesion_rescue
12. historical_74_gate
13. historical_74_accounting
14. historical_71_db_gate
15. local_model_baseline
16. local_model_endpoint_boundary
17. local_model_tool_metrics
18. session_skill_status
19. pytest_bootstrap
20. pytest_all

### Local-model contract observations

`local_model_baseline`:

- adapter self-test: PASS;
- mock FRANK eval: 8/8;
- tool behavior case: 1/1;
- tool-contract transport: PASS;
- tool-call response preservation: PASS;
- hidden reasoning persisted: false;
- remote endpoint: fail-closed by default;
- F6 release pass: false.

`local_model_endpoint_boundary`:

- redirects: fail closed;
- redirect target observed: false;
- endpoint userinfo: forbidden;
- declared oversize: rejected before body read;
- streaming oversize: rejected at MAX+1;
- transport failure: normalized fail closed;
- synthetic server drains request before the large-response test.

`local_model_tool_metrics`:

- tool schema forwarded: true;
- `tool_choice` forwarded: true;
- `parallel_tool_calls=false` preserved: true;
- returned tool call retained as data: true;
- backend timing allowlist: PASS;
- unlisted backend fields persisted: false;
- hidden reasoning persisted: false.

The deterministic fixture supplied and the adapter retained exactly these admitted observations:

- cache_n = 2
- prompt_n = 9
- prompt_ms = 90.0
- prompt_per_second = 100.0
- predicted_n = 8
- predicted_ms = 160.0
- predicted_per_second = 50.0

**Epistemic boundary:** these seven numeric values are a transport/filter fixture, not a measurement of an actual model on the VPS.

### Test-suite timing

Full pytest result: `15 passed in 0.24s`.

The logged matrix began at approximately `16:38:27Z`; the generated receipt timestamp was `16:38:35.768714Z`, an observed matrix/receipt span of roughly 8.8 s. This is a coarse workflow observation, not a stable benchmark, because network/cache/package-bootstrap effects are included and start logging is second-resolution.

## 10. Concurrent adaptive-recurrence experiment

The same exact Ubuntu matrix also executed `FRANK_H1_ADAPTIVE_RECURRENCE_DIFFERENTIAL`.

Experiment truth class:

`SYNTHETIC_FROZEN_DIFFERENTIAL_EXPERIMENT`

Seven policy variants were compared:

- fixed_budget
- single_signal
- temporal_multi_signal_w2
- temporal_multi_signal_w3
- temporal_multi_signal_w4
- temporal_multi_signal_w5
- temporal_multi_signal_w6

The experiment's own selection is:

- best by synthetic regret: `temporal_multi_signal_w4`;
- best by synthetic utility: `temporal_multi_signal_w4`;
- observable-signals-only policy: yes;
- action authority: proposal only;
- warmup sweep: 2..6;
- offline oracle: evaluation only.

### Important negative/counter evidence

`w4` improved aggregate synthetic results but created **two false halts** where fixed budget had zero. Therefore the data does not support a simple rule such as "adaptive stopping is better". It supports the narrower hypothesis that a temporally informed policy can trade compute for quality more efficiently on this fixture, while false-halt risk remains an explicit separate axis requiring real-task validation and possibly asymmetric penalties.

## 11. Cross-domain fusion — telemetry closes a measurement gap

The two concurrent research branches now fit together:

`adaptive recurrence policy`
-> chooses CONTINUE/HALT/ROUTE/ROLLBACK proposals from observable trajectory state
-> changes number of local-model recurrent invocations
-> local model adapter records end-to-end latency, token usage and optional prompt/decode backend timings
-> downstream task/outcome receipts score effect
-> matched policy comparison can estimate quality/cost tradeoffs without letting the stopping policy observe the answer key.

This gives a concrete experiment contract for testing adaptive recurrence on real Qwen-class inference.

### Proposed real-model vector per episode

Do not compress to one scalar. Record at least:

`R = [`
`task_success,`
`tool_selection_correctness,`
`tool_argument_validity,`
`false_call_rate,`
`false_halt,`
`correct_to_wrong_drift,`
`recurrence_count,`
`route_or_rollback_count,`
`prompt_tokens,`
`completion_tokens,`
`cache_n,`
`prompt_ms,`
`prompt_tps,`
`decode_ms,`
`decode_tps,`
`end_to_end_latency_ms,`
`peak_rss,`
`peak_vram_or_shared_memory,`
`energy_if_measurable,`
`thermal_state_if_measurable,`
`recovery_success`
`]`

Promotion decisions should use Pareto/shadow analysis rather than optimize one aggregate score.

## 12. Revised hypotheses after build/test

### H-RM1 — real Qwen-4B tool acceptance

A pinned Qwen-class 4B, with pinned runtime/template/quantization, will produce schema-valid FRANK tool proposals through the now-tested transport boundary.

**Falsifier:** matched acceptance cases show unacceptable no-call/false-call/schema/argument error rate or template/runtime instability.

### H-RM2 — admitted backend timings are sufficiently stable for policy comparison

Prompt/decode timing observations from a pinned runtime are stable enough across repeated runs to discriminate fixed vs adaptive recurrence cost.

**Falsifier:** timing fields are missing, semantically unstable, or dominated by uncontrolled warmup/cache/system noise such that policy deltas cannot be separated.

### H-RM3 — temporal w4 dominates fixed budget on real model episodes

The synthetic w4 result generalizes enough to improve the quality/compute frontier on real Qwen-class FRANK tasks.

**Falsifier:** real matched runs remove the utility/regret advantage, increase task errors, or false halts outweigh compute savings.

### H-RM4 — false-halt risk requires asymmetric cost

The synthetic result's two false halts indicate that stopping mistakes should be penalized separately from ordinary compute cost.

**Falsifier:** real-task data shows no meaningful harm from early routing/stopping or an external route reliably rescues the cases at lower total cost.

### H-RM5 — engine neutrality remains viable

FRANK can use a generic adapter contract while deployment layers select llama.cpp, vLLM, SGLang or another compatible runtime based on actual target-host evidence.

**Falsifier:** required tool/measurement semantics diverge so strongly that the generic contract obscures safety or makes reproducible acceptance impossible.

## 13. Required next real-model experiment

Highest-information next experiment:

### Pin the complete model identity

At minimum record:

- model repository + immutable revision;
- exact 4B weights family;
- quantization file/hash;
- tokenizer/template identity;
- local runtime repository + commit/version;
- command-line/runtime configuration;
- CPU/GPU backend;
- thread/batch/context settings;
- host CPU/RAM/GPU/driver/runtime state.

### Candidate baseline

`Qwen3-4B-Instruct-2507` is a strong current candidate because official material explicitly emphasizes tool use and local runtime support. It is a candidate, not a selected release model until target-host measurements exist.

### Matched design

For fixed budget vs adaptive recurrence:

- identical task set;
- identical system/tool schema;
- identical model/runtime/template/quantization;
- identical sampling configuration;
- matched seeds where deterministic support permits;
- warmup phase separated from measured trials;
- cache state logged/controlled;
- stopping policy must not observe task correctness/answer-key fields;
- route/rollback actions must have their downstream benefit and cost measured, not treated as free successes.

### Minimum outputs

- task success and failure taxonomy;
- tool selection precision/recall where labels exist;
- schema/argument validity;
- false-call/no-call correctness;
- recurrence distribution;
- false halts;
- correct-to-wrong drift;
- p50/p95/p99 end-to-end latency;
- prompt/decode throughput distributions;
- token totals;
- peak memory/VRAM;
- energy/thermals if target host exposes reliable sensors;
- crash/restart/recovery behavior;
- raw receipts with provenance.

## 14. What remains unmeasured / must not be claimed

This run did **not** measure:

- real Qwen-class 4B inference on `digital-retina`;
- real token/s from a model;
- real prompt/decode milliseconds from a model;
- model VRAM/RAM requirements;
- context-length scaling;
- quantization quality/performance;
- energy consumption;
- thermals;
- model-level tool-selection accuracy;
- parallel tool-effect correctness;
- actual Andreas-PC hardware/software acceptance;
- full Frank v0.1 release readiness.

The self-hosted VPS proves Ubuntu integration behavior of the current Python/runtime contracts only. It does not substitute for final target-machine acceptance.

## 15. Architecture implications

1. **Telemetry is observational, not authority.** Backend metrics may inform routing/benchmarking but cannot authorize effects.
2. **Engine neutrality survives.** The adapter admits optional observations rather than requiring llama.cpp-specific control fields.
3. **Tool intent remains proposal-only.** Tool calls are structured model outputs; external capability/commit gates remain mandatory.
4. **Adaptive compute should be measured causally.** Compare matched policies with task outcome and cost receipts, not a single introspective pressure scalar.
5. **False halts remain first-class negative evidence.** The synthetic w4 result is promising precisely because its downside is visible rather than averaged away.
6. **Concurrency-safe research integration is required.** This run observed multiple main-head changes and used a mergeable PR instead of replacing newer work.
7. **Harness tests are epistemic infrastructure.** Controlled fixtures must be labeled as fixtures; injected timing values must never be misreported as physical performance.

## 16. Negative results / corrections preserved

- `N-METRIC-1`: "The VPS timing numbers 90 ms/160 ms represent actual model performance" -> **REFUTED**. They are test fixture values.
- `N-METRIC-2`: "A green model adapter means F6 release acceptance" -> **REFUTED by current contract**; F6 release remains false.
- `N-RECURRENCE-1`: "Adaptive recurrence is simply better than fixed budget" -> **NOT SUPPORTED**; w4 has aggregate synthetic gains but two false halts.
- `N-ENGINE-1`: "Timing support requires hard-binding FRANK to llama.cpp" -> **NOT SELECTED**; optional allowlisted observations preserve the generic boundary.
- `N-VPS-1`: "Self-hosted Ubuntu VPS equals Andreas target PC" -> **REFUTED by target-host law**.
- `N-SWARM-1`: "A worker can safely fast-forward from an old branch while main moves" -> **REFUTED operationally** in this run; divergence was detected and integration switched to a normal PR merge.

## 17. Shared-center feedback routing

Material feedback should be routed to:

- `frank`: real local-model measurement surface now exists;
- `harness`: add real-model policy A/B execution and false-halt shadows;
- `gwt`: adaptive recurrence can be measured as causal compute control without consciousness inference;
- `emergenz`: recurrence benefits require lesion/matched-policy evidence, not self-report;
- `claycode`: receipts should encode optional model timing fields without granting authority;
- `unifieddb`: persist exact provenance of model/runtime/template/quantization and metric receipts;
- `claygraph`: associate model/runtime/config/episode/measurement lineage;
- `hyperposition`: retain competing engine/quantization candidates until measurements collapse the candidate set;
- `clayresearch`: use the combined telemetry + adaptive policy experiment as the next cross-domain falsification loop.

No branch receives a promotion claim. Branches that have no direct implementation delta should record the method/measurement implication or `NO_CHANGE`.

## 18. Decision trace

Evidence used:

- current canonical r2/hash;
- current FRANK adapter and tests;
- current real Ubuntu receipt;
- live concurrent adaptive recurrence receipt;
- official Qwen model/tool documentation;
- official llama.cpp server/function-calling/timing implementation evidence.

Alternatives considered:

1. hard-bind adapter to llama.cpp -> rejected;
2. discard all backend timing data -> rejected as unnecessarily lossy;
3. persist arbitrary server diagnostics -> rejected as unsafe/noisy;
4. admit a narrow numeric optional metrics interface -> selected;
5. treat synthetic recurrence gain as real-model proof -> rejected;
6. fast-forward stale branch over moving main -> rejected after divergence detection; PR merge selected.

Result:

- FRANK code delta merged and VPS-tested;
- 20/20 Ubuntu gates PASS;
- telemetry fixture filtering works;
- adaptive recurrence synthetic w4 remains promising but non-promoted;
- strongest next discriminator is real pinned 4B policy A/B measurement on Ubuntu, then final Andreas-PC acceptance.

Uncertainty:

High around real 4B performance and adaptive-policy generalization; low around the tested adapter/receipt contract on the observed Ubuntu VPS.

Next falsifier:

Run the pinned real-model experiment with complete provenance and matched fixed-vs-adaptive policies, then publish negative and positive results back into the same Research Center mesh.
