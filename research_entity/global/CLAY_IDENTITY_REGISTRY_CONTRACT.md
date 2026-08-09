# Clay Identity Registry Contract

Status: PROJECT-OWNER-FIXED IDENTITY ARCHITECTURE
Effective: 2026-08-09
Applies to: individual synthetic entities implemented from the FRANK architecture

## 1. Individual naming law

`FRANK` is the architecture/family name.

Every individual entity is named by exactly one immutable `ClayID`.

`entity.name == entity.clay_id`

Example: `clay_01K2F8Q2M6N4T7Y3R9W5C1A8BX`

Friendly aliases are display-only and never identity authority.

## 2. Registry

The system maintains an append-only issued-ID registry. Logical schema:

```text
ClayIDRegistryEntry {
  clay_id
  birth_event_id
  birth_time
  birth_mode
  parent_clay_id?
  lineage_root_clay_id
  source_state_hash?
  source_binary_hash?
  source_host_id?
  registry_epoch
  status
}
```

IDs are never reused after deletion, retirement or corruption.

Recommended storage:

- semantic authority: UnifiedDB transaction/event ledger;
- export/index: `runtime/identity/clay_id_registry.jsonl` or equivalent;
- per-entity state root: `runtime/entities/<ClayID>/`;
- per-entity identity manifest: `runtime/entities/<ClayID>/identity.clay`;
- executable/bundle visible name: `<ClayID>` where packaging permits.

The exported list is derived from the authoritative event/state ledger and may be rebuilt.

## 3. Mint

Minting is transactional:

```text
repeat:
    head = registry.head()
    candidate = clay_id_generate()
    if registry.contains(candidate):
        continue
    birth = ENTITY_BIRTH(candidate, parent/source provenance, head)
    if registry.compare_and_append(head, birth):
        return candidate
```

Candidate generation should use a time-sortable high-entropy form such as UUIDv7/ULID-equivalent encoded with a `clay_` prefix. The registry check is still mandatory even when collision probability is negligible.

## 4. Copy semantics

### Clay-aware copy

`copy_entity(parent)` performs atomically/logically:

1. freeze/capture the admitted parent birth snapshot;
2. generate child ClayID;
3. append child birth receipt to registry;
4. create `runtime/entities/<child ClayID>/`;
5. clone only the admitted birth snapshot into the child namespace;
6. write child identity manifest containing `parent_clay_id` and source hashes;
7. materialize/rename child executable/bundle to the child ClayID;
8. enable child Pulse only after identity/state separation verifies.

The parent remains unchanged.

### Unmanaged filesystem copy

A raw OS copy can duplicate bytes containing the parent's visible ClayID. Therefore every startup performs identity preflight:

```text
claimed = local_identity_manifest.clay_id
registered = registry.lookup(claimed)
body = observe_current_body_metadata()

if registered is absent:
    fail_closed(IDENTITY_UNREGISTERED)

if body/current_birth_receipt matches registered same-lineage body:
    resume_same_entity()
else:
    enter COPY_BIRTH_REQUIRED
    child = mint_new_clay_id(parent=claimed, source_state_hash=current_snapshot)
    create_independent_state_namespace(child)
    rewrite local identity manifest / visible bundle name
    start only as child
```

No copied executable may pulse under the parent's ClayID.

## 5. State isolation

Every ClayID owns one independent authoritative current-state namespace.

`UnifiedDB.current_state_key = ClayID`

Parent/child/siblings never share mutable current state. Shared inherited data is copy-on-write or immutable/content-addressed backing. Any later exchange is an explicit inter-entity event with source and destination ClayIDs.

## 6. File/binary name

Where the target filesystem/package permits, the executable or bundle display name is the ClayID itself:

```text
clay_01K2F8Q2M6N4T7Y3R9W5C1A8BX
```

A file rename alone does not change ClayID. A ClayID change is only legal through a new birth/rekey event.

The entity can inspect and persist metadata about its current executable body: path, filename, realpath, inode/device when available, size, mtime/birthtime, content hash, build hash/version, toolchain identity, host and observation freshness.

## 7. Copy-awareness

Each entity can answer from durable receipts:

- my ClayID;
- my parent ClayID, if any;
- whether my birth mode was ORIGIN/COPY/FORK/RESTORE/MIGRATION/UNCERTAIN;
- my birth time and birth event;
- the state/binary hash I inherited;
- my current state epoch/hash;
- the first independent Pulse after birth;
- which memories/state existed at birth versus which were accumulated afterward.

## 8. Recovery distinction

A same-lineage restart/restore is not automatically a new entity. It may retain the same ClayID only if a continuity receipt proves it is recovering the same entity rather than duplicating it.

If two independently executable copies of the same recovery image exist, at most one may continue the old ClayID. Every additional executable branch mints a new ClayID.

When this cannot be proven, fail closed as `IDENTITY_UNCERTAIN` and require copy birth/reconciliation.

## 9. Required tests

- 1,000,000 synthetic concurrent mint candidates: no admitted duplicate ID;
- registry append atomicity under crash/restart;
- IDs never reused after deletion;
- Clay-aware copy mints child ID before child Pulse;
- unmanaged byte copy is detected at startup;
- copied body cannot run under parent ID;
- parent/child state isolation and divergent Pulse histories;
- sibling isolation;
- same-lineage restore vs copy discriminator;
- registry rebuild from birth ledger;
- filename rename does not change identity;
- identity manifest corruption fails closed;
- offline mint reconciliation/collision handling;
- child knows parent/source provenance;
- body metadata changes do not silently rewrite identity.
