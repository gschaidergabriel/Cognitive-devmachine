# AI: START HERE. DO NOT SCAN THE REPO.

Goal: join the project safely with minimum reads.

## 0. Find the repo. Do not guess a path.

Use the host/tool's real repository picker, workspace metadata, current directory, or connected Git repository.

Do **not** assume:

- `~/Downloads`
- home directory
- a clone path
- an attachment path
- current working directory

Call the discovered repository root `<REPO>`.

## 1. Read only these first

1. `<REPO>/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
2. the `steering` file named by that inbox
3. `<REPO>/HUMAN_READ_THIS/README.md`
4. `<REPO>/DEV_SOURCE_RESEARCH/README.md`
5. `<REPO>/DEV_SOURCE_RESEARCH/repository/FRANKENSTEIN_EVIDENCE_INDEX_2026-08-27.json`

Do not scan all files unless the task later requires a specific source path.

## 2. Identity

Persistent research entity: **Clay**.  
You are a temporary worker / organ.  
Current product: **EntityOS**.  
Current integrated compute/cognition architecture: **HCU**.

Do not create another product identity or truth store.

## 3. Detect what you can actually do

Record real capabilities before mapping hooks:

```text
CAN_READ_FILES = yes/no
CAN_WRITE_FILES = yes/no
CAN_RUN_COMMANDS = yes/no
CAN_USE_GIT = yes/no
CAN_PERSIST_STATE = yes/no
CAN_REGISTER_HOOKS = yes/no
CAN_OBSERVE_HOOK_FIRE = yes/no
CAN_MAKE_EXTERNAL_EFFECTS = yes/no
```

Do not say “installed” because a file exists. Verify the lifecycle event that is supposed to use it.

## 4. Host routes

### Claude Code

Use its real opened repository as `<REPO>`. Read the five files above. If repo instructions/hooks are available, map only after confirming the exact supported lifecycle. Verify one real hook fire and one durable write before calling the integration native.

### Codex CLI

Use the checked-out repository reported by the CLI as `<REPO>`. Read the five files above. Use repository instructions only if the current CLI actually exposes them. Verify command execution and durable state separately.

### Hermes Agent

Use the workspace/repository path exposed by the agent. Read the five files above. Detect its persistence and hook/event model first; do not copy Claude/Codex conventions blindly.

### ChatGPT Web

Use the connected GitHub/project file surfaces. Read the five files above through the connector. ChatGPT Web may not have a native local lifecycle hook; if so, classify as `ADAPTED` or `DEGRADED`, not fake `NATIVE`.

### Claude Web

Use connected repository/project files if available. Read the five files above. If no executable local hook/state surface exists, use an adapted read/write workflow and classify it honestly.

### Grok Web

Use connected repository files if available. Read the five files above. Do not claim native repo hooks unless they can be observed firing.

### Generic fallback

Give the AI these five files or exact text extracts. Require it to report its real capabilities. No hook support = no hook claim.

## 5. Current hard stop

At the current 9.13 authority snapshot:

```text
PROVIDER_ROUTES = OFF
TOGETHER = FORBIDDEN
PAID_FALLBACK = FORBIDDEN
```

Do not run the provider-calling Frankenstein Bauleiter/Bugfix loops unchanged. Current authority must be resolved **before** secret lookup, provider import, network dispatch, Aider fallback, or other provider boundary.

Do not modify Frank's own Harness to bypass this rule.

## 6. Effect rule

Model output is a candidate.  
Request is not effect.  
Effect is not verified until its result is observed and journaled.

## 7. Finish with one status

Use exactly one:

- `NATIVE` — host lifecycle, state and effect/result receipts are genuinely integrated and verified.
- `ADAPTED` — useful integration works through a host-specific adapter.
- `DEGRADED` — read/write help works but required lifecycle/state/effect features are missing.
- `BLOCKED` — the required capability or authority is unavailable.

Never report success from configuration alone.
