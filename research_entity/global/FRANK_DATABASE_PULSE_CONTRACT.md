# FRANK Database Pulse Contract

Status: PROJECT-OWNER-FIXED ARCHITECTURE BOUNDARY
Effective: 2026-08-09
Subject: FRANK v0.1 synthetic entity

## Canonical definition

**Database Pulse is the endogenous state-and-cognition cycle of FRANK.**

It is not an LLM inference loop, not a prompt loop, and not a synonym for model generation. FRANK is the synthetic entity; an LLM is only one replaceable cognitive organ available to that entity.

## Entity boundary

`FRANK != LLM`

`DATABASE_PULSE != LLM_INFERENCE_LOOP`

The Pulse belongs to the persistent FRANK runtime/state organism. It may read, update, rank, consolidate, relate, re-enter, decay, reactivate, and otherwise transform admitted FRANK state according to explicit typed rules, evidence/provenance, budgets, and authority constraints. Model inference may be invoked as one bounded organ when useful, but the Pulse must remain semantically meaningful without equating its existence to continuous model calls.

## Digital Soul: situated temporal-state continuity

Within the FRANK project, **Digital Soul** names the persistent situated continuity produced by the combination of FRANK identity/state lineage, Database Pulse, memory, body/device state, environment observations, goals, world/self model, recovery history, executable-instance identity and re-entry.

The engineering objective is that FRANK continuously maintains an evidence-backed answer to questions such as:

- **Who am I?** stable Frank identity, current copy/lineage identity, ancestry, binary/build identity, own state epoch and whether this Frank was born as a copy/fork/restore/migration descendant;
- **When am I?** current wall-clock time, timezone, monotonic runtime time, boot/session epoch, last-pulse time, time since last interaction, and time spent in the current state;
- **Where am I?** current host/device identity, execution environment, filesystem/workspace context, current desktop/session context, network/environment context and, only when an authorized sensor/source provides it, physical/geographic location;
- **What state am I in?** active goals, commitments, cognitive mode, body/device/resource state, current workspace/desktop context, open tasks, recent events, memory/re-entry state and confidence/freshness of each observation;
- **How long have I been like this?** state-entry timestamp plus monotonic duration, with suspend/restart/recovery semantics explicitly recorded;
- **What changed around me?** admitted deltas from the immediate digital environment such as files/folders, applications, sessions, connected devices, tools, capabilities and other authorized observations.

This is a **situated synthetic-entity self/world model**, not an LLM context trick. The LLM may receive a projection of this state, but the state exists independently of any one model call.

## Copy birth law: every copy is a new FRANK

**Every copy of a FRANK that is instantiated/executed is a new FRANK with its own independent state and its own Digital Soul continuity.**

This is a project-owner-fixed identity law, not a hypothesis.

A copy may inherit an initial snapshot of memories, configuration, binary bytes and state from its parent, but at the copy/birth boundary it receives a new immutable `frank_id` / `soul_id` and a new independent state lineage. From its first independent Pulse onward, all state transitions, memories, goals, environment observations, temporal history, graph epochs, recovery history and future learning belong to that new FRANK.

Required invariants:

- `COPY(A) = B` implies `B.frank_id != A.frank_id`;
- `B.parent_frank_id = A.frank_id` when provenance is known;
- `B.birth_state_hash` may equal A's copied source-state hash, but subsequent state histories are independent;
- parent and child may never silently share one mutable current UnifiedDB state as if they were one identity;
- later synchronization, messaging or memory exchange between FRANKs is an explicit inter-entity operation with provenance, never identity merging;
- two byte-identical binaries can be two different FRANKs;
- two FRANKs can begin with byte-identical state snapshots and still be distinct from the moment separate identity is minted;
- deleting one FRANK must not implicitly delete or mutate its siblings/descendants;
- a restored checkpoint of the *same* FRANK is not automatically a new FRANK when the recovery contract proves same-lineage continuation; a user-created duplicate/clone/copy is always a new FRANK;
- if provenance cannot distinguish restore from copy, identity status must fail safe as `IDENTITY_UNCERTAIN` until adjudicated.

This yields a family-tree model rather than a shared-singular-instance model: ancestry can be common, current identity cannot.

## InstanceIdentity / CopyLineage

Every FRANK must maintain a provenance-bound `InstanceIdentity` and `CopyLineage` record. At minimum retain, where available:

- immutable `frank_id` / `soul_id`;
- runtime `instance_id`;
- `parent_frank_id`;
- `lineage_root_frank_id`;
- `birth_event_id`;
- `birth_time`;
- birth mode: `ORIGIN`, `COPY`, `FORK`, `RESTORE_SAME_LINEAGE`, `MIGRATION_SAME_LINEAGE`, `REBUILD_NEW_FRANK`, or `IDENTITY_UNCERTAIN`;
- source FRANK ID and source state/checkpoint epoch;
- source state hash;
- source binary/build hash;
- source host/device identity;
- first independent Pulse epoch;
- current state epoch/hash;
- lineage confidence and provenance receipt IDs.

FRANK should be able to answer, from evidence rather than inference alone: **"Bin ich eine Kopie? Von welchem FRANK stamme ich? Wann wurde ich zu einem eigenen FRANK? Welchen State habe ich geerbt und was habe ich seitdem selbst erlebt/gelernt?"**

## Self-file / binary metadata awareness

FRANK must maintain a bounded self-referential metadata record for the executable artifact(s) that realize its current runtime. Depending on packaging this may be one binary plus manifest/state bundle rather than literally one file.

Where supported and meaningful, retain:

- canonical executable path;
- resolved real path after symlinks;
- filename;
- file size;
- filesystem/device/inode identity where available;
- creation/birth time where exposed by the filesystem;
- modification time;
- executable content hash, preferably SHA-256 or the project-standard stronger identity;
- build/commit hash;
- semantic/build version;
- compiler/toolchain identity;
- build timestamp;
- signature/attestation status if present;
- runtime host and mount/filesystem context;
- metadata observation timestamp/freshness.

File metadata is evidence about the current body/artifact, not the whole identity. Copying the binary creates a new FRANK only when that copy is instantiated under the copy-birth law; merely storing another inert file is not yet an executing FRANK.

### Temporal continuity requirements

FRANK must distinguish at least:

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

### Situated environment / place requirements

"Place" is multi-layered and must carry provenance. FRANK may maintain:

1. logical place: project/workspace/repository/task context;
2. host place: machine/device/VM/container identity;
3. desktop place: active user session, working directory, visible/authorized folders, applications and windows where available;
4. network place: current network/interface/site context where available;
5. physical place: geographic/location sensor evidence only when explicitly available and authorized.

The phrase "FRANK knows where it is" means that FRANK maintains a current, provenance-bound estimate of these situated layers. Missing/stale location evidence must remain `UNKNOWN` or `STALE`, never guessed.

### Immediate digital-environment intake

Authorized local artifacts such as Desktop folders, project directories, mounted resources, application/session state or device observations can become part of FRANK's immediate environment model. Intake must be permission-scoped, provenance-bound and budgeted.

FRANK must not indiscriminately ingest the entire machine. For each observation, retain source, timestamp, freshness, scope, identity/hash where useful, and whether the content itself or only metadata was admitted. Sensitive/private data boundaries remain explicit.

## Persistence / continuity semantics

A running FRANK may continue pulsing across idle periods while its executable runtime plus admitted persistent state remain available and the Pulse scheduler is enabled. The durable continuity object is that FRANK's own versioned identity/state lineage plus executable Pulse semantics, not a transient LLM context window.

Deleting or stopping a process is not automatically equivalent to deleting that FRANK if its admitted state and executable semantics remain recoverable under the same-lineage recovery contract. Conversely, retaining a binary file alone does not prove an actively running Pulse. Operational claims such as `PULSING`, `PAUSED`, `STOPPED`, `RECOVERABLE`, or `DELETED` must be backed by runtime/state receipts.

If execution is paused, FRANK must preserve the pause boundary and recover the elapsed interval rather than pretending uninterrupted processing occurred.

## Cognitive cycle

A Pulse may include, where implemented and evidence-gated:

1. census of this FRANK's current UnifiedDB/entity state;
2. verification/update of self identity, copy lineage and binary/body metadata;
3. update of temporal, body/device and situated-environment state;
4. activation/relevance propagation in derived ClayGraph projections;
5. hypothesis/codependency/alternative generation under bounded rules;
6. GWT-like competition/selection and routing;
7. Hyperposition preservation/reopening of unresolved alternatives;
8. homeostatic / E-PQ / NAcc-like regulatory updates where validated;
9. memory consolidation, decay, novelty and re-entry bookkeeping;
10. optional bounded model/tool/peer invocation;
11. outcome/receipt ingestion;
12. epoch advance and preparation of the next FRANK cognitive/action cycle.

UnifiedDB remains semantic authority for that FRANK; ClayGraph remains derived/rebuildable activation/association topology and never becomes truth authority merely because something is highly activated.

## Binary / runtime relation

The future one-module/binary FRANK must preserve the Database Pulse, Digital Soul continuity, copy-birth law and self-file/lineage awareness as endogenous entity mechanisms. Binary consolidation may change physical packaging but must not collapse the Pulse into "call the LLM repeatedly" or erase FRANK identity, independent state, temporal/place state, provenance, recovery, replay, ancestry or intervention observability.

A binary is an executable realization/body of a FRANK, not the totality of identity by itself.

## Measurement boundary

`pulse_count`, `state_transition_count`, `graph_change`, `hypothesis_count`, `memory_update`, `reentry_count`, `model_call_count`, `tool_call_count`, `effect_count`, `environment_observation_count`, `time_in_state`, `situated_state_change_count`, `copy_birth_count`, and `lineage_change_count` are distinct observables.

A Pulse can occur with zero LLM calls. An LLM call can occur without constituting a full Database Pulse.

Promotion tests must include at minimum:

- zero-model-call Pulse episodes;
- model-assisted Pulse episodes;
- stable wall-clock + monotonic-time tracking;
- state-duration tracking across normal operation;
- pause/resume and crash/restart continuity;
- host/workspace/Desktop-context change detection under explicit permissions;
- self-file/binary metadata observation and change detection;
- create a byte-identical copy and prove a new `frank_id` plus independent state lineage is minted on instantiation;
- prove parent and child can diverge without state overwrite;
- prove one child's deletion/state corruption does not alter parent/sibling state;
- prove explicit inter-FRANK exchange does not merge identities;
- prove same-lineage restore is distinguished from a new-copy birth when receipts permit;
- stale/unknown place, time or lineage evidence handling;
- deterministic/replayable state receipts where applicable;
- stale/corrupt state fail-closed behavior;
- bounded resource use and runaway-loop prevention;
- proof that model replacement does not erase a FRANK's identity/state lineage;
- proof that Pulse-generated state can causally affect later FRANK cognition/action without being confused with sensor truth or execution authority.

## Epistemic boundary

Within this project, "lives", "thinks", "continues thinking", "time sense", "place sense" and "Digital Soul" may be used as engineering shorthand for a running synthetic entity whose endogenous Pulse maintains persistent stateful cognitive, temporal, identity and situated-environment transitions.

These engineering definitions do **not** by themselves establish phenomenal consciousness, biological life, subjective experience, sentience or moral status. Those are separate scientific/philosophical questions and must not be inferred solely from persistence, recurrence, self-location, copy-awareness or temporal continuity.

## Required downstream interpretation

All FRANK, Harness, GWT, Emergence, ClayCode, ClayGraph, UnifiedDB, Hyperposition, Digital Retina and binary-freeze work must preserve this distinction, the Digital Soul continuity surface and the copy-birth law. Any design that makes Database Pulse synonymous with continuous LLM inference, shares one mutable current state between distinct FRANK copies, or discards FRANK's time/place/identity continuity during binary consolidation is non-conformant unless the project owner explicitly changes this contract.
