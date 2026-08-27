# AI installer contract

Schema: `FRANKENSTEIN_AI_INSTALL_CONTRACT/v1`

## Purpose

Install/adapt the Project Frankenstein / EntityOS research workflow into the capabilities the host actually provides. Never claim native integration when only documentation or file access exists.

## Inputs

- actual checkout/mount path discovered at runtime;
- exact current Git HEAD;
- current supervisor authority selected by `SUPERVISOR_INBOX.json`;
- host capability inventory;
- intended lifecycle/state/effect features.

## Required capability discovery

Record each as `YES`, `NO`, or `UNKNOWN`:

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

`UNKNOWN` fails closed for a feature that requires that capability.

## Authority check before effects

Before any provider/network/credential/effect boundary:

1. refresh exact current main/HEAD as applicable;
2. read current owner/supervisor authority;
3. resolve route/provider/effect permission;
4. if authority is HARD_OFF or ambiguous, stop **before** secret lookup/provider import/network dispatch;
5. preserve a receipt that distinguishes blocked-by-authority from runtime failure.

At frozen base `854f6bc8…`, 9.13 HARD_OFF means provider routes false, Together forbidden, paid fallback forbidden.

## Minimal installation sequence

```text
DISCOVER_ROOT
-> READ_CURATED_INDEX
-> REFRESH_AUTHORITY
-> INVENTORY_HOST_CAPABILITIES
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

Use only when all required capabilities are natively present and observed.

### ADAPTED

Use when required behavior works through a different verified host mechanism with no material semantic loss.

### DEGRADED

Use when a useful subset works but one or more intended lifecycle/state/effect features are unavailable.

### BLOCKED

Use when a required capability is absent, current authority forbids the action, or exact state cannot be resolved safely.

## Verification receipt

A conforming installer should emit a small machine-readable receipt shaped like:

```json
{
  "schema": "FRANKENSTEIN_AI_INSTALL_RECEIPT/v1",
  "host": "<detected host>",
  "repo_root": "<detected path>",
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
    "hook_fired": false,
    "durable_state_write": false,
    "effect_receipt": false,
    "outcome_reobserved": false
  },
  "result": "ADAPTED",
  "notes": []
}
```

Do not populate `true` from configuration existence alone. Observe the event/result.

## Path rule

Never hard-code Downloads/home/current directory. Resolve dynamically from the host or Git. Relative paths in this curation layer are intentionally rooted from the discovered repository checkout.

## Repository-scan rule

Do not recursively scan the repository as the first action. Start from:

1. `HUMAN_READ_THIS/README.md`
2. `DEV_SOURCE_RESEARCH/README.md`
3. `DEV_SOURCE_RESEARCH/EVIDENCE_LEDGER.md`
4. `DEV_SOURCE_RESEARCH/ARCHIVE_INDEX.json`

Then read only task-relevant source paths.

## Evidence rule

Installation evidence is scoped:

- config exists != hook fired;
- hook fired != durable state is correct;
- state write != effect happened;
- effect request != verified outcome;
- one component working != entire EntityOS/HCU acceptance.

Final output must be exactly one of `NATIVE`, `ADAPTED`, `DEGRADED`, `BLOCKED`, with the bounded reasons and observed evidence.