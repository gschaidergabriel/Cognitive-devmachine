# HCU J-SPACE INTERVENTION BACKEND SELECTION v1

Status: CURRENT-FACING SOURCE / RESEARCH CONTRACT — NO MODEL-RUNTIME CREDIT
Authority epoch at creation: 8.68
Program: ENTITYOS_HCU
Product: EntityOS
Architecture: HCU
Mode: FREE_ONLY

## Decision

Use a **single local HuggingFace/PyTorch model execution family** for J-Space observation and controlled activation intervention. Keep the existing `llama.cpp` service as a separate `LOCAL_INFERENCE_CAPABLE` path.

Current preferred execution ladder:

1. **Primary:** `tools/hcu_jspace_local_activation_probe.py` in `observation` mode on an exact local model snapshot. This is the cheapest ordinary discriminator and performs no hidden-state modification.
2. **Exact-target observation/sensitivity donor:** `the artefact/blogpost_entity/mini_cognition/check_qwen35_jlens_admission.py` for Qwen3.5-0.8B layout, weighted forward activation recording and bounded Jacobian evidence.
3. **Primary intervention:** the same in-repo `tools/hcu_jspace_local_activation_probe.py` in `intervention` mode, only after a valid canonical create-only `go` experiment lease. It runs the clean/corrupted/target/sham/off-target family.
4. **Fallback donor:** direct local NNsight/PyTorch only if the in-repo hook path cannot expose or modify the required activation reliably for the exact target architecture.
5. **Higher-complexity fallback:** local NNsight/vLLM or `nnsight-serve` only if model/resource/throughput constraints justify worker-process indirection and exact identity binding can still be closed.
6. Remote NDIF or other hosted inference is NOT selected under current provider quarantine and has zero credit by default.

This selects execution mechanisms only. It creates no new truth store, product, effect authority, persistent identity, provider authority or canonical model memory.

## Why this convergence

`tools/local_research_model_server.sh` records `jspace_intervention_capable=false`. Its post-load `/props` observation and executable/model-file hashes are useful local inference identity evidence, but they do not expose a named internal activation intervention ABI and are not loader-consumption attestation.

The current in-repo activation probe closes the missing **source implementation path** without adding another dependency stack:

- it forces Hugging Face/Transformers offline mode before model imports;
- it requires a local model directory;
- it resolves current supervisor authority dynamically;
- it records exact local model tree identity and post-load parameter-value identity;
- it installs a Python socket network fence;
- `observation` mode performs one forward pass, records one named layer/position activation and output digests, and explicitly requires no unusual-experiment lease because no hidden state is modified;
- `intervention` mode requires the canonical atomic claim and executes clean/corrupted/target/sham/off-target conditions using direct PyTorch forward-hook manipulation;
- emitted records remain bounded candidate evidence and do not mint truth or broad runtime credit.

Therefore NNsight is no longer the preferred first implementation. Its current external documentation remains useful corroboration that activation access/modification and vLLM-backed intervention are established mechanisms, but duplicating the now-existing in-repo PyTorch hook path would have lower information value.

TransformerLens activation patching remains a useful experimental reference: clean and corrupted executions, targeted activation replacement, and output recovery measurement. It is donor methodology, not EntityOS authority.

## Backend capability classes

### `LOCAL_INFERENCE_CAPABLE`

May produce local model outputs with exact model/runtime identity. Does not imply internal activation observability or causal intervention capability.

Current `llama.cpp` server remains here until an independently verified intervention gate says otherwise.

### `JSPACE_OBSERVATION_CAPABLE`

Requires exact admitted runtime evidence binding at minimum:

- canonical repo/source identity and current authority epoch;
- exact model/config/checkpoint tree identity;
- exact tokenizer identity;
- exact backend/runtime/package/build identity;
- post-load model/parameter identity with loader-consumption status stated separately;
- causal event, admission, route, generation and InferenceReceipt identity;
- named activation site identity including layer and position;
- activation tensor shape/dtype/device and digest;
- exact input token identity;
- exact model output/logit digest;
- no network attempts on the offline local path;
- explicit field classification as observed/derived/candidate/unknown.

Observation alone does not establish causality.

### `JSPACE_INTERVENTION_CAPABLE`

Requires all observation requirements plus the full current `HCU_JSPACE_LOCAL_INTERVENTION_BACKEND_GATE_V1.md` control structure and a valid canonical unusual-experiment claim before hidden-state modification.

Minimum causal family:

- `BASELINE_CLEAN`
- `BASELINE_CORRUPTED`
- `INTERVENTION_TARGET`
- `SHAM_CONTROL`
- `OFF_TARGET_CONTROL`

The target intervention must outperform the sham on the predeclared target metric while the off-target regression stays inside its declared bound. One successful patched output is not sufficient.

## Exact approximately-0.8B target donor

Current repository donor code already targets:

`Qwen/Qwen3.5-0.8B`

via:

`the artefact/blogpost_entity/mini_cognition/check_qwen35_jlens_admission.py`

Source-observed donor phases:

1. `layout`: constructs/validates the Qwen3.5 text layout and `jlens` compatibility at source/runtime-layout scope;
2. `forward`: loads exact weighted local bytes, validates weighted dtype and records activations across the stack through `jlens.ActivationRecorder`;
3. `jacobian`: computes one bounded `jacobian_for_prompt` and verifies finite fp32 `[d_model, d_model]` output.

This donor is high-value for exact-target structural, activation-observation and sensitivity evidence. Its current source does **not** execute the target/sham activation-manipulation family, so it must not be promoted to `JSPACE_INTERVENTION_CAPABLE` by itself.

Preferred fusion on the same exact Qwen3.5-0.8B snapshot:

`exact model tree -> jlens layout/forward/Jacobian observation -> in-repo observation probe -> leased in-repo intervention probe -> InferenceReceipt/J-Space trace binding`

Qwen3-0.6B or another smaller already-present local model may be used only as a mechanism-debug fallback if the exact 0.8B target is blocked by local compatibility/resources. Success on a smaller model grants zero exact Qwen3.5-0.8B credit.

The official Qwen3.5-0.8B checkpoint exists and has a Transformers path, but **local execution compatibility and resource fit remain UNKNOWN until observed on the authorized surface**.

## Receipt requirements

For observation mode, emit the current probe receipt with:

- canonical Git SHA/source identity;
- current supervisor hashes;
- exact local model tree identity;
- runtime/package/model/tokenizer classes and versions;
- post-load parameter-value identity with `loader_consumption_attestation=false` unless separately proven;
- causal event/admission/route/generation/InferenceReceipt IDs;
- named activation site and activation/output digests;
- network-attempt count;
- exact result/exit status and evidence classification.

For intervention mode, additionally bind:

- canonical atomic claim identity and result path;
- clean/corrupted token identities;
- target/sham/off-target condition identities;
- reference activation/vector identity;
- before/after activation digests;
- fixed target and off-target metrics;
- measured deltas against controls;
- result credit fixed to bounded candidate scope unless current canonical admission explicitly promotes it.

Loader-consumed source bytes remain a separate unsolved evidence boundary. Post-load parameter-value hashing is not loader-consumption attestation.

## Security / isolation

- Local model snapshots only for the current offline probe; no implicit model download.
- Provider credentials are unnecessary and must not be used to bypass provider quarantine.
- Python socket fencing is useful evidence but does not automatically equal OS-level network isolation; an authorized local/VPS capsule may add an OS-level no-network namespace/fence where practical.
- If NNsight/vLLM is later used, keep any intervention service loopback/sandbox scoped; serialized intervention payloads must be treated as trusted executable-local input, not exposed as an unauthenticated network service.
- Model text, logits, activations, Jacobians and intervention outcomes remain measurements/candidates only; they cannot mint canonical truth or bypass EffectGate/EffectJournal.

## Falsifiers

Downgrade or reject the selected path if any of these is observed:

- exact local Qwen3.5-0.8B snapshot cannot be loaded inside the zero-cost resource envelope;
- the in-repo layer resolver cannot stably identify the exact target activation site;
- forward-hook modification does not affect the exact forward pass that produces the bound output;
- observation mode touches network or requires provider secrets;
- exact model/tokenizer/runtime/generation provenance is ambiguous;
- post-load identity is incorrectly presented as loader-consumption attestation;
- sham effects are comparable to or exceed the declared target effect;
- off-target regression exceeds the predeclared bound;
- the canonical atomic claim cannot be validated before intervention;
- a proposed fallback requires an unadmitted hosted/provider path.

If the direct in-repo PyTorch hook mechanism fails due to architecture-specific hook semantics rather than resources, NNsight becomes a justified fallback discriminator. If it fails only because of memory/throughput, test a smaller debug model or local vLLM without weakening the causal acceptance gate.

## Next exact discriminator

On an exposed authorized zero-cost local normal-user or `clay-direct-dev` execution surface:

1. re-enter exact current `main` and authority;
2. resolve whether an exact local `Qwen/Qwen3.5-0.8B` snapshot is already present and identity-bind it without network;
3. execute `tools/hcu_jspace_local_activation_probe.py --mode observation` at one fixed named layer/position with exact causal IDs and output receipt;
4. in parallel only where nonduplicate, execute the existing offline-first Qwen3.5 `jlens` layout/forward gate against the same snapshot;
5. compare model/tokenizer/runtime/activation identities and preserve loader-consumption as UNKNOWN unless independently attested;
6. do **not** run `--mode intervention` for a `go` macrocycle unless the canonical create-only atomic lease exists and is reproducible;
7. once a valid future lease is available, execute the five-run intervention family and bind its receipt to current `InferenceReceipt/v4`/successor identity;
8. re-enter current main before any J-Space/model/training promotion.

## Track effect

- Track A — `ENTITYOS_EXECUTABLE_CONVERGENCE`: advanced by converging on the already-landed in-repo PyTorch probe instead of introducing a redundant primary runtime, while keeping `llama.cpp` as the stable local inference service.
- Track B — `HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT`: advanced at HCU interface/evidence-contract level through explicit inference/observation/intervention capability classes and causal receipt bindings.
- Track C — `GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS`: advanced at source/prototype level by fusing the exact Qwen3.5-0.8B `jlens` donor with the now-existing observation-first/intervention probe and making an ordinary no-lease observation run the next executable discriminator.

Runtime credits remain zero until exact admitted execution evidence exists.
