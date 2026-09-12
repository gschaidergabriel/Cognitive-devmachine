# GO — exact-current-daemons shared HostEffectFence shadow integration — 2026-09-12

Status: **ACCEPTED_AT_SCOPE / REAL_HOST EXACT-DAEMON-COPY SHADOW INTEGRATION / NO SERVICE OR LIVE MUTATION**

## Boundary

Goal: prove the two *currently installed* local bridge implementations can execute their real operation-dispatch paths behind one shared physical-host effect critical section without merging their separate Git control/result fabrics.

Exact observed daemon subjects:

- generic Clay bridge `/home/ai-core-node/.local/share/clay-local-bridge/bin/daemon.py`
  - SHA-256 `22d56fddd760bbda096e8cd58b8d826dbfbfd7df46155a62ef98f64d5ecdbacf`
- Frank machine-specific bridge `/home/ai-core-node/.claude/star/local_bridge_daemon.py`
  - SHA-256 `836173805c8919492c1d52540c50f8b97dfd5beb8d02196d5630dbce52da342f`

Shared adapter/fence candidate source:

- branch `chatgpt-gpt56sol-host-effect-adapter-candidate-20260912`
- tested head `a6634c351e6a76f1ec2dc5678996a2a58d2674af`

## Negative evidence preserved

First shadow run `go-host-effect-current-daemons-shadow-integration-gpt56sol-20260912` failed after both READ_ONLY paths and the generic live-operation path had already passed. Root cause was harness-only: redirected Frank `HOME` was selected as an implicit exec cwd but the scratch directory had not been created. The test also had a stale guessed journal filename (`host_effects.sqlite3` instead of canonical `host-effect.sqlite3`) that would have invalidated the later contention probe.

Classification: **EVIDENCE_INVALID / HARNESS_DEFECT**, not PRODUCT_NEGATIVE.

Repair commit `a6634c351e6a76f1ec2dc5678996a2a58d2674af`:

- creates redirected scratch HOME before importing/executing daemon copies;
- resolves the contention probe against the canonical `host-effect.sqlite3` path.

## Corrected real-host result

Command: `go-host-effect-current-daemons-shadow-integration-v2-gpt56sol-20260912`

Receipt scope: `EXACT_CURRENT_DAEMON_COPIES_REAL_OPERATE_PATHS_SHARED_FENCE_SCRATCH_ONLY_NO_SERVICE_OR_LIVE_MUTATION`

Execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`

PASS markers:

- `GENERIC_REAL_OPERATE_READONLY_ADAPTER_PASS`
- `FRANK_REAL_OPERATE_READONLY_ADAPTER_PASS`
- `GENERIC_REAL_OPERATE_LIVE_VERIFIED_PASS`
- `FRANK_REAL_OPERATE_LIVE_VERIFIED_PASS`
- `CURRENT_GENERIC_VS_FRANK_SHARED_LEASE_EXCLUSION_PASS`
- `CURRENT_FRANK_AFTER_GENERIC_VERIFICATION_PASS`
- `EXACT_CURRENT_DAEMONS_SHARED_FENCE_SHADOW_INTEGRATION_PASS`
- `CURRENT_DAEMONS_SHARED_FENCE_SHADOW_GATE_V2=PASS`

The cross-daemon discriminator waited until the generic daemon's journal row was actually `RUNNING`, then attempted Frank's real `operate(exec)` path against the same fence. Frank received the shared lease exclusion and its body did not execute. After the generic effect completed and independent scratch-file readback promoted it to `VERIFIED_SUCCEEDED`, Frank's real operation path was admitted and independently verified.

## Exact promotion

Promoted:

- HostEffectFence real-host scratch runtime evidence;
- bridge-effect adapter real-host scratch runtime evidence;
- compatibility of the **exact current installed daemon source subjects** with the shared fence contract in an executable shadow integration;
- cross-daemon mutual exclusion and post-readback continuation using the real operation-dispatch functions.

Still zero / not established:

- either installed daemon actually imports/calls the shared fence in production;
- systemd/service restart/recovery with the fence enabled;
- canonical shared state-root deployment/permissions for both services;
- production command admission migration for legacy effect-bearing commands;
- a real avatar live mutation serialized between both daemons;
- irreversible/system-effect authority;
- whole-product/effect-loop completion;
- HCU/GWT/J-Space/training credit.

## Next exact gate

Implementation owner should now integrate the already-tested adapter/fence into both current daemon execution paths behind exact source-hash preconditions and a rollbackable service deployment. Acceptance must prove:

1. both services resolve the same canonical `CLAY_HOST_EFFECT_STATE_DIR`;
2. legacy intrinsically read-only commands remain non-journaled;
3. effect-bearing commands without explicit classification fail closed rather than silently bypass the fence;
4. service restart converts leftover PREPARED/RUNNING rows to UNKNOWN before admitting new live effects;
5. receipts preserve command identity plus machine/owner attribution;
6. one reversible live test mutation with independent readback is serialized across the two actual running services;
7. exact rollback restores both daemon subjects if any discriminator fails.

This packet is evidence/reconciliation only. It does not steal mutation authority from `chatgpt-work/local-bridge-single-writer-20260912`.