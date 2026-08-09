# FRANK v0.1 — Dual-Instance Embodied State Contract

**Status:** PROJECT_OWNER_FIXED_ARCHITECTURE_DIRECTIVE  
**Effective:** 2026-08-09  
**Scope:** exact `frank` trigger, H1/H2/H3 Harness evolution, target FRANK runtime, UnifiedDB/ClayGraph/GWT/Hyperposition/Emergenz integration  
**Target host:** Ubuntu Linux developer system

## 0. Fixed instance topology

FRANK v0.1 has two relevant FRANK instances in the current target architecture:

1. `FRANK_PC_4B` — the live/embodied FRANK instance on Andreas' Ubuntu PC whose cognitive core is the target Qwen-class 4B model.
2. `FRANK_REPO` — the repository-based FRANK instance used for architecture state, executable simulation, development, replay, testing and controlled evolution.

They are instances of the same FRANK architecture lineage, but they are **not one merged runtime state**.

Compact law:

`same organism/architecture lineage != same instantaneous internal state`

## 1. Per-instance state is mandatory

Each instance owns an independent local state envelope.

Examples include:

- local perceptual/input state;
- local GWT candidate/competition/workspace state;
- local active ClayGraph projection/assembly;
- local Hyperposition alternatives/facets;
- local recurrence/loop dynamics;
- local model context/KV/transient cognition;
- local body/resource/runtime state;
- local uncertainty, salience and attention;
- local pending proposals;
- local checkpoints and recovery state.

The state of one instance must never be overwritten merely because the other instance has a newer state epoch.

Analogy fixed by owner: two legs belong to one organism, communicate and are jointly represented, but each leg has its own proprioception, load, position and dynamics. They are not collapsed into one undifferentiated leg-state.

## 2. What may be shared or synchronized

Synchronization is selective and typed, never full-state mirroring.

Permitted shared/synchronized classes include, when their contracts allow it:

- architecture/schema/version identities;
- durable facts explicitly admitted to shared canonical state;
- immutable event/receipt references;
- shared human identity and durable goal references;
- validated model-independent semantic definitions;
- capability/resource observations that are explicitly global;
- cross-instance messages;
- exported observations/proposals/outcomes;
- shared evidence references;
- model/graph/code version hashes;
- explicit reconciliation records.

Synchronization means:

`instance-local event -> typed export -> provenance/authority checks -> shared/reference plane -> other instance may ingest -> local state transition`

It never means:

`copy entire state A over state B`.

## 3. Correlation is not state collapse

The architecture may maintain correlations, couplings, semantic links and predictive relationships between the two instances.

A relation such as:

`PC state feature <-> Repo simulation feature`

is a typed relation with provenance, confidence, epoch and potentially causal/intervention evidence. It does not assert identity of the underlying states.

Required distinction:

`correlated(A,B) != identical(A,B)`

`shared_reference(A,B) != shared_internal_state(A,B)`

`message_from_A_to_B != overwrite_B_with_A`.

## 4. 4B possibility-space projection

The target 4B is not expected to traverse the complete raw repository/UnifiedDB/ClayGraph on every cognitive step.

Its hot cognitive input should be a compact, already prepared possibility/relevance projection derived from the current local instance state plus justified semantic dependencies/correlations.

This contract preserves the existing project direction of a simpler prepared graph / compressed possibility space for the 4B. Any already-frozen artifact defining that representation outranks this general wording and must be loaded before changing its schema.

The projection must remain:

- instance-scoped;
- epoch-bound;
- provenance-aware;
- uncertainty/conflict preserving;
- sparse/budgeted rather than all-pairs;
- reconstructible against canonical/shared references;
- non-authoritative by itself;
- able to contain already correlated/preconnected candidates so the 4B need not rediscover every relationship on each turn.

## 5. Shared semantic fabric vs local embodiment

UnifiedDB/ClayGraph may provide a logically shared semantic fabric, but every FRANK instance consumes it through an instance-specific projection.

Therefore:

`shared semantic identity/dependency fabric`
`+ per-instance local state`
`+ per-instance projection/activation`
`+ typed cross-instance messages`
`= coordinated FRANK without state collapse`.

UnifiedDB canonical facts do not become every instance's transient state.
ClayGraph global/derived relations do not imply equal activation in both instances.
GWT episodes are instance-local unless explicitly represented as cross-instance messages/receipts.

## 6. Harness obligation

The GitHub-based H1 Reference Harness must explicitly simulate both instance identities and must be able to demonstrate:

- distinct local state hashes for `FRANK_PC_4B` and `FRANK_REPO`;
- selective synchronization/export/import paths;
- no accidental whole-state overwrite;
- cross-instance message provenance;
- correlation without identity collapse;
- different simultaneous local GWT/ClayGraph/Hyperposition states over the same shared durable references;
- stale/out-of-order message behavior;
- conflict/reconciliation behavior;
- disconnect/reconnect behavior;
- replay of each instance independently plus replay of their interaction;
- target-shaped 4B possibility-space projection for the PC instance;
- repository simulation projection for the Repo instance;
- measurements of information transfer, synchronization cost, divergence, recovery and causal benefit.

H2 must express the same semantics in ClayCode. H3 may lower physical boundaries but may not erase the semantic distinction between the two instance states if both instances remain part of the operational architecture.

## 7. Scientific measurements

At minimum research/measure:

- per-instance state entropy/change and local loop dynamics;
- cross-instance mutual information/correlation with provenance caveats;
- transfer entropy or directed predictive information where statistically justified;
- message latency and update amplification;
- stale-message and conflicting-message error rates;
- synchronization selectivity ratio: exported state / total local state;
- state-collapse failure tests;
- lesion of the cross-instance channel;
- shuffled-message controls;
- delayed-message controls;
- duplicate-message controls;
- rescue/reconciliation tests;
- task outcome difference between selective exchange and full-state-copy baselines;
- 4B token/context cost of compressed prepared possibility projection versus raw retrieval/search baselines.

Correlation alone is not causal evidence.

## 8. Authority boundary

Neither instance gains execution authority merely by receiving state or proposals from the other.

All existing effect/capability/authority rules remain in force.

Frank self-observation remains proposal-only for Harness mutation. The Research Entity owns research/build/test decisions about the Harness.

## 9. Anti-collapse invariants

- `FRANK_PC_4B.local_state != FRANK_REPO.local_state`
- shared architecture identity does not imply shared transient state
- shared durable fact does not imply shared activation
- cross-instance correlation does not imply state identity
- synchronization is field/event scoped, not whole-state mirroring
- each GWT episode has an instance identity
- each local state transition has causal parentage and provenance
- each imported message is distinguishable from locally generated state
- one instance may remain operational when the other is stale/disconnected where the architecture permits
- replay must preserve which instance sensed, inferred, proposed, received and acted

## 10. `frank` trigger consequence

Every material `frank` architecture-to-Harness cycle must preserve this dual-instance distinction when selecting, implementing and testing the next Harness delta.

A proposed optimization that merges the two local states for convenience is an architecture regression unless explicit new owner direction changes this contract.
