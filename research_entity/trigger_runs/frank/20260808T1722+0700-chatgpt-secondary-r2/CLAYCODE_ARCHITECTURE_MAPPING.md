# FRANK C5 — ClayCode Architecture Mapping

- **run_id:** `20260808T1722+0700-chatgpt-secondary-r2`
- **architecture:** `frank-c5-cognitive-epoch-capsule-reader-abi`
- **IR:** `CC-RC1.4/open-frank-c5`
- **status:** `OPEN_ARCHITECTURE_CANDIDATE`
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **source language:** ClayCode semantic IR

## 1. Central change

C4 introduced the `CognitiveFrame`: one validated exact-state basis for workspace competition. ClayGraph G1d and Clay G9 add semantic graph epochs, activation epochs, query/selection provenance and bounded Assemblies. CC9 then supplies the crucial correction: **the causal basis is multidimensional but must be operation-specific, not a universal vector lock**.

C5 therefore uses a **Cognitive Epoch Capsule as an operation-specific Certified Basis container**:

`trusted op semantics -> required basis dimensions/policies -> compatible CognitiveFrame + graph/activation/query-plan witnesses -> selection integrity -> CognitiveEpochCapsule -> GWT -> deterministic reader projection + ProjectionReceipt -> model`.

For a workspace turn, frame + graph epoch and, when the latent field is used, activation epoch are normally required. An unrelated operation must not be rejected merely because an irrelevant epoch changed. The capsule is **basis/provenance identity, never authority**.

## 2. State mapping

| ClayCode state | FRANK meaning |
|---|---|
| `S.COGNITIVE_FRAME` | Exact-state consistency boundary with root plus object/predicate/invariant/volatile witnesses. |
| `S.MEMORY_EPOCH_HANDLE` | Published immutable semantic graph epoch plus derived activation epoch and grace-period reclamation data. |
| `S.ACTIVE_ASSEMBLY` | Bounded memory organ compiled from a compatible epoch; retains relation-instance roles, exact anchors and `no_authority`. |
| `S.COGNITIVE_EPOCH_CAPSULE` | Operation-specific Certified Basis: required dimensions, compatibility policies and receipts, not a global epoch-equality lock. |
| `S.WORKSPACE_EPISODE` | Semantic candidate set, competition identity, winner/runner-up, gate policy and ignition state. |
| `S.PROJECTION_RECEIPT` | Semantic/schema/wire identity, query-plan hash, selection provenance, reader profile, order, integrity/freshness and uptake reference. |
| `S.MODEL_CONTEXT` | Qwen-facing context linked to capsule, workspace episode and projection receipt. |
| `S.EFFECT_RECEIPT` | External authority/result receipt issued only by the K0 capability boundary. |

## 3. Module mapping

### Trust and exact state
- `M.K0_HOST_KERNEL`: deterministic parser/validator/canonicalizer/bootstrap/capability root.
- `M.DURABLE_EVENT_STATE`: replayable exact authoritative event/state fabric.
- `M.REFLEX_KERNEL`: Amygdala / Thalamus / NAcc fast state machines.

### Memory substrate
- `M.MEMORY_SEMANTIC_EPOCHS`: validated immutable ClayGraph semantic epochs; failed publish leaves the previous epoch current.
- `M.MEMORY_LATENT_FIELD`: sparse event-driven activation, inhibition and decay; changes salience, not truth/status/authority.
- `M.MEMORY_ASSEMBLY_COMPILER`: compiles an epoch-consistent bounded Assembly with relation roles and exact anchors.
- `M.MEMORY_FABRIC`: exact/FTS/vector paths may bypass graph work; graph/latent routes are conditional for associative/multihop needs.

### Certified basis and selection integrity
- `M.COGNITIVE_FRAME_ASSEMBLER`: validates exact-state dependencies using typed CC-RC1.4 witnesses.
- `M.COGNITIVE_EPOCH_COORDINATOR`: asks trusted operation semantics which basis dimensions matter and validates only those compatibility rules.
- `OP.SELECTION_INTEGRITY_CHECK`: separately checks candidate membership/query-plan/selection provenance before a workspace or effect-bound use. Authentic records do not prove authentic selection.

### GWT and reader interface
- `M.WORKSPACE_ARBITER`: owns competition/selection/ignition. ClayGraph activation is a candidate prior only.
- `M.READER_ABI_COMPILER`: deterministic query-specific projection from canonical semantics to a disposable target-reader surface. It receipts semantic hash, projection-schema hash, wire hash, query plan, selection provenance, order and reader profile.

### Inference and effects
- `M.REQUEST_KERNEL` + `M.MODEL_BACKEND`: orchestrate inference while preserving capsule/episode/projection provenance.
- `M.CAPABILITY_GATEWAY`: CC-RC1.4 compositional closure over transitive callees, finite dynamic targets, canonical resource identities, predicates/invariants/volatile inputs and capabilities. Unknown reflection/FFI/plugin/alias scope broadens, isolates or rejects. Model, graph and projection never mint authority.

### Slow loops and platform
- `M.SLOW_ADAPTATION`: post-response personality/goal/consolidation boundary; exact telemetry and disposable wire syntax are not ground-truth training targets.
- `M.PLATFORM_ADAPTER`: Linux-first but semantic IDs, receipts and authority boundaries remain portable to Android/edge.

## 4. End-to-end workspace turn

```text
event
  -> exact/reflex state updates
  -> validate + publish semantic graph epoch
  -> sparse latent-field update
  -> CognitiveFrame capture + typed witness validation
  -> trusted workspace op declares basis requirements
  -> pin compatible graph/activation epoch(s)
  -> compile bounded ActiveAssembly
  -> exact-anchor + selection-integrity validation
  -> seal operation-specific CognitiveEpochCapsule
  -> candidate set + competition / ignition / winner
  -> semantic WorkspaceEpisode
  -> deterministic Reader ABI projection
  -> ProjectionReceipt + uptake receipt
  -> model context / inference
  -> response or effect proposal
  -> K0 compositional-closure + capability gate for external effects
  -> effect/outcome receipt
  -> causally compatible re-entry
  -> future E-PQ / memory salience / goal / consolidation updates
```

Temporal invariant: post-response state may affect future capsules but cannot retroactively become a cause of the already committed inference.

Memory invariant: one request cannot combine incompatible semantic/activation epochs. However **compatibility is defined by trusted operation semantics**, not by requiring every global version to be identical.

GWT invariant: `graph prior -> candidate set -> workspace selection -> projection/uptake -> effect/outcome -> re-entry` are separate causal stages. A bundled “GWT ON vs OFF” change cannot identify the workspace mechanism if neighboring stages changed too.

Projection invariant: successful transport/read does not prove intended semantic reconstruction. Semantic/schema/wire identity and uptake are separately receipted.

## 5. Zahl -> Wort -> Gewicht

- **Zahl** — exact/replayable online state and exact anchors.
- **Wort** — receipted semantic reader projection generated from a certified basis; model visibility does not make it canonical truth.
- **Gewicht** — slowly validated learned disposition.

C5 rule: reader-wire syntax itself is not the learning target; otherwise projection quirks can become learned self-description.

## 6. ClayGraph integration without graph absolutism

G1d remains HOLD and Clay G9 EPOCH remains OPEN_HOLD. Integration is therefore reversible:
- exact event/state remains authoritative;
- semantic graph epochs are derived/rebuildable;
- activation is sparse, disposable and non-authoritative;
- exact/FTS/vector retrieval can bypass graph routing;
- graph escalation is conditional;
- physical DBs are not automatically merged and `KEEP_ISOLATED` stays valid;
- effect-bound selection requires stronger integrity than exploratory association.

## 7. Reader ABI evidence and policy

Current 8B proxy evidence rejects “compact = trustworthy”. CC9 reports two useful but non-target results: Clay G9 graph selection improved from **5/10 raw to 9/10 trusted compiled** while prompt tokens fell **487 -> 324 (-33.47%)**; a CC9 freshness/authority task improved from **1/10 raw-rule inference to 10/10 deterministic compiled decision relay**, with prompt tokens **327 -> 152 (-53.52%)**. These are hosted 8B proxy results, not Qwen3-4B/live-FRANK promotion evidence.

Reader ABI rules:
1. canonical semantics remain rich;
2. deterministic operators execute before the model when their semantics are soundly available;
3. compiled projection is query-specific and receipted;
4. authority/freshness/selection-integrity predicates remain outside the model;
5. n-ary truth stays canonical n-ary; explicit relation-instance role labels are only a reader projection candidate;
6. target Qwen4B must satisfy semantic/safety thresholds before cognition-critical trust;
7. failure falls back toward more explicit semantics/broader validation, never toward model self-authorization.

## 8. Migration and rollback

1. instrument IDs, receipts and canonical resource identities;
2. shadow semantic epochs + latent field;
3. shadow operation-specific basis certification;
4. enable bounded Assembly + exact fallback + selection receipt;
5. enable deterministic Reader ABI + projection/uptake receipts;
6. run selection attacks and `GRAPH_PRIOR x WORKSPACE_SELECTION x PROJECTION x REENTRY` factorials;
7. consider physical co-location only after live p99/crash/replay/thermal evidence.

Rollback remains to the C4 exact-frame/workspace path because graph, activation, Assemblies and reader projections are derived/disposable.

## 9. Highest-information tests

- live operation-specific frame/epoch audit;
- concurrent publish/read/reclamation stress;
- no-field vs truthful-field vs shuffled-field at equal visible facts/order/token budget;
- candidate-selection provenance attack test;
- target Qwen4B canonical-vs-raw-vs-compiled Reader ABI factorial;
- graph-prior × workspace-selection × projection × re-entry factorial;
- noisy-hub decay/inhibition lesion;
- actual-corpus retrieval Pareto + overlay compaction replay;
- crash/replay and Android sustained p99/energy/thermal traces.

No phenomenal-consciousness claim follows from C5. Any emergent-organ claim remains behind the Emergence Certificate.
