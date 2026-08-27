# AI: START HERE. DO NOT SCAN THE REPO.

Small words on purpose.

Do not crawl this repository to “understand everything.” Start here, detect what your host can really do, then read only the files needed for the task.

## Rule 0

**Do not guess paths.**

Do not assume:

- `~/Downloads`
- a home directory layout
- the clone is called `clay-global-research-entity`
- the attachment is mounted under `/mnt/data`
- your current working directory is the repo
- Git is available
- hooks exist
- you can write files
- you can run shell commands
- you can call external models/providers

Find out first.

## Rule 1 — find the repo you actually have

If you have shell + Git, use the repository itself as the locator:

```sh
REPO="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
printf '%s\n' "$REPO"
```

If that fails, **do not invent a location**. Ask the host/user for the mounted/checked-out repository path or use the host's file-picker/project attachment UI.

From then on, build paths from `$REPO`:

```sh
HUMAN="$REPO/HUMAN_READ_THIS/README.md"
DEV="$REPO/DEV_SOURCE_RESEARCH/README.md"
AI="$REPO/AI_START_HERE_DO_NOT_SCAN_REPO/README.md"
AUTH="$REPO/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json"
```

## Rule 2 — read four small things, not the whole tree

Read in this order:

1. this file;
2. `HUMAN_READ_THIS/README.md`;
3. `DEV_SOURCE_RESEARCH/README.md`;
4. `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`.

Then read only task-relevant source/evidence linked by the developer index.

The fast bootstrap/project prompt may help continuity, but it is not canonical truth when newer Git authority exists.

## Rule 3 — detect capabilities before mapping features

Record true/false for:

```text
can_read_files
can_write_files
can_run_shell
can_run_python
can_use_git
can_create_branch
can_commit
can_open_pull_request
has_lifecycle_hooks
can_verify_hook_firing
has_durable_local_state
can_observe_tool_results
can_observe_effect_results
can_access_current_git_remote
can_access_external_provider
```

**Current repository authority at the Trigger-3 snapshot says external provider routes are not admitted and Together is forbidden.** Host capability does not override repository authority.

## Result words

Every install/adaptation ends with exactly one of these meanings:

- `NATIVE` — host directly supports the needed lifecycle/tool/state features and they were verified.
- `ADAPTED` — host lacks a native feature but a tested adapter provides the required behavior.
- `DEGRADED` — useful subset works; important lifecycle/state/effect features are missing.
- `BLOCKED` — required capability or authority is absent; do not fake success.

Source files existing is not enough for `NATIVE` or `ADAPTED`.

## Claude Code

Repository evidence includes:

- `.claude/settings.json`
- `.claude/hooks/rae_hook.py`

That makes Claude Code a **native-candidate**, not an automatic `NATIVE` result.

Do:

1. find `$REPO` dynamically;
2. inspect the host's current hook capability;
3. inspect `.claude/settings.json` and the referenced hook path;
4. run a harmless lifecycle event allowed by current host/repo policy;
5. verify the hook actually fired;
6. verify the expected durable state write/receipt;
7. verify restart/re-entry can read it;
8. only then mark `NATIVE` or `ADAPTED`.

If hooks cannot be observed, result is `DEGRADED`, not “probably installed.”

## Codex CLI

Do not assume Claude hook semantics map to Codex.

Do:

1. find `$REPO` dynamically;
2. detect filesystem, shell, Git, write, and lifecycle capabilities exposed by the installed Codex version;
3. read this installer + Dev front door + current supervisor inbox;
4. map only capabilities that actually exist;
5. use repository files/commits as durable state where appropriate;
6. verify a harmless read -> bounded write on a branch -> read-back cycle if writes are authorized;
7. verify tool/result receipts the host exposes.

If no lifecycle hook exists, use explicit start/end re-entry steps and mark `ADAPTED` or `DEGRADED` according to what was actually verified.

## Hermes Agent

Hermes versions/integrations can differ. Do not assume a plugin API.

Do:

1. detect filesystem/shell/Git/lifecycle/memory/tool-result capabilities;
2. map repository re-entry to the capabilities found;
3. keep canonical project truth in the repository, not in an opaque agent memory;
4. test a harmless state write and restart/re-read if the host supports it;
5. record `NATIVE`, `ADAPTED`, `DEGRADED`, or `BLOCKED` from observation.

If Hermes cannot expose durable write/read or result receipts, it can still help with analysis, but that is a degraded integration.

## ChatGPT Web

Web chat normally does not equal a local lifecycle-hook/runtime host.

Do:

1. use the connected GitHub/project files if available;
2. read this file + Dev index + current supervisor inbox;
3. use connected Git actions only when explicitly available and authorized;
4. preserve exact branch/SHA/path identities in outputs;
5. never claim a local hook fired unless a real tool showed it;
6. never claim background execution.

Without a durable host hook, classify this as `DEGRADED` for native lifecycle installation, even if repository read/write through a connector is strong.

## Claude Web

Use the same discipline as ChatGPT Web:

- connected repository/files if actually available;
- no invented local filesystem;
- no invented hooks;
- no opaque chat memory as canonical state;
- exact source/commit identities;
- explicit re-entry from current repository state.

Typical result for lifecycle integration is `DEGRADED` unless the host exposes and verifies stronger connected capabilities.

## Grok Web

Again, do not simulate a local agent host in prose.

If only web-chat/file context exists:

- use the curated entry files;
- keep state/evidence in the repository or user-provided artifacts;
- manually re-enter current authority each session;
- classify lifecycle integration as `DEGRADED`.

If a real connector/runtime is present, detect and test it before upgrading the status.

## Generic fallback

For any other AI host:

```text
FIND REPO
READ AI ENTRY
READ HUMAN ENTRY
READ DEV ENTRY
READ CURRENT SUPERVISOR INBOX
DETECT REAL CAPABILITIES
MAP ONLY WHAT EXISTS
TEST HARMLESS READ/WRITE/READ-BACK IF AUTHORIZED
TEST HOOK FIRING IF HOOKS EXIST
TEST DURABLE RE-ENTRY
TEST RESULT RECEIPTS
CLASSIFY NATIVE / ADAPTED / DEGRADED / BLOCKED
```

No root scan required.

## Minimum re-entry capsule

If the host cannot keep lifecycle state automatically, carry only this compact record:

```text
repo: <owner/name or local resolved root>
branch: <branch>
canonical_main: <sha observed at re-entry>
current_authority: <exact supervisor/owner file + digest/sha if available>
task: <one sentence>
completed: <paths/commits>
evidence_scope: <source/local-test/runtime/etc>
blocked: <exact missing capability/authority>
next_exact_action: <one action>
```

Then refresh `main` before claiming current state.

## Safe verification test

A host integration is not proven by installation output. Verify behavior.

For a repository-write-capable host, a safe pattern is:

1. create a dedicated test branch from an exact SHA;
2. write a tiny non-authoritative test receipt under an allowed test path;
3. read it back;
4. confirm the exact commit contains it;
5. restart/re-enter the host if lifecycle persistence is being claimed;
6. confirm the host can resolve the same receipt from repository truth;
7. clean up/close the test lane if project policy requires it.

Do not test external-provider execution while current authority says HARD_OFF.

## Effect/result verification

If a host can request real effects, verify separately:

```text
request created
!=
request admitted
!=
effect executed
!=
outcome known
!=
outcome verified
```

An unknown network/tool outcome stays UNKNOWN until checked. Never replay an irreversible request just because the chat/tool transport returned an error.

## Current hard stop

At this Trigger-3 snapshot, repository authority says:

- external provider routes are not admitted;
- Together is forbidden;
- zero paid fallback;
- Frankenstein 72-hour provider orchestration is quarantined/non-operative;
- local non-provider source/test work is allowed within current authority.

So an installer that “helpfully” enables NVIDIA/Groq/Mistral/Together provider loops has failed the install contract.

Correct result: `BLOCKED` for that capability until authority changes and the caller boundary is re-verified.

## Done means verified

A useful final install receipt looks like:

```text
HOST: <actual host/version if observable>
REPO: <actual repo identity>
SHA: <exact re-entry SHA>
FILES: PASS/FAIL
WRITE: PASS/FAIL/NOT_AVAILABLE
HOOK: PASS/FAIL/NOT_AVAILABLE
DURABLE_STATE: PASS/FAIL/NOT_AVAILABLE
RESULT_RECEIPT: PASS/FAIL/NOT_AVAILABLE
EXTERNAL_PROVIDER: BLOCKED_BY_CURRENT_AUTHORITY
CLASSIFICATION: NATIVE|ADAPTED|DEGRADED|BLOCKED
NOTES: <bounded evidence, no hype>
```

If you cannot fill a field from observation, write `NOT_AVAILABLE` or `UNKNOWN`. That is better than a fake green check.