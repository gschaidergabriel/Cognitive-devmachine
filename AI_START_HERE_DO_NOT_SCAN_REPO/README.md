# AI: start here. Do not scan the repository.

Goal: connect an AI host to the Frankenstein research/project context **without assuming where the repository lives** and without pretending unsupported lifecycle hooks exist.

## Caveman version

```text
1. Find this file.
2. Its parent directory is AI_START_HERE_DO_NOT_SCAN_REPO.
3. Repository root = parent of that directory.
4. Read HUMAN_READ_THIS/README.md.
5. Read DEV_SOURCE_RESEARCH/README.md.
6. Read current authority files listed below.
7. Detect what your host can actually do.
8. Install only the route your host supports.
9. Prove the hook/state/effect path works.
10. Report NATIVE / ADAPTED / DEGRADED / BLOCKED.
```

Never assume `~/Downloads`, `$HOME`, a clone folder name, an attachment mount, or the current working directory.

## Resolve the repository root

If you can execute a shell and you know the path to **this** file:

```sh
AI_START_FILE="/absolute/path/to/AI_START_HERE_DO_NOT_SCAN_REPO/README.md"
REPO_ROOT="$(cd "$(dirname "$AI_START_FILE")/.." && pwd -P)"
printf '%s\n' "$REPO_ROOT"
```

If you cannot execute a shell, use the host's own file-reference metadata. The repository root is exactly one directory above `AI_START_HERE_DO_NOT_SCAN_REPO/`.

## Minimum files to read

Do not recursively scan the repo. Read only:

```text
HUMAN_READ_THIS/README.md
DEV_SOURCE_RESEARCH/README.md
DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_RESEARCH_CHRONICLE.md
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json
```

Then follow links only when the task requires them.

### Current safety/authority note

At the 2026-08-27 Trigger-3 base, provider authority epoch 9.13 is HARD-OFF: autonomous external provider routes are not admitted, Together is forbidden, and there is no paid fallback. An installer must not infer permission from a key, historical plan, or provider availability.

## Capability detection

Before installing anything, answer these with evidence from the host:

```text
can_read_project_files?
can_write_project_files?
can_execute_local_shell?
can_run_on_session_start?
can_run_before_each_turn/task?
can_run_after_each_turn/task?
can_persist_local_state?
can_call tools/connectors?
can observe tool/effect result receipts?
can enforce a pre-effect gate?
```

Do not map a feature that the host does not have.

## Host routes

### Claude Code

Target: **NATIVE** when repository instructions can live in project files and lifecycle/tool hooks can be verified on the actual installed Claude Code version.

Procedure:

1. resolve `REPO_ROOT` dynamically;
2. read the minimum files above;
3. inspect the actual Claude Code project-instruction/hook capabilities installed on this machine;
4. map only supported lifecycle events;
5. write one test state record from a harmless hook;
6. run one harmless tool/action through the intended path;
7. verify the hook fired and the result/receipt re-entered state;
8. if a needed lifecycle event is unavailable, classify `ADAPTED` or `DEGRADED` instead of inventing it.

### Codex CLI

Target: **NATIVE** when the installed Codex CLI exposes project instructions plus the required local execution/state capabilities; otherwise **ADAPTED**.

Procedure:

1. resolve `REPO_ROOT`;
2. read minimum files;
3. inspect the installed CLI's actual repository-instruction/config behavior;
4. preserve existing project instructions rather than replacing them blindly;
5. test one harmless read/write lifecycle path;
6. verify persistent state and effect/result receipt visibility;
7. report the classification.

### Hermes Agent

Target: `NATIVE` only if the installed Hermes runtime has equivalent persistent project-context, lifecycle, state, and tool-result surfaces.

If it lacks one or more required surfaces:

- wrap only through documented supported interfaces;
- keep canonical project state external;
- do not create a second hidden memory authority;
- classify `ADAPTED`, `DEGRADED`, or `BLOCKED` honestly.

### ChatGPT Web

Typical route: **ADAPTED** or **DEGRADED** unless the session has a connected project/repository surface and the required write/effect lifecycle.

1. attach/connect only the project sources needed;
2. use the minimum-file list as the entry context;
3. do not claim a local shell hook if none exists;
4. use available connectors/tools for explicit actions;
5. verify every actual write through the connector result;
6. treat conversation memory as context, not canonical state.

### Claude Web

Use the same rules as ChatGPT Web: project/file context may be useful, but a browser chat is not automatically a local runtime daemon. Map only real connected tool/file/action surfaces. Missing lifecycle hooks mean `ADAPTED`/`DEGRADED`, not fake `NATIVE`.

### Grok Web

Same principle: read/import the minimal project context if supported; do not imply local process hooks, durable SQLite state access, or effect receipts unless the actual host provides and verifies them.

### Generic fallback

Any AI host can at minimum implement this degraded contract:

```text
READ minimum project context
RESOLVE current authority
DO requested reasoning/work
NEVER mint canonical truth from model output
RETURN proposed delta + evidence + unresolved gates
DO NOT claim persistent installation
```

Classification: `DEGRADED` unless durable lifecycle/state/effect integration is actually verified.

## Verification — required before saying “installed”

A host-specific installation must prove, where applicable:

1. **Path proof** — resolved actual repository root; no hard-coded Downloads/home assumption.
2. **Instruction proof** — host loaded the intended project instruction/context.
3. **Lifecycle proof** — the claimed hook/event actually fired.
4. **State proof** — a harmless durable state write can be read back after the relevant lifecycle boundary.
5. **Effect proof** — a harmless effect/tool request traveled through the intended gate and produced an observable result/receipt.
6. **Re-entry proof** — the result was visible to later cognition/state without being silently promoted beyond its evidence class.
7. **Failure proof** — disabling/breaking the hook produces a detectable failure rather than silent fake success.
8. **Authority proof** — current provider/effect authority is resolved before any external action.

If a required proof cannot be run, installation is not `NATIVE`.

## Final result vocabulary

```text
NATIVE    = host directly supports the needed lifecycle/state/effect contract and proofs pass
ADAPTED   = supported through a bounded adapter without creating a second authority
DEGRADED  = useful project context works, but one or more required runtime capabilities are absent
BLOCKED   = required capability/authority is unavailable or unsafe to emulate
```

Never use “installed successfully” as a fifth status.

## Machine-readable contract

See [`INSTALL_CONTRACT.json`](INSTALL_CONTRACT.json).
