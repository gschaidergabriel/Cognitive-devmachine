# OMEGA bounded runtime credit — ai-core-node — 2026-09-13

Status: **PASS — bounded Gabriel Voice/OMNI runtime activation credit**

This record does not mint whole-product, Andreas-VM, GRID/GWT/HCU/J-Space, training, provider, or effect-authority credit.

## Exact subject

- owner: `gabriel`
- machine_id: `ai-core-node`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`
- final Frankenstein source head installed: `065e03acca024ab03d6eb2cd036f931fc8dc11be`
- final product tree: `/home/ai-core-node/.local/lib/frankenstein-voice-final`

## Evidence chain

1. Stale `95/99-omega-777-organ-floor.conf` Voice overrides were disabled without restarting the process. Receipt `omega-disable-stale-voice-overrides-20260913-0055-gpt56sol` PASS proved the effective future Voice ExecStart points to `voice_final_runtime.py` while PID and ActiveEnterTimestamp were unchanged.
2. The exact final OMEGA assembly from Frankenstein head `065e03a...` was composed into the already-bound final Voice tree. `voice_final_runtime.py` policy bytes remained unchanged; OMEGA source selftest passed. This stage deliberately carried source-composition credit only.
3. Receipt `omega-runtime-activate-ai-core-node-20260913T0053-gpt56sol` PASS performed the separately admitted controlled lifecycle activation and exact readback.
4. Post-activation runtime subjects:
   - Voice PID `2667903`: `python3 /home/ai-core-node/.local/lib/frankenstein-voice-final/scripts/voice_final_runtime.py`
   - OMNI client PID `2667899`: `python3 /home/ai-core-node/.local/lib/frankenstein-voice-final/scripts/voice_host_777_live_client.py`
   - both `ActiveState=active`, `SubState=running`, `Result=success`, `ExecMainStatus=0`, `NRestarts=0`
   - runtime epoch / ActiveEnterTimestamp: `Sun 2026-09-13 00:53:41 +07`
5. Independent follow-up receipt `omega-runtime-quiescence-preflight-ai-core-node-20260913T0054p07` PASS re-read both exact processes as still active/running from the final product tree.

## Credit decision

`OMEGA_GABRIEL_VOICE_OMNI_RUNTIME_CREDIT = PASS`

Reason: exact source -> exact installed final tree -> controlled new runtime epoch -> exact process cmdline/systemd binding -> independent post-activation readback.

The `omega selftest` field `runtime_credit=false` remains correct for that command's narrower source-composition scope; runtime credit here is awarded from host-bound lifecycle receipts, not from model/self-report.

## Still open / explicitly not promoted

- Andreas `entityos-vm.service` durable semantic-state cutover/restart credit remains open until the disposable-rootfs SQLite stores are durably staged, exact binds/manifest verified, and a separately admitted lifecycle readback succeeds.
- No whole OMEGA/EntityOS completion claim is made by this bounded credit record.
