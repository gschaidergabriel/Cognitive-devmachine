# ATOMIC REAL-RESULT REPORT — Telemetry Schema Authority / Migration Repair

Run: `20260810T2203p0700-chatgpt-secondary-real-schema-authority`  
Target: `self.root` / Frank v0.1  
Research Entity: Clay  
Disposition: **REAL TARGET REPAIR / PARTIALLY TARGET-VERIFIED / LIVE DEPLOYMENT BLOCKED**  
Architecture promotion: **none beyond the direct repair**  
Paid/final training: **not started**

## 1. Real problem selected

The then-current accepted-target deep-integrity receipt had one failing gate out of 23: `repo_static_integrity`.

The failure was not treated as a cosmetic test problem. Inspection of every flagged `executescript()` caller separated two materially different classes:

1. six bounded research/target probes that create disposable `:memory:` or TemporaryDirectory SQLite fixtures, with any live telemetry access read-only;
2. production `runtime/clay_vps_mcp_v02/clay_vps_mcp/telemetry.py`, which opened `/srv/frank-telemetry/frank_telemetry.sqlite3` and directly executed an embedded schema.

The second class was a real duplicate production schema-authority surface outside an explicit migrator.

## 2. Direct target-code repair

The target repository was changed, not merely the research repository.

- Dedicated telemetry schema authority moved into `telemetry_schema_migrator.py`.
- `TelemetryStore` no longer embeds or executes DDL directly.
- The repository static gate now distinguishes explicit production migrators from exactly enumerated disposable probe fixtures and continues to reject writable canonical DB references in those probes.
- The first migrator version was then falsified conceptually: `CREATE TABLE IF NOT EXISTS` is not an in-place migration for an existing table.
- The migrator was extended to admit only a known compatible base schema, add the eight TemporalEntityV2 columns additively, create required indexes/FTS/triggers, rebuild external-content FTS when introduced over existing rows, and fail closed on unknown older schemas.
- A second falsifier found a transaction-boundary problem: Python `sqlite3.executescript()` can commit a pending transaction before the script. The migration was therefore changed to require a clean caller transaction boundary and perform its DDL under explicit `BEGIN IMMEDIATE ... COMMIT`, with rollback on failure.

Current migration invariants include:

- one explicit production schema-authority module;
- no direct DDL authority in `TelemetryStore`;
- compatible additive migration only;
- no destructive guessed rewrite for unknown legacy layouts;
- legacy row preservation;
- FTS rebuild for pre-existing content;
- clean caller transaction boundary;
- one transaction for schema migration;
- failure must leave no partially added TemporalEntityV2 columns.

## 3. Real accepted-target VPS evidence

Durable receipt: target repository commit `f3ee4fdff836ec869dfd0160ce6d66c18c840a24`, GitHub Actions run `31403551674`, tested SHA `8fe4109ce4b4404eee354dfd07e2dd8c262abfd7`, artifact digest `3be83064229efbd7fda489fad7b947c4a6e71478b78cb78dadebddc6f917f037`.

Execution environment:

- self-hosted accepted target lane `clay@digital-retina`;
- Linux 6.8.0-117-generic x86_64;
- Python 3.12.3;
- SQLite 3.45.1;
- executor repository permission `contents:read`;
- checkout credentials absent from executor;
- no repository write attempted by executor;
- live telemetry access declared/read as read-only;
- no external network used by the discriminator.

Observed results on that target:

- `repo_static_integrity = PASS`;
- fresh disposable telemetry creation/insert/FTS/integrity = PASS;
- compatible legacy in-place migration = PASS;
- legacy row count before/after = 1/1;
- legacy row searchable through rebuilt FTS = PASS;
- `quick_check = ok` and `integrity_check = ok`;
- unsupported legacy schema = correctly rejected with original row preserved;
- production store direct schema authority = absent.

This is a real closure of the specific previous `repo_static_integrity` failure for the tested SHA.

## 4. Real negative result: target live telemetry is absent

The same receipt intentionally remained FAIL overall because:

`/srv/frank-telemetry/frank_telemetry.sqlite3 -> LIVE_DB_NOT_FOUND`

This is not converted into a PASS. The code/migration surface is target-executable; the live deployed telemetry subsystem is not currently present at the canonical location.

## 5. Real deployment blocker

A real MCP v0.2 deployment workflow on `clay@digital-retina` failed before install. Job log for run `31402114519`, job `93499375007` showed:

`sudo -n true -> sudo: a password is required`

Consequences in the persisted deployment receipt:

- install skipped;
- postdeploy skipped;
- backup probe skipped;
- no accepted release;
- `clay-vps-mcp.service` inactive;
- `frank-telemetry.service` inactive;
- `unifieddb-backup.timer` inactive.

This is classified as a host privilege-admission blocker, not a Frank code pass/fail.

## 6. Deployment evidence pipeline repaired

The deployment workflow itself previously performed `sudo -n true` before even running its unprivileged package/compile/test preflight. That erased useful target-code evidence whenever host privilege was unavailable.

Commit `e198bc9cb114b880cc96ddfa9e4adbd331b8251f` changes the ordering:

1. bind source bytes, now including the telemetry schema migrator blob;
2. create target-local venv;
3. install package and pytest without root;
4. compile package plus migration regression source;
5. run package tests plus telemetry schema-authority tests;
6. only then test noninteractive sudo as a separate admission step;
7. system install only if privilege admission succeeds;
8. receipt separately records unprivileged preflight and privilege admission.

Thus missing root privilege can no longer hide whether the package itself builds/tests on the target VPS.

## 7. Stronger atomic migration delta after first target receipt

After the first target receipt, the migration mechanism was strengthened further:

- `3b39e4f9929a0be763b7e7ec71782c48d146e878`: explicit transaction-atomic migration and clean caller-transaction gate;
- `e10f24897e97c189baa5fa4e8a608bbf1bbecb35`: forced later-DDL collision regression plus pending-transaction regression;
- `7f50bbd8195dc335e1ca9d6cfc84122a379bd5f7`: target-VPS discriminator extended with the same atomic rollback checks;
- `9bbb4bd8452540d379384a5d3b69abf870ae03ed`: static audit rebound to the stronger atomic-migration invariants.

A separate executable SQLite reproduction observed:

- fresh schema integrity `ok`;
- all eight TemporalEntityV2 columns added to compatible legacy schema;
- legacy row preserved;
- legacy FTS row rebuilt and searchable;
- forced later DDL collision raised `OperationalError` and left zero TemporalEntityV2 columns behind;
- pre/post column sets matched after failed migration;
- legacy row survived the forced failure;
- pending application transaction was rejected;
- caller rollback removed the uncommitted row, proving migration did not implicitly commit it.

These stronger current-head deltas still require their own current-source accepted-target VPS receipt before they receive target promotion.

## 8. Scientific/engineering result

This run did not produce another speculative cognitive module. It converted one real failing target integrity gate into a target-VPS PASS on the tested source, found a real duplicated production schema authority, found and repaired a hidden fresh-create-versus-migration bug, found and repaired a partial-migration transaction boundary, and isolated the remaining live blocker to host deployment/privilege rather than continuing to conflate source correctness with installed-system state.

The measured frontier is therefore sharper:

`SOURCE SCHEMA AUTHORITY / COMPATIBLE MIGRATION = TARGET-PROXY PASS on tested SHA`

`CURRENT TRANSACTION-ATOMIC MIGRATION = IMPLEMENTED + EXECUTABLE LOCAL DISCRIMINATOR, target-current receipt pending`

`LIVE /srv TELEMETRY = NOT PRESENT`

`SYSTEM DEPLOYMENT = BLOCKED BY NONINTERACTIVE SUDO ADMISSION`

`MCP V0.2 ACCEPTED RELEASE = NO`

`WHOLE FRANK V0.1 ACCEPTANCE = NO`

## 9. Highest-information next action

The next useful action is not more architecture ideation. It is to obtain/observe the current-source target receipts from the strengthened schema-authority gate and reordered deployment preflight. If unprivileged preflight passes while sudo admission fails, source/runtime readiness and host provisioning become cleanly separated. Full system deployment then requires an owner-approved narrowly scoped privilege/provisioning path; it must not be bypassed by weakening host security.
