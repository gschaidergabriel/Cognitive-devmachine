# J-Space Executor Sequence Evidence Contract v1

Status: **SOURCE-LEVEL ARCHITECTURE CONTRACT**  
Persistent research entity: **Clay**  
Product: **EntityOS**  
Compute architecture: **HCU**  
Supervisor: **8.63 / FREE_ONLY**

## Purpose

This contract defines the minimum evidence boundary for any future claim that a J-Space / Vector-Control state at logical step `t` causally precedes and controls an actual model invocation at `t+1`.

It exists because a caller-supplied `step_index`, timestamp, ordinal, predecessor label, trace label, or narrative ordering can describe a temporal relation without proving one. Such labels MUST NOT create recurrent/temporal J-Space credit.

The retained donor history contains an explicit negative discriminator: a caller-labelled temporal-binding primitive was reverted at donor snapshot `ff67cf4192e9fbb3ea8aee2819f2dbeddd576ee6`. The safe successor design therefore requires sequence/adjacency evidence to originate at the actual executor boundary and to be admitted through the existing deterministic canonical state/evidence substrate.

## Non-negotiable law

```text
CALLER_LABELLED_TIME_OR_STEP != EXECUTOR_SEQUENCE_EVIDENCE
```

and:

```text
PREDECESSOR_TRACE + SUCCESSOR_INPUT_BINDING + CALLER_ORDINALS
    != VERIFIED_TEMPORAL_CAUSAL_EDGE
```

A positive recurrent edge requires an executor-owned admitted adjacency record.

## Existing evidence that may be composed

This contract does not create another execution, state, inference, J-Space, dataset, or effect authority. It composes existing current mechanisms:

- scheduler-owned `ENTITYOS_HCU_GRID_PLAN/v2`;
- actual executor I/O observation and `HCU_VERIFIED_MODEL_EXECUTION/v1`;
- canonical MiniUnifiedDB atomic model-execution admission;
- `HCU_MODEL_INPUT_CONTROL_BINDING/v1` plus its canonical admission path;
- `HCU_INFERENCE_RECEIPT/v4`;
- `ENTITYOS_HCU_JSPACE_INFERENCE_BINDING/v3`;
- `ENTITYOS_HCU_JSPACE_TRAINING_TRACE/v1`;
- `JSPACE_VECTOR_CONTROL_ABI/v1`;
- the single deterministic canonical state/evidence substrate;
- `EffectGate`/`EffectJournal` remain the only real-effect authority.

## Required future sequence primitive

A future implementation MAY be named `HCU_EXECUTOR_SEQUENCE_ADMISSION/v1` or a successor-dynamic equivalent. Naming does not create authority; the following properties do.

The sequence primitive MUST:

1. run at the same actual model-executor I/O boundary that emits/adopts the admitted model-execution observation;
2. reuse the existing canonical MiniUnifiedDB/UnifiedDB-compatible state/evidence substrate rather than create a second ledger;
3. assign sequence position/adjacency inside the deterministic store transaction or from an executor-emitted sequence receipt that is independently admitted there;
4. never accept caller-supplied predecessor/successor ordinals as sufficient evidence;
5. bind exact `executor_id`, entity `generation`, and an executor-owned sequence-lane identity;
6. bind exact predecessor and successor invocation identities plus their admitted `VerifiedModelExecution` receipt identities;
7. reject reuse of one executor-scoped invocation identity with byte-distinct execution evidence;
8. reject stale-generation edges;
9. reject self-edges;
10. reject reversed or non-adjacent edges when adjacency is claimed;
11. define branch/concurrency semantics explicitly rather than forcing wall-clock serialization onto parallel executions;
12. persist replay-stable canonical bytes and SHA-256 identity for the sequence record;
13. preserve UNKNOWN when outcome/effect state is unknown;
14. grant zero model/J-Space/training/whole-product runtime credit until exact admitted runtime evidence shows the real executor used this path.

## Executor-owned sequence lane

The lane identity MUST NOT be a free-form caller label.

A valid lane identity must be derived from exact executor-owned or deterministic canonical context sufficient to distinguish independent recurrent streams. Candidate inputs include:

- executor incarnation identity;
- entity generation;
- deterministic admitted stream/parent identity from Typed Entry when recurrence crosses events;
- scheduler/control-plane lane identity when recurrence is intra-request;
- exact model role / controlled cell where required.

If the current Typed Entry / GRID10 evidence does not expose enough deterministic stream identity to derive such a lane, the system MUST fail closed with a specific `EXECUTOR_SEQUENCE_LANE_IDENTITY_UNAVAILABLE` class rather than invent one from timestamps or trace names.

## Adjacency record minimum envelope

A canonical admitted adjacency record should bind, at minimum:

```text
schema
canonicalization_schema
generation
executor_id
sequence_lane_id
predecessor_invocation_id
predecessor_verified_execution_sha256
successor_invocation_id
successor_verified_execution_sha256
successor_model_input_control_admission_sha256
predecessor_training_trace_sha256
predecessor_vector_control_packet_sha256
sequence_position_or_executor_sequence_receipt_sha256
adjacency_sha256
```

The exact schema may evolve, but no field may silently substitute caller narration for executor/store evidence.

## Recurrent Vector-Control closure

For a positive recurrent-control edge, all of the following must describe one causal chain:

```text
TrainingTrace(t)
  -> exact JSPACE_VECTOR_CONTROL packet(t)
  -> exact successor ModelInputControlBinding(t+1)
  -> canonical ModelInputControlAdmission(t+1)
  -> actual executor input bytes(t+1)
  -> executor-owned sequence adjacency(t -> t+1)
  -> VerifiedModelExecution(t+1)
  -> InferenceReceipt/v4(t+1)
  -> JSpaceBinding/v3(t+1)
```

The existing model-input-control closure can prove exact packet delivery into the bound invocation. The new sequence evidence is the missing temporal authority: it proves which admitted execution was the executor-owned successor rather than trusting caller step labels.

Even after this closure, the claim remains **observable dataflow/sequence causality**, not proof that hidden states used the control signal beneficially. Hidden-state causal-use/benefit still requires model-specific lesion/shuffle/rescue or equivalent admitted evidence.

## Branching and concurrency

Parallel execution is valid HCU behavior. Therefore a sequence store must not equate logical adjacency with a single global wall-clock order.

Required rule:

- adjacency is defined within one exact executor-owned sequence lane;
- different lanes may advance concurrently;
- one lane position cannot be claimed by two divergent successor executions unless the schema explicitly represents a branch and binds distinct branch identities;
- if branch semantics are absent, concurrent divergent claims for the same predecessor/lane position must resolve atomically to one admitted record and one deterministic rejection;
- wall-clock timestamps are metadata only and never adjudicate the winner.

## Deterministic regression obligations

Before source promotion, a successor implementation should include at least these deterministic tests:

1. **caller-labelled ordinal rejection** — changing only caller `t/t+1` labels cannot create a valid edge;
2. **executor-assigned adjacency** — accepted edge derives position/adjacency from executor/store evidence;
3. **reversed-edge rejection** — successor/predecessor swap fails;
4. **self-edge rejection** — same invocation/receipt on both ends fails;
5. **stale-generation rejection** — no write survives;
6. **wrong-lane rejection** — edge cannot cross deterministic recurrent lanes;
7. **control-packet ancestry rejection** — predecessor trace packet must equal the exact packet admitted into successor input;
8. **successor-input mismatch rejection** — byte-valid but different successor input cannot reuse the edge;
9. **divergent replay rejection** — same canonical edge identity cannot map to different execution bytes;
10. **concurrent same-position conflict** — deterministic one-winner semantics unless explicit branch schema is active;
11. **idempotent exact replay** — exact same edge is stable;
12. **canonical-byte revalidation** — stored bytes re-canonicalize to the stored digest.

These are source-level regression obligations only. They do not replace exact FREE_ONLY runtime acceptance.

## Evidence ladder

- `SOURCE_CONTRACT_ONLY`: this document or source design exists.
- `SOURCE_REGRESSION_PRESENT`: deterministic implementation/tests exist at exact source identity.
- `EXACT_FREE_COMPONENT_RUNTIME`: exact source/hash-bound component tests execute on an admitted FREE_ONLY surface.
- `ACTUAL_EXECUTOR_SEQUENCE_OBSERVED`: the real admitted executor emits/adopts sequence evidence at exact identity.
- `RECURRENT_JSPACE_DATAFLOW_EDGE_VERIFIED`: predecessor trace/control bytes, successor input, executor adjacency, execution, inference and J-Space binding close at exact identities.
- `MODEL_SPECIFIC_CAUSAL_EFFECT_VERIFIED`: separate lesion/shuffle/rescue or equivalent evidence supports control-use/benefit.

No higher level may be inferred from a lower one.

## Current credit boundary

At creation of this contract:

```text
whole EntityOS/HCU runtime credit = 0
full HCU runtime credit = 0
J-Space model runtime credit = 0
training credit = 0
whole-product PASS = false
```

This contract creates no runtime or training credit.

## Next exact implementation gate

Do **not** recreate the reverted caller-labelled temporal binder.

The next source implementation should extend the single retained HCU donor lane only after it can derive a recurrent `sequence_lane_id` from deterministic admitted context and atomically assign/admit successor adjacency at the actual model-executor boundary using the existing canonical MiniUnifiedDB/UnifiedDB-compatible substrate. If deterministic lane identity is not yet available, first extend Typed Entry / control-plane provenance so the lane can be derived without caller narration.
