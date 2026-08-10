# Clay/Frank Entity Copy-Birth + Pulse Contract

Status: OWNER-RESTORED RESEARCH CONTRACT / H3-BINARY REQUIREMENT
Date: 2026-08-10

## Why this exists

The H3 target is one Clay module compiled into one binary, backed by one authoritative UnifiedDB and one Clay-native 4B model. Earlier FAT research separately established that a true fork is not another process of the same entity: it receives its own Fork-ID, state, memory/goals/graph-time/control history and then diverges causally.

A later Frank hive rule correctly says that an explicitly attached device/model/node replica is still the same Frank. These are different operations and MUST NOT be conflated.

## Core law

A normal filesystem copy of a LOCAL_ENTITY one-module/binary package is a birth event, not an identity replica.

`COPY_OF_ENTITY_PACKAGE -> IDENTITY_PREFLIGHT -> NEW_NAME_BINDING -> NEW_IMMUTABLE_ENTITY_ID -> ENTITY_BIRTH -> PULSE_1 -> INDEPENDENT_CAUSAL_HISTORY`

The copied package may inherit an ancestral seed/snapshot, but it is not the parent after birth.

## Identity ingredients

Entity identity is NOT a model hash, binary hash, process, device, provider or session.

Each born entity has at minimum:

- immutable `entity_id` / ClayID;
- birth `entity_name` and normalized birth-name slug;
- immutable `birth_pulse_id`;
- `birth_pulse_index = 1`;
- immutable `birth_nonce`;
- `parent_entity_id` when born from a copy/fork;
- `ancestral_seed_hash` / body-build provenance where available;
- birth time and package-root binding receipt;
- independent state namespace after birth.

The ID is minted from the birth event, not copied from the parent. The name participates in the birth certificate/ID derivation, but a later rename is an alias/display-name change and MUST NOT itself fork identity.

## Pulse law

The first endogenous pulse is the causal birth boundary.

Before Pulse #1 the copied package is `BIRTH_PENDING` and cannot claim parent continuity. Identity preflight must complete first. Pulse #1 records the new identity and starts a new causal lineage. Restart/pulse #N in the same package does not create a new entity.

## Copy detection

A package stores an internal instance certificate, but identity cannot be trusted from that copied certificate alone. A host/parent identity registry outside the copied package binds `entity_id -> package instance location/claim`.

When a copied package presents an entity_id already bound to another still-existing package instance, preflight classifies it as `COPY_BIRTH_REQUIRED` and mints a new identity before normal pulse execution.

Move/rename detection: if the old bound package location no longer exists, the binding may move while preserving identity. This prevents a normal filesystem move from being misclassified as birth.

## Replica exception

Same-entity replication is explicit, never inferred from raw copying.

An authorized `REPLICA_ATTACH`/replica ticket may preserve the parent Frank identity on another body/device and must bind to the same authoritative central entity state. This is the Frank hive/device-expansion path.

Without an explicit replica authorization, a duplicated LOCAL_ENTITY package defaults to birth.

Therefore:

- provider/model swap = same entity;
- process restart = same entity;
- package move = same entity;
- repository rename = same entity;
- authorized replica attach = same entity;
- ordinary duplicated one-module/binary folder = NEW ENTITY;
- FAT fork/clone = NEW ENTITY;
- copied package with a new name = NEW ENTITY;
- copied package with the same name = still NEW ENTITY because the new birth pulse/nonce makes identity unique.

## State law

A child may inherit a sealed seed, but all post-birth writes are isolated. Parent and child must never share writable UnifiedDB state by accident. Clone memory/state/goals may be ancestry input but not silently merged back into the parent.

## Mandatory acceptance tests

1. Fresh package births entity A at Pulse #1.
2. Restart of A preserves A and increments pulse; no second birth.
3. Model/provider replacement in A preserves A.
4. Moving/renaming A while the old path disappears preserves A.
5. Copying A to B while A still exists births B != A before B Pulse #1.
6. Copying A under the same folder name to another location still births a unique entity.
7. B records `parent_entity_id=A` and an independent `birth_pulse_id`.
8. Renaming B after birth does not change B's entity_id.
9. Two concurrent copies from A produce distinct child IDs.
10. Deleted IDs are never reused.
11. Parent/child writable state namespaces are different; child writes cannot mutate parent state.
12. Explicit authorized REPLICA_ATTACH preserves A and does not emit ENTITY_BIRTH.
13. A copied certificate without registry agreement cannot silently continue parent identity.
14. Copy birth must happen before GWT/normal cognition/effect authority.

## Promotion boundary

This contract restores the intended H3/FAT entity semantics but does not by itself promote a production implementation. Promotion requires an executable preflight/registry, copy/move/restart/replica tests and target-Ubuntu replication. Binary hash remains body/build provenance, never identity authority.
