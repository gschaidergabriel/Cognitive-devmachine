# Trigger-3 current re-entry delta — post-synthesis caller gate

This file exists because `main` moved after the first research chronicle snapshot. It is a **delta**, not a new authority surface.

## Exact identities

- earlier curation base: `854f6bc87780f4a5242489a6c807d186b16a8c3d`
- intervening metrics main: `551ed48f9ebf8c610311c98ccaf84cdca3f487a7`
- newer main observed during re-entry: `3c3dbe5020f57065f47bd4d0a2dce3c537128797`
- current supervisor inbox observed after that commit: schema `9.13`, delta `9.13O_NON_AUTHORITY`
- authority file remains `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`

## What changed on main

Commit `3c3dbe5020f57065f47bd4d0a2dce3c537128797` is titled:

> trigger3: quarantine Frankenstein provider loops under 9.13 HARD_OFF

Its commit evidence says the canonical Frankenstein entrypoints now resolve `SUPERVISOR_INBOX` before provider import, secret lookup, network, Aider or fallback dispatch, and fail closed under current 9.13 HARD_OFF. It also sets the obsolete Together allowance to zero/quarantined provenance and reports focused local validation `10/10 PASS`.

Evidence classification:

- gate implementation: `CURRENT_SOURCE`
- 10/10 result: `PROJECT_REPORTED_LOCAL_UNIT_RESULT` / source-local-unit scope only
- provider runtime credit: **0**
- whole EntityOS runtime credit: **0**
- HCU full runtime credit: **0**
- training credit: **0**

## Why the P0 is not promoted to runtime-closed here

The current `SUPERVISOR_INBOX.json` still names the real free-pool caller boundary as P0 and keeps:

```text
provider_routes_admitted = false
Together = forbidden
paid fallback = forbidden
runtime quiescence/control closure = open
provider-path runtime pass = false
```

Therefore the correct combined interpretation is:

```text
SOURCE / LOCAL-UNIT CALLER GATE: candidate closure landed on main
CURRENT SUPERVISOR RUNTIME/CONTROL PROMOTION: still open / zero credit
PROVIDER EXECUTION AUTHORITY: still false
```

This is not a contradiction. Source closure and runtime/control promotion are different evidence levels.

## How to read the earlier chronicle

Sections in `FRANKENSTEIN_RESEARCH_CHRONICLE.md` that say the caller boundary is open describe the pre-`3c3dbe5` synthesis snapshot. Read them with this delta:

- historical provider bypass remains a `NEGATIVE_RESULT`;
- the stale 72-hour provider plan remains quarantined provenance;
- the new gate is a source/local-unit repair candidate;
- no external provider call is needed or authorized to validate the documentation layer;
- a later exact supervisor/runtime receipt is required before claiming provider-path runtime closure.

## Next discriminator

The highest-information next control discriminator is not another provider call. It is an admitted **non-provider** validation proving the current canonical entrypoint fails closed before any secret/provider boundary and produces evidence equivalent to:

```text
provider_calls = 0
secret_lookups = 0
network_dispatch = 0
Aider/provider fallback = 0
```

with exact current source identity and without changing Frank Harness.
