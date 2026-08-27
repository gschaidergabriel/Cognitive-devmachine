# AI: START HERE. DO NOT SCAN THE REPO.

Use this folder first.

## Rule 1

Do **not** read the whole repository.

Read only:

1. `CLAY_EXECUTION_AUTHORITY.md`
2. `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
3. `research_entity/rooms/PROGRAM_STATE.json`
4. `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
5. `DEV_SOURCE_RESEARCH/README.md`
6. files needed for the exact task

If these files disagree, newer owner/current supervisor authority wins. Do not average them.

## Rule 2

Find the repo. Do not guess Downloads, Home, Desktop, clone path, attachment path, or current directory.

Run:

```bash
python3 AI_START_HERE_DO_NOT_SCAN_REPO/detect_host_capabilities.py --start "$PWD"
```

If you are not inside the repo, point `--start` at the file/directory you were actually given. The detector walks upward for repository markers. It does not use the network. It does not read provider keys.

## Rule 3

A capability snapshot is not an install success.

Final installation status must be one of:

- `NATIVE` — host can use the project directly with verified lifecycle/state/effect hooks.
- `ADAPTED` — host can use it through a documented adapter and the adapter is verified.
- `DEGRADED` — useful read/reason/edit path exists, but lifecycle or durable hooks are missing.
- `BLOCKED` — required file/tool/state access is not available.

Until hook firing, durable state write and effect/result receipt are actually tested, say `UNVERIFIED` or `DEGRADED`. Never fake `NATIVE`.

## Host routes

### Claude Code

Candidate `NATIVE` route when the `claude` CLI, Git worktree, write access and required lifecycle/state hooks are really present. Read authority first. Verify one real hook event and one durable state write before saying NATIVE.

### Codex CLI

Candidate `NATIVE` route when the `codex` CLI, Git worktree, write access and required lifecycle/state hooks are present. Read authority first. Verify hook + durable write + result receipt.

### Hermes Agent

Default candidate is `ADAPTED`, not NATIVE. If a `hermes` command is present, map its available lifecycle/tool/state callbacks to the project contract, then verify them. If Hermes has no durable callback path, stay DEGRADED/BLOCKED.

### ChatGPT Web

Default `DEGRADED`. A web chat does not automatically have the local filesystem or lifecycle hooks. If the session has a connected GitHub/file tool, use it to read the six files above; do not infer local execution. Only upgrade the status if the connected surface actually supports and verifies the required operations.

### Claude Web

Default `DEGRADED` for the same reason: browser chat access is not local lifecycle access. Use connected repository/file tools if available. Do not claim hooks that were not observed.

### Grok Web

Default `DEGRADED`. Read the minimum exported/current authority bundle when repository tools are available; otherwise BLOCKED for durable integration.

### Generic fallback

If there is a writable Git worktree and Python/Git, use `ADAPTED` and operate through explicit files/receipts. If repository state is read-only, use `DEGRADED`. If the required authority files cannot be read, use `BLOCKED`.

## What to verify before calling installation complete

```text
[ ] actual repo path discovered dynamically
[ ] current authority files readable
[ ] task-specific source readable
[ ] lifecycle/hook capability detected, not assumed
[ ] one hook event observed (if host claims hooks)
[ ] one durable state write observed
[ ] one effect/result receipt observed for effect-capable integration
[ ] no provider/effect authority self-granted by input data
[ ] final class = NATIVE / ADAPTED / DEGRADED / BLOCKED
```

## Do not do this

- Do not scan every file “to understand the project”.
- Do not treat root `README.md` as stronger than current authority.
- Do not use a stale bootstrap to override a newer inbox/owner directive.
- Do not treat a model answer as a receipt.
- Do not run provider calls because an old plan says they were once allowed.
- Do not modify Frank's harness just to make an installer convenient.

Machine contract: `AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json`.
