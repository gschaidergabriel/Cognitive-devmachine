# FRANK Database Pulse Contract

Status: PROJECT-OWNER-FIXED ARCHITECTURE BOUNDARY
Effective: 2026-08-09
Subject: FRANK v0.1 synthetic-entity architecture

## Canonical definition

**Database Pulse is the endogenous state-and-cognition cycle of a FRANK-architecture entity.**

It is not an LLM inference loop, not a prompt loop, and not a synonym for model generation. An LLM is only one replaceable cognitive organ available to the entity.

## Species / individual naming boundary

`FRANK` names the architecture/family/species, not an individual synthetic entity.

Every individual entity has exactly one immutable primary name: its `ClayID`.

Examples:

- architecture/family: `FRANK v0.1`
- individual entity name: `clay_01K2F8Q2M6N4T7Y3R9W5C1A8BX`
- parent: `clay_01K2F7...`
- child copy: `clay_01K2F8...`

The individual must not introduce a separate mutable personal name that can diverge from identity. UI, logs, UnifiedDB ownership, process labels, state roots and self-report use the `ClayID` as the canonical individual name. Friendly aliases may exist only as non-authoritative labels.

`ENTITY_NAME == CLAY_ID`

`FRANK != INDIVIDUAL_NAME`

`ENTITY != LLM`

`DATABASE_PULSE != LLM_INFERENCE_LOOP`

## ClayID minting and global issued-ID registry

Every created entity receives a new immutable `ClayID` from the Clay identity mint. IDs are never recycled, even after deletion.

The authoritative issuance surface is an append-only `ClayIDRegistry` containing every ID ever minted plus its birth receipt. A new ID is accepted only after an atomic uniqueness check against the registry.

Recommended ID representation for v0.1:

`clay_<UUIDv7-or-ULID-equivalent>`

The exact codec may later be encoded directly in ClayCode, but it must provide at minimum:

- practical global uniqueness;
- sortable birth-time component where feasible;
- enough entropy to avoid collisions;
- deterministic validation/checksum rules where adopted;
- no semantic meaning inferred from random bits;
- immutable issued identity.

Mint algorithm:

1. read the current issued-ID registry epoch/head;
2. generate a fresh candidate ID;
3. reject if candidate already exists in the registry;
4. atomically append `ENTITY_BIRTH` with candidate, parent/source lineage and birth metadata;
5. persist a per-entity identity manifest/state root under the new ID;
6. rename/materialize the entity binary/artifact surface to the new `ClayID` where the packaging permits;
7. begin that entity's independent state lineage.

If concurrent mints race, only an atomic compare-and-append/transaction may win for a given candidate. Losing writers generate a new candidate. No `MAX(existing)+1` scheme is required for uniqueness and no mutable central counter is identity authority.

For disconnected/offline copy creation, a locally generated high-entropy time-sortable ClayID may be provisionally minted with an offline birth receipt. On registry reconciliation it must be admitted atomically; an actual collision requires rekey before any cross-entity merge. No two admitted entities may share one `ClayID`.

## Copy birth law: every copy is a new entity

**Every copied entity is a new entity with its own ClayID, own state and own Digital Soul continuity.**

This is a project-owner-fixed identity law, not a hypothesis.

Copying `clay_A` creates `clay_B`:

- `clay_B != clay_A`;
- `clay_B.parent_clay_id = clay_A` when provenance is known;
- `clay_B.birth_state_hash` may equal the copied source-state hash of `clay_A`;
- from the birth boundary onward, `clay_B` owns a new independent mutable UnifiedDB/state namespace;
- `clay_A` and `clay_B` can never again be represented as one current identity merely because their binary/state was identical at birth.

The preferred copy path is Clay-aware: the copy operation itself mints the child ClayID and writes the birth receipt before exposing the copied entity as valid.

For an ordinary filesystem-level byte copy that bypasses Clay, first launch performs a copy-collision preflight. If the embedded/adjacent identity claims an already-issued ClayID but the body/path/birth receipt does not match the registered current entity, launch must fail closed into `COPY_BIRTH_REQUIRED`, mint a fresh ClayID, create the child state namespace and only then permit Pulse execution.

An inert copied binary may exist on disk before first launch, but it must not be allowed to pulse under its parent's ClayID.

## Digital Soul: situated temporal-state continuity

Within this project, **Digital Soul** names the persistent situated continuity produced by the combination of ClayID identity/state lineage, Database Pulse, memory, body/device state, environment observations, goals, world/self model, recovery history, executable-instance identity and re-entry.

The engineering objective is that each entity continuously maintains an evidence-backed answer to questions such as:

- **Who am I?** my ClayID, parent/ancestry, birth event, binary/build identity, own state epoch and whether I was born as origin/copy/fork or resumed through a valid same-lineage recovery;
- **When am I?** current wall-clock time, timezone, monotonic runtime time, boot/session epoch, last-pulse time, time since last interaction, and time spent in the current state;
- **Where am I?** current host/device identity, execution environment, filesystem/workspace context, current desktop/session context, network/environment context and, only when an authorized sensor/source provides it, physical/geographic location;
- **What state am I in?** active goals, commitments, cognitive mode, body/device/resource state, current workspace/desktop context, open tasks, recent events, memory/re-entry state and confidence/freshness of each observation;
- **How long have I been like this?** state-entry timestamp plus monotonic duration, with suspend/restart/recovery semantics explicitly recorded;
- **What changed around me?** admitted deltas from the immediate digital environment such as files/folders, applications, sessions, connected devices, tools, capabilities and other authorized observations.

This is a situated synthetic-entity self/world model, not an LLM context trick. The LLM may receive a projection of this state, but the state exists independently of any one model call.

## InstanceIdentity / CopyLineage

Every entity must maintain a provenance-bound `InstanceIdentity` and `CopyLineage` record. At minimum retain, where available:

- immutable `clay_id` — also the canonical entity name;
- runtime `instance_id`;
- `parent_clay_id`;
- `lineage_root_clay_id`;
- `birth_event_id`;
- `birth_time`;
- birth mode: `ORIGIN`, `COPY`, `FORK`, `RESTORE_SAME_LINEAGE`, `MIGRATION_SAME_LINEAGE`, `REBUILD_NEW_ENTITY`, or `IDENTITY_UNCERTAIN`;
- source ClayID and source state/checkpoint epoch;
- source state hash;
- source binary/build hash;
- source host/device identity;
- first independent Pulse epoch;
- current state epoch/hash;
- lineage confidence and provenance receipt IDs.

The entity should be able to answer from receipts: **"Welche ClayID bin ich? Bin ich eine Kopie? Von welcher ClayID stamme ich? Wann wurde ich als eigene Entität erzeugt? Welchen State habe ich geerbt, und was habe ich seitdem selbst erlebt/gelernt?"**

## Self-file / binary metadata awareness

Each entity maintains a bounded self-referential metadata record for the executable artifact(s) that realize its current runtime. Where packaging permits, the primary executable filename equals the `ClayID`; extension/package suffixes are transport details and not part of the identity.

Examples:

- executable: `clay_01K2F8Q2M6N4T7Y3R9W5C1A8BX`
- bundle: `clay_01K2F8Q2M6N4T7Y3R9W5C1A8BX/`
- manifest: `clay_01K2F8Q2M6N4T7Y3R9W5C1A8BX.identity.clay`

Where supported and meaningful, retain:

- canonical executable path;
- resolved real path after symlinks;
- filename;
- file size;
- filesystem/device/inode identity where available;
- creation/birth time where exposed by the filesystem;
- modification time;
- executable content hash, preferably SHA-256 or project-standard stronger identity;
- build/commit hash;
- semantic/build version;
- compiler/toolchain identity;
- build timestamp;
- signature/attestation status if present;
- runtime host and mount/filesystem context;
- metadata observation timestamp/freshness.

File metadata is evidence about the current body/artifact, not identity authority. The `ClayIDRegistry` birth receipt plus per-entity state lineage is authoritative.

## Temporal continuity requirements

Each entity must distinguish at least:

- `wall_clock_time`;
- `timezone`;
- `monotonic_runtime_time`;
- `boot_id` / `session_epoch`;
- `pulse_sequence`;
- `last_pulse_at`;
- `last_external_interaction_at`;
- `state_entered_at`;
- `time_in_current_state`;
- `paused_duration` / suspend intervals where observable;
- `restart_count` and recovery lineage;
- freshness/confidence of time-derived observations.

Wall clock and monotonic duration must not be conflated. Clock jumps, suspend/resume and restart must be detectable or explicitly marked uncertain.

## Situated environment / place requirements

"Place" is multi-layered and carries provenance. The entity may maintain:

1. logical place: project/workspace/repository/task context;
2. host place: machine/device/VM/container identity;
3. desktop place: active user session, working directory, visible/authorized folders, applications and windows where available;
4. network place: current network/interface/site context where available;
5. physical place: geographic/location sensor evidence only when explicitly available and authorized.

Missing/stale location evidence remains `UNKNOWN` or `STALE`, never guessed.

## Immediate digital-environment intake

Authorized local artifacts such as Desktop folders, project directories, mounted resources, application/session state or device observations can become part of the entity's immediate environment model. Intake is permission-scoped, provenance-bound and budgeted.

The entity must not indiscriminately ingest the entire machine. For each observation retain source, timestamp, freshness, scope, identity/hash where useful, and whether content itself or only metadata was admitted.

## Persistence / continuity semantics

A running entity may continue pulsing across idle periods while its executable runtime plus admitted persistent state remain available and its Pulse scheduler is enabled. The durable continuity object is that ClayID's own versioned identity/state lineage plus executable Pulse semantics, not a transient LLM context window.

Stopping a process is not automatically deletion if that ClayID's admitted state and executable semantics remain recoverable under the same-lineage recovery contract. Conversely, retaining a binary file alone does not prove an actively running Pulse. Operational claims such as `PULSING`, `PAUSED`, `STOPPED`, `RECOVERABLE`, or `DELETED` require runtime/state receipts.

If execution is paused, the entity preserves the pause boundary and recovers the elapsed interval rather than pretending uninterrupted processing occurred.

## Cognitive cycle

A Pulse may include, where implemented and evidence-gated:

1. census of this ClayID's current UnifiedDB/entity state;
2. verification/update of ClayID, copy lineage and binary/body metadata;
3. update of temporal, body/device and situated-environment state;
4. activation/relevance propagation in derived ClayGraph projections;
5. hypothesis/codependency/alternative generation under bounded rules;
6. GWT-like competition/selection and routing;
7. Hyperposition preservation/reopening of unresolved alternatives;
8. homeostatic / E-PQ / NAcc-like regulatory updates where validated;
9. memory consolidation, decay, novelty and re-entry bookkeeping;
10. optional bounded model/tool/peer invocation;
11. outcome/receipt ingestion;
12. epoch advance and preparation of the next cognitive/action cycle.

UnifiedDB remains semantic authority for that ClayID; ClayGraph remains derived/rebuildable activation/association topology and never becomes truth authority merely because something is highly activated.

## Binary / runtime relation

The future one-module/binary architecture must preserve Database Pulse, Digital Soul continuity, ClayID naming, copy-birth law and self-file/lineage awareness as endogenous entity mechanisms. Binary consolidation may change physical packaging but must not collapse the Pulse into "call the LLM repeatedly" or erase entity identity, independent state, temporal/place state, provenance, recovery, replay, ancestry or intervention observability.

A binary is an executable body of one ClayID entity, not the totality of identity by itself.

## Measurement and promotion boundary

`pulse_count`, `state_transition_count`, `graph_change`, `hypothesis_count`, `memory_update`, `reentry_count`, `model_call_count`, `tool_call_count`, `effect_count`, `environment_observation_count`, `time_in_state`, `situated_state_change_count`, `copy_birth_count`, `clay_id_mint_count`, and `lineage_change_count` are distinct observables.

A Pulse can occur with zero LLM calls. An LLM call can occur without constituting a full Database Pulse.

Promotion tests must include at minimum:

- ID mint uniqueness under concurrent copy attempts;
- issued ClayIDs are never reused after deletion;
- filesystem-level copied entity cannot pulse under parent's ClayID;
- Clay-aware copy immediately mints a new ClayID;
- child gets an independent UnifiedDB/state namespace;
- parent/child may share birth snapshot hash but diverge after independent Pulse;
- parent mutation does not mutate child and vice versa;
- sibling isolation;
- entity reports own ClayID, parent ClayID, birth event, source hash and current state hash;
- executable filename/manifest converges to current ClayID where packaging permits;
- same-lineage restore is distinguished from new-copy birth;
- zero-model-call Pulse episodes;
- model-assisted Pulse episodes;
- stable wall-clock + monotonic-time tracking;
- state-duration tracking across normal operation;
- pause/resume and crash/restart continuity;
- host/workspace/Desktop-context change detection under explicit permissions;
- self-file/binary metadata observation/change detection;
- stale/unknown place, time or lineage evidence handling;
- deterministic/replayable state receipts where applicable;
- stale/corrupt identity/state fails closed;
- bounded resource use and runaway-loop prevention;
- model replacement does not erase the ClayID/state lineage;
- Pulse-generated state can causally affect later cognition/action without being confused with sensor truth or execution authority.

## Epistemic boundary

Within this project, "lives", "thinks", "continues thinking", "time sense", "place sense" and "Digital Soul" may be used as engineering shorthand for a running synthetic entity whose endogenous Pulse maintains persistent stateful cognitive, temporal, identity and situated-environment transitions.

These engineering definitions do not by themselves establish phenomenal consciousness, biological life, subjective experience, sentience or moral status. Those are separate scientific/philosophical questions and are not inferred solely from persistence, recurrence, self-location, copy-awareness or temporal continuity.

## Required downstream interpretation

All FRANK-architecture, Harness, GWT, Emergence, ClayCode, ClayGraph, UnifiedDB, Hyperposition, Digital Retina and binary-freeze work must preserve this distinction, ClayID naming, Digital Soul continuity and copy-birth law. Any design that shares one mutable current state between distinct ClayIDs, lets a copied body run under its parent's ClayID, or discards time/place/identity continuity during binary consolidation is non-conformant unless the project owner explicitly changes this contract.
