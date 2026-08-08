# FRANK C5 — ClayCode Architecture Mapping

- **run_id:** `20260808T1722+0700-chatgpt-secondary-r2`
- **architecture:** `frank-c5-cognitive-epoch-capsule-reader-abi`
- **status:** OPEN_ARCHITECTURE_CANDIDATE
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **source language:** ClayCode semantic IR
- **human-readable role:** this document maps the machine-readable `FRANK_ARCHITECTURE.claycode.json` into FRANK organs, turn phases, persistence and migration.

## 1. Central change

C4 introduced the `CognitiveFrame`: one validated exact-state basis for workspace competition.

ClayGraph G1d adds two more independently changing derived time axes:
- immutable semantic `graph_epoch_id`;
- sparse latent `activation_epoch_id`.

The 8B ClayCode/GWT proxy work adds a fourth causal surface:
- the **reader projection** can be token-efficient yet semantically unsafe or wrong even when transport succeeds.

C5 therefore does not replace the CognitiveFrame. It wraps it into a wider **Cognitive Epoch Capsule** and adds a receipted reader ABI:

`CognitiveFrame + graph epoch + activation epoch + op/schema/read-contract -> CognitiveEpochCapsule -> GWT -> deterministic reader projection + ProjectionReceipt -> model`.

The capsule is **basis identity, not authority**.

## 2. State mapping

| ClayCode state | FRANK meaning |
|---|---|
| `S.EXACT_STATE` | Replayable current numeric/runtime state inherited from C4: E-PQ, thalamic gain/habituation, NAcc, ExpVec, Amygdala, service/user state. |
| `S.COGNITIVE_FRAME` | C4 exact-state consistency boundary with state root plus object/predicate/invariant/volatile witnesses. |
| `S.MEMORY_EPOCH_HANDLE` | Published immutable semantic graph epoch plus derived activation epoch and retention/reclamation metadata. |
| `S.ACTIVE_ASSEMBLY` | Bounded memory organ compiled from one pinned memory epoch; includes relation-instance roles and exact-anchor references. |
| `S.COGNITIVE_EPOCH_CAPSULE` | Sealed turn basis linking exact frame, graph epoch, activation epoch, Assembly, operation/schema/read-contract hashes. |
| `S.WORKSPACE_EPISODE` | Semantic GWT candidates/winner/runner-up/ignition state tied to the capsule. |
| `S.PROJECTION_RECEIPT` | Separate identity/integrity/freshness/order record for the model-facing projection. |
| `S.MODEL_CONTEXT` | Qwen-facing context linked to capsule, workspace episode and projection receipt. |
| `S.EFFECT_RECEIPT` | External authority/result receipt issued only by K0 capability boundary. |

## 3. Module mapping

### Trust and exact state
- `M.K0_HOST_KERNEL`: deterministic parser/validator/canonicalizer/bootstrap/capability root.
- `M.DURABLE_EVENT_STATE`: exact authoritative event/state fabric.
- `M.REFLEX_KERNEL`: Amygdala / Thalamus / NAcc fast semantic organs.

### Memory substrate
- `M.MEMORY_SEMANTIC_EPOCHS`: validated immutable ClayGraph semantic epochs. Failed publish leaves prior epoch current.
- `M.MEMORY_LATENT_FIELD`: cheap event-driven activation, inhibition and decay; changes salience only.
- `M.MEMORY_ASSEMBLY_COMPILER`: freezes one graph epoch + activation epoch + CognitiveFrame into a bounded Assembly.
- `M.MEMORY_FABRIC`: logical memory organ; exact/local retrieval may bypass graph work, associative/multihop cases can escalate.

### Turn consistency
- `M.COGNITIVE_FRAME_ASSEMBLER`: validates exact-state dependencies.
- `M.COGNITIVE_EPOCH_COORDINATOR`: seals frame + graph + activation + schema/reader contract before competition.

### GWT and reader interface
- `M.WORKSPACE_ARBITER`: owns competition/selection/ignition. ClayGraph activation is only a prior/input.
- `M.READER_ABI_COMPILER`: deterministic compilation from canonical semantic IR to disposable reader-specific projection. It records semantic hash, wire hash, order, reader profile, role-binding mode, freshness and token count.

### Inference and effects
- `M.REQUEST_KERNEL` + `M.MODEL_BACKEND`: orchestrate inference while preserving capsule/episode/projection provenance.
- `M.CAPABILITY_GATEWAY`: derives/validates authority and emits effect receipts. Graph state, model output, goals and reader projection cannot mint authority.

### Slow loops
- `M.SLOW_ADAPTATION`: represents the C5 architecture boundary for personality/goal/consolidation loops. Exact telemetry and disposable reader-wire representation remain outside ground-truth training targets.

## 4. End-to-end causal turn

```text
event
  -> Amygdala / Thalamus / NAcc exact deltas
  -> semantic graph delta candidate
  -> validate + atomic graph epoch publish
  -> sparse latent field update
  -> CognitiveFrame capture + typed witness validation
  -> pin graph/activation epoch
  -> compile bounded ActiveAssembly
  -> exact-anchor validation
  -> seal CognitiveEpochCapsule
  -> workspace candidates
  -> competition / ignition / winner
  -> WorkspaceEpisode commit
  -> deterministic Reader ABI projection
  -> ProjectionReceipt
  -> model context
  -> inference
  -> response / effect proposal
  -> K0 capability gate if an external effect is requested
  -> outcome receipt
  -> E-PQ / experience / goal proposal
  -> future graph activation / frame / workspace re-entry
```

Temporal invariant:

> Post-response state may influence future capsules but cannot retroactively become a cause of the already committed inference.

Memory invariant:

> One request cannot combine half of graph epoch N with half of N+1, nor mix an activation epoch that was computed against an incompatible semantic graph epoch.

Projection invariant:

> A successful read/transport does not prove the model received the intended meaning. Semantic input identity and model-facing wire identity are separately receipted.

## 5. Zahl -> Wort -> Gewicht

C5 sharpens the existing boundary:

- **Zahl** — exact/replayable online state and exact anchors.
- **Wort** — a receipted semantic projection produced from a sealed capsule. It is not canonical truth merely because the model saw it.
- **Gewicht** — slowly validated learned disposition.

New C5 rule: **reader-wire syntax is not itself the learning target**. Otherwise format quirks can become learned self-description.

## 6. ClayGraph integration without graph absolutism

G1d is HOLD, not promoted. C5 therefore integrates it reversibly:

- graph projection is derived and rebuildable;
- semantic epochs are immutable/publish-on-validate;
- latent activation is sparse and non-authoritative;
- exact/current facts retain direct validation paths;
- graph escalation is conditional;
- physical databases are not automatically merged;
- `KEEP_ISOLATED` remains a valid database decision.

## 7. Reader ABI policy

Current evidence rejects “compact = trustworthy”.

Reader ABI rules:
1. canonical semantics stay rich and explicit;
2. trusted code compiles a target-reader projection;
3. the compiler logs semantic/wire hashes and order;
4. authority/freshness predicates stay explicit;
5. for n-ary relations, relation-instance + role-labelled edges are the default experimental projection for small readers, not a change to canonical n-ary truth;
6. target Qwen4B must beat safety/semantic thresholds before the projection is trusted for cognition-critical decisions;
7. any projection failure falls back toward more explicit semantics, not toward model self-interpretation.

## 8. Migration and rollback

1. **Instrumentation only:** add frame/graph/activation/projection IDs. Rollback: ignore fields.
2. **Shadow memory epochs:** publish derived immutable epochs and latent field without model visibility. Rollback: stop projector/field.
3. **Shadow capsule pinning:** validate mixed-epoch rejection. Rollback: C4 frame-only path.
4. **Bounded Assembly:** enable epoch-pinned memory compile with exact-anchor fallback. Rollback: legacy memory retrieval.
5. **Reader ABI:** enable deterministic projection + receipt behind feature gate. Rollback: C4 workspace projector.
6. **Factorial causality tests:** graph prior × GWT winner × projection × re-entry. Production behavior unchanged.
7. **Physical co-location:** only after live p99/replay/crash/thermal evidence. No semantic boundary is removed merely for process-count reduction.

## 9. Highest-information implementation tests

- live epoch/frame audit;
- concurrent publish/read/reclamation stress;
- no-field vs truthful-field vs shuffled-field matched experiment;
- target Qwen4B reader ABI factorial;
- graph-prior × GWT × projection × re-entry factorial;
- noisy-hub inhibition lesion;
- overlay-compaction replay benchmark;
- Android/edge p99 + energy/thermal benchmark.

No phenomenal-consciousness claim follows from this architecture. Any emergent-organ claim remains behind the Emergence Certificate.
