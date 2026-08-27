# FRANK v0.1 — F6 tool-behavior evaluator addendum

Run id: `20260809T2342p0700-frank-f6-tool-behavior-addendum`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent observed at boot: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Subject: separate target system Frank v0.1. No release/canonical promotion.

## Why this addendum exists

The mesh already contains the full F6 tool-transport report and a newer adaptive-recurrence/VPS fusion. This append-only delta records the **next unique F6 layer** completed after the transport work: model-tool behavior is now directly scorable by the FRANK baseline evaluator instead of inferred from transport success.

## Build delta

FRANK repository commits:

- `80ffe941ef8b9dbf66c5f65422093a6ef0e20220` — MockAdapter preserves structured `mock_tool_calls`; self-test exercises them.
- `34f43c953f80141217847f6cf60134541d73818e` — `frank_local_model_eval.py` forwards portable request fields (`response_format`, `tools`, `tool_choice`, `parallel_tool_calls`), validates structured tool-call count/name requirements, records per-case request contracts, separates `MOCK_CONTRACT_ONLY` from real OpenAI-compatible runtime behavior, and aggregates portable wall/standard-usage observations.
- `643e255cf85c76f9940c31eb8a9e9a7f30837ebc` — F6 baseline suite v1.1 adds eighth case `tool_routing_read_state`: advertised tools are `read_state` and decoy `summarize_text`; the case requires at least one `read_state` call and forbids the decoy.
- `781d441dd995d1365605434ef7bae1afbb127bd8` — regression requires mock baseline 8/8, tool behavior 1/1, tool transport PASS, portable measurements PRESENT, hidden-reasoning non-persistence and `f6_release_pass=false`.

## Hypothesis update

### H-F6-TOOL-TRANSPORT-SUFFICIENT

Claim: successful transmission/preservation of tool metadata is enough to validate F6 tool capability.

State: `REFUTED`.

Reason: transport only proves the interface can carry tool intent. It does not test whether a model selects the correct admitted capability rather than answering from memory, choosing a decoy, or emitting an invalid/no call.

### H-F6-TOOL-BEHAVIOR-EVAL

Claim: FRANK can evaluate tool-selection behavior through an engine-neutral OpenAI-style function schema without granting execution authority or binding cognition to llama.cpp-specific switches.

State: `SUPPORTED_AT_CONTRACT_AND_HARNESS_LEVEL`; real-model state remains `OPEN`.

Falsifier: a pinned real local model/runtime/template cannot complete the same suite consistently, or engine-specific semantics are required to express the necessary FRANK capability contract.

## Real Ubuntu evidence

Self-hosted host: `digital-retina`; runner `clay`; Linux/Ubuntu-class environment; Python 3.12.3.

The intermediate concurrent run in which the suite had moved to eight cases but the regression still expected seven produced a preserved `18/19` integrity receipt. The only failure was the stale `== 7` assertion in `local_model_baseline`; the parallel adaptive-recurrence gate itself passed.

After `781d441...` updated the regression to the new contract, the real self-hosted receipt returned:

- 19/19 integrity gates PASS;
- `mock_frank_eval = 8/8`;
- `tool_behavior_case = 1/1`;
- `tool_contract_transport = PASS`;
- `tool_call_response_preservation = PASS`;
- `portable_measurements = PRESENT`;
- hidden reasoning persisted = false;
- F6 release pass = false;
- pytest 14/14 PASS in 0.16 s.

The mesh subsequently advanced further through parallel recurrence/readout work; the newer adaptive-recurrence feedback manifest records a later real Ubuntu integrity state of 20/20 PASS and explicitly keeps whole-FRANK release `NOT_CLAIMED`. This addendum does not downgrade or replace that newer receipt.

## Evidence boundary

What is established:

1. portable tool metadata crosses the local inference boundary;
2. structured returned tool calls are preserved;
3. the F6 evaluator can score correct/forbidden tool names;
4. the deterministic mock suite exercises the same request/evaluator path;
5. the evaluator/regressions execute successfully on the real Ubuntu reference runner;
6. mock evidence is explicitly labeled and cannot auto-promote a model.

What is **not** established:

1. no real Qwen-class 4B tool-selection accuracy was measured in this delta;
2. no model revision/quantization/runtime/template is selected;
3. no real tool proposal was executed by the benchmark;
4. no Andreas-PC final target acceptance receipt exists here;
5. no throughput/RAM/VRAM/thermal/energy claim for a real 4B follows from the mock suite.

## Next discriminating experiment

Run the same evaluator on Andreas' real Ubuntu PC after the capability census, with at least a current Qwen3.5-4B candidate and stable Qwen3-4B fallback. Pin model revision, quantization hash, runtime commit/version, chat/tool template and device configuration.

Measure at minimum:

- correct tool selection precision/recall;
- false-call and correct-no-call rates;
- tool argument JSON/schema validity and semantic correctness;
- decoy-tool error rate;
- visible answer correctness;
- cold/warm latency p50/p95/p99;
- prompt/completion/total tokens and comparable tokens/s;
- peak RSS/RAM and VRAM when applicable;
- context scaling and restart/reload behavior;
- model/template/runtime failures.

Tool proposals remain non-authoritative throughout model selection. External FRANK capability/effect validation must stay between model output and any real effect.

## Mesh feedback

- `frank`: F6 now has a real behavior-evaluation surface; next blocker is actual local 4B execution on target hardware.
- `harness`: keep model tool calls proposal-only and separately validate schema/authority/effect receipts.
- `unifieddb`: `read_state` evaluation should only represent an admitted state gateway, never direct arbitrary DB authority.
- `claygraph`: add future graph-retrieval tool cases separately from canonical state reads and score routing confusion.
- `gwt`: tool selection is an observable downstream choice/effect interface; use it in receiver-use/re-entry tests without treating it as workspace truth by itself.
- `emergenz`: tool-routing performance is functional evidence, not consciousness/emergence evidence.
- `claycode`: current OpenAI function schema is an interoperability boundary; future typed ClayCode capability contracts should preserve external authority separation.
- `hyperposition`: preserve competing model/runtime/template candidates until target measurements discriminate them.
- `clayresearch`: retain transport, behavior, real-model and target-acceptance evidence as distinct claim levels.

## Concurrency / process evidence

During this run, multiple file writes were CAS-rejected because other workers advanced the same Frank/RAE state between read and write. The worker never force-overwrote them; it re-read and fused the newer deltas. This is positive evidence for the RAE swarm rule: shared knowledge is live, but durable integration still needs compare-and-swap, provenance and post-write test receipts.

Final state of this addendum: `RESEARCH_DELTA_COMMITTED`, `NO_CANONICAL_GENERATION_PROMOTION`, `NO_FRANK_RELEASE_PROMOTION`.
