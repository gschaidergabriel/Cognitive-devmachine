# AI INSTALLER — DO NOT SCAN THE REPO

Use this file when an AI/agent/tool needs to join the project.

Short words. Exact order. No fake success.

## Rule 0

Do **not** guess where the repo is.

Do **not** assume:

- Downloads;
- home folder;
- current working folder;
- clone folder;
- attachment mount.

Start from **this file**.

The repo root is the parent that contains the project sentinels.

## Rule 1 — run the detector if you have Python

From the directory containing this file:

```sh
python3 detect_install.py
```

If local file writes are allowed:

```sh
python3 detect_install.py --probe-write
```

The detector:

- does not scan the whole repo;
- does not use the network;
- does not read provider secrets;
- does not test provider keys;
- finds the repo from this file;
- checks a tiny known file set;
- checks Claude/Codex/Hermes CLI names if visible;
- can prove a bounded local write + fsync + reopen + delete;
- never says `NATIVE` by itself.

Read the JSON result.

## Rule 2 — read only these files first

Resolve the repo root as `<ROOT>`.

Read, in this order:

```text
<ROOT>/AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json
<ROOT>/CLAY_EXECUTION_AUTHORITY.md
<ROOT>/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
<ROOT>/HUMAN_READ_THIS/START_HERE.md
<ROOT>/DEV_SOURCE_RESEARCH/README.md
```

Stop.

Do not scan the rest of the repo unless your task needs a named source.

## Rule 3 — current authority beats old instructions

Before a real external provider call or real world effect:

1. read current owner authority;
2. read current supervisor inbox;
3. obey the newest applicable authority;
4. fail closed if they are ambiguous.

At the Trigger-3 re-entry that created this installer, supervisor `9.13` had:

```text
external provider routes: HARD OFF
Together: forbidden
paid fallback: forbidden
FreeSwarm emergency stop: true
```

That state can change. Re-read it. Do not copy it forever.

Do not probe keys just to see if they work.

## Result words

Use exactly one:

### NATIVE

Use only if the host really supports the integration **and** you observed the host path fire.

Need real evidence for the declared lifecycle/state/effect path.

A CLI existing is not enough.

A config file existing is not enough.

### ADAPTED

The host can work with the repo, but an adapter supplies part of the lifecycle/state/effect path.

### DEGRADED

The host can read/use context, but durable hooks/state/effect proof is missing.

### BLOCKED

The host cannot safely access the minimum project material or cannot establish the required path.

## Claude Code route

Use when the detector finds `claude` or the user says this is Claude Code.

1. Find `<ROOT>` from this installer. Do not use `$HOME` as the repo guess.
2. Read the five minimum files above.
3. Check whether `<ROOT>/CLAUDE.md` exists.
4. Check whether `<ROOT>/.claude/` exists.
5. Do **not** claim those files were loaded merely because they exist.
6. If Claude Code exposes a real project lifecycle hook, wire a bounded probe through that actual hook.
7. Make the hook write a small receipt to an allowed project state location.
8. Reopen the receipt from a fresh process/context.
9. For any allowed effect test, record request + observed result + outcome identity.
10. If the real hook fired and state/effect receipts verify: `NATIVE`.
11. If project instructions + filesystem/tool work are verified but hook semantics need an adapter: `ADAPTED`.
12. If only context works: `DEGRADED`.

Do not change Frank’s own Harness merely to make an installer test pass.

## Codex CLI route

Use when the detector finds `codex` or the user says this is Codex CLI.

1. Find `<ROOT>` from this installer.
2. Read the five minimum files.
3. Check `<ROOT>/AGENTS.md`.
4. Do not claim Codex loaded it until observed behavior/source proves that path.
5. If Codex exposes a real lifecycle/project hook, test the hook with a bounded receipt.
6. Reopen durable state.
7. Verify any allowed effect from its actual result, not from the request.
8. Real host-native hook + state/effect proof: `NATIVE`.
9. Adapter needed but useful filesystem/tool integration works: `ADAPTED`.
10. Context only: `DEGRADED`.

## Hermes Agent route

Use when the detector finds one of:

```text
hermes
hermes-agent
hermes_agent
```

1. Find `<ROOT>` from this installer.
2. Read the five minimum files.
3. Ask the installed Hermes runtime itself for its supported project/lifecycle/tool surfaces if that can be done locally without external provider execution.
4. Do not invent a hook name.
5. Map only real capabilities.
6. Install a bounded adapter only if needed.
7. Verify state write by reopen.
8. Verify effect by observed result/receipt.
9. Classify `NATIVE`, `ADAPTED`, `DEGRADED`, or `BLOCKED`.

If Hermes itself requires a provider call to discover capabilities while provider authority is HARD OFF, stop before that call and classify the provider-dependent part `BLOCKED`.

## ChatGPT Web route

There may be no local filesystem or lifecycle hook.

1. Use the connected repository/file source if available.
2. Read the five minimum files by exact path.
3. Do not ask ChatGPT to “scan the repo”.
4. Use exact named files for the task.
5. If no runtime bridge exists, do not claim local hooks/state/effects.
6. Default classification: `DEGRADED`.
7. If an authorized connected tool really writes/reads state or performs effects, verify those receipts separately. Only then upgrade the relevant capability.

A chat answer is not an effect receipt.

## Claude Web route

1. Use a connected project/repository/file source if available.
2. Read the five minimum files.
3. Use named files only.
4. No local hook claim unless a real connected runtime proves it.
5. Default without such a runtime: `DEGRADED`.

## Grok Web route

1. Use a connected repository/file source if available.
2. Read the five minimum files.
3. Do not invent shell/filesystem hooks.
4. Default without a verified runtime bridge: `DEGRADED`.

## Generic agent route

Unknown host? Capability first.

Check only:

```text
CAN_READ_FILES?
CAN_WRITE_FILES?
CAN_RUN_LOCAL_PROCESS?
CAN_USE_GIT_READ?
CAN_USE_GIT_WRITE?
HAS_PROJECT_INSTRUCTION_SURFACE?
HAS_REAL_LIFECYCLE_HOOK?
HAS_DURABLE_STATE?
CAN_EXECUTE_ALLOWED_EFFECT?
CAN_OBSERVE_EFFECT_RESULT?
```

Then map the project to what exists.

Do not rename a missing capability into existence.

If the host only accepts pasted text: `DEGRADED`.

If it cannot even access the minimum files: `BLOCKED`.

## Hook proof rule

A hook receipt only counts if the **host invoked the probe through the actual declared lifecycle hook**.

Running the probe by hand does not prove the hook.

Use a receipt shape like:

```json
{
  "schema": "FRANKENSTEIN_HOST_HOOK_RECEIPT/v1",
  "host": "<detected host>",
  "hook": "<real host hook name>",
  "event_id": "<host/runtime event id if exposed>",
  "observed_time": "<timestamp>",
  "repo_root_digest_or_identity": "<bounded identity>",
  "proof_scope": "HOOK_FIRED_ONLY"
}
```

Do not put secrets in it.

## State proof rule

Need:

```text
write
-> fsync/commit when applicable
-> close
-> fresh reopen
-> exact readback
```

A successful write function return is weaker than reopen proof.

## Effect proof rule

Need:

```text
request identity
-> gate decision
-> effect attempt
-> observed result
-> outcome = VERIFIED_SUCCESS | VERIFIED_FAILURE | UNKNOWN
```

If transport dies after submit and result is unknown:

```text
UNKNOWN
```

Do not blindly replay.

## Finish

Write one install result:

```text
HOST: <name>
RESULT: NATIVE | ADAPTED | DEGRADED | BLOCKED
REPO: <dynamic resolved root or connector identity>
INSTRUCTIONS: VERIFIED | UNVERIFIED
LIFECYCLE_HOOK: VERIFIED | UNVERIFIED | NOT_AVAILABLE
DURABLE_STATE: VERIFIED | UNVERIFIED | NOT_AVAILABLE
EFFECT_RECEIPT: VERIFIED | UNVERIFIED | NOT_AVAILABLE
AUTHORITY_READ: YES | NO
NOTES: <short exact limits>
```

No green badge without evidence.
