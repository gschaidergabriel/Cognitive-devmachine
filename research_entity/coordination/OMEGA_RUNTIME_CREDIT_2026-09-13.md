# OMEGA runtime credit — ai-core-node — 2026-09-13

Status: **PASS — real host runtime credit for the final OMEGA Voice/OMNI assembly**

Scope: `machine_id=ai-core-node`, `owner=gabriel`. This does not imply runtime credit for `andreas-maco`, EntityOS VM lifecycle, training, J-Space, or any unrelated subsystem.

## Canonical source

- `gschaidergabriel/frankenstein` source commit used for the successful final-tree install: `88847cb17157e0d6392110cc5cb12a7f80e7857e`
- That commit repairs the OMEGA installer gate to compare the stable `voice_final_runtime.py` subject path across `systemctl --user daemon-reload`, rather than comparing volatile `ExecStart` metadata (`start_time`, `pid`, `code`, `status`).
- Bound product tree: `/home/ai-core-node/.local/lib/frankenstein-voice-final`
- Final policy: `/home/ai-core-node/.local/lib/frankenstein-voice-final/scripts/voice_final_runtime.py`
- Final policy SHA-256: `56e47d00b23a63ab832dfa08bf12df3e9e5233f9f3a758e160ff3f875b5b43ee`

## Closed seam

Two stale Voice drop-ins (`95-omega-777-organ-floor.conf`, `99-omega-777-organ-floor.conf`) had been overriding the already-existing `95-voice-live-final.conf`, so the productive service resolved to the compatibility `voice_777_runtime.py` instead of the final policy overlay. They were reversibly moved out of the `.conf` namespace and `daemon-reload` was verified to change only the effective configured subject, not the running PID/epoch.

Receipt: `omega-disable-stale-voice-overrides-20260913-0055-gpt56sol`

Result: configured Voice subject became exactly:

`/home/ai-core-node/.local/lib/frankenstein-voice-final/scripts/voice_final_runtime.py`

with the pre-existing running PID and `ActiveEnterTimestamp` unchanged during the configuration-only cutover.

## Final-tree installation

Receipt: `omega-install-final-tree-88847cb-20260913-0100-gpt56sol`

Result:

- exact source head `88847cb17157e0d6392110cc5cb12a7f80e7857e`
- installer PASS / exit 0
- OMEGA source-composition selftest PASS
- canonical launcher installed at `~/.local/bin/omega`
- final Voice policy bytes preserved exactly
- Voice configured to final policy tree
- ChatGPT/OMNI client configured to final tree
- no service restart occurred during installation

## Runtime activation credit

Receipt: `omega-runtime-credit-activate-20260913-0102-gpt56sol`

A new host-safe lifecycle boundary was then executed for only the two user services; **no EntityOS VM restart occurred**.

Post-activation exact subjects:

- Voice PID `2720334`, start `2026-09-13 00:57:55 +07`, active
  - process args: `python3 /home/ai-core-node/.local/lib/frankenstein-voice-final/scripts/voice_final_runtime.py`
- ChatGPT/OMNI client PID `2719881`, start `2026-09-13 00:57:52 +07`, active
  - process args: `python3 /home/ai-core-node/.local/lib/frankenstein-voice-final/scripts/voice_host_777_live_client.py`

The post-activation `omega selftest` remained PASS and `omega status` reported SELF=`OMEGA`, body/runtime=`FranKenstein 2.0`, installed `stern.py`, identity, GRID, TITAN, arm bus, presentation floor, terminal, Voice compatibility organ and OMNI client organ.

## Stability readback

Receipt: `omega-runtime-credit-stability-20260913-0104-gpt56sol`

After an additional delayed readback, the same Voice and client PIDs remained active with the same final-tree process arguments.

Result marker: `OMEGA_RUNTIME_STABLE_PASS`.

## Credit statement

For the exact scope above, **OMEGA final Voice + persistent ChatGPT/OMNI client runtime credit on `ai-core-node` is promoted from source-only to real-host runtime PASS**.

The `omega selftest` field `runtime_credit=false` remains intentionally source-scope-only and is not rewritten to self-award runtime credit. Runtime credit is granted externally by the machine-bound Local Bridge receipts and exact process readback documented here.
