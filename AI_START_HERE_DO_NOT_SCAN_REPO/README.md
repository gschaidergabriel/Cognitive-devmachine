# AI START HERE — DO NOT SCAN THE REPO

You do **not** need to scan thousands of files.

## 1. Read only these first

1. `../HUMAN_READ_THIS/README.md`
2. `../DEV_SOURCE_RESEARCH/README.md`
3. `../DEV_SOURCE_RESEARCH/EVIDENCE_LEDGER.md`
4. `../DEV_SOURCE_RESEARCH/ARCHIVE_INDEX.json`
5. for live authority, read `../DEV_SOURCE_RESEARCH/repository/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json` and the exact steering it selects.

## 2. Basic law

- Persistent research entity: `Clay`.
- Product: `EntityOS`.
- Integrated cognition/compute architecture: `HCU`.
- Model/session/worker: temporary organ, not a second persistent entity.
- Model output != world fact.
- Request != effect.
- Memory != observation.
- Component PASS != whole-product PASS.
- Current authority beats stale plans.

## 3. Find the checkout dynamically

Never assume Downloads, `$HOME`, a clone path, an attachment mount, or current working directory.

With shell access:

```sh
ROOT="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 1
printf '%s\n' "$ROOT"
```

If this is not a Git checkout, ask the host/tool for the actual mounted repository path. Do not invent one.

The current technical source inside this curation layout is under:

```text
$ROOT/DEV_SOURCE_RESEARCH/repository/
```

Do not confuse the public curation root with the historical engineering root layout.

## 4. Host routes

### Claude Code

1. Resolve `$ROOT` dynamically.
2. Read the four curated files above and current authority.
3. Detect real file/shell/lifecycle/hook capabilities; do not assume them.
4. Work from exact source under `DEV_SOURCE_RESEARCH/repository/`.
5. If claiming hooks, observe a real hook fire.
6. If claiming durable state/effects, verify actual state/effect/result receipts.

Use `NATIVE` only when required native lifecycle/tool/state behavior is observed. Otherwise use `ADAPTED`, `DEGRADED`, or `BLOCKED`.

### Codex CLI

1. Resolve `$ROOT` with Git.
2. Read curated index + current authority.
3. Use exact current source; account for the `DEV_SOURCE_RESEARCH/repository/` relocation in this Draft topology.
4. Run relevant tests and preserve exact HEAD/stdout/stderr where evidence matters.
5. Never infer provider permission from available environment variables or credentials.

### Hermes Agent

1. Resolve the actual workspace/mount.
2. Detect file read/write, shell, persistent state, lifecycle and hook capabilities.
3. Map only observed capabilities.
4. If durable lifecycle support is absent, use explicit re-entry receipts and classify `ADAPTED` or `DEGRADED`.

### ChatGPT Web

Browser chat is not automatically a local shell agent.

1. Use connected repository/file tools when available.
2. Read curated indexes first.
3. Do not claim local hook/runtime evidence unless a real tool observed it.
4. Repository read/write can still support research/curation without implying runtime installation.

### Claude Web

Same rule: use actual connected tools; do not fabricate shell/lifecycle/hook support.

### Grok Web

Same rule: detect real tools first. Discussion of source is not a native runtime installation.

### Generic fallback

Determine:

```text
file_read
file_write
shell_exec
stdout_stderr_exit_observation
persistent_workspace
lifecycle_hook_registration
hook_fire_observation
durable_state_write
network_access
credential_access
external_effect_execution
external_effect_outcome_verification
```

Unknown required capability fails closed.

Classify:

- `NATIVE` — required native capabilities exist and are observed.
- `ADAPTED` — intended behavior works through a different verified mechanism.
- `DEGRADED` — useful subset works, material capability missing.
- `BLOCKED` — required capability absent or current authority forbids the action.

## 5. Current HARD_OFF warning

At the Trigger-3 fusion point, current supervisor authority is schema `9.13` with provider routes HARD_OFF, Together forbidden, and no paid fallback.

The **original** 2026-08-27 provider-backed Frankenstein orchestrator/bugfixer is retained only as quarantined donor provenance. Current `main` has a later stdlib-only fail-closed authority gate and records `10/10` focused local tests PASS, but this is only `SOURCE_AND_LOCAL_UNIT_ONLY` evidence. Provider-path runtime credit remains zero/unpromoted.

Therefore:

- do not execute quarantined provider-backed donors;
- do not use stale plan text to authorize Together/provider work;
- refresh current authority before any secret/provider/network/effect boundary;
- a local gate test is not provider runtime acceptance.

## 6. Installation is not success until observed

Do not stop at “file copied” or “config written.”

If the integration claims a capability, observe the relevant event:

- hook fired;
- state write exists;
- generation/provenance is correct;
- effect request passed the proper gate;
- effect/result receipt exists;
- outcome was re-observed when required.

Then output exactly one integration status: `NATIVE`, `ADAPTED`, `DEGRADED`, or `BLOCKED`.

For the formal contract, read [`INSTALLER_CONTRACT.md`](INSTALLER_CONTRACT.md).