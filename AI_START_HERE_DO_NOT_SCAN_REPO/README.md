# AI START HERE. DO NOT SCAN THE REPO.

Small steps. No guessing.

Machine-readable contract: `AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json`.  
Read-only discovery helper: `AI_START_HERE_DO_NOT_SCAN_REPO/detect_install_mode.sh`.

The helper is **discovery only**. It deliberately leaves lifecycle hook, durable state and effect receipt `UNVERIFIED`; it cannot mint an installation PASS by itself.

## 1. Find the repo you actually have

Do **not** assume Downloads. Do **not** assume home. Do **not** assume current directory.

If you have a shell:

```bash
pwd
git rev-parse --show-toplevel 2>/dev/null || true
```

If that prints a repo root, set it dynamically:

```bash
REPO="$(git rev-parse --show-toplevel)"
printf '%s\n' "$REPO"
```

If it prints nothing: you do not have a verified checkout yet. Use your host's real repository/connector checkout mechanism. Do not invent a path.

## 2. Read only these first

From the verified repo root:

```text
AI_START_HERE_DO_NOT_SCAN_REPO/INSTALL_CONTRACT.json
CLAY_EXECUTION_AUTHORITY.md
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
research_entity/global/OWNER_CORRECTION_ZERO_ENTITYOS_COGNITIVE_GRID_DB_CLAUDECODE_GLOBAL_JSPACE_2026-08-25.md
research_entity/continuity/BOOTSTRAP_MINIMAL.json
AI_START_HERE_DO_NOT_SCAN_REPO/README.md
```

Then read the steering file named by `SUPERVISOR_INBOX.json`.

For Frankenstein work also read:

```text
research_entity/topic_packets/frankenstein-master-cognition-concept/TRIGGERWORD3_HARD_OFF_CLOSURE_20260827_GPT56SOL.json
research_entity/topic_packets/frankenstein-master-cognition-concept/CONCEPT.md
```

Do not treat old plan text as newer authority. If fixed GRID10/HCU wording conflicts with the newest explicit owner correction, the owner correction wins.

## 3. Current expected provider result

At the 2026-08-27 Trigger-3 authority snapshot:

```text
providers: HARD_OFF
together: FORBIDDEN
paid fallback: FORBIDDEN
```

So a provider-capable Frankenstein launch is expected to **BLOCK before provider import, secret lookup, network, Aider, or fallback dispatch**.

That is correct behavior, not installation failure.

## 4. Current machine target

Do **not** install toward a fixed GRID10 identity.

Current explicit owner target:

```text
VARIABLE COGNITIVE GRID + PERSISTENT DATABASE + CLAUDE CODE
```

Rules:

```text
N = runtime parameter
GRID10 = benchmark/configuration
SIMULATE COGNITION; STORE DURABLE DATA
Claude Code = strong model/tool/code partner
```

The small-model grid distributes/simulates cognitive processes. Durable exact state belongs in the persistent database where deterministic storage is better. Claude Code is not replaced by the ~0.8B grid.

Global J-Space depth must never exceed the strongest interface actually exposed and causally evidenced. Do not invent activation access to Claude Code from a text/tool/session interface.

## 5. Detect what this host can really do

Check capabilities. Do not infer them from product name.

If a shell is available, the bounded helper can collect only local discovery facts:

```bash
bash "$REPO/AI_START_HERE_DO_NOT_SCAN_REPO/detect_install_mode.sh" "$REPO"
```

It performs no provider test, network test or secret lookup and does not itself classify the installation.

Required capability questions:

```text
filesystem read?       yes/no
filesystem write?      yes/no
git read?               yes/no
git write?              yes/no
python?                 yes/no
persistent local state? yes/no
lifecycle hooks?        yes/no/unknown
real effect execution?  yes/no/unknown
```

Unknown means unknown.

## 6. Result words

Every installation/integration route ends with exactly one of these meanings:

- `NATIVE` — host has the needed lifecycle/tool/state capabilities directly and they were verified.
- `ADAPTED` — equivalent behavior is mapped through a different verified host mechanism.
- `DEGRADED` — useful subset works; missing capabilities are named.
- `BLOCKED` — required capability/authority is absent or explicitly denied.

Never write `NATIVE` because a config file exists, a model says so, or a boolean flag says a hook was observed. Verify real firing/state/effect receipts produced or independently verified by the claimed mechanism.

## 7. Claude Code route

If Claude Code has a real shell + repo checkout:

1. locate repo dynamically with `git rev-parse --show-toplevel`;
2. read authority and owner-target files above;
3. inspect current Frankenstein gate/entrypoint files;
4. run only tests/actions allowed by current authority;
5. if adding hooks, prove the hook actually fires with a disposable local receipt;
6. prove a durable state write if persistence is claimed;
7. prove an effect/result receipt if effects are claimed.

Under current HARD_OFF, provider-backed Frankenstein operation stays blocked even if Claude Code itself is installed.

Possible result: `NATIVE` for repo editing/testing, `BLOCKED` for provider orchestration.

## 8. Codex CLI route

Same rule as Claude Code:

1. discover real repo root;
2. read current authority + owner target;
3. use exact source paths, not repo-wide scanning by default;
4. run bounded non-provider tests only when admitted;
5. verify any lifecycle integration by an observed receipt.

Possible result: `NATIVE` for code/research work, `BLOCKED` for provider orchestration under HARD_OFF.

## 9. Hermes Agent route

First detect whether Hermes really has:

- local filesystem access;
- shell/process execution;
- Git access;
- persistent state/lifecycle hooks.

If yes, map the same authority-first steps.

If it only has messages/tools but no durable repo lifecycle, use `ADAPTED` or `DEGRADED`. Do not fake a native hook.

## 10. ChatGPT Web route

ChatGPT Web may have a GitHub connector without a normal local shell.

Use the connector to:

1. read current `main`, authority and owner target;
2. read exact files;
3. create/update bounded repo artifacts when authorized;
4. keep runtime claims separate from source writes.

If no authorized runtime surface is attached, do not call source writes “runtime installation.”

Typical result: `ADAPTED` for repository research/editing; runtime status depends on actual connected execution capability.

## 11. Claude Web route

If Claude Web only has uploaded files/repository context and no verified executable host:

- use it for source/research analysis;
- produce exact patches/artifacts;
- do not claim hooks fired;
- do not claim state/effects executed.

Result is usually `ADAPTED` or `DEGRADED` until an executable host is verified.

## 12. Grok Web route

Same principle:

- detect connector/filesystem/runtime capability first;
- do not infer shell or hooks;
- source analysis may be useful without runtime authority;
- runtime claims need real receipts.

Use `ADAPTED`, `DEGRADED`, or `BLOCKED` according to observed capability.

## 13. Generic fallback route

If host is unknown:

```text
A. Can it read exact repo files?
   no  -> BLOCKED
   yes -> continue

B. Can it persist changes/state?
   no  -> DEGRADED (analysis only)
   yes -> continue

C. Can it execute bounded tests/processes?
   no  -> ADAPTED/DEGRADED (source work only)
   yes -> continue

D. Does current authority admit the requested action?
   no  -> BLOCKED for that action
   yes -> execute the smallest exact test

E. Did a real hook/state/effect receipt appear from or get independently verified against the claimed mechanism?
   no  -> do not claim native lifecycle integration
   yes -> NATIVE or ADAPTED, depending on mechanism
```

## 14. Frankenstein HARD_OFF check

Current main contains authority-gated Frankenstein entrypoints and focused tests.

Relevant source:

```text
research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_authority_gate_v1.py
research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_orchestrator_v1.py
research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_bugfix_v1.py
tests/test_frankenstein_provider_hardoff_gate_v1.py
```

The original provider-backed implementations are retained as quarantined provenance files. Do not bypass the supported gate by invoking historical donor files.

A valid HARD_OFF witness must demonstrate the boundary stops before provider/secret/network work. A source file existing is not enough.

## 15. Verify lifecycle and variable-grid claims

For any future host integration claiming “automatic start”, “hook”, “memory”, or “effect”:

1. create a unique local test receipt ID;
2. trigger the real lifecycle event;
3. observe the receipt generated by the hook itself;
4. restart/re-enter the host if persistence is claimed;
5. verify the receipt/state survives;
6. for effects, verify actual result/outcome re-entry;
7. delete disposable test state if appropriate.

A manually asserted boolean or model claim is not a receipt. No mechanism-produced or independently verified receipt = no native lifecycle credit.

For a variable-grid claim, also verify that changing `N`, restarting cells, or resizing the grid does not silently change the identity/semantics of the required cognitive process merely because the module count changed. Durable state and workspace handoff/re-entry need exact receipts too.

## 16. Do not scan the whole repository unless the task requires it

Use the curated routes:

```text
HUMAN_READ_THIS/README.md
DEV_SOURCE_RESEARCH/README.md
DEV_SOURCE_RESEARCH/repository/FRANKENSTEIN_SOURCE_INDEX.json
research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_MANIFEST.json
```

Then follow deep links.

Minimum tokens. Exact evidence. No fake success.
