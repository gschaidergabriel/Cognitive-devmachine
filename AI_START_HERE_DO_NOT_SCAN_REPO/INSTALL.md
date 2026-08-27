# AI INSTALL — DO NOT SCAN THE REPO

Use this file first.

Goal: connect an AI host to the project **without guessing paths, pretending hooks work, or scanning the whole repository**.

## Rule 0

Find this file. Its parent folder is `AI_START_HERE_DO_NOT_SCAN_REPO/`. The repository root is exactly its parent folder.

Do not assume `~/Downloads`.
Do not assume `$HOME`.
Do not assume current working directory.
Do not assume the clone name.

If you have a filesystem path to this file:

```text
THIS_FILE = absolute path to INSTALL.md
AI_DIR    = parent(THIS_FILE)
REPO_ROOT = parent(AI_DIR)
```

Then read only:

```text
AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json
HUMAN_READ_THIS/START_HERE.md
DEV_SOURCE_RESEARCH/README.md
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
```

Do not crawl everything unless a later task actually needs a specific source path.

## First command

From any directory:

```bash
python3 /absolute/path/to/repo/AI_START_HERE_DO_NOT_SCAN_REPO/install_probe.py --host <host>
```

Allowed `<host>` values:

```text
claude-code
codex-cli
hermes-agent
chatgpt-web
claude-web
grok-web
generic
```

The probe prints JSON. The final `result` is one of:

```text
NATIVE
ADAPTED
DEGRADED
BLOCKED
```

No fifth success word exists.

## Meaning

**NATIVE** — host has the lifecycle/tool/state abilities required by the selected route and the expected project-native instruction surface is present.

**ADAPTED** — host can do the job, but needs a small adapter or different instruction file.

**DEGRADED** — host can read/use project context, but cannot prove full hook firing + durable state write + effect/result receipt.

**BLOCKED** — required capability or project path is missing.

## Host routes

### Claude Code

Expected native project instruction surface today: `CLAUDE.md`.

Steps:

1. Resolve `REPO_ROOT` from this file.
2. Verify `REPO_ROOT/CLAUDE.md` exists.
3. Verify a `claude` executable exists in the actual host environment.
4. Read current supervisor inbox before any provider/network/effect work.
5. For any lifecycle hook claimed as installed, trigger it once with a harmless local event.
6. Verify the hook produced the expected durable state write.
7. Verify the resulting action/effect path produced a receipt if an effect was involved.
8. If steps 5–7 cannot be observed, result is **DEGRADED**, not NATIVE.

### Codex CLI

Expected project instruction surface today: `AGENTS.md`.

Steps:

1. Resolve `REPO_ROOT` dynamically.
2. Verify `REPO_ROOT/AGENTS.md` exists.
3. Verify a `codex` executable exists in the actual host environment.
4. Read current supervisor inbox.
5. Detect actual filesystem, shell, Git, and state-write capabilities before mapping automation.
6. Test one harmless local state write and read-back if the host exposes such a path.
7. If hooks/lifecycle events are not exposed, use the instruction surface but mark result **ADAPTED** or **DEGRADED**.

### Hermes Agent

No project-specific Hermes lifecycle contract is assumed.

Steps:

1. Resolve `REPO_ROOT` dynamically.
2. Detect the actual Hermes executable/API/tool surface.
3. Read `INSTALL_CONTRACT.json` and current supervisor inbox.
4. Map only capabilities that are actually exposed: filesystem read, filesystem write, Git, command execution, lifecycle hooks, durable state, effect receipts.
5. If Hermes can consume the project instructions but cannot prove lifecycle + durable write + receipt behavior, result is **ADAPTED** or **DEGRADED**.
6. Never invent a Hermes hook name.

### ChatGPT Web

Web chat alone is not assumed to have repository hooks or durable project filesystem writes.

Steps:

1. Provide this installer folder or a connected repository/file surface.
2. Read `INSTALL_CONTRACT.json`, Human start, Dev start, supervisor inbox.
3. Detect connected tools actually available in that session.
4. If repository read/write is connected, verify one harmless branch/file operation when the user asks for installation work.
5. If only chat/file reading exists, result is **DEGRADED**.

### Claude Web

Same law as ChatGPT Web: detect connected tools; do not infer repository hooks from chat access.

- Read-only context only → **DEGRADED**.
- Proven repo/state adapter without native lifecycle hooks → **ADAPTED**.
- Claim **NATIVE** only if hook firing, durable state and receipts are all actually observable for the selected route.

### Grok Web

Same law: web chat is not automatically an agent runtime.

- Context ingestion only → **DEGRADED**.
- Explicit connected repo/state actions with verified read-back → possibly **ADAPTED**.
- Never claim NATIVE from a successful chat response.

### Generic fallback

1. Resolve the repo root from this file.
2. Read the four small bootstrap surfaces listed above.
3. Inventory actual host capabilities.
4. Map only real capabilities.
5. Verify a harmless state transition if writes exist.
6. Verify a receipt if effects exist.
7. Emit NATIVE / ADAPTED / DEGRADED / BLOCKED.

## Current safety / authority note

At the Triggerword 3 branch base, the current supervisor is **9.13 HARD_OFF** for external providers. The fresh Frankenstein provider-loop orchestration is quarantined and non-operative. An installer must not revive it merely because source files exist.

Provider/network calls, Together, or external autonomous helper loops are **not** installation tests under the current authority.

A good install test is local, deterministic, cheap, reversible, and leaves a verifiable receipt.

## What success must prove

A claimed full installation needs evidence for all applicable items:

```text
[1] correct repository resolved dynamically
[2] correct current authority read
[3] host capability detected, not guessed
[4] lifecycle/hook fired if the route claims one
[5] durable state write observed and read back
[6] effect request distinguished from effect result
[7] receipt/result observed when an effect path is used
[8] no forbidden provider path activated
```

Missing [4] on a host with no lifecycle surface is not shameful. It just means **ADAPTED** or **DEGRADED**.
