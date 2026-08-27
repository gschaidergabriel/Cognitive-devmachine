# FRANK v0.1 Deep-Research / Build / Ubuntu Refusion Report

Run: `20260809T2353p0700-frank-v01-response-contract-refusion`  
Actor: `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Target: FRANK v0.1 Ubuntu acceptance path  
Research promotion: NONE  
Whole-FRANK release promotion: NONE

## 1. Requested execution cycle

This run executed the requested sequence as one evidence-gated loop:

`fresh canonical/research-center boot -> current FRANK/runtime evidence -> external primary research I -> fusion I -> falsifiable hypotheses/counterhypotheses -> external primary research II -> fusion II -> implementation delta -> conflict-aware integration -> self-hosted Ubuntu execution -> exact timing/host measurements -> deep evaluation -> cross-mesh refusion -> durable report/packet/branch feedback`

No queue entry, PR state or branch-only code was counted as executed Ubuntu evidence. The Ubuntu claim begins only at the self-hosted receipt that names the merged SHA.

## 2. Live shared-state observations

The run began from canonical RAE-8.8 revision 2 and continuously re-read the active FRANK and Research Entity heads. During the run, parallel workers committed:

- FRANK adaptive recurrence experiments and VPS receipts;
- per-gate timing and host-baseline measurement in the FRANK deep-integrity lane;
- disposable SQLite WAL runtime probes/receipts;
- read-only VPS local-model capability probe/receipt;
- Research Center knowledge packets and cross-branch refusion for H1, SQLite and model capability.

The main branch moved repeatedly while this worker was preparing the response-contract patch. A first PR was not forced when GitHub reported it non-mergeable. The delta was replayed on a fresh current-main parent, marked ready only after review, and merged only when GitHub reported `mergeable=true`. This is a concrete concurrency/split-brain control receipt, not just a workflow preference.

## 3. External research cycle I

### Python urllib primary documentation

Python's documented opener behavior installs a `ProxyHandler` by default when the opener does not already contain one. `ProxyHandler` without an explicit mapping can derive proxy configuration from environment/system configuration; an explicit empty proxy mapping disables auto-detected proxies.

Implication: the pre-patch local-model adapter's `build_opener(NoRedirect)` did not fully determine its network routing behavior from FRANK configuration alone.

### Python JSON + RFC 8259 primary documentation

Python's JSON decoder accepts `NaN`, `Infinity` and `-Infinity` by default as an interoperability extension. RFC 8259 does not permit those non-finite constants in JSON number syntax.

Implication: parsing an OpenAI-compatible model response with default `json.loads` was not equivalent to admitting portable RFC JSON.

### llama.cpp current primary implementation/docs

The current llama.cpp server exposes OpenAI-compatible chat-completion/tool behavior but also emits backend-specific fields such as timings and can expose reasoning-related fields depending on configuration/model. Its own documentation does not promise perfect universal OpenAI equivalence.

Implication: FRANK must treat OpenAI compatibility as an interface minimum, not as permission to persist every backend-specific field.

## 4. Fusion I: initial hypotheses

### H-RC-1 — Arbitrary nested backend metadata can become durable FRANK output

Pre-patch code copied `message.tool_calls` and top-level `usage` nearly unchanged into the public/durable adapter object. Therefore backend-specific nested text could cross the persistence boundary even though top-level `reasoning_content` was not deliberately persisted.

Counterhypothesis: existing backend metrics allowlisting might already prevent this.  
Discriminating observation: metrics were allowlisted separately, but `tool_calls`/`usage` were not projected through that allowlist. H-RC-1 survived.

### H-RC-2 — Default proxy behavior is a proven loopback exfiltration path

Counterhypothesis: Python/platform proxy-bypass logic may exempt loopback.  
Status after cycle I: OPEN / overstated.

### H-RC-3 — Non-finite JSON can be admitted and later serialized

Default Python decoder behavior supported this hypothesis. A direct negative regression was required.

### H-RC-4 — Strict response projection may be too expensive for FRANK's local inference hot path

Open. Required actual target-OS micro-measurement after implementation.

## 5. External research cycle II and hypothesis refinement

CPython's implementation confirms proxy routing includes host-specific bypass logic. Therefore H-RC-2 was narrowed: **this run does not claim that FRANK's loopback traffic was actually sent through an external proxy**. The supported architectural claim is that pre-patch behavior unnecessarily depended on ambient proxy discovery, while an explicit empty `ProxyHandler` makes the local-model transport deterministic with respect to that source of configuration.

Current llama.cpp response construction shows a compact standard usage surface plus backend-specific fields. This supports projection rather than wholesale backend rejection: preserve required visible/tool/usage semantics and separately admit known numeric backend measurements, while ignoring unknown fields.

## 6. Implementation delta

Merged FRANK PR #28 as main SHA:

`07f9af41ca3f4b7add75d198bebf92887c3b52d3`

Changed four files:

1. `runtime/model/frank_response_contract.py` — strict parser/encoder and bounded projections.
2. `runtime/model/frank_local_model_adapter.py` — explicit empty proxy handler, strict JSON, projected visible/tool/usage contract.
3. `tests/local_model_response_contract_regression.py` — adversarial sentinel/non-finite/proxy-discovery regression plus informational micro-measurement.
4. `tests/local_model_tool_metrics_regression.py` — binds the new regression into the already measured VPS F6 gate.

### Contract behavior

- URL scheme/userinfo/remote-by-default/redirect/body-size controls remain intact.
- Ambient proxy discovery is disabled for this adapter opener.
- Request canonicalization cannot emit non-finite JSON.
- Response parsing rejects non-finite JSON constants.
- Missing/malformed required non-streaming chat response structure fails closed.
- Tool calls retain only `id`, `type=function`, `function.name`, `function.arguments`.
- Usage retains bounded non-negative token count fields/details.
- Backend timings remain a separate numeric allowlist.
- Unknown response metadata is ignored instead of persisted.
- A returned tool call remains data; this patch does not grant execution authority.

## 7. Adversarial test design

The regression constructs a valid-looking local OpenAI-compatible response containing the sentinel:

`PRIVATE_SENTINEL_NOT_FOR_DURABLE_OUTPUT`

inside:

- `reasoning_content`;
- unknown message fields;
- unknown tool-call fields;
- unknown nested function fields;
- unknown `usage` fields/substructures;
- unknown timing fields;
- unknown top-level response fields.

PASS requires the sentinel to be absent from the durable projected output while the real tool name/arguments, admitted numeric usage and admitted numeric timing observations survive.

A second response deliberately contains `NaN` in usage. PASS requires fail-closed rejection.

The import test temporarily replaces `urllib.request.getproxies` with a function that raises. Adapter import must still succeed, proving that opener construction no longer performs automatic proxy discovery.

## 8. Real target-OS-type VPS receipt

Self-hosted receipt commit:

`b37a306e9266c44d1ab1b4faca9de643c96f440a`

Receipt binds execution to merged FRANK SHA:

`07f9af41ca3f4b7add75d198bebf92887c3b52d3`

Observed host:

- hostname: `digital-retina`;
- Linux `6.8.0-117-generic` x86_64;
- Python `3.12.3`;
- 4 logical CPUs;
- `16,376,020 KiB` total RAM;
- deep-integrity gates: 20;
- PASS: 20;
- FAIL: 0;
- matrix wall time: 8,878 ms;
- summed gate times: 8,673 ms.

Selected gate durations:

- compile_python: 167 ms;
- repo_static_integrity: 41 ms;
- transaction_replay: 94 ms;
- deep_integrity_v11: 647 ms;
- local_model_baseline: 878 ms;
- local_model_endpoint_boundary: 2,115 ms;
- local_model_tool_metrics + new response-contract regression: 1,220 ms;
- pytest_all: 449 ms.

## 9. Exact response-projection measurement

Within the real Ubuntu run, `extract_visible_contract` was measured over 2,000 iterations using the adversarial response document:

- p50: `1,469 ns` = `1.469 µs`;
- p95: `2,651 ns` = `2.651 µs`;
- no threshold was used for PASS.

Interpretation: current evidence does not support the hypothesis that the projection itself is a material inference-latency cost. The measured ~0.6 s increase in the surrounding CI gate is test-harness overhead from an additional subprocess, local HTTP servers and negative cases, not per-response production overhead.

Do not generalize this microbenchmark to every response size/backend. Large tool-call arrays, very large argument strings and future multimodal response forms need their own scaling tests.

## 10. Hypothesis outcomes after build/test

| Hypothesis | Outcome | Evidence boundary |
|---|---|---|
| H-RC-1 arbitrary nested backend metadata crossed pre-patch durable output | CONFIRMED / PATCHED | code inspection + adversarial sentinel test |
| H-RC-2 loopback definitely traversed proxy | NOT ESTABLISHED | platform bypass behavior prevents that claim |
| H-RC-2R ambient proxy discovery was an unnecessary transport dependency | SUPPORTED / REMOVED | Python primary docs + import probe |
| H-RC-3 non-finite JSON could be admitted by default decoder | CONFIRMED / PATCHED | Python docs + RFC 8259 + negative test |
| H-RC-4 projection causes material local inference overhead | NOT SUPPORTED in measured microcase | p50 1.469 µs, p95 2.651 µs |
| H-RC-5 this VPS currently supports real local Qwen-class 4B execution | REFUTED as current configured capability | read-only capability receipt |
| H-RC-6 20/20 deep-integrity means whole FRANK v0.1 release | REFUTED by scope | receipt explicitly says release not claimed |

## 11. Current VPS model-capability boundary

A separate parallel real-host probe shows:

- AMD EPYC 9354P host CPU exposed as 4 logical vCPUs;
- ~16 GiB RAM, zero swap;
- no visible `/dev/dri`, AMD KFD or NVIDIA devices;
- no `nvidia-smi`, `llama-server`, `llama-cli`, Ollama, vLLM or SGLang command;
- no Torch, Transformers, vLLM, SGLang or llama_cpp Python package;
- `real_model_executed=false`.

Therefore this VPS is currently a strong Ubuntu integration/falsification lane, but not yet a measured Qwen-4B performance lane. CPU-only installation remains technically open; no impossibility claim is made.

## 12. Cross-worker refusion with concurrent evidence

The newest Research Center refusion contributes three other live evidence families:

### H1 separated adaptive recurrence

On the same real Ubuntu runner, a proposal-only separated recurrence policy removed two frozen raw-W4 early-route false halts while preserving frozen accuracy. It costs more recurrence/compute than raw W4 and the task trajectories remain synthetic, so this is a Pareto candidate rather than selected production policy.

### SQLite WAL

Disposable Ubuntu tests reproduced held-reader/checkpoint behavior, single-writer `SQLITE_BUSY` behavior and a host-local durability/latency tradeoff. This informs UnifiedDB observability/recovery but does not establish multi-file crash atomicity.

### Model capability

The current VPS lacks a real-model runtime/accelerator configuration, so real Ubuntu execution and real local-model execution remain distinct evidence classes.

### Combined architecture implication

The four evidence families now align on one rule:

**separate observation, decision/policy, authority/effect and recovery receipts instead of collapsing them into one success scalar.**

- model response != authorized effect;
- recurrence diagnostic != stopping authority;
- SQLite file-open/integrity != multi-store semantic coherence;
- Ubuntu CI pass != real-model performance pass;
- integration gate pass != FRANK release pass.

## 13. Mesh feedback

### frank

Adopt strict response projection as CURRENT tested infrastructure. Keep F6 release false until a pinned real Qwen-class 4B backend executes tool/non-tool acceptance cases and Andreas-PC acceptance is obtained.

### harness

Treat model-returned tool calls as proposals/data until capability/effect gateway authorization. Keep the response-contract regression in the main deep-integrity lane.

### unifieddb

Persist admitted tool/usage/model observations with explicit provenance. Do not provide schema-free raw backend payload persistence. Preserve WAL/checkpoint/busy telemetry separately from semantic correctness.

### claygraph

Graph only admitted semantic observations; raw provider payload fields must not silently create graph truth/activation.

### claycode

Represent raw observation, projected observation, proposed effect, authorized effect and outcome receipt as distinct typed states. This is a useful executable compiler/runtime acceptance pattern later, but does not alter current BASE package PASS accounting by itself.

### gwt

Workspace availability/broadcast of a tool proposal is not execution authority. Maintain effect/outcome/reentry receipts as distinct causal surfaces.

### hyperposition

Keep runtime/backend alternatives set-valued until real pinned trials discriminate latency, correctness, memory, tool behavior and recovery.

### emergenz

No emergence or consciousness inference is warranted from response sanitization, recurrence policy improvement, WAL integrity or GWT-style routing.

### clayresearch

Highest-information next model experiment: pinned real Qwen-class 4B matched trials on a capable Ubuntu host through the now-hardened adapter, including tool-call correctness, TTFT, tokens/s, peak memory, recurrence policy, rollback and provenance.

## 14. Negative results and non-promotions

Retain explicitly:

- no proof that prior loopback requests actually traversed an external proxy;
- no real Qwen-class 4B executed on current `digital-retina` in this cycle;
- no evidence that microsecond projection timings generalize to arbitrarily large/multimodal responses;
- no whole-FRANK release claim;
- no ClayCode BASE package promoted by this response-contract work;
- no consciousness/emergence claim;
- old PR #27 remains superseded operationally by merged PR #28; do not treat both as separate accepted deltas.

## 15. Decision trace

Evidence used:

- current canonical/identity/program state;
- current FRANK adapter and test/runtime code;
- Python urllib/json primary documentation;
- RFC 8259;
- current llama.cpp server implementation/docs;
- live GitHub mergeability/concurrency state;
- real self-hosted Ubuntu deep-integrity receipt;
- real VPS read-only capability receipt;
- concurrent H1/SQLite/mesh refusion.

Alternatives considered:

1. persist raw OpenAI-compatible response metadata — rejected because provider/backend extension fields are not authority;
2. reject every unknown backend field — not selected because it would unnecessarily reduce compatibility; projection is safer and more extensible;
3. retain ambient proxy discovery — not selected for default local-model transport because it adds hidden configuration dependency;
4. infer full model/release readiness from 20/20 gate pass — rejected by explicit receipt scope and capability evidence.

Result:

A narrow security/provenance hardening delta was implemented, conflict-aware merged, executed on the real Ubuntu runner, measured, and packetized. It strengthens FRANK's local inference boundary without redesigning the model/runtime architecture.

Uncertainty:

Real-model semantics/performance, large-response scaling, streaming responses, backend-version compatibility and final Andreas-host behavior remain open.

Next falsifier:

Execute a pinned real Qwen-class 4B backend on a capable Ubuntu host through the hardened adapter, then compare at least llama.cpp/vLLM/SGLang-compatible surfaces where feasible with identical tool schema/prompt/template/sampling and immutable receipts.