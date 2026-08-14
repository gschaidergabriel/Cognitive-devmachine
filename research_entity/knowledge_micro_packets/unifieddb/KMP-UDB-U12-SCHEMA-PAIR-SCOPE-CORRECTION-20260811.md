# KMP-UDB-U12-SCHEMA-PAIR-SCOPE-CORRECTION-20260811

packet_id: `KMP-UDB-U12-SCHEMA-PAIR-SCOPE-CORRECTION-20260811`
domains: `unifieddb, claygraph, recovery, identity, harness`
epistemic_class: `STATIC_IMPLEMENTATION_FALSIFICATION_PLUS_TARGET_DIAGNOSTIC_PENDING`
status_hint: `OPEN_CORRECTION`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Correction

The current U12 `MaterializationPairCertificate` proves **schema/migration-pair compatibility and migration lifecycle state**, not arbitrary dynamic payload freshness of both SQLite files.

It binds:

- exact executable ordered UnifiedDB schema chain;
- exact executable ordered ClayGraph schema chain;
- role;
- shared schema-pair digest;
- lifecycle `UPDATING` / `CURRENT`.

It does **not** bind every later semantic-state transaction or every later ClayGraph projection update into the shared pair digest.

Therefore the stronger statement in `KMP-UDB-END-TO-END-CONTINUITY-SPINE-20260811` that an arbitrary one-file restore is necessarily rejected by the pair certificate is too broad.

## Static counterexample

Consider a valid certified pair at schema pair `P`.

1. ClayGraph changes dynamic payload/projection state from `G1` to `G2` without any schema migration.
2. Its certificate fields remain `P/CURRENT`, because U12 does not re-certify every graph data transaction.
3. Restore a backup containing `G1` that was taken after the same `P` certificate existed.
4. UnifiedDB still carries `P/CURRENT`; restored ClayGraph also carries `P/CURRENT`.
5. The current U12 equality checks can therefore accept the pair even though Graph payload has moved backward.

This is a scope limitation, not evidence that schema-pair admission is useless.

## Correct ring separation

### R1A — physical storage safety

SQLite build/journal/checkpoint topology is admissible.

### R1B — schema/migration pair admission

U12 proves both files use the exact admitted executable schema pair and are not left in an interrupted schema migration/certification state.

### R1C — derived Graph projection freshness

ClayGraph must separately prove that `graph_materialization_state.source_semantic_epoch`, graph epoch, derivation receipt/hash and status are compatible with the currently admitted UnifiedDB semantic state. Stale Graph should normally be quarantined/rebuilt or bypassed in favor of canonical retrieval; it must not mint truth.

### R2+ — authoritative semantic rollback continuity

A UnifiedDB content rollback is not solved by Graph projection checks. It requires selected semantic lineage/head plus rollback-domain-independent recovery authority/floor as already identified by the parent run.

Thus:

`schema_pair_current != graph_payload_current != semantic_lineage_current`

and none may substitute for another.

## Target diagnostic added to fused PR

Repository: `gschaidergabriel/Dr.-Unterweger`

Active fused draft PR: `#286`

Head after diagnostic addition: `a24d5dcd65042a1eccfc0fc9da1b7206fdb525b4`

`tests/unifieddb_u12_materialization_pair_gate.py` now includes:

1. disposable re-migration/bootstrap sentinel preservation;
2. injected failure after Graph DDL but before Unified DDL — normal pair open must reject and recovery must preserve sentinels;
3. injected failure after Graph certificate becomes CURRENT but before Unified certificate becomes CURRENT — normal pair open must reject and recovery must preserve sentinels;
4. same-certificate Graph payload rollback diagnostic: create Graph epoch A, snapshot, advance to epoch B without schema change, restore snapshot A, then observe whether schema-pair gate accepts while physical integrity remains clean.

The fourth case is diagnostic and does not make the test fail merely because the current schema-pair gate accepts. If accepted, it is recorded as the expected current scope limit and must route to Graph projection-freshness/rebuild logic rather than be misreported as a U12 pass for payload rollback safety.

## Fault-matrix correction

Replace the broad row:

`restore one physical DB only -> pair certificate REJECT`

with discriminated cases:

- restore a DB from a **different schema-pair certification/migration state** -> R1B REJECT;
- restore ClayGraph payload from an older point under the **same schema-pair certificate** -> R1B alone may ACCEPT; R1C must detect stale projection or rebuild/quarantine;
- restore UnifiedDB semantic payload backward under the same schema-pair certificate -> R1B alone may ACCEPT; selected-head/external recovery authority must reject or enter recovery;
- restore both databases together to an older same-pair state -> schema-pair check may ACCEPT; external recovery authority remains necessary.

## Promotion consequence

PR #286 can still be a valid R1B mechanism candidate, but no target PASS for #286 may be promoted into claims of dynamic Graph freshness, semantic rollback detection, whole continuity closure or Frank v0.1 acceptance.

F-V01-04 remains open until composed evidence proves the distinct layers and their recovery paths.

No canonical migration, merge authorization, Frank/self.root Harness mutation authority, external effect or final training authorization follows from this correction.
