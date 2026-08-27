# AI START HERE — DO NOT SCAN THE REPO

Short version: **find repo → read current authority → detect your tools → use the smallest supported adapter → verify real writes/results → report NATIVE / ADAPTED / DEGRADED / BLOCKED.**

This folder is an installer/re-entry map. It is **not** canonical authority.

## 0. Do not guess paths

If you have a terminal inside a Git checkout:

```sh
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 2
printf '%s\n' "$ROOT"
```

If that fails, you are not in a verified Git checkout. Do **not** guess `~/Downloads`, `$HOME/project`, a mount path, or the current directory.

If you received a ZIP/attachment, first use your host's file/attachment listing feature to locate it. Do not invent a path.

## 1. Read only this boot set first

From a verified repo root:

```text
AI_START_HERE_DO_NOT_SCAN_REPO/README.md
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
research_entity/continuity/BOOTSTRAP_MINIMAL.json
research_entity/rooms/PROGRAM_STATE.json
```

Then read **the steering file named by `SUPERVISOR_INBOX.json`** and any current explicit owner authority it points to or that outranks it.

Why: cached bootstrap/program files can be stale. At the 2026-08-27 trigger-3 snapshot, `SUPERVISOR_INBOX.json` was already on provider authority epoch 9.13 HARD_OFF while lower current-facing files still carried 8.78 pointers.

## 2. Current fail-closed rule

At this snapshot:

```text
provider authority: 9.13 HARD_OFF
external provider routes: false
Together: forbidden
paid fallback: forbidden
Frankenstein 72h provider loops: quarantined / non-operative
```

Do not turn an old plan, API key, provider import, successful auth, or model availability into authority.

## 3. Detect what your host can actually do

You need four capability classes:

```text
READ_FILES
WRITE_FILES
RUN_COMMANDS
PERSIST_STATE
```

Optional:

```text
GIT_READ
GIT_WRITE
HOOKS_OR_LIFECYCLE
NETWORK
```

Never fake a capability. If you cannot run commands, do not claim runtime verification. If you cannot persist state, do not claim durable memory installation.

## 4. Host routes

### Claude Code

Expected route: local repo + terminal + file edits + Git.

1. Resolve `ROOT` with `git rev-parse`.
2. Read the boot set above.
3. Read current source before edits.
4. Use repo-local files/state only unless current authority explicitly admits another surface.
5. Run the smallest relevant non-provider test.
6. Verify `git diff`, exact source identity, stdout/stderr and durable writes.
7. Result label:
   - `NATIVE` if file/command/Git/state lifecycle all work;
   - `ADAPTED` if one lifecycle feature needs a small repo-local wrapper;
   - `DEGRADED` if runtime or durable-state verification is unavailable;
   - `BLOCKED` if required authority/capability is absent.

### Codex CLI

Same local route as Claude Code. Do not special-case product identity.

1. Resolve actual Git root.
2. Read current inbox-selected authority.
3. Inspect exact target source/tests.
4. Edit on an isolated branch when appropriate.
5. Run bounded non-provider tests.
6. Verify diff + test output + Git identity.
7. Emit one of `NATIVE / ADAPTED / DEGRADED / BLOCKED`.

### Hermes Agent

Use only capabilities actually exposed by the Hermes installation.

- If it has filesystem + shell + durable workspace: follow the local CLI route.
- If it has filesystem but no shell: `DEGRADED` for runtime claims.
- If it has shell but no durable state: `DEGRADED` for persistent-memory installation.
- If it cannot read the canonical repo/attachments: `BLOCKED`.

Do not assume a particular Hermes plugin path or home directory.

### ChatGPT Web

ChatGPT Web is normally not a native local lifecycle host.

- If GitHub/Drive/files are connected, read current canonical sources through those connectors.
- If a file is uploaded, treat it as source material, not automatically current truth.
- Use available connected write tools only when they really exist and preserve exact repository identity.
- Do not claim local hook firing or shell runtime if no shell surface was used.

Typical result: `ADAPTED` for connected repo/file work, `DEGRADED` for host-lifecycle installation, `BLOCKED` if the required repo/source is inaccessible.

### Claude Web

Same principle as ChatGPT Web:

- use explicit connected repository/files if available;
- do not invent local paths;
- do not claim command/hook/runtime evidence without an actual execution surface;
- preserve current authority ordering.

Typical result: `ADAPTED` or `DEGRADED`, depending on connector/write/runtime support.

### Grok Web

Treat as a web host unless it exposes verified repo/file/runtime capabilities.

- source access only -> research/review adapter;
- source + durable write -> adapted authoring route;
- no shell -> no runtime proof;
- no current authority read -> `BLOCKED` for material current-state claims.

### Generic fallback

Ask the host itself only for its **observable capabilities**, not for a self-description of competence:

```text
Can you read this exact file?
Can you write a file and read it back?
Can you run a command and return stdout/stderr + exit code?
Can you persist state across a fresh invocation?
Can you show exact Git branch/commit identity?
```

Map observed results to the capability classes. Then choose the smallest route that works.

## 5. Installation result contract

Every installer/adaptation attempt must end with exactly one functional classification:

```text
NATIVE
ADAPTED
DEGRADED
BLOCKED
```

Definitions:

- `NATIVE`: host provides the required lifecycle/tool/state primitives directly and verification passed.
- `ADAPTED`: a bounded adapter maps host primitives to the project contract; verification passed.
- `DEGRADED`: useful subset works but at least one required lifecycle/runtime/persistence property is absent.
- `BLOCKED`: required authority, source, permission, or capability is unavailable.

Never convert "I wrote a setup file" into `NATIVE`.

## 6. What real verification means

### Hook/lifecycle

If an adapter claims a hook:

1. create a unique test event;
2. trigger the real lifecycle;
3. observe the hook receipt;
4. bind receipt to event ID + source version;
5. repeat once with a different event;
6. verify no duplicate/unexpected firing.

No observed firing -> no hook credit.

### Durable state

1. write a unique typed state value;
2. close/restart the relevant process/session when possible;
3. read it through the normal retrieval path;
4. verify value + provenance + generation;
5. verify stale/wrong-generation input fails closed where required.

A variable still present in the same process is not durable-state proof.

### Effect/result receipt

1. create a typed effect request;
2. pass deterministic authority gate;
3. observe the actual effect/result surface;
4. write EffectJournal/result receipt;
5. re-enter the observed outcome into canonical state;
6. prove replay/idempotence behavior where relevant.

Request != effect.

## 7. Frankenstein-specific quarantine

Do **not** launch these current source files as provider-calling long-running workers under 9.13 HARD_OFF:

```text
research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1.py
research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_bugfix_v1.py
```

Their non-network scheduling/rollback logic may be inspected/tested on an admitted non-provider surface, but current supervisor steering says the real external caller boundary must be gated before secret lookup/provider import/network/Aider/fallback dispatch.

Do not "fix" this by modifying Frank's own Harness unless newer explicit authority says so.

## 8. Human/research maps

After authority resolution:

```text
HUMAN_READ_THIS/README.md
DEV_SOURCE_RESEARCH/README.md
DEV_SOURCE_RESEARCH/FRANKENSTEIN_RESEARCH_CHRONICLE.md
DEV_SOURCE_RESEARCH/EVIDENCE_INDEX.json
```

These are fast navigation aids. When they disagree with current canonical source, **current canonical source wins**.

## 9. Minimal completion receipt

Use this shape for an installation/adaptation result:

```json
{
  "schema": "FRANKENSTEIN_HOST_ADAPTATION_RECEIPT/v1",
  "classification": "NATIVE|ADAPTED|DEGRADED|BLOCKED",
  "repo_root": "<observed or null>",
  "git_head": "<observed or null>",
  "authority_file": "<exact inbox-selected path>",
  "capabilities": {
    "read_files": true,
    "write_files": false,
    "run_commands": false,
    "persist_state": false,
    "git_read": true,
    "git_write": false,
    "hooks_or_lifecycle": false
  },
  "verified": [],
  "blocked": [],
  "runtime_credit_scope": "NONE_OR_EXACT_SCOPE_ONLY"
}
```

Caveman rule: **see it, bind it, test it, then claim it.**
