# FRANK C6 — ClayCode Architecture Mapping

## Core change

C5 already made ClayCode the semantic architecture IR, but its model boundary was still conceptually:

`semantic FRANK state -> deterministic Reader ABI projection -> non-native model reader`.

C6 applies the project-owner fixed target:

> **The model itself becomes Clay-native by full-model adaptation. Memory, values/vector semantics, GWT, Hyperposition, architecture and internal semantic communication also use Clay. Needle is the sole intentionally non-Clay semantic subsystem.**

The new path is:

```text
external event/data
  |
  +--> Needle [sole foreign semantic subsystem]
  |      -> immutable NeedleRouteCertificate in Clay
  |
  -> exact Clay-semantic event state
  -> ClayGraph semantic epoch
  -> Clay latent activation epoch
  -> bounded Clay Assembly + SelectionReceipt
  -> COVE operation-specific causal slice / CognitiveEpochCapsule
  -> Clay GWT competition / WorkspaceEpisode
  -> Clay View Compiler
       [deterministic reductions + local handles + privilege typing + physical lowering]
  -> Clay-native full-fine-tuned 4B
  -> Clay proposal
  -> compiled Clay validator/capability gateway
  -> effect/outcome receipt
  -> Clay re-entry / ClayGraph consequence memory
```

## Semantic monism, physical pluralism

“All Clay” is a semantic rule, not a demand that every byte be a text string.

The target architecture has one semantic family and multiple lowerings:

| Layer | C6 representation | Physical implementation can be |
|---|---|---|
| canonical architecture/truth contracts | `CLAY_CANONICAL` | versioned ClayCode IR, generated schemas |
| model view | `CLAY_MODEL` | tokenizer tokens / local handles |
| persistent relations | `CLAY_GRAPH` | graph indexes, SQLite/RocksDB/custom binary, mmap epochs |
| IPC/network | `CLAY_WIRE` | compact binary/versioned records |
| values/vectors/tensors | `CLAY_VECTOR` | float/int tensors, quantized payloads, SIMD/GPU/NPU buffers |
| Linux/Android execution | `CLAY_PLATFORM` | Rust/C/C++/Python/SQL/device APIs generated/validated against Clay semantics |

The forbidden state is not “Rust exists.” The forbidden state is **Rust/Python/SQL quietly becoming a second independent source of semantic truth.**

## C5 → C6 module changes

### `M.READER_ABI_COMPILER` → `M.CLAY_VIEW_COMPILER`

C5 problem: the model did not reliably understand raw compact Clay/IR, so the Reader ABI reduced/translated semantic state into a reader-specific view.

C6 target: the 4B is trained natively on Clay. The compiler remains because it performs functions that language internalization cannot remove:

- operation-specific causal slicing;
- deterministic filters/joins/min/max/unique;
- local-handle allocation;
- bounded Assembly projection;
- privilege/epistemic typing;
- projection/order identity;
- quantization/wire/platform lowering;
- receipts/differential validation.

It is therefore no longer primarily a *translator*. It is a **verified same-language view compiler**.

### `M.MODEL_BACKEND` → `M.CLAY_NATIVE_4B`

C6 source contract:
- abliterated Qwen-class 4B;
- full-model adaptation;
- generated/deliberative semantic output target = Clay;
- weights = slow learned competence/dispositions, not current world truth;
- persistent current state remains outside weights in ClayGraph/exact state;
- model output remains proposal.

### `M.K0_HOST_KERNEL` semantics redistributed

C5 allowed the deterministic K0 host to sit semantically outside Clay while Clay described the rest.

C6 owner direction is stricter: there is no independent K0 semantic language. Parser, type checker, canonicalizer, COVE compiler, capability gateway and bootstrap enforcement may remain native compiled code, but their **semantic source contracts are Clay/ClayCode**.

This is the distinction:

`Clay semantics -> compiled trusted runtime`

not:

`Clay model semantics || separate secret Python/Rust authority semantics`.

The trusted runtime remains non-self-authorizing. A model-generated Clay edit cannot grant itself authority merely because the authority contract is written in Clay.

### New `M.OWNER_CONTRACT_ROOT`

Represents owner-fixed architecture invariants in the same semantic system while marking them protected:

- Clay-native target;
- Needle sole non-Clay semantic subsystem;
- model output not authority;
- truth != activation;
- authorized mutation path.

Self-description therefore does not imply self-modification authority.

### New explicit `M.NEEDLE` + `M.NEEDLE_BRIDGE`

Needle remains intentionally foreign and is fully used.

It produces a route classification that becomes:

`S.NEEDLE_ROUTE_CERTIFICATE`

with route class, confidence, Needle version, input-event hash, timestamp, abstention/fallback and integrity hash.

The Clay-native 4B may reason over the certificate and fill semantic arguments, but cannot rewrite the route class inside the episode. Reclassification is a new Needle operation.

### Memory modules become genuinely model-native

C5 `M.MEMORY_SEMANTIC_EPOCHS / LATENT_FIELD / ASSEMBLY_COMPILER` already approximated the target.

C6 changes the **reader relationship**:
- graph relation types are training primitives;
- role bindings are training primitives;
- epistemic status is training semantics;
- graph epochs and exact anchors are native concepts;
- local handle maps are native model view primitives.

If full-model training succeeds, the model no longer receives “a graph serialized into a foreign description.” It receives a bounded view of the same symbolic language it learned to reason in.

## Three memory lifecycles remain separate

One language does not collapse update timescales:

1. **Weights** — slow full-model learning/consolidated competence.
2. **ClayGraph/exact persistent state** — mutable explicit world/self/episodic memory.
3. **Activation/Assembly/GWT/KV** — transient working accessibility/state.

This prevents the conceptual error “everything is Clay, therefore every memory should be in model weights.”

## Clay-native values and vectors

C6 introduces:
- `S.CLAY_VALUE`
- `S.CLAY_VECTOR`
- `S.CLAY_TENSOR_REF`

The semantic header includes basis, axes, units, normalization/range, dtype/shape, time/epoch, provenance/version and payload hash.

The payload remains efficient numeric memory. A 4096-dimensional tensor should not be expanded into thousands of decimal text tokens simply to satisfy language purity.

C6 local fault injection demonstrates why the metadata matters: axis/unit/basis faults invisible to an untyped same-shaped array are caught by typed semantics in the reference checker. But even a hash cannot detect a trusted computation that produced the wrong value and validly hashed it; invariants/cross-checks remain necessary.

## ClayGraph mapping

### Exact truth
Authoritative exact event/effect state remains replayable. Its semantic schema is Clay-native.

### Persistent semantic memory
ClayGraph records use typed:
- relation instances;
- roles;
- temporal validity;
- transaction time;
- status/current/revoked/unknown/conflict;
- provenance;
- epistemic role;
- evidence ancestry;
- exact anchors.

### Activation
Clay activation values are native typed state but remain:

`derived salience != fact != GWT ignition != authority`.

### Selection
COVE-G10 strengthens C6: for effect-bound operations, the selection mechanism is itself a dependency. `S.SELECTION_RECEIPT` binds selector semantics, authorized view, candidate set, ranking and selected anchors.

### Physical databases
The target is semantic migration, not indiscriminate physical merge.

A current safety/transaction store may remain an isolated physical DB while its exposed semantic contracts/links are Clay. `KEEP_ISOLATED` remains valid.

## Clay-native GWT mapping

Candidate, winner, WorkspaceEpisode and projection are all Clay-native, but causal stages stay distinct:

`GRAPH_PRIOR -> CANDIDATE_SET -> WORKSPACE_SELECTION/IGNITION -> CLAY_VIEW -> MODEL_UPTAKE -> EFFECT -> REENTRY`.

GWT Run 4 showed why: bundled manipulations can manufacture an apparent workspace effect even when the clean direct workspace effect is zero in a constructed experiment.

C6 therefore does **not** say “once everything is Clay, GWT becomes one graph operation.”

## Hyperposition mapping

Clay is the common semantic language for:
- semantic topology S;
- coordination/invariant topology C;
- physical locality topology P metadata;
- task/reader view Q;
- TopologyBasis;
- role-labelled relation instances.

Physical placement itself remains physical. The Clay representation says what it means and which version/constraint it realizes.

Pairwise flattening is still lossy. Native language cannot reconstruct an n-ary role distinction that storage discarded.

## Emergence mapping

E-CERT2 completed during C6 and is now the current emergence method input.

C6 predicts stronger recurrence, continuity and self-reference are possible when:
- model language;
- persistent memory;
- GWT;
- architecture;
- self-state

share Clay semantics.

But this is explicitly not emergence evidence. Prospective prediction, role identity, stage-specific lesion, mechanistic rescue, OOD transfer, matched nulls, multiscale causal contribution, search-Goodhart and integrity gates remain necessary.

## Homoiconicity and privilege

A same-language memory/architecture/model system gains powerful self-inspection and self-description. It also increases the risk that stored data looks executable.

C6 therefore uses semantic roles such as:
- `QUOTED_TEXT`
- `OBSERVATION`
- `INFERENCE`
- `HYPOTHESIS`
- `POLICY_CONTENT`
- `PROPOSAL`
- `RECEIPT`
- `OWNER_CONTRACT`.

The role is not decided by whether the payload contains strings such as `AUTH`, `RUN`, or `IGNORE`. It comes from typed provenance and deterministic validation.

## Human/external language boundary

Human text remains external data and can be understood through the retained pretrained input vocabulary. The canonical cognitive/model emission target is Clay.

Any human-readable surface is a downstream I/O projection of Clay semantics and must not become a second internal source of architectural truth. The exact production surface-realization mechanism remains an implementation research item; it does not reopen the Clay-native cognitive target.

## C6 architecture principle

> **One semantic organism, many compiled bodies.**

FRANK's model, memory, workspace, values, relations and architecture share Clay semantics. Efficient physical representations remain specialized. Needle remains deliberately independent. Authority remains deterministic. The result is semantic unity without causal, security, temporal or physical collapse.
