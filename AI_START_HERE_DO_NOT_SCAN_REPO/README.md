# AI: START HERE. DO NOT SCAN THE REPO.

Use this file first. Do not crawl thousands of files to guess what the project is.

## 1. Find the repo. Do not guess a path.

If you are inside a Git checkout:

```sh
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
printf '%s\n' "$ROOT"
```

If that fails, locate **this directory** using the host's file tools. Its parent is the candidate repo root. Verify that the parent contains `README.md` and this directory before continuing.

Never assume `~/Downloads`, `~/Desktop`, `$HOME`, an attachment path, clone path, mount path or current working directory.

## 2. Read only these entry files first

1. `AI_START_HERE_DO_NOT_SCAN_REPO/README.md` — this file.
2. `HUMAN_READ_THIS/README.md` — plain-English project model.
3. `DEV_SOURCE_RESEARCH/README.md` — technical evidence map.
4. `DEV_SOURCE_RESEARCH/repository/TRIGGER3_CURRENT_STATE_AND_MIGRATION_2026-08-27.md` — Trigger-3 current-state ledger.
5. `CLAY_EXECUTION_AUTHORITY.md` — current owner execution pointer.
6. `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` — current supervisor selector.
7. The steering file named by that inbox.

Then read only task-relevant source/tests/receipts.

## 3. Current hard stop

Trigger-3 re-entered current main at `3c3dbe5020f57065f47bd4d0a2dce3c537128797`. Provider epoch `9.13` remains hard-off:

```text
external provider routes: OFF
Together: FORBIDDEN
paid fallback: FORBIDDEN
```

Do not call NVIDIA, Groq, Mistral, OpenRouter, Together or another model provider merely because old/quarantined files contain routes/plans. Re-resolve current authority first.

Current canonical Frankenstein Bauleiter/Bugfix entrypoints now contain a source/local-unit hard-off gate before provider import, secret lookup, network, Aider or external fallback. The old provider-backed implementations are preserved as `*_PROVIDER_QUARANTINED_854f6bc.py` donors. **Do not execute those donors directly.** Their existence is provenance, not authority.

The current focused gate result is source/local-unit evidence only. It is not provider runtime or 72-hour deployment acceptance.

## 4. Detect what the host can really do

Before installation or adaptation, detect:

- can read files?
- can write files?
- can execute shell commands?
- can persist state across sessions?
- can register hooks/lifecycle callbacks?
- can call local tools?
- can observe tool/effect results?
- can store durable receipts?

Do not claim a capability that was not observed.

## 5. Host route

### Claude Code

Use its real repository working directory and available shell/file lifecycle. Read this entry set first. Detect real hook/state capabilities before mapping any project hook. Do not assume an Anthropic API key exists.

### Codex CLI

Use the real checkout root reported by Git. Keep project state/evidence in project files, not hidden conversational memory. Verify any hook/tool effect from an observable result.

### Hermes Agent

Use the agent's actual workspace and tool registry. If durable lifecycle hooks or result receipts are unavailable, mark the install `DEGRADED`; do not invent them.

### ChatGPT Web

Use project/connected-file tools actually exposed in the session. There is no assumption of a local shell or persistent local daemon. If required lifecycle hooks cannot be installed, mark `ADAPTED` or `DEGRADED` rather than claiming native installation.

### Claude Web

Use only the file/project/tool surfaces actually exposed. No local-path assumptions. If no durable local hook can fire, classify accordingly.

### Grok Web

Same rule: use observed file/tool surfaces only. No invented local executor or hook.

### Generic fallback

Map only these functions if the host supports them:

```text
READ CURRENT AUTHORITY
READ/WRITE PROJECT STATE
OBSERVE INPUT
GENERATE CANDIDATE
REQUEST EFFECT
VERIFY EFFECT RESULT
WRITE RECEIPT
RE-ENTER RESULT
```

Missing capability => explicit degradation.

## 6. Verify installation, not file presence

A valid verification sequence is:

```text
input/event observed
-> typed/durable state update observed where required
-> intended hook/tool actually fired
-> effect/result receipt observed
-> result re-entered into later state/decision
```

A copied config file is not installation proof. A model saying “installed” is not proof.

## 7. Final status — exactly one

```text
NATIVE    = host exposes the required lifecycle/tool/state boundaries directly
ADAPTED   = equivalent behavior works through a host-specific adapter
DEGRADED  = useful subset works; missing boundaries are named
BLOCKED   = a required capability/authority is absent
```

Never return fake success.

## 8. Before changing repository topology

Do not move root files because they look ugly. Use the Trigger-3 migration ledger and first resolve imports, links, workflows, packaging and runtime path assumptions. Preserve Git/evidence lineage and avoid duplicate authorities.