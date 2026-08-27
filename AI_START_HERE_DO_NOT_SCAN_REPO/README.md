# AI: start here. Do not scan the whole repository.

Goal: enter Project Frankenstein / EntityOS + HCU with minimum tokens, no invented paths, and no stale authority.

## 1. Find the repository you actually have

Do not assume Downloads, `$HOME`, clone path, attachment mount, or current working directory.

Locate a root containing both:

```text
research_entity/
the artefact/
```

If only one is present, classify the install `DEGRADED` and stay source/read-only until layout is resolved.

Optional local read-only helper:

```bash
python AI_START_HERE_DO_NOT_SCAN_REPO/frankenstein_host_preflight.py
```

The helper does not probe network/providers/secrets. It reports what it can actually observe and leaves unavailable capabilities as `NOT_PROBED`.

## 2. Read authority before project prose

Read in this order:

```text
CLAY_EXECUTION_AUTHORITY.md
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
<the steering file named by SUPERVISOR_INBOX.json>
research_entity/continuity/BOOTSTRAP_MINIMAL.json
research_entity/rooms/PROGRAM_STATE.json
```

Then read task-relevant exact source/tests/receipts.

Never let old bootstrap text, chat memory, model consensus, historical plan text, `.claude/`, or an installer script outrank current authority.

## 3. Snapshot at this Trigger-3 re-entry

Observed canonical `main` when this AI layer was rebased:

```text
ed70385760c03a30dea7b6ecf8f6b78cbbaa584a
```

Current selected supervisor semantics remain 9.13 HARD_OFF:

```text
provider routes: NOT ADMITTED
Together: FORBIDDEN
paid fallback: FORBIDDEN
```

Important source evolution: `main` has now replaced the provider-capable Frankenstein Bauleiter/Bugfix entrypoints with a stdlib-only authority-gated HARD_OFF closure and preserves the old implementations as quarantined donor provenance. Its focused local validation is source/local-unit evidence only; provider/HCU/training/whole-product runtime credit remains zero.

Do not launch quarantined provider-backed donors.

## 4. Detect host capabilities before mapping behavior

Record only what is observed:

```text
can_read_files
can_write_files
can_run_local_commands
can_use_git
can_access_github
can_persist_state
can_call_external_network
can_install_packages
can_receive_hooks/events
```

Unknown means unknown. A method being available does not prove an effect happened.

## 5. Host routes

### Claude Code

Use the actual repository clone. Resolve current authority first. Keep repository SHA/source identity in receipts. Historical `.claude/` or Harness instructions do not override supervisor authority.

### Codex CLI

Open the real clone, resolve authority, inspect `git rev-parse HEAD` and dirty state, then work on bounded files. Do not promote local tests beyond their scope.

### Hermes Agent

Map its actual file/tool/state lifecycle to the same contract. If Git/current authority cannot be verified, use `DEGRADED` and make no current runtime claim.

### ChatGPT Web

Use connected GitHub state for current repository claims. Uploaded bootstrap files are caches. Source inspection is not local runtime evidence.

### Claude Web

Use connected repository tools when available. Without current Git access, classify `DEGRADED` and keep conclusions source/historical only.

### Grok Web

Same authority rule. No connected repo/tool evidence means no invented runtime or hook status.

### Generic fallback

For text-only hosts:

1. obtain/export the authority files above;
2. obtain exact current `main` SHA;
3. work source-only;
4. classify `DEGRADED`;
5. do not claim hooks, persistent state, runtime execution, provider calls, or real effects.

## 6. Installation outcome vocabulary

Use exactly one:

```text
NATIVE    = host directly supports the required lifecycle/tool/state behavior
ADAPTED   = equivalent behavior is provided through a documented adapter
DEGRADED  = a useful subset works and missing capabilities are explicit
BLOCKED   = a required authority/capability cannot be satisfied safely
```

A copied config, installed package, or exit code 0 is not enough for `NATIVE`.

## 7. Verify behavior, not file presence

Where the host claims these functions, verify them:

```text
hook/event really fired
state write really persisted
read-after-write returns the expected generation
request / causal identity survives the round trip
effect request is distinct from effect result
failure is visible
restart/re-entry preserves required state
```

Do not manufacture a positive result for a capability the host cannot expose.

## 8. Frankenstein authority check

Before any path that could reach providers, secrets, Aider or network:

1. resolve current canonical provider authority without importing provider machinery;
2. fail closed if authority is missing or ambiguous;
3. under HARD_OFF require zero provider calls, zero secret lookups, zero provider-network calls and zero Aider/fallback dispatch;
4. do not modify Frank's Harness to bypass the authority boundary;
5. keep provider-authored post-HARD_OFF changes quarantined from runtime credit until clean independent non-provider review/reexecution.

## 9. Navigation

Human explanation:

```text
HUMAN_READ_THIS/README.md
```

Technical/evidence map:

```text
DEV_SOURCE_RESEARCH/README.md
```

Current research authority/archive:

```text
research_entity/
```

Product workspace:

```text
the artefact/
```

Do not root-scan unless the task genuinely requires it.
