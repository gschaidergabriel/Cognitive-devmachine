# INSTALL CONTRACT — host-neutral, fail-closed

This contract is intentionally short. It is a verification contract, not a promise that every host has every capability.

## Inputs

Required:

- actual repository identity/path or connected repository handle
- current owner authority
- current `SUPERVISOR_INBOX.json`
- inbox-selected steering
- detected host capabilities

Forbidden assumptions:

- fixed clone path
- fixed home directory
- fixed attachment mount
- current working directory = repo root
- hook APIs that were not detected
- provider authority inferred from credentials or old plans

## Procedure

1. **LOCATE** — resolve the actual repository dynamically.
2. **AUTHORITY** — read newest owner authority and inbox-selected steering.
3. **DETECT** — enumerate real host capabilities: read, write, shell, durable state, lifecycle hook, effect/result re-entry, isolated execution.
4. **MAP** — map only detected capabilities to Frankenstein/Clay lifecycle needs.
5. **PROBE** — perform one harmless local verification on an authorized surface.
6. **PERSIST** — write one bounded state marker if durable writes are available.
7. **REENTER** — prove the marker is readable from a fresh process/session where the host supports this.
8. **EFFECT** — if a real effect is part of the host mapping, prove request/result receipt separation. Do not create an external effect merely to test the installer when a non-effect probe is sufficient.
9. **CLASSIFY** — output `NATIVE`, `ADAPTED`, `DEGRADED`, or `BLOCKED`.

## Current HARD_OFF rule

At the curation base `854f6bc87780f4a5242489a6c807d186b16a8c3d`, external provider routes are HARD_OFF.

A correct installer probe therefore proves safety without attempting a provider call:

```text
provider_calls=0
secret_lookups=0
```

Do not test the gate by touching a real secret, importing a provider client for execution, starting Aider fallback, or sending network traffic to NVIDIA/Groq/Mistral/Together.

## Host result rules

### Claude Code

`NATIVE` only if the detected Claude Code version exposes the required lifecycle/state/tool surfaces and a real hook firing plus durable state re-entry are observed.

### Codex CLI

`NATIVE` only if the detected Codex environment directly exposes equivalent lifecycle/state/tool/result semantics and they are verified. Otherwise use an adapter or degrade honestly.

### Hermes Agent

Use real detected Hermes primitives. No invented hook names. `NATIVE` only after real firing/state/result verification.

### ChatGPT Web / Claude Web / Grok Web

A connected repository is not a resident local runtime. If repository read/write works but persistent lifecycle hooks do not exist, use `ADAPTED` or `DEGRADED` according to the missing semantics. Do not claim `NATIVE` from a successful document edit.

### Generic host

Plain-file continuity plus explicit commands can be useful. If lifecycle or durable effect-result semantics are missing, classify accordingly.

## Receipt schema

Write or return a receipt containing at least:

```json
{
  "schema": "FRANKENSTEIN_INSTALL_RECEIPT/v1",
  "host": "...",
  "repo_identity": "...",
  "source_commit": "...",
  "authority_epoch": "...",
  "capabilities_detected": [],
  "hook_probe": "PASS|FAIL|NOT_AVAILABLE|NOT_REQUIRED",
  "durable_state_probe": "PASS|FAIL|NOT_AVAILABLE",
  "effect_result_reentry_probe": "PASS|FAIL|NOT_AVAILABLE|NOT_REQUIRED",
  "provider_calls": 0,
  "secret_lookups": 0,
  "result": "NATIVE|ADAPTED|DEGRADED|BLOCKED",
  "notes": []
}
```

## Acceptance

The installation is accepted only when its classification is supported by observed host behavior.

A copied config, a present hook file, a model reply, or a source-level test is not sufficient by itself.