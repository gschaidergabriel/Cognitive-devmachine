# FRANK v0.1 deep research + F6 tool-contract build + real VPS falsification loop

Run id: `frank-20260809T2325p0700-chatgpt-f6-tool-contract-vps`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Invocation: direct owner request for deep research -> fusion -> hypotheses -> second research -> fusion -> build -> target-OS VPS test -> measurement -> repair -> retest -> research-center handoff. Not an exact reserved-word trigger.  
Research promotion: `NONE`  
FRANK release promotion: `NONE`  

## 1. Fresh grounding and Research Center synchronization

The run booted the current Clay/RAE canonical identity and verified revision 2 / state hash `04234efd...9346`. The active mission remains `Frank v0.1 voll lauffähig auf Andreas PC`. Research Entity and FRANK remain separate systems; ChatGPT is a temporary Clay research/synthesis organ acting on FRANK as target system.

Fresh FRANK repository state showed that the implementation had already advanced beyond older project notes. The current private FRANK repository contains a real self-hosted Ubuntu execution gate on host `digital-retina`, runner `clay`. Immediately before this run, the gate had a receipted 18/18 PASS, while `whole_frank_release_status` remained `NOT_CLAIMED`.

The current FRANK swarm contract requires fresh repo/research-center reads, primary-source refresh where material, cross-worker evidence deltas, real VPS testing for runtime-sensitive changes, explicit negative results, repair/retest, and no silent authority forks.

Google Drive research-institute material was also queried. Relevant archived documents such as `FRANK_Hypothesis_Engine_Konzept.txt`, `FRANK-v26.1-Fertigstellung.txt`, `KATALOG.md`, `Arbeits- und Forschungsbericht.txt`, and `digital-retina-emergent-readout.txt` were available, but current GitHub/runtime evidence outranked these historical snapshots.

## 2. External research cycle 1

### 2.1 Swarm/shared-memory governance

Current 2026 literature was used as hypothesis-generating evidence, not authority:

- arXiv:2605.22721, `Self-Evolving Multi-Agent Systems via Decentralized Memory`: supports testing branch-local/decentralized candidate memory to preserve exploration diversity and potentially reduce shared-context cost.
- arXiv:2606.24535, `Governed Shared Memory for Multi-Agent LLM Systems`: motivates explicit scope, supersession, provenance and propagation policy, with leakage/staleness/contradiction/provenance-collapse failure modes.
- arXiv:2603.10062, `Multi-Agent Memory from a Computer Architecture Perspective`: supports treating multi-agent memory as a consistency/coherence problem rather than an undifferentiated shared transcript.
- arXiv:2604.08206, `Theater of Mind for LLMs`: provides an event-driven Global-Workspace-inspired engineering candidate, without licensing consciousness claims.
- arXiv:2602.07845, `Recurrent-Depth VLA`: supports adaptive recurrent-depth/stopping experiments and explicit overthinking/overcoupling measurement.

Fusion 1 preserved the existing design rule: worker-local candidate diversity is useful only if it cannot mint competing FRANK truth. Shared admitted truth remains centrally governed; provenance, contradictions and negative results must survive fusion.

## 3. FRANK code audit and first hypothesis generation

The current F6 local-model adapter had substantial security hardening already present:

- only HTTP/HTTPS endpoints;
- loopback-only unless remote is explicitly enabled;
- userinfo rejected;
- redirects denied;
- declared and streaming response-size limits;
- transport failures normalized fail-closed;
- no credential lookup by the baseline adapter;
- visible content/tool calls/usage persisted, hidden reasoning not durably stored.

However, the outbound OpenAI-compatible request contained only `model`, `messages`, `temperature`, `max_tokens`, and optional `response_format`. Returned `tool_calls` were parsed, but tool definitions and tool-selection controls were not forwarded.

This yielded the first falsifiable hypothesis set:

### H1 — TOOL_TRANSPORT_GAP

If FRANK supplies tool schemas to the adapter, they are currently dropped before the local model server. A text-only baseline can therefore pass while real agentic tool selection fails.

Falsifier: demonstrate that the current adapter already transmits `tools`/`tool_choice` to a captured OpenAI-compatible endpoint.

### H2 — BACKEND_SPECIFIC_ONLY

The missing fields might be backend-specific and therefore inappropriate in the engine-neutral adapter.

Falsifier: primary OpenAI-compatible local server implementations consume these fields as part of their generic chat-completions contract.

### H3 — RESPONSE_ONLY_SUFFICIENT

Preserving returned `tool_calls` might be sufficient even without forwarding tool schemas.

Falsifier: show a server/template whose tool-aware generation is conditioned on the request's `tools` field.

## 4. External research cycle 2

Fresh primary implementation evidence from `ggml-org/llama.cpp` was then checked.

Observed 2026-08-09:

1. `docs/function-calling.md` states that `llama-server` supports OpenAI-style function calling, including native and generic handlers, and shows requests carrying a `tools` array. It also documents `parallel_tool_calls` as a request control.
2. `tools/server/server-common.cpp` parses `tools` and `tool_choice` from the OpenAI-compatible body. When Jinja tool templating is unavailable, tool-bearing requests are explicitly rejected instead of ignored.
3. Current Qwen3/Qwen3-Coder Jinja templates explicitly iterate over `tools` and inject function signatures into the model conversation.
4. `llama-server` remains an OpenAI-compatible `/v1/chat/completions` server, making these fields appropriate at an engine-neutral OpenAI contract boundary rather than a llama.cpp-only extension.

Fusion 2 therefore supported H1, refuted H2 for these fields, and refuted H3. The minimal justified change was to forward only the generic OpenAI tool contract, not llama.cpp-specific tuning.

## 5. Build

### 5.1 Product change

FRANK repo commit:

`37fea7876e7a7d967b0a2a8e1db26547782dfaea`  
`feat(model): forward OpenAI-compatible tool contract`

Changed `runtime/model/frank_local_model_adapter.py`:

- added an explicit forwarded-field allowlist:
  - `tools`
  - `tool_choice`
  - `parallel_tool_calls`
- fields are transmitted only when present/non-null;
- no new execution authority is granted to model output;
- backend-specific tuning remains outside the baseline adapter;
- existing endpoint/security/response-boundary invariants remain intact.

### 5.2 Deterministic contract regression

FRANK repo commit:

`d1727c1d7f385553c0102c682660d25cb8cffd95`  
`test(model): cover tool-call transport contract`

The existing F6 regression was extended with a loopback `ThreadingHTTPServer` that acts as a deterministic OpenAI-compatible endpoint. It captures the exact outbound JSON and returns a structured function call.

Assertions:

- exact tool schema arrives at the endpoint;
- `tool_choice = auto` arrives unchanged;
- `parallel_tool_calls = false` arrives unchanged;
- user message survives transport;
- returned function-call name survives parsing;
- returned arguments remain valid structured JSON;
- hidden reasoning remains non-persisted;
- F6 production/release acceptance remains false.

The change was first isolated on `chatgpt/f6-tool-transport-20260809`, compared against the verified parent (2 commits ahead, 0 behind, only adapter + regression changed), then fast-forwarded to `main` without force.

## 6. Real target-OS VPS experiment 1 — negative result

The existing self-hosted workflow executed the exact new main commit `d1727c1d7f385553c0102c682660d25cb8cffd95` on:

- host: `digital-retina`
- runner: `clay`
- OS/kernel: Linux 6.8.0-117-generic x86_64
- Python: 3.12.3
- evidence class: `REAL_SELF_HOSTED_UBUNTU_EXECUTION`

Result:

- 18 gates total
- 17 PASS
- 1 FAIL
- new `local_model_baseline`: PASS
- new `tool_contract_transport`: PASS
- new `tool_call_response_preservation`: PASS
- `pytest_all`: 13/13 PASS
- failing gate: `local_model_endpoint_boundary`
- release claim: false

The negative result was preserved rather than hidden.

### Failure trace

The chunked MAX+1 response-boundary regression expected `MODEL_RESPONSE_TOO_LARGE`, but the client received `ConnectionResetError` while reading the body. The adapter correctly normalized this to `MODEL_RESPONSE_TRANSPORT_ERROR`, causing the *test expectation* to fail.

## 7. Adversarial diagnosis

Three explanations were separated:

### H4 — PRODUCT_REGRESSION_FROM_TOOL_FORWARDING

Prediction: tool forwarding changed bounded response reading or endpoint admission.

Counterevidence: the patch did not modify the response reader/admission path; F6 baseline including the new tool test passed; the failure occurred in the pre-existing streaming-oversize harness.

Status: `NOT_SUPPORTED`.

### H5 — VALID_PRODUCT_TRANSPORT_FAILURE

Prediction: remote peer termination is genuinely ambiguous, so fail-closed `MODEL_RESPONSE_TRANSPORT_ERROR` is correct product behavior.

Evidence: the adapter received a real connection reset and intentionally normalizes reset/broken-pipe/OSError while reading.

Status: `SUPPORTED` as product invariant.

### H6 — HARNESS_HALF_DUPLEX_TEARDOWN

Inspection showed the synthetic HTTP/1.1 `StreamingOversize` handler immediately began sending an 8 MiB+1 chunked response without consuming the POST request body. This creates a timing/platform-dependent connection teardown path unrelated to the intended response-size experiment. The discriminating repair is to drain the complete request body before emitting the large response, while leaving the product reader unchanged.

Status before retest: `BEST_EXPLANATION`.

## 8. Harness repair

FRANK repo commit:

`c901358039c542678cf866876bc01b5539e15956`  
`test(model): drain request body in streaming boundary harness`

Change:

- added a small test-only request-body drain helper;
- both large-response handlers consume the declared request payload before returning their synthetic large response;
- product adapter code was not weakened;
- the regression now explicitly reports `harness_request_body = DRAINED_BEFORE_LARGE_RESPONSE`.

This is the smallest change that distinguishes response-size enforcement from request/connection teardown behavior.

## 9. Real target-OS VPS experiment 2 — repair confirmation

The self-hosted runner executed exact commit `c901358039c542678cf866876bc01b5539e15956`.

Final receipt:

- host: `digital-retina`
- Linux 6.8.0-117-generic x86_64 / glibc2.39
- Python 3.12.3
- 18/18 gates PASS
- fail_count = 0
- `local_model_baseline`: PASS
- tool transport: PASS
- structured returned tool call preservation: PASS
- `local_model_endpoint_boundary`: PASS
- declared oversize rejected before body read
- chunked streaming oversize rejected at MAX+1
- redirects fail closed
- endpoint userinfo forbidden
- transport read failures remain fail closed
- full pytest suite: 13/13 PASS in 0.15 s
- release claim: false
- whole FRANK release status: `NOT_CLAIMED`

H6 is therefore supported by the discriminating repair/retest; H4 remains unsupported. This is a harness defect fixed without weakening the product invariant.

## 10. Measurement interpretation

What the run establishes:

1. FRANK's engine-neutral local-model boundary can now carry the generic OpenAI-compatible tool contract end-to-end.
2. Structured tool-call responses remain available to higher layers.
3. Tool transport does not imply tool execution authority; the external effect/capability boundary remains necessary.
4. The repaired endpoint harness is stable on the actual Ubuntu VPS for the observed run.
5. The full current VPS integrity matrix remains green after the change.

What the run does NOT establish:

1. No real Qwen-class 4B was loaded during this run.
2. No model-level tool-selection accuracy was measured.
3. No quantization/backend was selected.
4. No throughput/tokens-per-second, VRAM/RAM, energy, thermal, or long-context performance was measured for a real 4B model.
5. No Andreas-PC target-machine execution receipt was produced.
6. Historical 74-module exact ledger and 71-DB payload-semantic migration remain separate release blockers.
7. FRANK v0.1 is therefore not release-complete.

## 11. Revised hypotheses and next discriminating experiments

### H7 — REAL_4B_TOOL_CALL_ACCEPTANCE

A pinned Qwen-class 4B + pinned local runtime can produce schema-valid FRANK tool calls through the now-complete transport boundary.

Required test:

- pin model revision + quantization + runtime commit + backend;
- enable/verify a tool-aware chat template;
- run deterministic FRANK tool-use cases;
- measure tool selection precision/recall, schema validity, argument validity, false-call rate, no-call correctness, latency and token cost;
- include adversarial/ambiguous tool cases;
- do not execute returned tools during the model-selection benchmark.

### H8 — PARALLEL_TOOL_CALLS_ARE_NOT_DEFAULT_SAFE

Although the transport can carry `parallel_tool_calls`, parallel tool intent should remain disabled until higher-layer conflict, authority, ordering and rollback semantics are tested.

Falsifier: matched experiments demonstrate no loss of deterministic authorization/order/recovery under parallel intents.

### H9 — TEMPLATE_IDENTITY_IS_PART_OF_MODEL_IDENTITY

For tool-using FRANK, model revision alone is insufficient; chat/tool template identity materially affects observable agent behavior.

Required evidence: hold weights/quantization fixed, vary template/runtime handling, measure tool-call correctness and failure modes.

### H10 — TARGET_PC_DOMINATES_RELEASE_DECISION

The Ubuntu VPS proves portability/integrity of current Python/runtime contracts, but cannot substitute for final Andreas-PC model/device acceptance.

Required test: complete the already-queued Andreas-PC hardware/software capability census and run the same pinned F6 tool/model suite there.

## 12. Architecture implication

The best current F6 layering is:

`FRANK cognitive request -> engine-neutral OpenAI contract (messages + tools + tool policy) -> local inference runtime -> structured non-authoritative model proposal -> FRANK validation/authorization/effect gateway -> observed effect receipt -> re-entry/outcome`

This is preferable to encoding llama.cpp-specific switches in the cognitive adapter. Runtime/template/quantization selection belongs in deployment/model configuration and acceptance evidence.

The result also reinforces the wider Research Center rule: test harnesses are part of the epistemic system. A test can be wrong while the product is behaving correctly; negative runs must retain enough trace detail to distinguish product defect, harness defect, environment defect and transient infrastructure.

## 13. Open blockers / next work priority

Highest-information next steps toward `Frank v0.1 voll lauffähig auf Andreas PC`:

1. Execute the Andreas-PC capability census already queued in FRANK state.
2. Select a small candidate matrix for real local 4B inference only after target hardware is known.
3. Run F6 real-model tool-call acceptance with exact model/runtime/template/quantization provenance.
4. Measure latency, tokens/s, first-token latency, RAM/VRAM, context/KV behavior, CPU/GPU path and failure recovery.
5. Then integrate model proposals with the existing external authorization/effect boundary; do not let model tool calls become authority by themselves.
6. Preserve the historical 74-services-tree ledger HOLD and incomplete 71-DB payload semantics until source-backed closure.
7. Final release gate remains real Andreas-PC acceptance, not repository/VPS greenness.

## 14. Final synthesis

This run produced a concrete FRANK v0.1 improvement rather than a report-only research cycle. Current external implementation evidence exposed a missing tool-request transport contract. The adapter was changed minimally, a deterministic regression was added, and the real Ubuntu VPS immediately falsified an unrelated assumption in an older response-boundary test. The negative result was traced to the harness, the product's fail-closed behavior was preserved, and the repaired suite returned to 18/18 PASS on the same real VPS.

The key scientific/engineering delta is therefore twofold:

- **positive**: F6 now has a verified engine-neutral request/response surface for local tool-capable models;
- **negative/epistemic**: a green local test is insufficient, and even a failing VPS test is not automatically a product defect. The causal repair loop must distinguish the tested invariant from the harness behavior that generates the observation.

No release or architecture promotion beyond this scoped transport contract is justified until real 4B and final Andreas-PC evidence exist.
