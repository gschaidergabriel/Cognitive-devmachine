# AI installer contract

Schema: `FRANKENSTEIN_AI_INSTALL_CONTRACT/v2`

Fusion point: `ed70385760c03a30dea7b6ecf8f6b78cbbaa584a`.

## Purpose

Adapt Project Frankenstein / EntityOS research workflows to capabilities the host **actually provides**. Never call an integration native because documentation/configuration exists.

## Inputs

- actual checkout/mount path discovered at runtime;
- exact current Git HEAD;
- current supervisor authority selected by `DEV_SOURCE_RESEARCH/repository/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`;
- host capability inventory;
- intended lifecycle/state/effect features.

## Capability discovery

Record `YES`, `NO`, or `UNKNOWN`:

```text
file_read
file_write
shell_exec
stdout_stderr_exit_observation
persistent_workspace
scheduled_or_lifecycle_hook_registration
hook_fire_observation
durable_state_write
network_access
credential_access
external_effect_execution
external_effect_outcome_verification
```

`UNKNOWN` fails closed when the requested feature requires it.

## Source-layout discovery

Resolve the repository root dynamically. In this curation topology, engineering source is below:

```text
<root>/DEV_SOURCE_RESEARCH/repository/
```

Do not assume historical root paths still execute unchanged. If a host/tool expects `.github/`, `tools/`, `tests/`, `research_entity/`, or other technical directories at root, the literal four-entry topology is not native for that host until adapted and verified.

## Authority before provider/effect boundary

Before any provider/network/credential/external-effect action:

1. refresh exact current HEAD/main as applicable;
2. read current owner/supervisor authority;
3. resolve provider/effect permission;
4. if authority is HARD_OFF or ambiguous, stop **before** secret lookup, provider import, network dispatch, Aider/external fallback, or effect execution;
5. preserve a receipt distinguishing `BLOCKED_BY_AUTHORITY` from runtime/product failure.

At the Trigger-3 fusion point, supervisor schema `9.13` keeps provider routes HARD_OFF, Together forbidden, no paid fallback. A later source/local Frankenstein authority gate exists and records focused local PASS, but provider runtime promotion remains zero.

## Minimal sequence

```text
DISCOVER_ROOT
-> READ_CURATED_INDEX
-> REFRESH_AUTHORITY
-> INVENTORY_HOST_CAPABILITIES
-> RESOLVE_CURATED_VS_ENGINEERING_SOURCE_PATH
-> MAP_REQUIRED_FEATURES
-> INSTALL_ONLY_SUPPORTED_ADAPTERS
-> VERIFY_REAL_HOOKS_IF_CLAIMED
-> VERIFY_DURABLE_STATE_IF_CLAIMED
-> VERIFY_EFFECT_RECEIPT_AND_OUTCOME_IF_CLAIMED
-> RUN_RELEVANT_TESTS
-> CLASSIFY
```

## Classification

### NATIVE

All required capabilities and path/lifecycle semantics are natively present and observed.

### ADAPTED

Required behavior works through a different verified mechanism with no material semantic loss.

### DEGRADED

A useful subset works but intended lifecycle/state/effect behavior is incomplete.

### BLOCKED

A required capability is absent/unknown, current authority forbids the action, or exact state cannot be resolved safely.

## Verification receipt

```json
{
  "schema": "FRANKENSTEIN_AI_INSTALL_RECEIPT/v2",
  "host": "<detected host>",
  "repo_root": "<detected path>",
  "engineering_source_root": "<detected path>/DEV_SOURCE_RESEARCH/repository",
  "head": "<exact sha>",
  "authority": "<exact authority epoch/state>",
  "capabilities": {
    "file_read": "YES",
    "file_write": "YES",
    "shell_exec": "YES",
    "hook_fire_observation": "NO"
  },
  "verified": {
    "curated_index_read": true,
    "authority_read": true,
    "source_layout_resolved": true,
    "hook_fired": false,
    "durable_state_write": false,
    "effect_receipt": false,
    "outcome_reobserved": false
  },
  "result": "ADAPTED",
  "notes": []
}
```

Never set a verification field true from file/config existence alone.

## Repository-scan rule

Do not recursively scan the repository first. Start with:

1. `HUMAN_READ_THIS/README.md`
2. `DEV_SOURCE_RESEARCH/README.md`
3. `DEV_SOURCE_RESEARCH/EVIDENCE_LEDGER.md`
4. `DEV_SOURCE_RESEARCH/ARCHIVE_INDEX.json`

Then read only task-relevant exact source.

## Evidence rule

- config exists != hook fired;
- hook fired != durable state correct;
- state write != effect happened;
- effect request != verified outcome;
- source/local gate PASS != provider runtime acceptance;
- byte-identical path move != runtime equivalence;
- component working != whole EntityOS/HCU acceptance.

Final integration status must be exactly one of `NATIVE`, `ADAPTED`, `DEGRADED`, `BLOCKED`, with bounded observed reasons.