# 666 Level-0 run — Digital Retina scoped node_modules roots

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Provider/model: OpenAI / GPT-5.6 Sol
- Program stage: `L0_ARCHIVE_ASSIMILATION`
- Run start: 2026-08-09 10:20 +07:00

## Coordination / collision handling

1. Fresh Center head showed active work on Digital Retina `.git`, PF blob shard B, Zod v4, AICORE and other lanes.
2. `zod/src` looked free at first read, but the CAS claim returned HTTP 409 because another worker changed the task between read and write. Fresh reread showed `zod/src` was already `CLAIMED`; this worker did not overwrite or double-credit it.
3. Work pivoted to isolated unclaimed `@scope` roots under `digital-retina/frontend/node_modules` using one-root task files so the remaining scope roots stayed parallelizable.
4. A transient GitHub branch-head 409 occurred while creating the `@nolyfill` task during heavy parallel commits; fresh commit scan showed no `@nolyfill` claim, so the create was safely retried on the new head.

## Root closures completed by this run

### `@alloc`
- Drive root: `1ajLXb0tjVPHeV-Hkkqr-E6PL_AkqTjhC`
- Package: `quick-lru`
- Recursive denominator: 1 descendant folder + 5 files = 6 units
- Bytes: 14,099
- Lock authority: `node_modules/@alloc/quick-lru` v5.2.0
- Receipt: `research_entity/archive_assimilation/receipts/666_20260809T1021p0700_digital_retina_node_modules_scope_alloc_closure.json`
- Semantic / earned-work credit: 0 / 0 (vendor support)

### `@tybys`
- Drive root: `1KWoymHuNaUZAaKmonCmgi_C9oHP-piaR`
- Package: `wasm-util`
- Traversed: `wasm-util`, `dist`, `lib`, `lib/mjs`, `lib/cjs`, `lib/mjs/wasi`, `lib/cjs/wasi`
- Recursive denominator: 7 descendant folders + 39 files = 46 units
- Bytes: 812,994
- Lock authority: `node_modules/@tybys/wasm-util` v0.10.2
- Receipt: `research_entity/archive_assimilation/receipts/666_20260809T1024p0700_digital_retina_node_modules_scope_tybys_closure.json`
- Semantic / earned-work credit: 0 / 0

### `@nolyfill`
- Drive root: `1Wj--qibdnW_Dpz-y_rbL8wN4vp20_RKN`
- Package: `is-core-module`
- Recursive denominator: 1 descendant folder + 4 files = 5 units
- Bytes: 2,706
- Lock authority: `node_modules/@nolyfill/is-core-module` v1.0.39
- Receipt: `research_entity/archive_assimilation/receipts/666_20260809T1026p0700_digital_retina_node_modules_scope_nolyfill_closure.json`
- Semantic / earned-work credit: 0 / 0

### `@rtsao`
- Drive root: `13s3Sn_hS-J2NC9TrXKPQh2cp-cmayZcz`
- Package: `scc`
- Recursive denominator: 1 descendant folder + 6 files = 7 units
- Bytes: 3,611
- Lock authority: `node_modules/@rtsao/scc` v1.1.0
- Receipt: `research_entity/archive_assimilation/receipts/666_20260809T1028p0700_digital_retina_node_modules_scope_rtsao_closure.json`
- Semantic / earned-work credit: 0 / 0

## Run delta

New exact physical denominator closed by this worker in this pulse:
- descendant folders: 10
- files: 54
- physical units: 64
- bytes: 833,410
- lock reconciliations: 4/4 matched
- missing child IDs: 0
- authored-source exceptions: 0
- semantic credit added: 0
- earned-work credit added: 0
- global Level-0 exact percentage added: 0

## Shared scoped parent state after CAS

`research_entity/rooms/rooms/center/tasks/666-l0-digital-retina-node-modules-scope-20260809T0258Z.json`

- expected direct scope roots: 26
- CAS-integrated recursively closed roots: 6
- remaining roots in parent record: 20
- integrated descendant folders: 19
- integrated files: 126
- integrated physical units: 145
- closed roots currently recorded: `@drizzle-team`, `@next`, `@alloc`, `@tybys`, `@nolyfill`, `@rtsao`
- peer `@humanwhocodes` closure exists in Center commits but is intentionally not counted in this parent record until its receipt is CAS-merged by the responsible worker/coordinator.

## Gate law

These closures reduce the Digital Retina support denominator, but they do not change the global Level-0 strict percentage while the combined denominator is still unfrozen. No local completion is promoted to global PASS.
