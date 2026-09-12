# FRED — Andreas semantic-state cutover closure

Date: 2026-09-13 +07
Trigger: `FRED`
Scope: reality-bound continuation after `FRED_RUN_2026-09-13T0231P07.md`.

## Superseding runtime evidence

The earlier FRED report correctly preserved `VOLATILE_STATE_MIGRATED=0` at its observation boundary. Later real-host receipts on `machine_id=andreas-maco`, `owner=andreas` advanced that boundary and therefore supersede that part of the earlier snapshot.

### Controlled rescue + stop

Receipt: `fred-20260913T0250p0700-andreas-controlled-stop`

- pre-stop EntityOS subject: active, MainPID `319869`, ActiveEnterTimestamp `Tue 2026-09-08 12:04:36 CEST`;
- exact rescue manifest: `/var/lib/entityos/data/volatile-state-rescue/fred-20260913T0246p0700/MANIFEST.json`;
- six semantic SQLite subjects were preserved before stop:
  - `agentzero/consciousness.db` — 483328 bytes
  - `agentzero/unified.db` — 24576 bytes
  - `agentzero/welt.db` — 536576 bytes
  - `frank/db/amygdala.db` — 36864 bytes
  - `frank/db/world_experience.db` — 327680 bytes at rescue observation
  - `frank/db/world_experience.db.vor-maerz-20260910` — 4096 bytes
- post-stop: EntityOS inactive; rootfs preservation asserted by the receipt; no restart performed.

### Durable cutover

Receipt: `fred-20260913T0255p0700-andreas-stage-transition-fix`

The command was host/user bound and required the productive `self-integration` checkout to equal:

`2f9fa1004ab140eb312302f799bf2e6165c4aff6`

Verified result:

- temporary staging holding drop-in was installed only for the stage boundary and then removed;
- `/usr/local/libexec/entityos/semantic-state-cutover.py stage --execute` completed;
- `/usr/local/libexec/entityos/semantic-state-cutover.py verify` completed;
- durable manifest exists at `/var/lib/entityos/data/semantic-state/CUTOVER.json`;
- manifest SHA-256: `fe7cd20eb0574799d84ac4dd15d089948490fd1fb113a1cbec5aafefd950c916`;
- durable destinations contain all six semantic DB subjects;
- `ENTITYOS_IDENTITY_BINDS` now includes:
  - `--bind=/var/lib/entityos/data/semantic-state/agentzero:/root/.local/share/agentzero`
  - `--bind=/var/lib/entityos/data/semantic-state/frank:/root/.local/share/frank`
- final effective ExecCondition is `semantic-state-cutover.py condition`;
- final condition result: `START FREI -- durable_cutover_verified`;
- post-stage state remained inactive and the receipt explicitly recorded `NO_START=1`.

## Scope discipline

Promoted at this boundary:

- `VOLATILE_STATE_RESCUED=1`
- `DURABLE_SEMANTIC_CUTOVER_STAGED=1`
- `CUTOVER_MANIFEST_VERIFIED=1`
- `DURABLE_WRITER_BIND_CONFIGURATION_PRESENT=1`
- `CUTOVER_START_CONDITION_PASS=1`

Not promoted from these receipts alone:

- `POST_CUTOVER_ENTITYOS_START_VERIFIED=0`
- `POST_CUTOVER_RUNTIME_EPOCH_VERIFIED=0`
- `POST_CUTOVER_WRITER_READBACK_VERIFIED=0`
- whole GRID/GWT/HCU/J-Space/training credit remains unchanged.

## Independent adjacent evidence

Gabriel's canonical OMEGA source-to-GRID-to-UnifiedDB path was separately production-admitted on `ai-core-node`, including the DB-side legacy-writer guard and independent readback. This does not collapse Gabriel and Andreas host/DB identities.

A cross-host GRID-envelope scratch command on Andreas failed before product execution because HTTPS Git clone could not obtain credentials. Classify as host/tooling infrastructure failure, not GRID/source-envelope negative evidence.

## Current frontier

The semantic data-loss boundary that previously forbade EntityOS lifecycle work is closed at the durable cutover/condition scope. The next lifecycle-bearing gate is a separately admitted controlled **start** (not blind restart), followed immediately by exact readback of runtime epoch, mounted durable semantic paths, DB integrity/hash/row evidence and writer-path behavior. FRED itself does not expand effect authority; no start credit is claimed here.
