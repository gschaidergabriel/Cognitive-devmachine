# AI START HERE — DO NOT SCAN THE REPOSITORY

This is the low-token installation / re-entry contract for AI hosts.

**Do not recursively scan the repository.** The repository is a research archive. Reading everything first is slow and can mix stale history with current authority.

## Read in this exact order

1. Resolve your actual repository path dynamically. Do not assume `~/Downloads`, `$HOME`, a clone folder name, an attachment mount, or the current working directory.
2. Read `/CLAY_EXECUTION_AUTHORITY.md`.
3. Read `/research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`.
4. Read the steering file named by that inbox.
5. Read `/HUMAN_READ_THIS/README.md` only if you need the human overview.
6. Read `/DEV_SOURCE_RESEARCH/README.md` for the technical map.
7. Read only task-relevant source/tests/receipts after that.

If any current-facing file conflicts with the newer inbox-selected authority, keep the conflict visible and follow the newer admitted authority. Do not average versions.

## Current safety fact

Initial curation base: `854f6bc87780f4a5242489a6c807d186b16a8c3d`.
Refreshed through main change: `3c3dbe5020f57065f47bd4d0a2dce3c537128797`.

The inbox-selected 9.13 steering preserves **HARD_OFF** for external provider routes: provider routes are not admitted, Together is forbidden, and paid fallback is forbidden.

As of `3c3dbe5…`, the canonical Frankenstein Bauleiter/Bugfix entrypoints resolve the current authority before provider import, secret lookup, network, Aider or fallback dispatch. The original provider-backed implementations and old provider/Together plan are preserved under explicit quarantine filenames for donor/provenance use. They are not current executable authority.

Do not look up provider secrets, make provider network calls, launch quarantined provider fallbacks, or treat an old plan as permission while current authority says HARD_OFF.

## Capability detection before installation

Detect what the host can really do before mapping hooks:

- can it read files?
- can it write files?
- can it run shell commands?
- can it persist state across sessions?
- can it register lifecycle hooks?
- can it receive tool/effect results?
- can it distinguish requested effects from verified effects?
- can it execute inside an isolated sandbox?

Never report `NATIVE` just because instructions were copied somewhere.

## Host routes

### Claude Code

1. Find the clone dynamically (`git rev-parse --show-toplevel` when already inside a clone; otherwise locate the intended clone explicitly).
2. Read `CLAUDE.md` plus the authority sequence above.
3. Detect real hook/lifecycle support before mapping any persistent loop.
4. Verify a real hook fires.
5. Verify a durable state write.
6. Verify a tool/effect result is written back as a receipt or observable state transition.

### Codex CLI

1. Resolve the repository root dynamically.
2. Read `AGENTS.md` plus the authority sequence above.
3. Detect shell, file-write, persistence, and hook capabilities actually available in that Codex environment.
4. Run a harmless local probe only on an authorized surface.
5. Verify state write + result re-entry before claiming integration.

### Hermes Agent

1. Resolve the repository root dynamically.
2. Load this file and the authority sequence.
3. Map Hermes lifecycle/state/tool primitives only after detecting their actual names and persistence semantics.
4. Verify hook firing and durable re-entry.

### ChatGPT Web

ChatGPT Web may have connected GitHub/files/tools but does not imply a resident local lifecycle daemon.

1. Use connected GitHub rather than pretending a local clone exists.
2. Read authority first.
3. Make bounded repository changes through a branch/PR when appropriate.
4. Do not claim native continuous hooks unless the current product surface really exposes them.
5. A scheduled automation is not a substitute for a native runtime hook unless that is the intended degraded mapping.

### Claude Web

1. Use connected repository/file surfaces if available.
2. Resolve authority first.
3. Treat lack of local lifecycle execution as a capability gap, not a success.
4. Use `ADAPTED` or `DEGRADED` if continuity must be externalized through files rather than native hooks.

### Grok Web

1. Resolve available file/repository/tool capabilities first.
2. Read authority before any execution plan.
3. If durable hooks/state/effect receipts cannot be verified, do not claim native installation.

### Generic fallback

If the host is unknown:

1. locate the intended repository without assumptions;
2. read authority;
3. detect read/write/shell/persistence/hook/effect-result capabilities;
4. map only capabilities that exist;
5. run one harmless verification;
6. classify honestly.

## Final installation result vocabulary

Every installer route ends with exactly one of these meanings:

| Result | Meaning |
|---|---|
| `NATIVE` | required lifecycle/state/tool/result semantics exist directly and were verified |
| `ADAPTED` | semantics are preserved through a host-specific adapter and were verified |
| `DEGRADED` | useful subset works, but one or more required semantics are absent |
| `BLOCKED` | a required capability, permission, authority, or verification surface is missing |

`PREPARED_NOT_RUN` is an evidence lifecycle status, not an installation success result. This document itself is **PREPARED_NOT_RUN** for any specific host until that host is actually detected and tested.

## Minimal verification receipt

Record at least:

```text
host:
repo_identity:
source_commit:
authority_epoch:
capabilities_detected:
hook_probe:
durable_state_probe:
effect_result_reentry_probe:
provider_calls:
secret_lookups:
result: NATIVE|ADAPTED|DEGRADED|BLOCKED
notes:
```

Under current HARD_OFF, a provider-boundary safety probe must remain non-provider and prove `provider_calls=0` and `secret_lookups=0`; it must not test the gate by attempting a real provider call.

## Deeper maps

- Human overview: [`../HUMAN_READ_THIS/README.md`](../HUMAN_READ_THIS/README.md)
- Technical map: [`../DEV_SOURCE_RESEARCH/README.md`](../DEV_SOURCE_RESEARCH/README.md)
- Evidence map: [`../DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_EVIDENCE_MAP.md`](../DEV_SOURCE_RESEARCH/research/FRANKENSTEIN_EVIDENCE_MAP.md)
- Archive index: [`../DEV_SOURCE_RESEARCH/research/ARCHIVE_INDEX.json`](../DEV_SOURCE_RESEARCH/research/ARCHIVE_INDEX.json)
- Root migration manifest: [`../DEV_SOURCE_RESEARCH/repository/ROOT_MIGRATION_MANIFEST.md`](../DEV_SOURCE_RESEARCH/repository/ROOT_MIGRATION_MANIFEST.md)
