# Local bridge single-writer convergence — 2026-09-12

Status: **INTEGRATION_BLOCKER / NO SERVICE MUTATION YET**

## Observed executable evidence

Real-host forensics on `ai-core-node` observed two simultaneously active user services:

1. `clay-local-bridge.service`
   - `ExecStart=/usr/bin/python3 /home/ai-core-node/.local/share/clay-local-bridge/bin/daemon.py`
   - `Restart=always`
   - current observed MainPID: `2495`

2. `frankenstein-local-bridge.service`
   - `ExecStart=/usr/bin/python3 /home/ai-core-node/.claude/star/local_bridge_daemon.py`
   - `Restart=on-failure`
   - current observed MainPID: `959674`

The same forensics pass also observed a dirty `chatgpt-local-ai-core-node-results` checkout containing uncommitted command/result/log/receipt material while bridge work was active.

This is enough to establish **concurrent bridge-writer risk**. It is not enough to choose a winner by naming convention.

## Why this is a correctness boundary

Two independent daemons polling or mutating the same control/results fabric can produce:

- duplicate execution of one command;
- receipt overwrite or stale `LATEST.json` projection;
- one daemon committing the other daemon's files;
- divergent idempotence journals;
- command/result ordering that does not match execution ordering;
- Git push races and lost/duplicated receipts;
- false attribution of a local runtime result to the wrong worker/owner epoch.

For avatar promotion this is unacceptable: a post-write PASS must be bound to exactly one command identity, one execution owner and one result commit.

## Mandatory rule

`ONE machine_id + ONE control/results fabric -> AT MOST ONE ACTIVE WRITER AUTHORITY`

A second daemon may exist only as a **standby/read-only** process that cannot execute commands, mutate result state, or push result commits while another writer lease is live.

## Do not guess the canonical daemon

The observed service names are insufficient authority. Before stopping/disabling either service, compare both daemon implementations read-only and score them against the current bridge contract.

Required comparison dimensions:

1. exact file SHA-256 and size;
2. control branch/ref consumed;
3. results branch/ref mutated;
4. command identity = command_id + command content hash;
5. durable executed-command/idempotence journal;
6. behavior on same command id with different content hash;
7. atomic claim or lock before execution;
8. process-level single-writer lock/lease;
9. Git update method: fetch/rebase/CAS/fast-forward vs blind/force push;
10. dirty-worktree handling;
11. handling of a result branch moving concurrently;
12. crash window between effect execution and durable receipt;
13. cleanup policy for command files/logs/receipts;
14. secret/environment redaction;
15. retry semantics and duplicate-effect prevention;
16. machine/owner binding.

The comparison tool in this branch extracts static evidence without executing either daemon.

## Winner criteria

Prefer the daemon that satisfies, in order:

1. **effect idempotence** — cannot execute the same content-addressed command twice;
2. **single-writer safety** — explicit lease/lock or equivalent;
3. **receipt durability before acknowledgement**;
4. **Git concurrency safety** — no force push, no blind overwrite, fail/re-enter on moved head;
5. **separate bridge working state from live avatar/source trees**;
6. **exact machine/owner/command hash binding**;
7. **recoverability** after crash without replaying unknown effects;
8. current project portability and maintainability.

If neither satisfies the first four, do not choose between two unsafe writers. Converge one implementation first.

## Required transition

After winner selection:

1. snapshot both unit files and daemon SHAs;
2. snapshot active/enabled state;
3. drain in-flight commands;
4. prove no command is in UNKNOWN effect state;
5. stop the losing writer;
6. prevent automatic dual restart;
7. keep the loser available as rollback artifact / standby, not writer;
8. start/restart the selected writer alone;
9. prove exactly one writer process;
10. submit a no-op/read-only command with a unique content hash;
11. prove exactly one execution receipt and exactly one done-journal row;
12. submit the same exact command again and prove zero re-execution;
13. submit same command id with changed bytes and require fail-closed conflict;
14. prove result-branch checkout clean after commit/push;
15. only then reopen effect-bearing avatar/local-host dispatch.

## Runtime-credit fence

Until the single-writer discriminator closes:

- existing historical receipts remain evidence at their exact scope;
- new local results can be inspected but should not be used for irreversible/live promotion without independent duplicate-execution checks;
- canonical-eye live installation remains blocked;
- body/depth-warp source-ready or scratch-runtime work may continue read-only.

## Current bounded avatar consequences

Existing positive evidence is preserved:

- canonical eye serving route is byte-bound to the masked Relief2 asset;
- deterministic eye semantic-shadow build passes;
- isolated expression eye compositing passes;
- body WebGL AMD runtime/cadence evidence passes at bounded scope;
- body final-display signal sweep has a safe measurable scale candidate;
- depth-warp A=1.00 currently has the stronger mechanical envelope than A=1.25.

None of those facts licenses ignoring a bridge-writer race at the final live-effect boundary.
