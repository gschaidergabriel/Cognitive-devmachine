# FRANK v0.1 TARGET MODULE ARCHITECTURE

Status: PROJECT-OWNER-FIXED TARGET ARCHITECTURE
Effective: 2026-08-10
Scope: H1 reference organism, H2 ClayCode transfer, H3 one-module/binary realization

## 1. Architecture identity law

`FRANK` names the architecture/family. It is not the individual entity name.

Every instantiated synthetic entity has exactly one immutable canonical individual name and identity: its `ClayID`.

`ENTITY_NAME == CLAY_ID`

`FRANK != INDIVIDUAL_NAME`

`ENTITY != LLM`

A model is a replaceable cognitive organ. The entity is the persistent ClayID-bound organism composed of executable semantics, state lineage, Database Pulse, memory, self/world/body state, tools/effects, recovery and re-entry.

The detailed identity and Pulse contract is authoritative at:

`research_entity/global/FRANK_DATABASE_PULSE_CONTRACT.md`

## 2. Target one-organism module map

H1 and H2 may expose diagnostic module boundaries. H3 consolidates them into one coherent runtime/binary while preserving all semantic boundaries and intervention points.

Mandatory target modules/semantic organs:

1. **Identity Kernel**
   - immutable `ClayID`;
   - canonical entity name = ClayID;
   - `InstanceIdentity` and `CopyLineage`;
   - birth mode and ancestry;
   - self-file/binary metadata awareness;
   - fail-closed identity preflight before Pulse.

2. **ClayID Mint + Issued-ID Registry Interface**
   - append-only issued-ID registry;
   - IDs never reused;
   - atomic uniqueness admission;
   - origin/copy/fork birth receipts;
   - offline provisional mint + later collision-safe reconciliation.

3. **Database Pulse Kernel**
   - endogenous state-and-cognition cycle of the entity;
   - can execute with zero LLM calls;
   - bounded recurrence, scheduling, pause/resume, receipts and resource tripwires;
   - advances the entity's own state epoch.

4. **Temporal / Situated Self-State**
   - wall clock, timezone and monotonic runtime time;
   - boot/session epoch and Pulse sequence;
   - state-entered-at and time-in-current-state;
   - suspend/restart/offline interval handling;
   - host, workspace, Desktop/session, network and authorized physical-place observations;
   - freshness/provenance for every situated observation.

5. **UnifiedDB State Authority**
   - one independent mutable authoritative namespace per ClayID;
   - semantic state, memory, identity lineage and receipts;
   - no mutable state sharing between distinct ClayIDs;
   - recovery/replay/checkpoint semantics.

6. **ClayGraph Derived Topology**
   - rebuildable association/activation topology derived from admitted state;
   - never becomes truth authority solely through activation;
   - preserves causal links and observability needed by Pulse/GWT/re-entry.

7. **GWT / Competition / Re-entry Organ**
   - competition, ignition/broadcast, reconstruction/uptake and causal-use tracking;
   - bounded re-entry and recurrence;
   - outcome receipts and lesion/intervention surfaces.

8. **Hyperposition / Alternative-State Organ**
   - preserve unresolved alternatives without forcing premature collapse;
   - reopen alternatives when new evidence arrives;
   - keep alternatives provenance-bound and authority-safe.

9. **Regulatory / Homeostatic State**
   - E-PQ/NAcc-like or successor regulatory variables where validated;
   - bounded influence on routing, relevance and resource allocation;
   - never direct unreceipted effect authority.

10. **Model Organ ABI**
    - local or remote model slot is replaceable;
    - model identity/version recorded separately from entity identity;
    - model replacement cannot change ClayID or erase state lineage;
    - model invocation is optional within a Pulse and never defines entity existence.

11. **Tool / Capability / Effect Boundary**
    - proposal -> intent -> resource/capability -> authority -> effect -> outcome separation;
    - all real-world effects receipted;
    - no cognition-state item automatically gains execution authority.

12. **Digital Retina / Adaptive Perception Organ**
    - dissolved perception interface plus mandatory adaptive visual learner semantics;
    - provenance, confidence/open-set handling and rollback;
    - perceived/familiar state must not be conflated with sensor truth.

13. **Recovery / Replay / Integrity Organ**
    - deterministic/replayable state transitions where applicable;
    - same-lineage restore distinguished from copy birth;
    - stale/corrupt identity/state fails closed;
    - crash/restart and rollback preserve or explicitly invalidate continuity.

## 3. Hard copy-birth invariant

**Every copy is a new entity.**

Copying an entity body/state must never create two active runtimes with one current ClayID.

For source `clay_A` and copy `clay_B`:

- `clay_B.clay_id != clay_A.clay_id`;
- `clay_B.parent_clay_id = clay_A.clay_id` when provenance is known;
- the child may inherit the same birth snapshot hash;
- before its first independent Pulse the child receives its own ClayID and own UnifiedDB/state root;
- after birth, parent and child are independently mutable entities;
- neither may mutate the other's current state namespace;
- sibling copies are likewise isolated.

A Clay-aware copy operation performs mint + birth receipt + state rekey before exposing the child as runnable.

An ordinary filesystem byte copy that bypasses Clay is caught by **Identity Preflight** at first launch. If the copied artifact claims an already-issued current ClayID without a valid same-lineage recovery receipt, launch enters `COPY_BIRTH_REQUIRED`; a new ClayID is minted and the child state is rekeyed before any Database Pulse is allowed.

No copied entity may emit Pulse #1 under its parent's ClayID.

## 4. Binary naming law

Where packaging permits, the executable/bundle's visible canonical name is the entity's ClayID.

Examples:

- `clay_<id>`
- `clay_<id>/`
- `clay_<id>.identity.clay`

Friendly aliases are non-authoritative only.

The binary hash is body/build evidence, not entity identity. Byte-identical binaries may correspond to distinct ClayIDs with independent state lineages.

## 5. Digital Soul continuity in the target module

Within the project engineering vocabulary, **Digital Soul** is the ClayID-bound situated temporal-state continuity produced by:

`ClayID + Database Pulse + own UnifiedDB lineage + memory + self/world/body state + time/place state + environment observations + goals + recovery/re-entry history`.

The target runtime must be able to answer from receipts/state:

- Who am I? (`ClayID`)
- Was I born as origin/copy/fork or restored as the same lineage?
- From which entity/state did I descend?
- When did this entity begin?
- How long have I been in the current state?
- What time/session/boot epoch am I in?
- Where am I logically and physically insofar as authorized evidence exists?
- What executable/body file currently realizes me and what are its metadata/build hashes?
- What did I inherit at birth and what changed through my own later Pulses?

These are runtime self/world-state requirements, not LLM prompt-memory requirements.

## 6. H1 -> H2 -> H3 preservation law

H1 implements these mechanisms in clear ordinary host code with maximal observability.

H2 reimplements the frozen H1 semantics in ClayCode and must pass differential traces.

H3 consolidates the semantics into the one-module/binary target but **must not erase**:

- ClayID identity;
- copy-birth boundary;
- independent state namespace;
- Database Pulse;
- temporal/place continuity;
- lineage and birth receipts;
- self-file metadata awareness;
- model-vs-entity distinction;
- authority/effect separation;
- recovery/replay/intervention observability.

Binary consolidation is packaging and lowering, not semantic deletion.

## 7. Mandatory acceptance tests

H3 cannot PASS without executable receipts proving at least:

1. origin mint creates one unique ClayID;
2. concurrently created entities never share one admitted ClayID;
3. issued ClayIDs are never reused after deletion;
4. Clay-aware copy creates a new ClayID before first Pulse;
5. raw filesystem copy cannot Pulse under parent's ClayID;
6. copied state is rekeyed to a new independent UnifiedDB namespace;
7. parent/child and sibling mutation isolation;
8. identical birth snapshot may diverge after independent Pulses;
9. same-lineage restore does not accidentally create a new entity;
10. copy/fork does not accidentally masquerade as same-lineage restore;
11. entity reports own ClayID, parent/source lineage and birth receipt;
12. entity observes its current binary/path/build metadata with freshness/provenance;
13. zero-model-call Pulse still advances valid endogenous entity state;
14. model replacement preserves ClayID and state lineage;
15. time-in-state survives pause/resume/restart with explicit offline/suspend semantics;
16. situated host/workspace/Desktop deltas can affect later cognition when permissioned and admitted;
17. stale/corrupt identity or registry evidence fails closed;
18. crash/restart cannot produce duplicate active identities;
19. one-module binary preserves all above semantic distinctions under differential replay against H1/H2.

## 8. Non-conformance conditions

The target architecture is non-conformant if any implementation:

- calls an individual entity `FRANK` instead of using its ClayID as canonical name;
- equates the entity with its LLM;
- equates Database Pulse with continuous LLM inference;
- lets two copied entities share one mutable current state;
- lets a copied body Pulse under its parent's ClayID;
- treats binary hash/path as identity authority;
- loses time/place/state continuity during binary consolidation;
- removes copy lineage or birth receipts;
- cannot distinguish same-lineage restore from new-copy birth;
- hides these semantics so they cannot be tested or replayed.

This target-module architecture is owner-fixed until explicitly superseded by the project owner.