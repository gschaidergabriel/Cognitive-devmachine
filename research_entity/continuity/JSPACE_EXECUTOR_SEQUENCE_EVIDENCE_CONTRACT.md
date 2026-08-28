# J-Space Executor Sequence Evidence Profile v1

Status: **SUBORDINATE SOURCE-LEVEL TEST / EXECUTOR-SEQUENCE PROFILE**  
Persistent research entity: **Clay**  
Product: **EntityOS**  
Compute architecture: **HCU**  
Supervisor: **8.63 / FREE_ONLY**

## Authority and non-duplication

The canonical current temporal-control acceptance guard is:

`research_entity/claycode/HCU_JSPACE_CONTROL_TEMPORAL_CAUSALITY_GATE_V1.md`

This profile is subordinate to that guard. It MUST NOT create a second temporal-control authority, admission authority, truth/state store, effect path, executor, J-Space, dataset authority, or competing causal schema.

If this profile conflicts with the canonical temporal gate or a newer admitted successor, the canonical/newer gate wins and this profile must be updated or retired.

The purpose of this profile is narrower: specify executor/store-owned sequence, adjacency, replay, branch/concurrency, and deterministic negative-test requirements that can strengthen the canonical gate without replacing it.

## Why this subordinate profile exists

The retained donor history contains an explicit negative discriminator: a caller-labelled temporal-binding primitive was reverted at donor snapshot `ff67cf4192e9fbb3ea8aee2819f2dbeddd576ee6`.

The canonical temporal gate independently establishes the required forward topology:

`JSpaceStep(t) / VectorControlPacket(t)`
`  -> successor ModelInputControlBinding(t -> t+1)`
`  -> ModelExecutionObservation(t+1)`
`  -> VerifiedModelExecution(t+1)`
`  -> InferenceReceipt(t+1)`
`  -> contribution/output(t+1)`
`  -> JSpaceStep(t+1) / VectorControlPacket(t+1)`

This profile adds one stricter implementation/testing principle:

```text
CALLER_LABELLED_TIME_OR_STEP != EXECUTOR_OR_CANONICAL_SEQUENCE_EVIDENCE
```

A caller-supplied `step_index`, timestamp, ordinal, predecessor label, trace label, or narrative ordering may describe a relation but cannot prove the admitted predecessor/successor relation required by the canonical temporal gate.

## Permitted implementation shape

Do not introduce a standalone competing `HCU_EXECUTOR_SEQUENCE_ADMISSION` authority merely because this profile discusses sequence evidence.

Prefer extending the existing canonical temporal predecessor binding/admission chain or one subordinate edge object already admitted through the single MiniUnifiedDB/UnifiedDB-compatible deterministic state/evidence substrate.

Any sequence/adjacency fields used to satisfy the canonical temporal gate should be derived from executor-owned or deterministic admitted context and should bind, as applicable:

- exact generation;
- executor identity/incarnation;
- deterministic recurrent stream/lane/parent identity from Typed Entry or control-plane evidence;
- predecessor J-Space trace identity;
- predecessor Vector-Control packet identity;
- controlled successor invocation identity;
- exact successor executor input SHA-256/size;
- successor model-input-control admission/binding identity;
- successor ModelExecutionObservation / VerifiedModelExecution identity;
- causal event identity and concrete Entry admission identity;
- exact GRID plan, cell and role;
- replay-stable canonical bytes and digest.

If deterministic stream/lane identity cannot be derived from admitted evidence, fail closed rather than invent it from timestamps or caller narration. A suitable failure class is `EXECUTOR_SEQUENCE_LANE_IDENTITY_UNAVAILABLE` unless the canonical implementation defines a more specific successor-dynamic class.

## Executor/store-owned ordering requirement

A positive predecessor/successor relation must be supported by at least one admitted ordering source that is not a caller assertion. Valid designs may include:

1. an executor-emitted sequence/parent receipt admitted into the existing canonical store; or
2. deterministic sequence/parent assignment within the existing canonical store transaction at the executor admission boundary; or
3. an equivalent successor-dynamic mechanism explicitly admitted by the canonical temporal gate.

Wall-clock timestamps are metadata only. Pre-load hashes or caller-provided ordinals are not sequence authority.

## Branching and concurrency

HCU execution may be parallel. Therefore the canonical temporal edge must not be implemented as an unjustified single global wall-clock order.

Required properties for any sequence-capable implementation:

- adjacency/order is scoped to an exact deterministic recurrent stream/lane/parent context;
- different streams may advance concurrently;
- one claimed lane position cannot silently map to byte-distinct successor executions;
- if branching is supported, branch identity must be explicit and canonicalized;
- if branching is not supported, concurrent divergent claims for the same predecessor/position require atomic deterministic one-winner semantics;
- timestamps never adjudicate the winner.

## Recurrent Vector-Control closure

The canonical temporal gate remains the authority. A strong implementation-level closure is:

```text
TrainingTrace(t)
  -> exact JSPACE_VECTOR_CONTROL packet(t)
  -> successor ModelInputControlBinding(t+1)
  -> canonical successor control admission(t+1)
  -> exact executor-consumed input bytes(t+1)
  -> admitted predecessor/successor ordering evidence
  -> VerifiedModelExecution(t+1)
  -> InferenceReceipt/v4(t+1)
  -> JSpaceBinding/v3(t+1)
```

This proves, at most, observable forward dataflow/order at the admitted evidence scope. It still does NOT prove beneficial hidden-state causal use. Model-specific influence requires separately admitted lesion/shuffle/rescue or equivalent intervention evidence under the atomic unusual-experiment law.

## Deterministic regression profile

A successor implementation of the canonical temporal gate should, where applicable, cover:

1. **same-invocation post-hoc rejection** — packet produced from output of invocation `i` cannot be credited as controlling invocation `i`;
2. **caller-labelled ordinal rejection** — changing only caller `t/t+1` labels cannot create a valid edge;
3. **admitted predecessor ordering** — positive edge derives ordering from executor/store/canonical evidence;
4. **reversed-edge rejection**;
5. **self-edge rejection**;
6. **stale-generation rejection** with no surviving canonical write;
7. **wrong-stream/lane/parent rejection**;
8. **control-packet ancestry rejection** — predecessor trace packet must equal the exact packet admitted into successor input;
9. **successor-input mismatch rejection**;
10. **divergent replay rejection** for byte-distinct evidence under one edge identity;
11. **concurrent same-position conflict** with deterministic semantics unless an explicit branch schema is active;
12. **idempotent exact replay**;
13. **canonical-byte revalidation**.

These are source/integration regression requirements. They do not replace exact FREE_ONLY runtime acceptance at the corresponding claim scope.

## Evidence and credit boundary

This profile creates no runtime or training credit.

```text
whole EntityOS/HCU runtime credit = 0
full HCU runtime credit = 0
J-Space model runtime credit = 0
training credit = 0
whole-product PASS = false
```

Higher evidence levels require exact admitted current-source execution and remain governed by the canonical temporal gate, current supervisor authority, and existing execution/effect laws.

## Next exact gate

Extend only the single retained HCU donor/evidence lane with the canonical `HCU_JSPACE_CONTROL_TEMPORAL_CAUSALITY_GATE_V1` forward predecessor edge. Reuse existing state/admission primitives. Add executor/store-owned ordering evidence only as needed to prevent caller-labelled chronology from satisfying the gate, and propagate that edge identity through successor VerifiedModelExecution -> InferenceReceipt -> J-Space/Training provenance.

If parallel current `main` already implements this exact closure, do not create a duplicate mechanism; re-enter its exact source/tests and move to the next falsifiable gap.
