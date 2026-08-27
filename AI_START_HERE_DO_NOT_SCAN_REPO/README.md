# AI: start here. Do not scan repo root.

Short words. Exact order. Fail closed.

## 1. Find repo root

Do **not** assume Downloads, home, clone path, attachment path, or current directory.

Find the directory that contains this file and repository metadata. Call that `<REPO>`.

If you cannot resolve one exact repository root: **BLOCKED**.

## 2. Read authority first

Read, in order:

1. `<REPO>/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
2. the exact steering path selected by that inbox
3. `<REPO>/research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md`
4. `<REPO>/research_entity/topic_packets/frankenstein-master-cognition-concept/CURRENT_AUTHORITY_OVERRIDE_20260827.md`

Current expected state on 2026-08-27:

- supervisor/provider epoch: **9.13 HARD_OFF**
- external provider routes: **OFF**
- Together: **FORBIDDEN**
- paid fallback: **FORBIDDEN**
- 72h Frankenstein provider orchestration: **QUARANTINED / DO NOT RUN**
- non-provider local/sandbox validation: allowed only inside current authority boundaries.

If current files disagree with this page, current authority files win.

If authority cannot be resolved: **BLOCKED**.

## 3. Do not run these now

Do not run provider-calling paths in:

- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1.py`
- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_bugfix_v1.py`
- the provider/Together parts of `BUILD_ORCHESTRATION_PLAN_20260827.json`

Do not read provider secrets “just to test.”

Do not import/call a provider before authority check.

Do not modify Frank's Harness to bypass the gate.

## 4. Read only the small map

Now read:

1. `<REPO>/HUMAN_READ_THIS/README.md`
2. `<REPO>/DEV_SOURCE_RESEARCH/README.md`
3. `<REPO>/DEV_SOURCE_RESEARCH/repository/TRIGGERWORD3_REPOSITORY_MIGRATION_MANIFEST_2026-08-27.json`

Only then open task-specific files.

Do not crawl the whole repository unless the task truly needs it.

## 5. Detect host capability

Detect what this host can really do. Do not invent hooks.

Check for these classes:

- shell / files
- Git read
- Git write
- process execution
- persistent local state
- lifecycle hooks / startup hooks
- tool-result receipts
- network access
- user approval boundary

Record only observed capability.

## 6. Map the host

Use one route only.

### Claude Code

Use native repository files, Git, shell, and project instructions if available. Keep current authority files above convenience prompts.

Result:
- `NATIVE` if real hooks/state/tool receipts required by the task are observed;
- `ADAPTED` if equivalent behavior is implemented with available local mechanisms;
- `DEGRADED` if only partial continuity/state/effect verification exists;
- `BLOCKED` if required authority/capability is missing.

### Codex CLI

Use repository instructions + Git + shell if actually available. Verify any persistence/hook behavior; do not assume it from product name.

Same result classes: `NATIVE | ADAPTED | DEGRADED | BLOCKED`.

### Hermes Agent

First inspect the actual installed tool/lifecycle/state API. Map only capabilities that exist. No guessed plugin/hook names.

Same result classes.

### ChatGPT Web

Use connected repository/file tools when available. Web chat alone is not a local daemon and cannot be called “native” if lifecycle hooks or persistent local execution are absent.

Usually `ADAPTED` or `DEGRADED` unless the exact required capability is exposed and verified.

### Claude Web

Use connected project/repository surfaces if present. Do not claim local hooks/process control from browser chat alone.

Usually `ADAPTED` or `DEGRADED` unless verified otherwise.

### Grok Web

Same rule: inspect actual connected capabilities first. Browser chat does not imply local lifecycle/process/state hooks.

### Generic fallback

If the host can only read files and answer text:

1. read authority;
2. read the two small maps;
3. edit/generate artifacts only if the host can write safely;
4. never fake runtime verification;
5. report `DEGRADED` or `BLOCKED`.

## 7. Install/adapt in this order

1. Resolve `<REPO>`.
2. Resolve current authority.
3. Identify exact host capabilities.
4. Choose `NATIVE`, `ADAPTED`, `DEGRADED`, or `BLOCKED` target.
5. Bind state path dynamically under `<REPO>` or an explicitly supplied host state directory. Never assume `$HOME`.
6. Bind task-specific source paths.
7. Add the smallest host adapter needed.
8. Verify the adapter fires for a real test event.
9. Verify durable state really changes when expected.
10. Verify a tool/effect result produces a real receipt/result that can be read back.
11. Verify restart/re-entry if continuity is claimed.
12. If any required proof is missing, downgrade the result. Never fake success.

## 8. Success report

Return exactly one installation class:

`NATIVE`

or

`ADAPTED`

or

`DEGRADED`

or

`BLOCKED`

Then give:

- exact repo path used;
- exact authority file + version used;
- exact adapter/files changed;
- exact tests fired;
- exact persistent state write observed;
- exact effect/result receipt observed;
- missing capability, if any.

No real receipt = no claim of real effect.

## 9. Current machine target

Do not install toward a fixed GRID10 identity.

Current owner target:

`VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE`

GRID10 is a benchmark configuration.

Rule:

`SIMULATE COGNITION; STORE DURABLE DATA.`

Global J-Space depth must never exceed the strongest interface actually exposed and causally evidenced.