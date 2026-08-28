# HCU J-Space Model-Input Control Causality Gate v1

Status: **CURRENT RESEARCH / ACCEPTANCE GUARD**  
Authority: subordinate to current owner/supervisor authority; current admitted supervisor is `SUPERVISOR_STEERING_8_65.json`  
Product: **EntityOS**  
Compute architecture: **HCU**  
Mode: **FREE_ONLY**

## Successor authority / runtime update — supervisor 8.65

The current retained executor is `gschaidergabriel/Dr.-Unterweger#810 @ 2da99e0458809988190c129b04cae913d1f15d92`. Provider runtime logs establish HTTP 200 serverless **function-runtime** execution at that exact deployed source, but only at the declared diagnostic no-Sandbox scope.

This narrows the executable blocker without promoting this guard: remaining included Vercel Sandbox quota is still not directly observed, so `Sandbox.create` remains fail-closed. No Python/sqlite3/_sqlite3, HCU execution, local-model execution, Vector-Control consumption, J-Space/GWT causality, training, or whole EntityOS/HCU runtime credit follows from the HTTP 200 observation.

The required `HCU_MODEL_INPUT_CONTROL_BINDING/v1` discriminator below therefore remains current. Source-guard proliferation is paused unless executable counterevidence requires another guard; work should converge this primitive into the single retained donor/executor causal path rather than create a competing lane.

## Purpose

Prevent a source/runtime association between `JSPACE_VECTOR_CONTROL_ABI/v1` and an HCU model inference from being promoted into a claim that the model actually consumed that control packet.

This guard creates no second state, truth, effect, model, executor, or dataset authority. It only tightens the evidence boundary for J-Space/model-runtime promotion.

## Exact observed source boundary

Observed retained HCU donor snapshot:

`gschaidergabriel/clay-global-research-entity#1263 @ 511d568932bf47828679e3ca6ba05650f18d284d`

Observed retained executor snapshot:

`gschaidergabriel/Dr.-Unterweger#810 @ b6fcb5e26b66f30951a308caf6f23df8192d4040`

At the donor snapshot, `ENTITYOS_HCU_JSPACE_INFERENCE_BINDING/v3` carries both:

- `vector_control_packet_sha256`, sourced from the admitted J-Space training trace; and
- `input_sha256` / `input_size`, sourced from `HCU_INFERENCE_RECEIPT/v4` / verified model execution.

However the current v3 constructor/validator does not establish a dataflow identity between those two evidence objects. It proves that the same binding record references both, not that the actual executor input bytes contained or deterministically derived from the exact Vector Control packet.

The integrated producer regression makes this distinction observable. It constructs `ModelExecutionObservation.input_sha256` independently, admits model execution, and only afterwards constructs the Global J-Space/GWT step and its Vector Control packet used by `TrainingTrace/v1`. Therefore the current regression can pass even when the observed model input bytes have no demonstrated dependency on the Vector Control packet.

## Hypothesis and counterhypothesis

**H1 — CONTROL-CONSUMED**  
The exact `JSPACE_VECTOR_CONTROL_ABI/v1` packet (or one explicitly admitted deterministic transform of it) is present in the exact bytes consumed by the model executor for the bound invocation.

**H0 — POST-HOC ASSOCIATION**  
The model executor consumes unrelated input bytes; a J-Space step and Vector Control packet are constructed later and are associated with the same execution through trace metadata only.

Current `JSpaceBinding/v3` source invariants do not discriminate H1 from H0.

## Promotion law

Until an exact model-input control binding is implemented and executed:

- `JSpaceBinding/v3` may receive **association / causal-metadata component** credit at its exact tested scope;
- it must not receive credit for **Vector-Control consumption by the model**;
- it must not receive credit for **model-internal J-Space causality**;
- it must not receive **J-Space model-runtime credit**;
- it must not unlock training promotion by itself.

Current whole EntityOS/HCU runtime, full-HCU runtime, J-Space model-runtime, and training credit remain zero.

## Required next primitive

Converge one non-competing primitive, provisionally:

`HCU_MODEL_INPUT_CONTROL_BINDING/v1`

It must bind, at minimum:

- current generation;
- Entry event identity;
- concrete Entry admission identity;
- route decision identity;
- exact GRID10 plan identity;
- output/target model cell and role;
- exact `JSPACE_VECTOR_CONTROL_ABI/v1` packet identity;
- exact packet JCS UTF-8 bytes or an explicitly versioned deterministic transform identity;
- exact executor-consumed input SHA-256 and byte count;
- executor/invocation identity when available;
- a self-authenticating binding digest under the current canonicalization authority.

The executor-side producer must validate the binding against the **actual input bytes before or at invocation admission**, not against a caller-asserted hash after the fact.

An acceptable direct-byte discriminator is:

1. canonicalize/validate the exact Vector Control packet;
2. obtain the exact bytes presented to the model executor;
3. require either:
   - the exact packet wire bytes occur in one unambiguous admitted location in the model input envelope, or
   - an explicitly versioned deterministic input-envelope transform reproduces the exact consumed input bytes from the packet plus other admitted inputs;
4. bind the resulting input digest/size to the executor-minted invocation observation;
5. require downstream `VerifiedModelExecution`, `InferenceReceipt`, and J-Space binding to echo that binding identity.

Byte occurrence alone is dataflow evidence, not proof that hidden states causally used the signal. Model-specific causal credit still requires admitted intervention/lesion/rescue evidence under the current experiment-coordination law.

## Fail-closed cases

Reject model-input control promotion on any of:

- packet generated only after the observed model invocation;
- packet digest co-located with an inference receipt but no input-byte relation;
- caller-asserted input hash without executor-side byte observation;
- multiple ambiguous packet occurrences without a versioned envelope rule;
- stale generation;
- cell/role mismatch;
- route/GRID identity mismatch;
- input-byte mutation after binding;
- transform schema/version ambiguity;
- inferred hidden-state use from coherence, output similarity, self-report, or metadata recurrence.

## Current executor interaction

The retained PR810 `SOURCE_REBOUND_READY` 17-blob capsule remains useful for the narrower component question it was designed to answer: exact source/executor closure through `VerifiedModelExecution/v1 -> InferenceReceipt/v4 -> Global J-Space/GWT -> TrainingTrace/v1 -> JSpaceBinding/v3` with its declared regression fence.

This guard does **not** invalidate that component test and does not force a duplicate executor lane. It only prevents a future green run of that capsule from being over-promoted into proof that the Vector Control packet was consumed by the model.

The next executor extension should occur in the same retained donor/executor lanes after the FREE_ONLY Sandbox gate is directly admitted and the current exact-source environment probe passes, or when newer executable counterevidence justifies advancing the single-lane source contract.

## Coordination / execution boundary for this macrocycle

No shared immutable macrocycle/request ID was exposed to this organ, and available user-message metadata is only minute-precision. Therefore no canonical unusual-experiment trigger key can be proven under the current atomic lease protocol:

`COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`

No unusual intervention, paid execution, Together preflight, VPS/self-hosted/production test, Vercel Sandbox creation while quota is unobserved, or Vercel upgrade path is authorized or used by this guard.
