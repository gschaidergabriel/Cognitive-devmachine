# Root topology audit — Triggerword 3 — 2026-08-27

Observed tree: canonical `main` tree `e7cee5640aa2f05edc695adadc50d6e20ccb8755` at commit `854f6bc87780f4a5242489a6c807d186b16a8c3d`.

This is a migration audit, not a move receipt. No historical root file is claimed moved by this document.

## Target

Human-visible root target:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

Repository infrastructure that must remain at root for Git/GitHub/tooling semantics (for example `.gitignore`, `.github/`, and any tool-required dot-directory) is treated as a hidden infrastructure exception rather than “public navigation clutter”.

## Observed root problem classes

### A — old/current-looking authority and bootstrap surfaces

Examples observed:

```text
000_CLAY_CURRENT.md
000_FRANK_GLOBAL_RESEARCH_ENTITY_AUTOBOOT.txt
AGENTS.md
AUTHORITATIVE_STATE_RESOLUTION.md
CLAUDE.md
CLAUDE_CODE_INTRODUCTION.md
CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json
CLAYVERSE_CANONICAL_DIRECTIVE.md
CLAY_EXECUTION_AUTHORITY.md
JOIN_RAE_CLAUDE_CODE.txt
PROJECT_AUTO_BOOT_KERNEL_FINAL.txt
PROJECT_SOURCE_SINGLE_BOOTSTRAP.txt
PROJECT_SOURCE_SINGLE_BOOTSTRAP_V2.txt
RAE_VNEXT_RUNTIME.md
rae.py
```

Risk: filenames make several historical/current-looking surfaces appear equally authoritative. Current authority resolution already shows 8.78-vs-9.13 drift, so moving or replacing these blindly could worsen ambiguity.

Proposed class: `DEV_SOURCE_RESEARCH/repository/compat_root_authority/` plus compatibility strategy decided per reference count. Do not move until all inbound references are enumerated.

### B — research/archive roots

Examples observed:

```text
agentZero/
agentzeroforschung/
benchmarks/
dump/
dump archive/
frank_reference/
free swarm/
governance/
rae_core/
receipts/
research_entity/
research_sources/
runtime_checks/
schemas/
tests/
the artefact/
```

These are not all “clutter” in the same sense. Several are active source/evidence locations. Triggerword 3 should expose them through `DEV_SOURCE_RESEARCH/` navigation before considering physical relocation.

Proposed class: preserve active canonical paths until reference-safe migration is demonstrated. Prefer indexes/links first, moves second.

### C — dashboard/result presentation at root

Observed:

```text
000_FREE_SWARM_LIVE_DASHBOARD.md
ZZZ_FREE_SWARM_RESULTS.md
```

Proposed class: `DEV_SOURCE_RESEARCH/repository/live_status_or_history/`, but only after readers and automation are checked.

### D — suspicious accidental code/text filenames

Observed exact entries:

```text
"gemeinsamer State)"                         blob e69de29bb2d1d6434b8b29ae775ad8c2e48c5391 (empty blob)
"libc.malloc_trim(0)"                        blob 56449f7a37c0593798d05e67687af3ed244ef058
"madvise(ptr, length, MADV_FREE);"            blob d4b4da997a55a9567842f2a182f7cc6046b708d8
```

These look like accidental shell/editor artefacts or captured code fragments, but that is an **INFERENCE**, not a deletion authorization.

Required discriminator before removal/move:

1. fetch content;
2. search all repository references by exact filename and blob/content signatures;
3. inspect first verified Git introduction commit;
4. classify as evidence, active dependency, accidental artefact, or unknown;
5. only then move/delete with a receipt.

The empty blob is still evidence of repository history and should not be silently erased.

## Migration manifest schema

Every physical root move should first have a machine-readable record like:

```json
{
  "source_path": "...",
  "source_blob_sha": "...",
  "target_path": "...",
  "byte_identity_required": true,
  "inbound_references": [],
  "automation_references": [],
  "compatibility_stub_required": false,
  "authority_role": "current|historical|none|unknown",
  "classification": "active|historical|archive|accidental|unknown",
  "move_status": "prepared-not-run"
}
```

## Migration acceptance

A move is accepted only if:

- source blob identity is recorded;
- destination content is byte-identical unless an intentional edit is separately evidenced;
- inbound references are updated or a compatibility shim is justified;
- current authority pointers still resolve;
- tests/automation that depend on paths are checked;
- Git history remains recoverable;
- no duplicate current authority is introduced;
- public navigation improves measurably.

## Current result

`PREPARED_NOT_RUN` for physical migration.

What Triggerword 3 completed in this lane is the prerequisite navigation layer and this auditable move protocol. Performing bulk moves before reference enumeration would optimize cosmetic root cleanliness at the cost of reproducibility and is therefore rejected.
