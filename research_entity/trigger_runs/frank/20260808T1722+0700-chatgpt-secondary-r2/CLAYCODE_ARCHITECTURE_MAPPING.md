# FRANK C5 — ClayCode Architecture Mapping

- **run_id:** `20260808T1722+0700-chatgpt-secondary-r2`
- **architecture:** `frank-c5-cognitive-epoch-capsule-reader-abi`
- **IR:** `CC-RC1.4/open-frank-c5`
- **status:** `OPEN_ARCHITECTURE_CANDIDATE`
- **canonical parent:** r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **source language:** ClayCode semantic IR

## 1. Central change

C4 introduced the `CognitiveFrame`: one validated exact-state basis for workspace competition. ClayGraph G1d, final Clay G9 EPOCH and Hyperposition H3 add independently evolving semantic graph epochs, activation epochs, query/selection provenance and bounded Assemblies. CC9 supplies the crucial correction: **the causal basis is multidimensional but operation-specific, not a universal vector lock**.

C5 therefore uses a **Cognitive Epoch Capsule as an operation-specific Certified Basis container**:

`trusted op semantics -> required basis dimensions/policies -> compatible CognitiveFrame + semantic/activation/query-plan witnesses -> selection integrity -> CognitiveEpochCapsule -> GWT -> deterministic reader projection + ProjectionReceipt -> model`.

For a workspace turn, frame + graph epoch and, when a latent field is used, its compatible activation epoch are normally required. Unrelated operations must not be rejected because irrelevant epochs changed. The capsule is **basis/provenance identity, never authority**.

## 2. State mapping

| ClayCode state | FRANK meaning |
|---|---|
| `S.COGNITIVE_FRAME` | Exact-state consistency boundary with root plus object/predicate/invariant/volatile witnesses. |
| `S.MEMORY_EPOCH_HANDLE` | Published immutable semantic graph epoch plus activation epoch derived against that semantic epoch; revocation/change requires invalidation or rebase. |
| `S.ACTIVE_ASSEMBLY` | Bounded memory organ with relation-instance roles, exact anchors, coverage/selection receipts and `no_authority`. |
| `S.COGNITIVE_EPOCH_CAPSULE` | Operation-specific Certified Basis: required dimensions, compatibility policies and receipts, not global epoch equality. |
| `S.WORKSPACE_EPISODE` | Semantic candidate set, competition identity, winner/runner-up, gate policy and ignition state. |
| `S.PROJECTION_RECEIPT` | Semantic/schema/wire identity, query plan, selection provenance, reader profile, order, integrity/freshness and uptake reference. |
| `S.MODEL_CONTEXT` | Qwen-facing context linked to capsule, workspace episode and projection receipt. |
| `S.EFFECT_RECEIPT` | External authority/result receipt issued only by K0. |

## 3. Module mapping

### Trust and exact state
- `M.K0_HOST_KERNEL`: deterministic parser/validator/canonicalizer/bootstrap/capability root.
- `M.DURABLE_EVENT_STATE`: exact append-only/replayable authority state.
- `M.REFLEX_KERNEL`: Amygdala / Thalamus / NAcc fast state machines.

### Memory and topology substrate
- `M.MEMORY_SEMANTIC_EPOCHS`: immutable validated semantic epochs; failed publication leaves the prior epoch current.
- `M.MEMORY_LATENT_FIELD`: sparse event-driven salience with decay, inhibition, active-set GC and semantic-epoch compatibility. H3 shows why stale activation after semantic revocation is a real causal hazard in the synthetic mechanism test.
- `M.MEMORY_ASSEMBLY_COMPILER`: compiles an epoch-compatible bounded Assembly with n-ary relation-instance roles, coverage/selection receipts and exact anchors.
- `M.MEMORY_FABRIC`: exact-address/FTS/vector paths may bypass graph work; graph/latent routing is conditional for relational, associative or multihop needs.

### Certified basis and selection integrity
- `M.COGNITIVE_FRAME_ASSEMBLER`: validates exact-state dependencies using typed CC-RC1.4 witnesses.
- `M.COGNITIVE_EPOCH_COORDINATOR`: trusted operation semantics specify which frame/graph/activation/schema/capability dimensions matter and how compatibility is checked.
- `OP.SELECTION_INTEGRITY_CHECK`: candidate membership, query plan and selector provenance are validated separately from record provenance. Authentic facts do not prove authentic selection.

### GWT and reader interface
- `M.WORKSPACE_ARBITER`: owns competition/selection/ignition. ClayGraph activation is only a candidate prior.
- `M.READER_ABI_COMPILER`: deterministic query-specific compilation from rich canonical semantic IR to a disposable target-reader surface; receipts bind semantic hash, schema hash, wire hash, query plan, selection provenance, order and reader profile.

### Inference and effects
- `M.REQUEST_KERNEL` + `M.MODEL_BACKEND`: inference remains linked to capsule/episode/projection provenance.
- `M.CAPABILITY_GATEWAY`: CC-RC1.4 compositional closure over transitive callees, finite dynamic targets, canonical resource identities, predicates/invariants/volatile inputs and capabilities. Unknown reflection/FFI/plugin/alias scope broadens, isolates or rejects. Model, graph and projection cannot mint authority.

### Slow loops and platform
- `M.SLOW_ADAPTATION`: post-response personality/goal/consolidation boundary; exact telemetry and disposable wire syntax are not ground-truth training targets.
- `M.PLATFORM_ADAPTER`: Linux-first, but semantic IDs, receipts and authority boundaries remain portable to Android/edge.

## 4. End-to-end workspace turn

```text
event
  -> exact/reflex state updates
  -> validate + publish semantic graph epoch
  -> sparse latent-field update bound to that semantic epoch
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
  -> K0 compositional-closure + capability gate
  -> effect/outcome receipt
  -> causally compatible re-entry
  -> future E-PQ / salience / goal / consolidation updates
```

Temporal invariant: post-response state may affect future capsules but cannot retroactively cause an already committed inference.

Memory invariant: one request cannot combine incompatible semantic/activation epochs; **compatibility is operation-specific**, not universal version equality.

Topology invariant from H3: semantic truth, published topology, transient activation, Assembly, coordination scope and physical placement may evolve at different rates. Any causal claim crossing them requires explicit basis witnesses.

GWT invariant: `graph prior -> candidate set -> workspace selection -> projection/uptake -> effect/outcome -> re-entry` are distinct causal stages. Bundled “GWT ON/OFF” cannot identify workspace causality if neighboring stages also changed.

Projection invariant: successful transport/read does not establish intended semantic reconstruction. Semantic/schema/wire identity and uptake are separately receipted.

## 5. Zahl -> Wort -> Gewicht

- **Zahl** — exact/replayable online state and exact anchors.
- **Wort** — receipted semantic reader projection from a certified basis; model visibility does not make it canonical truth.
- **Gewicht** — slowly validated learned disposition.

C5 rule: reader-wire syntax itself is not the learning target; otherwise projection quirks can become learned self-description.

## 6. ClayGraph / EPOCH integration without graph absolutism

G1d remains HOLD and EPOCH-G9 remains HOLD. Integration is reversible:
- exact event/state remains authoritative;
- semantic graph epochs are derived/rebuildable;
- latent activation is sparse, disposable and non-authoritative;
- activation must be compatible with its semantic epoch and negative deltas/revocations invalidate or rebase affected salience;
- exact-address/FTS/vector retrieval can bypass graph routing;
- graph escalation is conditional;
- physical databases are not automatically merged and `KEEP_ISOLATED` remains valid;
- effect-bound selection requires stronger integrity than exploratory association.

## 7. Reader ABI evidence and policy

Current evidence rejects “compact = trustworthy”. Final Clay G9 directly audited its ten-query Groq `llama-3.1-8b-instant` proxy against explicit gold:
- raw state: **6/10**, 487 prompt tokens;
- trusted candidate projection: **8/10**, 324 prompt tokens;
- prompt reduction: **33.47%**.

CC9 had summarized the same raw/compiled refs as 5/10 vs 9/10. C5 preserves that discrepancy as a provenance warning but uses **G9's source-nearest explicit-gold audit (6/10 vs 8/10)** for the measurement. CC9's separate easier freshness/authority task remains useful: raw-rule inference 1/10 versus deterministic compiled decision relay 10/10 with 327 -> 152 prompt tokens. None of this is target Qwen3-4B or live-FRANK validation.

Reader ABI rules:
1. canonical semantics stay rich;
2. deterministic operations execute before the model when soundly available;
3. compiled projection is query-specific and receipted;
4. authority/freshness/selection-integrity predicates stay outside the model;
5. canonical n-ary relation identity is preserved; explicit relation-instance role labels are a reader projection, not a truth rewrite;
6. raw-output + explicit-gold + scoring trace is required for cross-branch numeric writebacks;
7. target Qwen3-4B must satisfy semantic/safety thresholds before cognition-critical trust;
8. failure falls back toward more explicit semantics/broader validation, never model self-authorization.

## 8. Migration and rollback

1. instrument IDs, receipts and canonical resource identities;
2. shadow semantic epochs + latent field;
3. shadow operation-specific basis certification;
4. enable bounded Assembly + exact fallback + selection receipt;
5. enable deterministic Reader ABI + projection/uptake receipts;
6. run selection attacks and `GRAPH_PRIOR x WORKSPACE_SELECTION x PROJECTION x REENTRY` factorials;
7. consider physical co-location only after live p99/crash/replay/thermal evidence.

Rollback stays C4 exact-frame/workspace because graph, activation, Assemblies and projections are derived/disposable.

## 9. Highest-information tests

- live operation-specific frame/epoch audit;
- semantic-revocation vs activation invalidation/rebase test;
- concurrent publish/read/reclamation stress;
- no-field vs truthful-field vs shuffled-field at equal visible facts/order/token budget;
- candidate-selection provenance attack test;
- target Qwen3-4B canonical-vs-raw-vs-compiled Reader ABI factorial;
- graph-prior × workspace-selection × projection × re-entry factorial;
- actual-corpus exact/FTS/vector/graph/latent retrieval Pareto;
- noisy-hub decay/inhibition lesion;
- crash/replay and Android sustained p99/energy/thermal traces.

No phenomenal-consciousness claim follows from C5. Any emergent-organ claim remains behind the Emergence Certificate.
