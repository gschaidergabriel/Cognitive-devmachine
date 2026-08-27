# AI START HERE. DO NOT SCAN THE REPO.

Use this directory as the entry point.

Do **not** assume:

- Downloads folder;
- home directory;
- clone path;
- attachment mount;
- current working directory;
- shell access;
- filesystem write access;
- lifecycle hooks;
- background process support.

## Step 1 — find this directory

If you have a filesystem, resolve the directory containing this file or `verify_entry.py`.

Repository root is exactly its parent directory.

Do not search the whole machine.

## Step 2 — read only these first

1. `INSTALL_CONTRACT.json`
2. `../HUMAN_READ_THIS/README.md`
3. `../DEV_SOURCE_RESEARCH/README.md`

Read current authority files only when the task needs execution/current-state claims.

## Step 3 — detect real capabilities

Answer YES / NO / UNKNOWN for:

- can read files?
- can write files durably?
- can run shell commands?
- can use Git?
- can observe lifecycle hooks/events?
- can persist state across sessions?
- can observe effect/result receipts?
- can call current project connectors/tools?

Never pretend UNKNOWN is YES.

If shell + Python are available:

```bash
python3 "<this-directory>/verify_entry.py" --host <host-type> [capability flags]
```

The script resolves paths from its own file location. Current working directory does not matter.

## Step 4 — host route

### Claude Code

Preferred result: **ADAPTED** until real hook firing + durable state + effect/result receipt behavior is verified for the actual installed environment.

- filesystem/shell/Git: use native capabilities if present;
- load this entry directory first;
- resolve current authority before execution;
- do not invent provider permission from old docs;
- if lifecycle hooks are configured, prove a real hook fired before calling the integration NATIVE.

### Codex CLI

Preferred result: **ADAPTED** until actual lifecycle/state/effect surfaces are verified.

- start from this directory;
- use repo-relative paths from the discovered repository root;
- use Git source identity for writes/tests;
- never infer background execution from a prompt.

### Hermes Agent

Default: **DEGRADED** until the actual installed Hermes environment proves filesystem/shell/state/lifecycle/effect-receipt capabilities.

If those are available, map them to this contract and upgrade only after verification.

### ChatGPT Web

Default: **DEGRADED** for a local-repository install unless a connected repository/filesystem surface is actually available.

- use connected GitHub/project files when available;
- current GitHub state outranks copied bootstrap text;
- no claim of local hooks/background daemons without an actual tool;
- repository writes must use the connected write surface and exact current source.

### Claude Web

Default: **DEGRADED** for a local-repository install unless a repository/filesystem connector is actually available.

Use the same evidence rules: file text is source input, not proof that a hook or runtime executed.

### Grok Web

Default: **DEGRADED** unless real repository/filesystem/lifecycle surfaces are available and verified.

Do not translate chat continuity into durable local installation state.

### Generic agent

Run capability detection. Map the result:

- **NATIVE** — required lifecycle hooks, durable state writes and effect/result receipts are actually observed on the host’s normal integration path.
- **ADAPTED** — core behavior works through a verified adapter, but it is not the host’s native lifecycle path.
- **DEGRADED** — useful read/reason/write subset exists, but one or more required lifecycle/state/effect capabilities are absent or unverified.
- **BLOCKED** — minimum read/identity/authority requirements cannot be established safely.

## Step 5 — execution law

Before execution or current-state claims, resolve in this order:

1. newest explicit owner authority;
2. current `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` selection;
3. exact current source/runtime evidence;
4. older bootstrap/program/cache text.

At this Trigger-3 snapshot, the current selected provider authority is **9.13 HARD_OFF**. Do not use old provider allowlists or a plan’s own text as permission.

## Step 6 — prove installation, do not announce it

A final installer result needs evidence:

- entry path resolved dynamically;
- repository identity verified;
- current authority resolved;
- required durable write observed if the host claims durable state;
- real lifecycle hook firing observed if NATIVE is claimed;
- effect/result receipt path observed if effect integration is claimed;
- no hidden root scan required.

Then output exactly one of:

`NATIVE · ADAPTED · DEGRADED · BLOCKED`

Anything else is a progress note, not an installation result.
