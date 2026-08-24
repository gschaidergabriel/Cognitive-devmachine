# HCU J-SPACE INTERVENTION BACKEND SELECTION v1

Status: CURRENT-FACING SOURCE / RESEARCH CONTRACT — NO MODEL-RUNTIME CREDIT
Authority epoch at creation: 8.68
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Mode: FREE_ONLY

## Decision

Keep the current local `llama.cpp` path as `LOCAL_INFERENCE_CAPABLE` and add a separate, provider-independent **instrumentable local intervention lane** for J-Space experiments.

Preferred first implementation candidate:

1. `NNsight(LanguageModel)` over a locally loaded HuggingFace/PyTorch checkpoint when the selected model fits the authorized zero-cost local/VPS resource envelope.
2. `nnsight` + local `vLLM` / `nnsight-serve` only when a persistent engine materially improves throughput or model compatibility and the exact local package/build/model identity can be bound.
3. Remote NDIF or any other hosted inference is NOT part of this selection under current authority. It requires separate typed FREE provider/admission treatment before secrets or network and receives zero credit by default.

This file selects an experimental mechanism, not a new truth store, product, effect path, model authority, or provider authority.

## Why this split

The existing `tools/local_research_model_server.sh` deliberately records `jspace_intervention_capable=false`. Its post-load `/props` observation is useful identity evidence but does not expose named internal activations for controlled causal intervention and is not loader-consumption attestation.

Current external mechanisms provide the missing primitive:

- NNsight local tracing wraps PyTorch language models and exposes named intermediate module outputs during forward execution.
- NNsight permits in-place activation modification during a trace, supporting ablation, steering and patch-style causal interventions.
- NNsight's vLLM integration exposes intervention hooks inside an engine whose model execution may live in worker processes; this is a higher-complexity option and therefore secondary to direct local PyTorch for the first discriminator.
- TransformerLens activation patching provides a useful experimental template: clean run, corrupted run, replace a selected corrupted activation with its clean counterpart, then measure target-output recovery.

These are donor principles only. Clay keeps its canonical evidence, state, causal identity and EffectGate/EffectJournal boundaries.

## Backend capability classes

### `LOCAL_INFERENCE_CAPABLE`

May produce local model outputs with exact model/runtime identity. Does not imply activation observability or intervention capability.

Current `llama.cpp` server remains here unless its runtime gains an independently verified activation-intervention mechanism satisfying the current gate.

### `JSPACE_OBSERVATION_CAPABLE`

Requires, at minimum:

- exact model/checkpoint identity;
- exact tokenizer identity;
- exact backend/runtime/package/build identity;
- process/load identity sufficient to bind the observed forward execution;
- named activation site identity;
- observed tensor shape/dtype/device and digest;
- exact input/token identity;
- exact model output identity;
- trace identity bound to the causal event/admission/route/model-execution chain.

Observation alone still does not establish causality.

### `JSPACE_INTERVENTION_CAPABLE`

Requires all `JSPACE_OBSERVATION_CAPABLE` fields plus the full gate in `HCU_JSPACE_LOCAL_INTERVENTION_BACKEND_GATE_V1.md`, including target intervention, sham control, off-target control, output metric deltas and trace-to-`InferenceReceipt/v4` binding.

## First implementation profile: `NNsight` direct local PyTorch

Use this profile first because it minimizes moving parts.

Required deterministic preflight before any causal credit:

1. resolve exact canonical current authority and FREE_ONLY mode;
2. verify the selected checkpoint/model is already available or can be obtained through an authorized zero-monetary-cost path;
3. record package versions and hashes for Python, PyTorch, Transformers and NNsight where reproducibly available;
4. bind exact model config/checkpoint/tokenizer file identities;
5. load the model locally with provider secrets absent from the experiment environment;
6. enumerate the model module tree and choose one explicit activation site by stable module path plus layer/position/component identity;
7. run one deterministic observation-only probe and verify the activation tensor can be saved and digested;
8. only then execute the minimal causal family.

Do not claim loader-consumed-byte attestation merely from hashing files before or after `from_pretrained`. Loader-consumption remains a separate exact evidence problem.

## Minimal causal family

Use one fixed prompt pair and one fixed target metric:

- `BASELINE_CLEAN`
- `BASELINE_CORRUPTED`
- `INTERVENTION_TARGET`: patch or replace exactly one declared activation site in the corrupted run using the clean activation or another predeclared intervention vector
- `SHAM_CONTROL`: identical trace machinery with an intervention that should have no causal target effect
- `OFF_TARGET_CONTROL`: measure at least one unrelated output/behavior metric under the target intervention

For a first discriminator, prefer same-length/same-token-layout clean/corrupted inputs where possible so position identity does not become an avoidable confound.

## Receipt schema minimum

Emit a bounded candidate receipt such as `HCU_JSPACE_LOCAL_INTERVENTION_RECEIPT/v1` containing:

- canonical repo SHA/tree and authority epoch;
- experiment source manifest digest;
- backend class and exact package/build identities;
- checkpoint/config/tokenizer identities;
- loader-consumption status: `VERIFIED | UNKNOWN | REJECTED`;
- causal event/admission/route/generation/model-execution identities;
- activation site path, layer, position, component, tensor shape/dtype/device and pre/post digests;
- clean/corrupted/target/sham/off-target run identities;
- intervention operator and source vector/activation identity;
- target metric definition fixed before comparison;
- target metric values for every run;
- off-target metric definition and values;
- stdout/stderr/result digests and exit status;
- resource measurements;
- explicit epistemic classification per result field;
- credit section fixed to zero unless a higher current authority/evidence gate explicitly promotes it.

## Security / isolation

- Bind local intervention servers to loopback by default.
- Do not inherit external provider secrets into local experiment processes unless separately required and admitted; the first profile requires none.
- `nnsight-serve` accepts serialized intervention payloads and therefore must never be exposed as an unauthenticated external service. If used, keep it loopback/sandbox scoped and treat trace payloads as executable/trusted-local input.
- Do not use remote NNsight/NDIF as a shortcut around current provider quarantine.
- Model-generated text, hidden states and intervention outcomes remain measurements/candidates only and cannot mint canonical truth or real effects.

## Acceptance ladder

`BACKEND_SELECTED_SOURCE_ONLY`
: this document only.

`LOCAL_BACKEND_IMPORT_AND_MODEL_LOAD_OBSERVED`
: exact zero-cost local environment can import the chosen backend and load the selected model; no J-Space credit.

`JSPACE_OBSERVATION_CAPABLE`
: exact named activation is observed and bound to source/model/runtime/input/output identities.

`JSPACE_INTERVENTION_CAPABLE`
: minimum causal family passes the current intervention gate with sham/off-target controls.

`JSPACE_CAUSAL_CANDIDATE`
: intervention effect survives declared controls and exact provenance/generation checks; still requires canonical review/promotion.

No stage automatically grants whole EntityOS/HCU, full HCU, training or canonical semantics credit.

## Falsifiers

Reject this backend selection for the first experiment if any of these is observed:

- the exact local Qwen checkpoint cannot be loaded through the selected NNsight/PyTorch path inside the zero-cost resource envelope;
- the target model's module/activation path is unstable or cannot be deterministically identified;
- activation modification is not actually applied to the forward pass that produces the bound output;
- vLLM worker/process indirection prevents exact activation/run identity binding at acceptable complexity;
- sham controls change the target metric as much as the declared target intervention;
- off-target regressions violate the predeclared bound;
- source/model/runtime/tokenizer/generation identity is ambiguous;
- the experiment would require an unadmitted hosted/provider path.

If direct NNsight/PyTorch fails only on memory/throughput rather than intervention semantics, then evaluate the local `nnsight` vLLM runtime as the next candidate instead of weakening the causal gate.

## Existing exact-target donor: Qwen3.5-0.8B + `jlens`

Current repository donor code already contains an offline-first exact-target gate at:

`the artefact/blogpost_entity/mini_cognition/check_qwen35_jlens_admission.py`

It targets `Qwen/Qwen3.5-0.8B`, validates the text configuration/layout, can record weighted forward activations across the residual stack through `jlens.ActivationRecorder`, and has a bounded `jacobian_for_prompt` phase. This is valuable and should be reused rather than replaced.

Capability classification from source inspection only:

- layout phase -> `SOURCE_LAYOUT_COMPATIBILITY_CANDIDATE`;
- weighted forward hooks -> candidate precursor to `JSPACE_OBSERVATION_CAPABLE` after exact runtime/model/tokenizer/load identities are bound;
- bounded Jacobian -> `JSPACE_LOCAL_SENSITIVITY_MEASUREMENT_CANDIDATE`;
- target/sham activation manipulation -> **NOT PRESENT IN THE CURRENT DONOR SCRIPT**;
- `JSPACE_INTERVENTION_CAPABLE` -> **NOT ESTABLISHED**.

Therefore the preferred fusion is:

1. keep the existing Qwen3.5-0.8B `jlens` lane for exact-target layout/forward/Jacobian observation and sensitivity evidence;
2. add NNsight on the same exact local PyTorch model/checkpoint for target/sham activation manipulation;
3. bind both measurements to one canonical event/admission/route/model-execution/InferenceReceipt identity family where feasible;
4. use Qwen3-0.6B or another smaller model only as a mechanism-debug fallback if exact Qwen3.5-0.8B resource/compatibility constraints block the first instrumented run; smaller-model success must not be promoted into exact 0.8B model credit.

The official Qwen3.5-0.8B Transformers checkpoint is an exact-size target candidate, but NNsight compatibility with that concrete multimodal/composite architecture remains `UNKNOWN` until locally executed. Do not infer it from generic PyTorch support alone.

## Next exact discriminator

On an exposed authorized zero-cost local normal-user or `clay-direct-dev` execution surface:

1. re-enter exact current main and authority;
2. prefer exact `Qwen/Qwen3.5-0.8B` when its local checkpoint is already present or can be obtained through an authorized zero-monetary-cost path;
3. execute/reuse the offline-first `jlens` layout -> forward gates to establish exact-target structural/activation observation evidence without claiming intervention credit;
4. install/use NNsight only inside the authorized local/sandbox environment and attempt an observation-only trace on the same exact loaded model;
5. bind the first named residual-stream/equivalent activation site to exact input/token/output and runtime identities;
6. if that succeeds, execute the five-run clean/corrupted/target/sham/off-target family;
7. emit the bounded exact-identity receipt and re-enter main before any promotion.

This discriminator is ordinary deterministic research/acceptance work. A genuinely novel/unusual intervention remains subject to the canonical `go` atomic lease protocol.

## Track effect

- Track A — `ENTITYOS_EXECUTABLE_CONVERGENCE`: advanced by separating the stable local inference service from the higher-risk instrumentable causal research backend rather than overloading one runtime with incompatible evidence semantics, while reusing the exact-target Qwen3.5 `jlens` donor instead of inventing a parallel observation lane.
- Track B — `HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT`: advanced at HCU interface-contract level through explicit backend capability classes and exact causal identity/receipt requirements.
- Track C — `GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS`: advanced at source/research-contract level by fusing the existing Qwen3.5-0.8B Jacobian/activation-observation donor with NNsight as the missing manipulation backend and defining falsifiers plus the five-run acceptance family.

Runtime credits remain zero until exact admitted execution evidence exists.
