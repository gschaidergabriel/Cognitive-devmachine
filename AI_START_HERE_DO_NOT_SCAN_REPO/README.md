# AI START HERE — DO NOT SCAN THE REPO

You do **not** need to scan thousands of files.

## 1. Read only these first

1. `../HUMAN_READ_THIS/README.md`
2. `../DEV_SOURCE_RESEARCH/README.md`
3. `../DEV_SOURCE_RESEARCH/EVIDENCE_LEDGER.md`
4. `../DEV_SOURCE_RESEARCH/ARCHIVE_INDEX.json`
5. for current execution authority, read `../DEV_SOURCE_RESEARCH/repository/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` and the exact steering file it selects.

## 2. Basic law

- Persistent research entity: `Clay`.
- Current product: `EntityOS`.
- Integrated cognition/compute architecture: `HCU`.
- Model/session/worker: temporary organ, not a new persistent entity.
- Model output is not world fact.
- Request is not effect.
- Component pass is not whole-product pass.
- Current authority beats stale plans.

## 3. Find the actual checkout dynamically

Never assume `~/Downloads`, `$HOME/project`, an attachment mount, or the current working directory.

If you have shell access:

```sh
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
printf '%s\n' "$ROOT"
```

If the directory is not a Git checkout, ask the host/tool for the mounted repository path. Do not invent one.

## 4. Host routes

### Claude Code

**Target result:** `NATIVE` when Claude Code has local file read/write + shell + lifecycle access to the checkout.

1. Resolve `$ROOT` dynamically.
2. Read the four files above.
3. Read current supervisor authority.
4. Detect whether hooks/background lifecycle features actually exist in this host; do not assume them.
5. Use repository-native tests and receipts.
6. Verify a real hook firing if the integration claims hooks.
7. Verify durable state writes and effect/result receipts if the integration claims them.

If hooks are unavailable but files/shell work, classify `ADAPTED`, not `NATIVE`.

### Codex CLI

**Target result:** usually `NATIVE` for file/shell engineering if the checkout is writable.

1. Resolve `$ROOT` with Git.
2. Read the four files above + current authority.
3. Work only from exact current source.
4. Run relevant tests.
5. Record exact HEAD and changed files.
6. Do not simulate external provider authority from environment variables alone.

### Hermes Agent

1. Resolve its real workspace/mount path.
2. Check whether it can read/write files, run shell commands, and preserve state across turns/runs.
3. Map only capabilities that really exist.
4. If durable lifecycle hooks are missing, use explicit re-entry files/receipts and classify `ADAPTED` or `DEGRADED`.

### ChatGPT Web

ChatGPT Web does not automatically equal a local shell agent.

1. Use connected repository/file tools if present.
2. Read the curation indexes first.
3. Do not claim local hook firing or local runtime unless an actual tool observed it.
4. If only repository read/write is available, classify the integration by those observed capabilities.

### Claude Web

Same rule: browser chat is not automatically a local executor.

1. Use connected repo/file tools when available.
2. Prefer exact source and current authority.
3. Do not fake lifecycle, shell or hook support.

### Grok Web

Same rule: detect real tools first. If it can only discuss uploaded/linked source, that is not a native runtime installation.

### Generic fallback

Ask the host these capability questions:

- Can you read files from this checkout?
- Can you write them?
- Can you run commands?
- Can you observe command exit code/stdout/stderr?
- Can you persist state across invocations?
- Can you install/register lifecycle hooks?
- Can you prove a hook actually fired?
- Can you observe effects and later verify outcomes?

Then classify:

- `NATIVE` — required lifecycle/tool/state capabilities exist and are verified.
- `ADAPTED` — core function works through a different verified mechanism.
- `DEGRADED` — only part of the intended integration works.
- `BLOCKED` — a required capability is absent or authority forbids the action.

## 5. Current critical warning at this frozen base

The new Frankenstein Bauleiter/Bugfix scripts contain direct external provider fallback code. Current 9.13 HARD_OFF authority says provider routes are off and Together/paid fallback are forbidden. Do **not** deploy those provider-calling loops unchanged.

A future safe version must resolve canonical provider authority before secret lookup, provider import, network, Aider or external fallback dispatch, and must fail closed under HARD_OFF.

## 6. Installation is not success until observed

Do not stop at "file copied" or "config written".

For any integration that claims lifecycle/state/effect support, verify the relevant observable:

- hook fired;
- state write exists;
- generation/provenance is correct;
- effect request passed the proper gate;
- effect/result receipt exists;
- outcome was re-observed when the claim requires it.

Then output one final status: `NATIVE`, `ADAPTED`, `DEGRADED`, or `BLOCKED`.

For a more formal contract, read [`INSTALLER_CONTRACT.md`](INSTALLER_CONTRACT.md).