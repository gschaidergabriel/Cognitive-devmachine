# AI START HERE — DO NOT SCAN REPO

Use this file to connect an AI/tool host to the repository **without crawling the repository**.

## 0. STOP

Do not scan the repo.  
Do not read secrets.  
Do not call providers just to test installation.  
Do not assume Downloads, home, clone path, attachment path, or current working directory.

At the 2026-08-27 snapshot used for this installer, `SUPERVISOR_INBOX.json` admits **9.13 / surface 9.13O** and provider execution + secret use are **HARD_OFF**. Re-read current authority before doing anything executable.

## 1. FIND THE ROOT

Use a path the host actually gives you.

If shell + Git are available:

```sh
git -C "<path-you-actually-have>" rev-parse --show-toplevel
```

If no shell exists, treat the directory containing this file as the repository root through the host's file API. Do not invent a filesystem path.

Call the result `ROOT`.

## 2. READ ONLY THIS BOOT SET

Read, in order:

```text
ROOT/CLAY_EXECUTION_AUTHORITY.md
ROOT/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
ROOT/<steering file named by SUPERVISOR_INBOX.json>
ROOT/AI_START_HERE_DO_NOT_SCAN_REPO/README.md
ROOT/DEV_SOURCE_RESEARCH/README.md
ROOT/HUMAN_READ_THIS/README.md
```

If these disagree, do not average them. Newest admitted authority wins. Fail closed on execution.

## 3. PROBE CAPABILITIES, NOT PROVIDERS

Answer these with observed host behavior:

```text
A. Can this host read repository files?
B. Can it execute a local command/tool?
C. Does it expose a real lifecycle event/hook?
D. Can that hook create a harmless durable local state/receipt?
E. Can the receipt be read back and tied to the event that caused it?
F. Can execution be denied before secret lookup/network/provider import when authority says HARD_OFF?
```

A provider request is **not** an installation probe under HARD_OFF.

## 4. CLASSIFY THE RESULT

Use exactly one:

- `NATIVE` — host-native lifecycle hook fired, current authority was respected, durable state/receipt was observed, and result re-entry was verified.
- `ADAPTED` — an external/local adapter supplied the missing lifecycle bridge and the same observations were verified.
- `DEGRADED` — files/instructions work, but hook/state/effect receipt is not fully verified.
- `BLOCKED` — required files/capabilities/authority are unavailable or ambiguous.

Never report `NATIVE` because a hook file merely exists.

## 5. HOST ROUTES

### Claude Code

Candidate native route exists in source:

```text
ROOT/.claude/settings.json
ROOT/.claude/hooks/rae_hook.py
ROOT/.claude/hooks/stop-auto-continue.sh
```

`.claude/settings.json` registers lifecycle events including `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`, `PreCompact`, `Stop`, and `SessionEnd`.

Important: the current `rae_hook.py` still contains older Frank/Research-Entity identity language. Therefore **source presence is not installation acceptance**. Before `NATIVE`, prove that the effective hook behavior obeys the newest current Clay/EntityOS/HCU authority, then perform one harmless local event and observe its exact durable receipt/state write. No provider call.

If old identity semantics remain active: `DEGRADED` or `BLOCKED`, not `NATIVE`.

### Codex CLI

No canonical Codex-specific lifecycle adapter was verified in the exact repository evidence inspected for this pass.

1. Detect the CLI's actual repository-instruction and lifecycle facilities.
2. If a real event can invoke a bounded local adapter, map it to the same authority-first contract.
3. Trigger one harmless local event.
4. Verify durable write + event-linked receipt + re-entry.

Verified wrapper/bridge: `ADAPTED`.  
Instructions only: `DEGRADED`.  
Do not invent a hook: `BLOCKED` if lifecycle integration is required and unavailable.

### Hermes Agent

No canonical Hermes-specific lifecycle adapter was verified in the exact repository evidence inspected for this pass.

Use the same sequence: detect real lifecycle/tool/state capability → bind authority-first adapter if supported → fire one harmless local event → verify durable receipt → classify.

Do not map a similarly named provider/model entry to Hermes Agent installation evidence.

### ChatGPT Web

Do not pretend a local CLI hook exists.

Use only capabilities actually exposed in the current ChatGPT workspace/project/connectors. If repository files can be read and instructions retained but there is no verified host lifecycle event that produces an event-linked durable receipt, classify `DEGRADED`.

A connector write or tool action is an effect request. Verify the resulting effect separately before credit.

### Claude Web

Do not reuse Claude Code hook claims for Claude Web. They are different hosts.

Detect project/file/tool capabilities available in the actual web session. Without a verified lifecycle adapter + durable receipt: `DEGRADED`. If the required repository access is absent: `BLOCKED`.

### Grok Web

Same rule: detect actual capabilities first. Do not infer local filesystem hooks from a web chat. Files/instructions only: `DEGRADED`; missing required access: `BLOCKED`.

### Generic fallback

```text
READ boot set
→ detect lifecycle/tool/state capabilities
→ resolve current authority
→ bind only a local non-provider adapter if possible
→ fire one harmless event
→ observe durable state/receipt
→ re-read receipt
→ classify NATIVE / ADAPTED / DEGRADED / BLOCKED
```

## 6. MINIMUM ACCEPTANCE RECEIPT

An installation test receipt should bind at least:

```json
{
  "host": "<observed host>",
  "classification": "NATIVE|ADAPTED|DEGRADED|BLOCKED",
  "repo_identity": "<observed repository + commit/ref>",
  "authority_surface": "<observed admitted surface>",
  "event": "<actual harmless lifecycle event or null>",
  "adapter": "<actual adapter path or null>",
  "durable_write": "<observed path/id or null>",
  "result_reentry": "OBSERVED|NOT_OBSERVED",
  "provider_execution": "NONE",
  "secret_lookup": "NONE",
  "notes": "<bounded evidence / blocker>"
}
```

Do not fill unknown fields with guesses.

## 7. DONE MEANS VERIFIED

`file exists` != hook fired  
`hook fired` != state persisted  
`request emitted` != effect happened  
`model said success` != success  
`provider unavailable` != scientific negative  
`source-ready` != runtime-observed

Return the exact classification and the exact missing discriminator. Then stop. Do not scan the rest of the repo to make the answer look more complete.