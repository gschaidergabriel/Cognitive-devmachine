# AI: START HERE. DO NOT SCAN THE REPO.

Short route. No guessing paths.

## Rule 0

**Do not assume Downloads. Do not assume `$HOME`. Do not assume clone path. Do not assume current directory.**

You need one real path: the repository root or this file's path.

If you only have this file, resolve the parent directory containing:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

During migration, old root entries may still exist. That is okay.

---

## 1. Read only these files first

```text
AI_START_HERE_DO_NOT_SCAN_REPO/README.md
DEV_SOURCE_RESEARCH/repository/CURRENT_AUTHORITY_AND_EVIDENCE.md
DEV_SOURCE_RESEARCH/repository/ARCHIVE_INDEX.json
HUMAN_READ_THIS/README.md
```

Do **not** recursively scan `research_entity/`, `agentZero/`, Git history, or the whole repo unless the task needs a specific source shard.

---

## 2. Resolve the task

### Human asks for explanation / history

Read:

```text
HUMAN_READ_THIS/README.md
DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_RESEARCH_CHRONICLE.md
```

### Human asks for current architecture / authority

Read:

```text
DEV_SOURCE_RESEARCH/repository/CURRENT_AUTHORITY_AND_EVIDENCE.md
```

Then open the exact authority/source paths named there.

### Human asks for code change

1. Read current authority file.
2. Find exact target source.
3. Find overlapping PR/branch/work.
4. Read target tests.
5. Patch smallest useful surface.
6. Run exact tests.
7. Record exact commit/source identity and scope.

### Human asks for historical research

Use:

```text
DEV_SOURCE_RESEARCH/repository/ARCHIVE_INDEX.json
```

Open only relevant indexed shards.

---

## 3. Host route

Pick **one** route. Do not pretend another host's lifecycle exists.

### Claude Code

1. Resolve real repo path.
2. Run host capability probe:

```text
python3 <REAL_REPO>/AI_START_HERE_DO_NOT_SCAN_REPO/probe_host.py --repo <REAL_REPO> --host claude-code --state-dir <REAL_WRITABLE_STATE_DIR>
```

3. If `claude` command is absent: result cannot be `NATIVE`.
4. Map project boot instructions only to Claude Code lifecycle/tools that actually exist.
5. Fire one real hook/event if configured.
6. Verify its receipt file exists and contains the expected run ID.
7. Verify one durable state write survives a fresh process/read.
8. Verify one harmless tool/effect request has a distinct result receipt.

### Codex CLI

Same sequence, host name:

```text
--host codex-cli
```

`codex` command must be detected before `NATIVE` is possible.

### Hermes Agent

Same sequence, host name:

```text
--host hermes-agent
```

A Hermes executable/tool surface must actually be detected before `NATIVE` is possible.

### ChatGPT Web

Do not invent a local lifecycle hook.

1. Use the connected GitHub/repository tool if available, or provide the repository files explicitly.
2. Read the four start files above.
3. If the web session can read/write GitHub but cannot receive native repository lifecycle hooks, classify installation as `ADAPTED` or `DEGRADED`, not `NATIVE`.
4. A chat message saying "hook fired" is not a hook receipt.
5. Durable project state must be verified on an actual connected state surface.

### Claude Web

Same rule as ChatGPT Web. Web chat alone is not a local hook runtime.

### Grok Web

Same rule as ChatGPT Web. Web chat alone is not a local hook runtime.

### Generic fallback

Use:

```text
python3 <REAL_REPO>/AI_START_HERE_DO_NOT_SCAN_REPO/probe_host.py --repo <REAL_REPO> --host generic --state-dir <REAL_WRITABLE_STATE_DIR>
```

Then map only capabilities the host really has.

---

## 4. Capability mapping

Need these capability classes:

```text
READ_SOURCE
WRITE_SOURCE
RUN_CODE
DURABLE_STATE
LIFECYCLE_HOOK
TOOL_EFFECT
RESULT_RECEIPT
GIT_IDENTITY
```

Each class is:

```text
PRESENT
ABSENT
UNKNOWN
```

`UNKNOWN` is not `PRESENT`.

If a host lacks a native capability, adapt it explicitly. Example: a web host can use a connected GitHub write instead of a local filesystem write. That is an adaptation, not native parity.

---

## 5. Required proof before calling installation complete

### A. Real hook firing

A configured lifecycle event must create a receipt containing at least:

```text
run_id
host
hook_name
time
repo_identity
```

No receipt -> hook status `UNKNOWN` or `ABSENT`.

### B. Durable state

Write a unique value through the intended state path.

Close process/session.

Read it through the intended read path.

Exact value must survive.

### C. Effect/result separation

For one harmless tool action, persist two identities:

```text
request_id
result_id
```

The result must point to the request. A requested command is not proof the command ran.

### D. Current source identity

Record Git commit/ref or exact file digest. Do not say "current" without identity.

---

## 6. Final installation result

Output exactly one of:

### `NATIVE`

Host has the required lifecycle/tool/state surfaces directly and all required proofs passed.

### `ADAPTED`

Required behavior works through explicit adapters/connected tools and proofs passed.

### `DEGRADED`

Useful operation is possible, but one or more required lifecycle/state/effect proofs are unavailable.

### `BLOCKED`

The host cannot provide enough read/write/run/state/tool capability for the requested integration, or current authority forbids the required action.

Never convert `UNKNOWN` into success.

---

## 7. Current project guardrails

At the curation snapshot used to build this installer:

- product: EntityOS;
- compute architecture: HCU;
- final owner target: variable cognitive grid + persistent DB + Claude Code;
- GRID10: benchmark configuration, not final identity;
- local/VPS `clay-direct-dev`: broad owner-authorized development sandbox;
- provider authority: 9.13 HARD_OFF;
- current provider calls: forbidden;
- recent 72h Frankenstein provider orchestrator: quarantined, not deployable under current authority;
- root README: intentionally not rewritten by Triggerword 3.

Always refresh current authority before real execution.

---

## 8. One-line installer contract

```text
RESOLVE REAL PATH -> READ 4 SMALL FILES -> DETECT REAL HOST CAPABILITIES -> MAP ONLY WHAT EXISTS -> PROVE HOOK + DURABLE STATE + REQUEST/RESULT -> REPORT NATIVE|ADAPTED|DEGRADED|BLOCKED
```
