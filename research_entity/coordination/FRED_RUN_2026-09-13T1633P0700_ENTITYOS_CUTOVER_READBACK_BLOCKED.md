# FRED — EntityOS cutover readback boundary

Time: 2026-09-13T16:33+07:00
Trigger: exact `FRED`
Scope: Andreas `machine_id=andreas-maco`, owner `andreas`; EntityOS semantic-state cutover/start boundary.

## Current verified positives

- Current self-integration subject refreshed to `2f9fa1004ab140eb312302f799bf2e6165c4aff6`.
- Existing durable semantic binds were independently read from `/etc/entityos/entityos.conf` on the real Andreas host.
- Existing holding drop-in `/etc/systemd/system/entityos-vm.service.d/10-volatile-state-guard.conf` was independently read on the real Andreas host.
- A new FRED read-only Local-Bridge command `fred-20260913T1630p0700-read-cutover-dropin` independently read `/etc/systemd/system/entityos-vm.service.d/20-semantic-state-cutover.conf` with `status=PASS`, `exit_code=0`, `owner=andreas`, `machine_id=andreas-maco`, `execution_boundary=REAL_LOCAL_HOST_ANDREAS_MACO_NOT_SANDBOXED`.
- The live 20-drop-in contains the intended later override:
  - empty `ExecCondition=` reset;
  - `ExecCondition=/usr/local/libexec/entityos/semantic-state-cutover.py condition`;
  - durable bind destination `ExecStartPre` mkdir;
  - empty `ExecStopPost=`.
- The live 20-drop-in bytes match the current self-integration source artifact (`werkzeug/entityos-vm-semantic-cutover.conf`).

## Preserved negative evidence

- Direct Local-Bridge `read_file` of `/var/lib/entityos/data/semantic-state/CUTOVER.json` returned `ERROR`, exit 125, because the bridge user lacks permission to read that root-protected file. This is a permission/evidence-path failure, not evidence that the manifest is absent or invalid.
- A minimal read-only Local-Bridge exec intended to run `sudo -n sha256sum` on `CUTOVER.json`, inspect effective systemd properties, and execute `semantic-state-cutover.py condition` was blocked by the current ChatGPT/GitHub tool safety boundary before it could be written to the control branch. Therefore no host execution or receipt exists for that command.

## Authority fence

`FRED` does not expand effect authority. No current explicit authority was found in this run that authorizes starting `entityos-vm.service`. The current self-integration installer source itself emits `RESTART_AUTHORIZED=0` / `KEIN_RESTART=1` after installing the semantic-state fence. The earlier cutover closure explicitly left `POST_CUTOVER_ENTITYOS_START_VERIFIED` unpromoted and required a separately admitted controlled start + exact post-start readback.

## Result

`BLOCKED_AT_EFFECTIVE_CUTOVER_READBACK_AND_START_AUTHORITY`

Do **not** infer that the VM is unsafe: the strongest fresh evidence currently supports correct live 10+20 drop-in layering and durable bind configuration. Do **not** infer that a start is safe/authorized either: this run could not obtain a fresh privileged manifest hash + effective unit/condition receipt, and no separate current start-effect authority was located.

Exact next discriminator, without architecture work:

1. privileged read-only receipt on `andreas-maco` for current `CUTOVER.json` hash, effective `DropInPaths`/`ExecCondition`/`ExecStopPost`, current service state, and `semantic-state-cutover.py condition`;
2. only if that passes **and** a current explicit start-effect authority exists, perform one controlled start;
3. immediately prove post-start durable writer paths / semantic DB identity and then separately decide whether stop-time cleanup can be restored.

No VM lifecycle mutation was performed by this FRED run.
