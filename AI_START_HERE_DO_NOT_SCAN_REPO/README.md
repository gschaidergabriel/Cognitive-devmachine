# AI START HERE — DO NOT SCAN THE REPO

Use this folder when an AI/tool needs to work with the project without first crawling the whole repository.

## Rule zero

Do **not** guess where the repository lives.

Do **not** assume:

- `~/Downloads`;
- the home directory;
- a clone path;
- an attachment mount;
- the current working directory;
- that a tool has hooks, durable memory, a terminal, GitHub write access or background execution.

Find the actual repository path or ask the host/tool for it through its native file/repository interface.

## Minimum read order

Read only these first:

1. `../CLAY_EXECUTION_AUTHORITY.md`
2. `../research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
3. the steering file named by that inbox
4. `../HUMAN_READ_THIS/README.md`
5. `../DEV_SOURCE_RESEARCH/README.md`
6. task-relevant exact source/evidence only

If a listed path moved, discover the current equivalent. Do not force an old filename to remain authoritative.

## Capability test

Before installation/integration, determine whether the host has these capabilities:

- `FILES_READ`
- `FILES_WRITE`
- `SHELL`
- `GIT_READ`
- `GIT_WRITE`
- `LIFECYCLE_HOOK`
- `DURABLE_STATE`
- `EFFECT_RECEIPT`
- `NETWORK` (only when current authority permits the exact route)

Unknown means unknown. A tool description is not proof that a hook really fires.

## Final result vocabulary

Every installation attempt ends in exactly one class:

- **NATIVE** — the host exposes the needed primitive directly and you verified it.
- **ADAPTED** — the host uses a different primitive, but the mapped behavior was verified.
- **DEGRADED** — useful subset works; missing capabilities are named.
- **BLOCKED** — a required capability is absent or cannot be verified.

Never report success just because files were copied.

## Common verification loop

```text
DETECT host + repo path
-> RESOLVE current authority
-> MAP host capabilities
-> INSTALL smallest adapter
-> TRIGGER one real lifecycle event if supported
-> VERIFY durable state changed where expected
-> VERIFY effect/result receipt where an effect occurred
-> RESTART/REOPEN if persistence is claimed
-> REPORT NATIVE / ADAPTED / DEGRADED / BLOCKED
```

## Claude Code

Use Claude Code's actual working repository/session primitives.

1. Confirm the repository root from Git, not from the shell prompt text alone.
2. Read the minimum read order above.
3. Detect existing project instructions such as `CLAUDE.md` only after current authority is resolved.
4. If lifecycle hooks are available, install an adapter that records a deterministic receipt when the hook fires.
5. Re-open or restart once if durable state is claimed.
6. Do not modify Frank's own Harness to work around provider authority; current supervisor explicitly forbids that closure path.

Target classification: `NATIVE` when repo/files/shell/Git and the required lifecycle receipt are directly observable; otherwise `ADAPTED` or `DEGRADED`.

## Codex CLI

1. Start from the actual checked-out repository.
2. Resolve current authority before code changes.
3. Detect shell/Git/write capability.
4. Use repository-native tests rather than inventing a host-specific state store.
5. If no lifecycle hook exists, do not fake one. Store explicit task/reentry receipts in an approved repository path only when the task requires persistence.

Target classification: usually `NATIVE` for source editing/testing if shell/Git are available; lifecycle automation may be `DEGRADED` if no hook exists.

## Hermes Agent

1. Detect its real file/shell/tool surfaces first.
2. Map each requested project capability to an actually exposed Hermes primitive.
3. Where a lifecycle feature differs, use an adapter only if its firing can be observed.
4. If durable state cannot be verified across a restart/reopen, mark `DEGRADED`.

Do not assume Hermes-specific plugin names or directories without host evidence.

## ChatGPT Web

1. Use connected GitHub/file tools when available; do not pretend the browser has a local shell.
2. Read current authority through the connected repository before current-state claims.
3. Repository writes must use the connected GitHub write surface when authorized.
4. A chat response is not a durable repository write.
5. A scheduled/background process does not exist unless an actual supported scheduling surface was invoked.

Typical classification: `ADAPTED` for repository research/edit workflows; local runtime hooks may be `BLOCKED` or `DEGRADED` depending on available connectors.

## Claude Web

1. Use its real project/connector/file surfaces only.
2. Do not assume Claude Code shell/hooks exist in Claude Web.
3. If GitHub is connected, resolve exact current files there; otherwise imported snapshots are caches.
4. Mark local runtime integration `BLOCKED` when no real execution surface exists.

## Grok Web

1. Detect repository/file/connectors before assuming access.
2. Treat pasted or uploaded repository archives as snapshots unless current Git state can be verified.
3. Do not invent shell or lifecycle-hook support.
4. Use `DEGRADED` when it can analyze sources but cannot verify durable writes/runtime effects.

## Generic fallback

For any other tool:

1. Find repository root.
2. Read current authority.
3. Make a capability table.
4. Map only supported primitives.
5. Install the smallest reversible adapter.
6. Fire one observable test event.
7. Check state/receipt.
8. Reopen/restart if persistence is claimed.
9. Report one final class.

## Authority warning for the current 2026-08-27 state

At the authority state inspected when this file was written, provider epoch 9.13 is HARD_OFF: all provider routes false, Together forbidden, no paid fallback. A recently authored 72-hour Frankenstein Bauleiter/Bugfixer orchestration that directly selects NVIDIA/Groq/Mistral and treats Together as available is quarantined and non-operative.

Do not use an installer/agent integration as a side door around that boundary.

## Source-only helper

`detect_install_mode.sh` in this folder performs only local, non-network capability hints. It does not prove lifecycle hooks, durable state, provider authority or whole installation PASS. Treat its output as discovery input, then run the verification loop above.