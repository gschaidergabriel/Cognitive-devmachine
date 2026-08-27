# AI START HERE. DO NOT SCAN THE REPO.

Small steps. No guessing.

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
CLAY_EXECUTION_AUTHORITY.md
research_entity/claycode/autonomous/SUPERVISOR_INBOX.json
DEV_SOURCE_RESEARCH/repository/CURRENT_AUTHORITY_AND_EVIDENCE.md
DEV_SOURCE_RESEARCH/repository/FRANKENSTEIN_SOURCE_INDEX.json
AI_START_HERE_DO_NOT_SCAN_REPO/README.md
```

Then read the steering file named by `SUPERVISOR_INBOX.json`.

For Frankenstein implementation work also read:

```text
research_entity/topic_packets/frankenstein-master-cognition-concept/TRIGGERWORD3_HARD_OFF_CLOSURE_20260827_GPT56SOL.json
research_entity/topic_packets/frankenstein-master-cognition-concept/CONCEPT.md
```

For history/research synthesis use:

```text
DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_RESEARCH_CHRONICLE.md
```

Do not treat old plan text as newer authority.

## 3. Current expected provider result

At the 2026-08-27 Trigger-3 authority snapshot:

```text
providers: HARD_OFF
together: FORBIDDEN
paid fallback: FORBIDDEN
```

So a provider-capable Frankenstein launch is expected to **BLOCK before provider import, secret lookup, network, Aider, or fallback dispatch**.

That is correct behavior, not installation failure.

## 4. Detect what this host can really do

Check capabilities. Do not infer them from product name.

```text
filesystem read?       yes/no
filesystem write?      yes/no
shell?                  yes/no
git read?               yes/no
git write?              yes/no
python?                 yes/no
persistent local state? yes/no
lifecycle hooks?        yes/no/unknown
real effect execution?  yes/no/unknown
```

Unknown means unknown.

If Python + a checkout exist, use the fail-closed probe instead of hand-waving:

```bash
python3 "$REPO/AI_START_HERE_DO_NOT_SCAN_REPO/probe_host.py" \
  --repo "$REPO" \
  --host <claude-code|codex-cli|hermes-agent|chatgpt-web|claude-web|grok-web|generic> \
  --state-dir <REAL_WRITABLE_STATE_DIR>
```

The probe performs **no network call, provider call, secret lookup, or repository-wide scan**. It does not treat an installed CLI binary as proof that hooks fired.

For lifecycle/effect promotion, supply receipts created by the real host integration:

```bash
--hook-receipt <REAL_HOOK_RECEIPT.json> \
--effect-receipt <REAL_EFFECT_RESULT_RECEIPT.json>
```

For a connected-tool adaptation also add:

```bash
--adapter
```

## 5. Result words

Every installation/integration route ends with exactly one of these meanings:

- `NATIVE` — host has the needed lifecycle/tool/state capabilities directly and they were verified.
- `ADAPTED` — equivalent behavior is mapped through a different verified host mechanism.
- `DEGRADED` — useful subset works; missing capabilities are named.
- `BLOCKED` — required capability/authority is absent or explicitly denied.

Never write `NATIVE` because a config file or CLI binary exists. Verify real firing/state/effect receipts.

## 6. Claude Code route

If Claude Code has a real shell + repo checkout:

1. locate repo dynamically with `git rev-parse --show-toplevel`;
2. read authority files above;
3. run `probe_host.py --host claude-code`;
4. inspect current Frankenstein gate/entrypoint files;
5. run only tests/actions allowed by current authority;
6. if adding hooks, prove the hook actually fires with a disposable local receipt;
7. prove a durable state write if persistence is claimed;
8. prove an effect/result receipt if effects are claimed.

Under current HARD_OFF, provider-backed Frankenstein operation stays blocked even if Claude Code itself is installed.

Possible result: `NATIVE` for repo editing/testing, `BLOCKED` for provider orchestration.

## 7. Codex CLI route

Same rule as Claude Code:

1. discover real repo root;
2. read current authority;
3. run `probe_host.py --host codex-cli`;
4. use exact source paths, not repo-wide scanning by default;
5. run bounded non-provider tests only when admitted;
6. verify any lifecycle integration by an observed receipt.

Possible result: `NATIVE` for code/research work, `BLOCKED` for provider orchestration under HARD_OFF.

## 8. Hermes Agent route

First detect whether Hermes really has local filesystem, shell/process, Git, persistent state and lifecycle hooks.

Use:

```bash
python3 "$REPO/AI_START_HERE_DO_NOT_SCAN_REPO/probe_host.py" \
  --repo "$REPO" --host hermes-agent --state-dir <REAL_WRITABLE_STATE_DIR>
```

If it only has messages/tools but no durable repo lifecycle, use `ADAPTED` or `DEGRADED`. Do not fake a native hook.

## 9. ChatGPT Web route

ChatGPT Web may have a GitHub connector without a normal local shell.

Use the connector to:

1. read current `main` and authority;
2. read exact files;
3. create/update bounded repo artifacts when authorized;
4. keep runtime claims separate from source writes.

If an external/local executor runs the probe for the web integration, classify the mapping with `--host chatgpt-web --adapter` and real receipts. A web chat message saying a hook fired is not a hook receipt.

If no authorized runtime surface is attached, do not call source writes “runtime installation.”

Typical result: `ADAPTED` for repository research/editing; runtime status depends on actual connected execution capability.

## 10. Claude Web route

If Claude Web only has uploaded files/repository context and no verified executable host:

- use it for source/research analysis;
- produce exact patches/artifacts;
- do not claim hooks fired;
- do not claim state/effects executed.

Result is usually `ADAPTED` or `DEGRADED` until an executable host is verified.

## 11. Grok Web route

Same principle:

- detect connector/filesystem/runtime capability first;
- do not infer shell or hooks;
- source analysis may be useful without runtime authority;
- runtime claims need real receipts.

Use `ADAPTED`, `DEGRADED`, or `BLOCKED` according to observed capability.

## 12. Generic fallback route

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

E. Did a real hook/state/effect receipt appear?
   no  -> do not claim native lifecycle integration
   yes -> NATIVE or ADAPTED, depending on mechanism
```

Use `probe_host.py --host generic` where a Python executor exists.

## 13. Frankenstein HARD_OFF check

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

## 14. Verify lifecycle claims

For any future host integration claiming “automatic start”, “hook”, “memory”, or “effect”:

1. create a unique local test receipt ID;
2. trigger the real lifecycle event;
3. observe the receipt generated by the hook itself;
4. restart/re-enter the host if persistence is claimed;
5. verify the receipt/state survives;
6. for effects, verify actual result/outcome re-entry;
7. feed the receipts to `probe_host.py` where possible;
8. delete disposable test state if appropriate.

No receipt = no lifecycle credit.

## 15. Do not scan the whole repository unless the task requires it

Use the curated routes:

```text
HUMAN_READ_THIS/README.md
DEV_SOURCE_RESEARCH/README.md
DEV_SOURCE_RESEARCH/repository/CURRENT_AUTHORITY_AND_EVIDENCE.md
DEV_SOURCE_RESEARCH/repository/FRANKENSTEIN_SOURCE_INDEX.json
DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_RESEARCH_CHRONICLE.md
research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_SOURCE_IDENTITY_HISTORY_ANCHOR_20260827.json
```

Then follow deep links.

Minimum tokens. Exact evidence. No fake success.
