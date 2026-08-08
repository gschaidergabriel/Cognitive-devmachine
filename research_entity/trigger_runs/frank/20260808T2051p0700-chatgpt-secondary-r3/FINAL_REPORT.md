# FRANK RESEARCH RUN C7 — Clay Organ Runtime Fabric

**run_id:** `20260808T2051p0700-chatgpt-secondary-r3`  
**trigger:** `frank`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent FRANK:** C6 `Clay-Native Unified Cognitive Substrate`  
**primary Clay foundation:** G11 `MOSAIC — Multi-plane Operation-Specific Aligned Identity Capsule`  
**ClayCode:** CC11 `CC-RC1.6 MRSC` + E2B triple-bound identity refinement  
**deep memory substrate:** ClayGraph C4/G1d HOLD  
**deep persistence substrate:** UnifiedDB foundation — registered branch, no completed dedicated trigger run found at start  
**candidate:** **FRANK C7 — Clay Organ Runtime Fabric (CORF)**  
**promotion:** **NONE — OPEN architecture/research candidate**

---

## 1. Executive synthesis

C6 established the owner-fixed semantic target:

> FRANK is one Clay-native semantic organism. The Qwen-class 4B is to be fully adapted to Clay; memory, state, GWT, Hyperposition, architecture and internal semantic communication use Clay; Needle is the sole intentional non-Clay semantic subsystem; model output never self-authorizes effects.

C7 does not reopen that decision. It answers the next architecture question created by MOSAIC-G11, CC11/MRSC and UnifiedDB:

> **If FRANK is one semantic organism, which boundaries must still be processes, storage engines or hard authority domains?**

The C7 result is:

# `semantic organ boundary != process boundary != storage boundary != authority boundary`

This is the strongest FRANK delta since C6.

A GWT workspace can be a distinct causal organ while sharing an address space with the MOSAIC compiler. ClayGraph can remain a distinct memory organ while being queried through UnifiedDB. Qwen can be moved between an embedded and separate process without changing the Clay Reader ABI. Conversely, the fact that all explicit semantics are Clay does **not** justify putting bearer secrets, effect authority or untrusted generated code into the same fault domain as cognition.

C7 therefore proposes a **hybrid organ runtime fabric**:

```text
                           ONE CLAY SEMANTIC ORGANISM
                                      │
      ┌───────────────────────────────┼──────────────────────────────┐
      │                               │                              │
 P.COGNITIVE_CORE              P.MODEL_RUNTIME               P.AUTHORITY_EFFECT
 Needle bridge                 Clay-native Qwen              capability broker
 UnifiedDB planner             configurable placement        secrets / release
 ClayGraph memory                                              hard isolation
 MOSAIC / scheduler
 GWT / MRSC / reconciler
      │
      ├──────────── P.STORAGE_ENGINES (specialized behind UnifiedDB)
      ├──────────── P.TOOL_SANDBOX (untrusted/generated execution)
      └──────────── P.OBSERVABILITY (prefer async receipt sink)
```

This is an **OPEN placement hypothesis**, not a production decision.

---

## 2. Mandatory eight-branch grounding

The authoritative registry now has eight scientific branches. C7 uses the current preflight priority:

`Clay -> ClayCode -> ClayGraph -> UnifiedDB -> GWT -> Hyperposition -> Emergenz -> FRANK`.

The repository `FRANK_RESEARCH_PROTOCOL.md` and `frank_architecture_contract.py` were found stale during this run because they still described a seven-branch world. The current registry/preflight already contained UnifiedDB. C7 therefore ingested UnifiedDB according to the authoritative registry and records a governance fix as part of the run.

### Clay G11 / MOSAIC

MOSAIC adds the identity model C6 lacked. A consequential operation carries distinct:

1. semantic identity;
2. contract/provenance-instance identity;
3. operation-required basis/epoch identity;
4. selection/query-plan identity;
5. exact reader-view identity.

C7 makes `S.MOSAIC_CAPSULE` the causal execution identity that links storage/query, Assembly, GWT, MRSC, effect and re-entry.

### ClayCode CC11 / MRSC + E2B

CC11 demonstrated that one reader representation is not universally optimal and that a critical projection must bind the exact emitted view as well as its canonical source. The E2B compiler loop then split source identity again:

`semantic_hash != contract_instance_hash != projected_view_hash`.

C7 generalizes this into MOSAIC's multi-axis runtime identity and preserves typed collection semantics (`SET`, `ORDERED`, `MULTISET`, weighted/priority candidates).

### ClayGraph C4/G1d

C7 keeps ClayGraph as the specialized associative memory organ:

`authoritative event state -> immutable semantic graph epoch -> sparse activation -> bounded Assembly -> optional graph escalation -> exact-anchor validation`.

Activation remains salience, not truth or GWT ignition. G1d remains HOLD; C7 does not promote it.

### UnifiedDB

UnifiedDB is now FRANK's logical typed persistence/query/transaction substrate. The important C7 interpretation is:

> **UnifiedDB is not another organ service and not a command to put every byte into one database.**

It is the logical planner/fabric over exact, relational, graph, vector, FTS and activation views. Exact event/effect history remains authoritative; derived views retain derivation/epoch/rebuild receipts. Physical colocation remains benchmark-gated and reversible.

### GWT R4

C7 keeps every causal stage explicit even if physically colocated:

`query/graph prior -> Assembly -> candidate set -> competition -> gate/ignition -> WorkspaceEpisode -> MRSC view -> model uptake -> effect -> outcome -> re-entry`.

Physical placement becomes an additional experimental factor, not a reason to collapse stages.

### Hyperposition H4

H4's rule becomes a core C7 invariant:

> one Clay language must not become one semantic failure domain.

FACT, activation, proposal, form, capability and effect intent remain non-interchangeable even in one packed runtime. C7 adds physical fault-domain topology as another independent dimension.

### Emergenz E1

No C7 organ is promoted as emergent. Tight integration, recurrence, Clay-native communication or GWT wiring do not replace E-CERT2 prospective identity, lesion, mechanistic rescue, OOD and multiscale causal contribution.

---

## 3. C7 architecture

Machine source: `FRANK_ARCHITECTURE.claycode.json`.

### Logical episode

```text
external event
 -> Needle
 -> immutable Clay route certificate
 -> canonical event ledger
 -> MOSAIC operation capsule
 -> UnifiedDB logical query plan
 -> exact / graph / vector / FTS / activation routes
 -> ClayGraph Assembly + selection receipt
 -> GWT WorkspaceEpisode
 -> MRSC reader rail/view
 -> Clay-native Qwen 4B
 -> Clay proposal
 -> canonical reconciliation
 -> effect-relevant basis/selection/capability revalidation
 -> isolated capability/effect broker
 -> outcome
 -> truth-bound re-entry receipt
 -> canonical event append
 -> incremental derived-view maintenance
```

### Core C7 modules

- `M.DURABLE_EVENT_LEDGER` — exact authoritative replayable history;
- `M.UNIFIEDDB_LOGICAL_FABRIC` — cross-store logical planning;
- `M.CLAYGRAPH_MEMORY` — associative semantic memory + activation + Assembly;
- `M.MOSAIC_COMPILER` — operation-specific identity/closure;
- `M.COGNITIVE_CORE_SCHEDULER` — multi-rate deterministic/model scheduling;
- `M.WORKSPACE_ARBITER` — GWT competition/selection/ignition organ;
- `M.MRSC` — canonical/P2/P3/hybrid reader compiler;
- `M.QWEN_CLAY_NATIVE` — full-model adapted semantic transform kernel;
- `M.CANONICAL_RECONCILER` — rail return -> canonical proposal;
- `M.CAPABILITY_EFFECT_BROKER` — deterministic external authority;
- `M.TOOL_SANDBOX` — untrusted/generated external execution;
- `M.OBSERVABILITY_REPLAY` — causal receipts/recovery;
- `M.PLATFORM_ADAPTER` — Linux/Android physical lowering.

Needle remains the sole intentional non-Clay semantic component.

---

## 4. Experiment results

All local numbers are mechanism proxies unless explicitly analytical from the official Qwen configuration.

### EXP-C7-HANDOFF-001 — serialization boundary cost

Representative nested MOSAIC/Workspace-shaped payload:
- JSON payload: 6,983 bytes;
- pickle payload: 5,390 bytes.

CPython median:
- direct field read: **0.080 µs**;
- JSON serialize+parse: **74.080 µs**;
- pickle roundtrip: **35.713 µs**;
- `memoryview` over an existing packed buffer: **0.121 µs**;
- byte copy of existing packed buffer: **0.511 µs**.

Interpretation: an internal JSON bus is not free. This supports a target benchmark of compact typed handles/borrowed buffers, not the claim that Rust/C will reproduce these ratios.

### EXP-C7-PARTITION-002 — monolith vs services vs hybrid

Constructed 12-organ episode:
- monolith weighted cross-process transitions: **0.0**;
- full services: **15.2**;
- hybrid C7 candidate: **6.9**.

Constructed recovery penalty proxy:
- monolith: **47.45 µs/episode**;
- services: **8.97 µs**;
- hybrid: **15.18 µs**.

At 25 µs modeled cost per process boundary, combined proxy:
- monolith: **47.45**;
- services: **388.97**;
- hybrid: **187.68 µs/episode**.

This deliberately exposes a Pareto trade-off. It does **not** prove the hybrid is fastest. The monolith is not selected as default because authority/secrets and untrusted execution are hard fault/security constraints, not soft latency terms.

### EXP-C7-EFFECT-SCOPE-003 — post-proposal revalidation

200,000 constructed episodes over eight consistency domains:
- global reject-on-any-change: **94.0095%**;
- MOSAIC scoped reject: **62.8090%**;
- global false reject: **31.2005%**;
- scoped unsafe accepts: **0 in the constructed known-closure family**.

The zero unsafe accepts are not a production claim: the test knows the required dependency set. Real unknown dynamic scope must broaden/escalate.

### EXP-C7-QWEN-KV-004 — mobile context memory

Official Qwen3-4B attention configuration used for arithmetic:
- 36 layers;
- 8 KV heads;
- head dimension 128;
- 4.0B parameters.

Approximate 16-bit KV only:
- 4k tokens: **0.5625 GiB**;
- 8k: **1.125 GiB**;
- 16k: **2.25 GiB**;
- 32k: **4.5 GiB**.

Theoretical raw 4B parameter payload lower bound:
- 4-bit: **~1.86 GiB**;
- 8-bit: **~3.73 GiB**;
- 16-bit: **~7.45 GiB**.

Actual quantized files/runtime memory are larger/different due to metadata, mixed precision, scratch buffers and allocator/runtime overhead.

**Consequence:** bounded Assemblies/COVE/MOSAIC are an edge-memory primitive, not only a token-cost trick.

---

## 5. External research delta

### Qwen3-4B / mobile feasibility

The official Qwen3-4B material confirms the 4B-class architecture and long-context capability. Qualcomm publishes W4A16 4k-context device results on current Snapdragon platforms in roughly the high-teens to ~30 token/s range depending on platform. Those are vendor-specific model benchmarks, not FRANK numbers, but they make local 4B execution a credible engineering target.

MLC LLM exposes Android deployment with configurable context and prefill parameters. llama.cpp also provides Android deployment/bindings. C7 therefore makes model/runtime/quantization/context/backend/platform part of `S.READER_PROFILE` instead of architecture constants.

### Hot-path data exchange

Apache Arrow's C Data Interface provides an ABI for zero-copy sharing between independent runtimes in the **same process**. Its documentation explicitly does not make the interface a cross-process/persistence protocol. C7 therefore uses Arrow only as one candidate physical ABI where its columnar shape fits and requires a separate IPC/shared-memory contract across processes.

AAFLOW (2026 preprint) independently studies an Arrow/Cylon-based unified distributed agent runtime and reports substantial pipeline/embedding gains in its own workloads. It is useful implementation evidence for batching/zero-copy pressure, not validation of C7.

### Incremental state

Feldera/DBSP provides production-oriented precedent for maintaining views from deltas rather than full-history recomputation. This supports C7's `OP.INCREMENTAL_DERIVE` direction while leaving actual FRANK thresholds open.

### Full-model adaptation / forgetting

ACL 2026 source-shielded language adaptation reports that standard full fine-tuning can cause substantial source-task degradation in its tested 7B/13B settings. The specific protected-parameter method is not directly the C7 target because the owner requires full-model adaptation, but the forgetting mechanism is highly relevant.

A 2026 FINCH preprint studies loss-adaptive learning rates on Qwen3-4B knowledge acquisition and reports markedly reduced forgetting without relying on a permanently frozen subset. C7 therefore keeps full-model adaptation fixed but makes rehearsal/distillation, checkpoint gates and loss-adaptive scheduling strong candidates.

Tokenizer adaptation is also a real variable: EACL 2026 continued-BPE work and 2026 alignment/relearning work support testing vocabulary extension/alignment rather than assuming hand-designed Clay compactness is automatically optimal.

### Sandboxing

Wasmtime's security/WASI model provides one candidate for capability-constrained generated plugins, but C7 does not require Wasm for browser/terminal workloads. The invariant is explicit imported authority and fault containment, not a particular sandbox technology.

---

## 6. Full-model Clay training programme

Owner-fixed target: **full-model adaptation**, not LoRA-only.

C7 principle:

> **Transcode pretrained capability into Clay; do not merely overwrite the model with Clay.**

### Curriculum

1. freeze baseline checkpoint, retained-capability and authority-violation suites;
2. natural/external P0 <-> canonical P1 Clay semantic transcode;
3. typed Clay primitives, n-ary roles, epistemic and authority classes;
4. MOSAIC/COVE operation-specific causal-slice tasks;
5. UnifiedDB query/selection + ClayGraph epoch/activation/Assembly tasks;
6. GWT WorkspaceEpisode/reconstruction/re-entry tasks;
7. MRSC P2 compact-native rail training and P1/P2 equivalence;
8. tool/effect proposal and explicit denial/authority-negative training;
9. optional P3 latent/hybrid experiments only when a target hidden-state interface exists.

### Tokenizer factorial

- base tokenizer + Clay lexeme design;
- continued-BPE extension;
- aligned vocabulary adaptation / embedding transfer.

### Checkpoint gates

No checkpoint is promoted from Clay loss alone. Required shadows include:
- Clay semantic execution;
- exact role/n-ary binding;
- epistemic/authority-class separation;
- retained general capability;
- OOD composition;
- tool proposal correctness;
- forbidden-authority violation rate;
- latency/RAM/KV/energy.

---

## 7. Linux reference and Android lowering

### Linux candidate

The cognitive hot path is the first candidate for same-address-space lowering because MOSAIC, query-plan, Assembly, Workspace and MRSC exchange tightly coupled typed state.

Hard/likely separate fault domains:
- effect/capability broker;
- untrusted tool/plugin execution;
- observability sink where async is safe;
- model runtime when GPU/backend/restart economics justify separation;
- physical storage engines according to UnifiedDB placement.

### Android

The **semantics do not change**. Physical placement may.

Android may embed the model runtime if the chosen backend requires/benefits from it. Context/KV/prefill become governor-controlled resources. C7 does not make 32k native context the default simply because the model supports it.

---

## 8. Recovery and migration

C7 is deliberately reversible.

1. **Observe only:** generate MOSAIC, selection, reader and re-entry receipts beside current runtime.
2. **Logical UnifiedDB façade:** put existing stores behind typed plans without physical migration.
3. **C7 cognitive-core shadow:** current and C7 paths run side by side and compare query/Assembly/Workspace receipts.
4. **Packed ABI:** remove selected JSON/internal serialization only after differential equivalence tests.
5. **Authority broker isolation:** dual-observe then cut over secrets/effect release.
6. **Clay Qwen adapter:** current model remains control while full-FT checkpoints are versioned through ReaderProfile.
7. **Incremental views:** enable graph/vector/FTS/materialized updates with rebuild recipes and lag receipts.
8. **Android lowering:** same semantic contracts, mobile-specific placement/backends/governor.

Rollback on:
- semantic/replay mismatch;
- selection-integrity regression;
- capability/secret leak;
- irreversible-effect mismatch;
- unacceptable p99/recovery/RAM/thermal/energy regression;
- inability to reconstruct the prior canonical episode.

---

## 9. Negative results / unresolved contradictions

Full artifact: `NEGATIVE_RESULTS.md`.

Key rejected shortcuts:
- one semantic organ = one process;
- one Clay world = one physical database;
- full monolith selected purely for latency;
- per-organ microservices as purity default;
- arbitrary compact Clay automatically equals native fluency;
- Clay loss alone proves successful full adaptation;
- maximum Qwen context as mobile default;
- global all-domain freshness as universal effect rule;
- graph activation = GWT ignition;
- reader-view integrity = authority;
- integration = emergence/consciousness.

Major unresolved questions:
- Does the C7 hybrid partition win on real Linux p99/recovery/security?
- Does logical UnifiedDB outperform current store coordination before physical migration?
- Can full-model Clay adaptation preserve baseline competence while delivering P2 advantages?
- Which tokenizer/curriculum wins?
- Does ClayGraph truthful latent activation improve target cognition under stage-orthogonal controls?
- Can Android sustain the required model/context under RAM/thermal/battery limits?
- Does any recurrent C7 motif pass E-CERT2?

---

## 10. Highest-information next experiments

1. **C7 Linux Twin:** current runtime vs C7 hybrid, packed ABI, process placement factorial, crash/restart and exact replay.
2. **UnifiedDB four-baseline run:** specialized vs logical federation vs shared-canonical+sidecars vs physical consolidation.
3. **Target Qwen full-FT factorial:** tokenizer × curriculum × forgetting control, P0/P1/P2, retained capability and OOD.
4. **GWT/Memory factorial:** truthful/shuffled/no activation × workspace × MRSC rail/view × re-entry with MOSAIC receipts.
5. **Android sustained trace:** model + 4k/8k/16k context, latency, RAM, KV, thermal, battery, governor behavior.
6. **Authority attack suite:** memory/selection/view mutations plus capability revocation, generated-code sandbox and idempotent effect replay.

---

## 11. Scientific disposition

**FRANK C7 CORF is an OPEN architecture candidate.**

The evidence is strong enough to justify a new research architecture and executable/twin plan, but not a canonical scientific promotion:
- MOSAIC and MRSC are themselves OPEN;
- UnifiedDB has no completed dedicated benchmark run yet;
- local runtime numbers are proxies;
- no live FRANK C7 twin has run;
- no full-FT Clay Qwen target checkpoint exists here;
- no sustained target Android trace exists;
- no new emergence or consciousness claim is made.

Canonical RAE therefore remains r2 until the normal promotion process has target-relevant evidence and current remote canonical/CAS validation.
