# AI: start here. Do not scan repo root.

Short words. Exact order. Fail closed.

## 1. Find repo root

Do **not** assume Downloads, home, clone path, attachment path, or current directory.

Find the directory that contains this file and repository metadata. Call it `<REPO>`.

No exact root: **BLOCKED**.

## 2. Read authority first

Read, in order:

1. `<REPO>/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
2. the exact steering file selected by that inbox
3. `<REPO>/research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md`
4. `<REPO>/research_entity/topic_packets/frankenstein-master-cognition-concept/CURRENT_AUTHORITY_OVERRIDE_20260827.md`

Expected current state on 2026-08-27:

- provider authority: **9.13 HARD_OFF**
- external provider routes: **OFF**
- Together: **FORBIDDEN**
- paid fallback: **FORBIDDEN**
- remaining Together paid runs: **0**
- old provider-backed Frankenstein implementations: **QUARANTINED**
- canonical Frankenstein entrypoints: **AUTHORITY-GATED / FAIL CLOSED UNDER HARD_OFF**

If current authority files changed, they win.

Cannot resolve authority: **BLOCKED**.

## 3. Know current Frankenstein files

Current canonical files:

- `frankenstein_authority_gate_v1.py`
- `frankenstein_orchestrator_v1.py`
- `frankenstein_bugfix_v1.py`
- `BUILD_ORCHESTRATION_PLAN_20260827.json`

These current entrypoints are designed to check authority before provider import, secret lookup, network, Aider, or fallback dispatch.

Old provider-backed donors are preserved with names like:

- `frankenstein_orchestrator_v1_PROVIDER_QUARANTINED_854f6bc.py`
- `frankenstein_bugfix_v1_PROVIDER_QUARANTINED_854f6bc.py`
- `BUILD_ORCHESTRATION_PLAN_20260827_PROVIDER_QUARANTINED_854f6bc.json`

**Do not execute quarantined donors under current HARD_OFF.**

Do not read provider secrets “just to test.”

Do not call a provider before authority admission.

Do not modify Frank's Harness to bypass the gate.

A fail-closed test of the canonical gate is not a provider run. It should prove zero provider calls and zero secret lookups under HARD_OFF.

## 4. Read the small map

Now read:

1. `<REPO>/HUMAN_READ_THIS/README.md`
2. `<REPO>/DEV_SOURCE_RESEARCH/README.md`
3. `<REPO>/DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_EVIDENCE_INDEX_2026-08-27.json`
4. `<REPO>/DEV_SOURCE_RESEARCH/repository/TRIGGERWORD3_REPOSITORY_MIGRATION_MANIFEST_2026-08-27.json`

Only then open task-specific source.

Do not crawl the whole repository unless the task needs it.

## 5. Detect real host capability

Check only what exists:

- shell / files
- Git read
- Git write
- process execution
- persistent local state
- lifecycle/startup hooks
- tool-result receipts
- network access
- user approval boundary

Do not invent hooks from a product name.

## 6. Pick one host route

### Claude Code

Use native repo files, Git, shell and project instructions if present. Current authority stays above convenience prompts.

### Codex CLI

Use repo instructions + Git + shell if actually present. Verify persistence/hooks; do not assume them.

### Hermes Agent

Inspect its installed tool/lifecycle/state API first. Use only observed capabilities.

### ChatGPT Web

Use connected repo/file tools when present. Browser chat alone is not a local daemon and does not imply lifecycle/process control.

### Claude Web

Same rule. Connected project/repo surfaces may support adaptation; browser chat alone does not imply local hooks.

### Grok Web

Same rule. Detect actual connected capability first.

### Generic fallback

If host can only read files and answer text:

1. read authority;
2. read the small map;
3. write only if a real safe write path exists;
4. never fake runtime evidence;
5. report `DEGRADED` or `BLOCKED`.

## 7. Installation/adaptation order

1. Resolve `<REPO>`.
2. Resolve current authority.
3. Detect host capabilities.
4. Select task-specific source only.
5. Bind state dynamically under `<REPO>` or an explicitly supplied state path. Never assume `$HOME`.
6. Add the smallest adapter needed.
7. Verify a real lifecycle/test event fires.
8. Verify durable state writes if persistence is claimed.
9. Verify a real effect/result receipt if effects are claimed.
10. Verify restart/re-entry if continuity is claimed.
11. If any required proof is missing, downgrade the result.

## 8. Final installation class

Return exactly one:

`NATIVE`

or

`ADAPTED`

or

`DEGRADED`

or

`BLOCKED`

Then state:

- exact repo path;
- exact authority file/version;
- exact adapter/files changed;
- exact tests fired;
- exact persistent write observed;
- exact effect/result receipt observed;
- missing capability, if any.

No receipt = no claim of real effect.

## 9. Current machine target

Do not install toward fixed GRID10 identity.

Current owner target:

`VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE`

GRID10 = benchmark configuration.

Rule:

`SIMULATE COGNITION; STORE DURABLE DATA.`

Global J-Space depth must never exceed the strongest interface actually exposed and causally evidenced.