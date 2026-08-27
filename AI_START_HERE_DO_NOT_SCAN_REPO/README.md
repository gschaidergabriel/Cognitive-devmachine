# AI START HERE — DO NOT SCAN THE REPO

Use little context. Discover first. Do not guess paths.

## 0. Find the repo

If you have a shell:

```sh
ROOT="$(git rev-parse --show-toplevel 2>/dev/null || true)"
[ -n "$ROOT" ] || { echo "BLOCKED: not inside a git checkout"; exit 2; }
printf '%s\n' "$ROOT"
```

Never assume Downloads, `$HOME`, Desktop, clone path, attachment mount, or current working directory.

If you do **not** have a shell, use the repository/file attachment the host actually exposes. Do not invent a filesystem path.

## 1. Read only these first

Relative to real repo root:

```text
AI_START_HERE_DO_NOT_SCAN_REPO/README.md
CLAY_EXECUTION_AUTHORITY.md
research_entity/continuity/BOOTSTRAP_MINIMAL.json
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
research_entity/claycode/autonomous/FREE_PROVIDER_ADMISSION.json
HUMAN_READ_THIS/README.md
DEV_SOURCE_RESEARCH/README.md
```

Then read only task-relevant source/tests/receipts.

## 2. Identify capability

Answer these with observed capability, not guesses:

```text
CAN_READ_FILES: yes/no
CAN_WRITE_FILES: yes/no
CAN_RUN_SHELL: yes/no
CAN_RUN_TESTS: yes/no
CAN_USE_GIT: yes/no
CAN_PUSH_GIT: yes/no
CAN_CALL_EXTERNAL_NETWORK: yes/no
CAN_SCHEDULE/LIFECYCLE_HOOKS: yes/no
CAN_PERSIST_STATE: yes/no
CAN_OBSERVE_EFFECT_RESULT: yes/no
```

External network capability is not provider execution authority. Current canonical provider admission can still say HARD_OFF.

## 3. Resolve current authority

Order:

1. newest explicit owner authority;
2. current `SUPERVISOR_INBOX.json` selected steering;
3. current bootstrap/program state;
4. exact executable evidence.

Do not trust old chat memory over current source.

At the Trigger-3 branch creation point on 2026-08-27, provider admission is HARD_OFF and Together is forbidden. Re-read current files every time; do not hardcode that state forever.

## 4. Pick host route

### Claude Code

Open the actual checkout. Read this file first. Use native file/shell/git tools. Do not install another agent layer unless a missing capability requires adaptation.

### Codex CLI

Start inside the actual checkout. Resolve repo root with Git. Read this file first. Use native shell/tests/git. Keep current authority checks before provider/network actions.

### Hermes Agent

Give Hermes this file as the first repository contract. Map its real file/shell/state tools to the capability list above. If durable hook/state support is absent, mark that feature `DEGRADED`; do not fake persistence.

### ChatGPT Web

Use connected GitHub/repository tools if available. Read exact current files before claims/writes. A web chat cannot be treated as a daemon or background process unless an actual supported lifecycle/scheduling tool exists.

### Claude Web

Attach or connect the repository, then provide this file first. If the host cannot execute tests or Git writes, research/documentation may continue but installation status cannot be `NATIVE` for those capabilities.

### Grok Web

Attach/connect current source and begin from this file. Detect real tools. Do not infer shell, hooks or durable state from conversational ability.

### Generic fallback

Provide this file plus the six current authority/index files named above. Ask the host to fill the capability block. Continue only with operations the block supports.

## 5. Install/adapt only after detection

Use the smallest mapping possible:

```text
file read      -> host native file/repo reader
file write     -> host native write/patch tool
shell/test     -> host native sandbox/terminal
state          -> existing canonical project state interface; never create a competing truth DB
hooks          -> host native lifecycle hooks only when real
external effect-> deterministic project effect boundary + observed result receipt
```

Do not create a second canonical database, second persistent entity, or second effect path.

## 6. Verify real behavior

A setup is not installed because files exist.

Prove, where the host supports it:

1. **Hook fires:** trigger the real lifecycle event and capture evidence.
2. **State persists:** write a harmless typed test record through the admitted state path; reopen/re-read it.
3. **Effect receipt exists:** for an authorized harmless effect, prove request -> effect gate -> observed result/receipt.
4. **Restart/re-entry works:** restart the host/session if supported and show the state can be re-entered without conversational memory.
5. **Failure is honest:** remove/deny one capability and prove the adapter reports failure instead of fake success.

Current provider HARD_OFF tests must prove the caller stops before provider import, secret lookup, network or Aider dispatch.

## 7. Final status word

End installation/adaptation with exactly one of:

- `NATIVE` — host provides required capabilities directly and verification passed.
- `ADAPTED` — a small verified adapter maps host capabilities to the project contract.
- `DEGRADED` — useful subset works; missing capabilities are named.
- `BLOCKED` — a required capability/authority cannot be satisfied safely.

Never call a source-only setup `NATIVE` if hooks, state writes, tests or effect receipts were not actually observed.
