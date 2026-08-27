# HCU J-Space Control Temporal Causality Gate v1

Status: **CURRENT RESEARCH / ACCEPTANCE GUARD**  
Authority: subordinate to current owner/supervisor authority; current observed supervisor is `SUPERVISOR_STEERING_8_66.json`, with execution authority resolved through `CLAY_EXECUTION_AUTHORITY.md`  
Product: **EntityOS**  
Compute architecture: **HCU**  
Mode: **FREE_ONLY**

## Purpose

Prevent a byte-valid `HCU_MODEL_INPUT_CONTROL_BINDING/v1` from being misinterpreted as causal evidence when the bound `JSPACE_VECTOR_CONTROL_ABI/v1` packet was produced only after the model invocation it is claimed to control.

This guard creates no second state, truth, effect, model, executor, J-Space, or dataset authority. It adds an explicit temporal/causal-order acceptance boundary to the existing HCU evidence chain.

## Exact observed source boundary

At the observed retained donor source, `global_jspace_gwt_v1.step(...)` computes a Global J-Space vector from the current contribution set and then emits the role-relevant Vector-Control packet from that vector.

The integrated execution/J-Space regression first admits a `ModelExecutionObservation`, then constructs the J-Space `CellContribution` set using that verified execution's output-producing cell/role, then calls `step(...)`, and finally builds the TrainingTrace from the resulting prototype/control packet.

Therefore, for that same regression episode:

`model invocation(i) -> observed model execution(i) -> contribution/output(i) -> J-Space step(i) -> control packet(i)`

The generated `control packet(i)` is temporally downstream of `model invocation(i)`. It cannot simultaneously be evidence that it controlled the exact input bytes of `model invocation(i)`.

`HCU_MODEL_INPUT_CONTROL_BINDING/v1` correctly proves a narrower byte-level fact when given exact pre-existing packet bytes and exact executor input bytes. That primitive does not itself prove that the packet existed before invocation or that the packet belongs to the correct predecessor J-Space step.

## Hypothesis and counterhypothesis

**H1 — FORWARD CONTROL EDGE**  
A packet produced by an admitted J-Space step at causal time/step `t` is incorporated into the exact executor input bytes of a distinct later invocation at `t+1`, and the later model output can then contribute to a new J-Space step at `t+1`.

**H0 — SAME-STEP POST-HOC LOOP**  
A model invocation is observed first; its output contributes to J-Space; J-Space then produces a packet; metadata later binds that packet back onto the already-completed same invocation. All hashes may be internally consistent while the claimed control direction is impossible.

A byte-occurrence proof without temporal predecessor identity does not distinguish H1 from H0.

## Required causal topology

For positive `CONTROL_PRESENT_AT_EXECUTOR_INPUT` promotion, require an acyclic edge of the form:

`JSpaceStep(t) / VectorControlPacket(t)`  
`        -> ModelInputControlBinding(t -> t+1)`  
`        -> ModelExecutionObservation(t+1)`  
`        -> VerifiedModelExecution(t+1)`  
`        -> InferenceReceipt(t+1)`  
`        -> contribution/output(t+1)`  
`        -> JSpaceStep(t+1) / VectorControlPacket(t+1)`

The packet that controls invocation `t+1` MUST NOT be the packet whose producer depends on the output of invocation `t+1`.

A boot/initial invocation may explicitly carry `NO_PREDECESSOR_CONTROL` or another versioned null-control condition. Missing predecessor control must not be silently filled with a packet generated after the invocation.

## Required next binding delta

Extend the existing single-lane evidence chain with a temporal predecessor identity. A compatible successor may add these fields to a versioned model-input-control admission/binding or a single subordinate edge object:

- `predecessor_jspace_trace_sha256`;
- `predecessor_vector_control_packet_sha256`;
- `predecessor_step_id` or another deterministic causal-step identity;
- `controlled_invocation_id`;
- `controlled_model_execution_observation_sha256` once admitted;
- `causal_event_id` / Entry event identity and concrete Entry admission identity already required by current HCU provenance;
- exact generation;
- exact GRID plan, cell and role;
- exact consumed input SHA-256/size;
- self-authenticating binding digest under the current canonicalization authority.

The producer must prove ordering from admitted evidence, not from wall-clock text supplied by a caller. Prefer deterministic causal sequence/parent identity over timestamps.

## Promotion law

Until the forward temporal edge is implemented and verified at exact identity:

- `HCU_MODEL_INPUT_CONTROL_BINDING/v1` may receive **byte-level packet-presence / input-binding source or component credit** at its exact tested scope;
- a same-invocation post-hoc packet association receives **zero control-direction credit**;
- `JSpaceBinding/v3` receives no proof that the current packet caused the current invocation;
- no model-internal J-Space causality credit is granted;
- no J-Space model-runtime credit is granted from this relation alone;
- no training promotion is unlocked by this relation alone.

Byte delivery still does not prove hidden-state causal influence. Model-specific influence requires separately admitted intervention/lesion/rescue evidence under the atomic unusual-experiment law.

## Fail-closed cases

Reject forward-control promotion on any of:

- packet producer trace depends on output from the same invocation being claimed as controlled;
- predecessor J-Space trace identity absent or not externally admitted;
- predecessor packet identity differs from the exact packet found in consumed input bytes;
- invocation identity reused as both packet producer parent and packet-controlled child without an explicit acyclic step edge;
- ordering inferred only from mutable wall-clock strings or caller narration;
- generation mismatch;
- Entry event/admission mismatch;
- route/GRID/cell/role mismatch;
- input bytes mutated after binding;
- packet exists only after model execution admission;
- null/boot control silently relabelled as a real predecessor packet;
- hidden-state use inferred from byte presence, coherence, output similarity, self-report, recurrence or majority.

## Cheapest high-information discriminator

Do not run a new unusual experiment for this gate.

First add a deterministic source regression with two adjacent logical steps:

1. produce `packet(t)` from a completed prior J-Space step;
2. construct exact immutable executor input bytes for invocation `t+1` containing `packet(t)` exactly once;
3. bind/admit those bytes before or at model-execution admission;
4. reject a forged edge where `packet(t+1)` produced from `output(t+1)` is rebound to `invocation(t+1)`;
5. echo the predecessor-control binding identity through VerifiedModelExecution -> InferenceReceipt -> J-Space/Training provenance without changing truth/effect authority.

This deterministic temporal regression is ordinary source/integration work. It does not require the unusual-experiment lease and grants no runtime/model/training credit until executed on an admitted exact-source surface at the corresponding scope.

## Current execution / coordination boundary

Current observed supervisor 8.66 remains `FREE_ONLY`. The active owner authority at `CLAY_EXECUTION_AUTHORITY.md` -> `governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md` authorizes zero-monetary-cost development/test execution inside `clay-direct-dev` and on the local workstation as the normal Linux development user, with the declared resource/evidence boundaries. Unrelated VPS-host changes, new local root/sudo authority, new external production effects, Together inference/training/preflight, paid fallback, and paid/subscription/unknown monetary provider execution remain fail-closed unless separately authorized.

The retained Vercel controller's `Sandbox.create` quota gate is a separate provider-specific FREE_ONLY admission boundary. It must not be generalized back into the obsolete blanket prohibition on owner-authorized local/`clay-direct-dev` execution, and local/VPS success still does not by itself mint whole EntityOS/HCU or J-Space runtime credit.

For the current `go`, no shared immutable macrocycle/request identity is exposed to this organ and the available user-message time is minute precision only. Therefore:

`COORDINATION_BLOCKED_NO_UNUSUAL_EXPERIMENT`

No local/VPS bridge tool is exposed to this ChatGPT organ in the current session, so bridge health and exact-source runtime execution remain unobserved here. That is tool-surface/infrastructure status, not product failure.

This guard is a deterministic research/architecture delta only and does not itself grant execution authority beyond the current owner/supervisor stack.
