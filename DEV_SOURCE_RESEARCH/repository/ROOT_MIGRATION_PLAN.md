# Triggerword 3 Root Migration Plan

**Status:** `PREPARED_NOT_RUN`  
**Purpose:** converge the public repository surface without breaking GitHub, host-native agent discovery, imports, workflows, or historical reproducibility.

This file is a migration protocol, not permission to move files blindly.

## Target

The Triggerword 3 public navigation target is:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

The word **public** matters. Some root-level machine-control surfaces are discovered by external tools only at fixed locations. Moving them can break the repository even if the new tree looks cleaner.

## Current result

`TARGET_NOT_REACHED`.

The curation branch adds the three missing public layers first. It deliberately leaves the root `README.md` unchanged and does not relocate existing technical files in the same commit series.

## Non-negotiable invariants

1. Preserve Git object history; do not rewrite historical commits.
2. Preserve source bytes during pure moves. A move plus an edit is an intentional source change and must be reviewed as such.
3. No second current authority tree. The new directories are navigation/index layers over canonical source, not copies of the product.
4. Do not move a path until every repository reference to it is inventoried.
5. Do not use a passing self-derived validator as proof that a moving authority path is correct.
6. Hidden or host-required root surfaces may remain as explicit operational exceptions when the hosting tool requires that exact location.
7. Root `README.md` is out of scope for this Triggerword 3 turn unless the owner explicitly requests its rewrite.

## Root classes

Every tracked top-level path must be classified before relocation.

| Class | Meaning | Default action |
|---|---|---|
| `PUBLIC_ENTRY` | the four Triggerword 3 navigation surfaces | retain at root |
| `HOST_REQUIRED` | a host/tool discovers this path only at root | retain as explicit exception or prove an adapter before moving |
| `GITHUB_REQUIRED` | GitHub behavior depends on the conventional root path | retain as operational exception unless replacement is proven |
| `SOURCE_RUNTIME` | executable product/research source | move only after import/path/workflow audit |
| `EVIDENCE_ARCHIVE` | receipts, historical material, generated research state | move/index only with provenance-preserving mapping |
| `COMPATIBILITY_SHIM` | root file retained only to point to a new canonical path | keep minimal; never create a second authority |
| `SAFE_TO_MOVE` | no fixed-path consumer remains after audit | relocate under `DEV_SOURCE_RESEARCH/repository/` |
| `UNKNOWN` | dependency surface not established | fail closed; do not move |

## Known fixed-location risks

These are not exhaustive; they are examples that make a blind move unsafe.

### `.github/`

GitHub Actions and repository automation use conventional `.github/...` locations. Treat as `GITHUB_REQUIRED` until GitHub behavior is explicitly replaced. Hiding it under the developer tree would make the root prettier by breaking automation.

### `.gitignore`

Moving the root ignore file changes which paths its patterns cover. Treat as `GITHUB_REQUIRED`/repository-control metadata unless a generated equivalent is proved.

### `CLAUDE.md`

The current AI installer uses this as the Claude Code project instruction surface. Treat as `HOST_REQUIRED` until an exact Claude Code discovery/adapter test proves another location.

### `AGENTS.md`

The current AI installer uses this as the Codex CLI project instruction surface. Treat as `HOST_REQUIRED` until an exact Codex discovery/adapter test proves another location.

### authority/bootstrap pointers

Files such as `CLAY_EXECUTION_AUTHORITY.md` or current bootstrap pointers may be referenced by scripts and workers. Their physical location is not cosmetic. Inventory every reference before any move; use a tiny compatibility pointer only if a move is later justified.

## Mechanical migration gate

A top-level path may be moved only when all of the following are true:

```text
[ ] exact source path and blob/tree identity recorded
[ ] all text references inventoried
[ ] Python/import references inventoried
[ ] shell/workflow/config references inventoried
[ ] host-native discovery requirements checked
[ ] relative Markdown links checked
[ ] generated artifact/receipt paths checked
[ ] destination is not a competing authority
[ ] byte identity preserved for pure moves
[ ] post-move negative path checks exist
[ ] post-move required-path checks exist
[ ] rollback mapping old_path -> new_path recorded
```

If any item is unknown: `BLOCKED_UNKNOWN_DEPENDENCY`.

## Proposed destination map

This is a **candidate map**, not an executed relocation.

```text
DEV_SOURCE_RESEARCH/repository/
  current-control/          # indexed pointers to current authority/control surfaces
  source/                   # product/runtime source families after dependency-safe moves
  research/                 # research programs and current technical notes
  evidence/                 # receipts/measurements/negative evidence indexes
  history/                  # historical donor/provenance material
  operations/               # dashboards/automation/operator docs that are movable
  compatibility/            # minimal documented shims where fixed paths cannot disappear at once
```

Do not duplicate full source trees into these directories merely to make the map look complete. Prefer links/indexes until a real move is mechanically safe.

## Public-root interpretation

There are two possible interpretations of the Triggerword 3 target:

1. **Strict physical root:** literally no tracked paths except the four public entries.
2. **Canonical public root:** those four are the only human navigation surfaces, while hidden GitHub metadata and host-required instruction files remain operational exceptions.

The current evidence favors interpretation 2 because strict relocation of `.github`, `CLAUDE.md`, `AGENTS.md`, and similar conventional files can remove functionality. This is an `INFERENCE`, not an owner-authority rewrite. A future owner instruction can require strict physical-root migration, but that migration must first supply working replacements for fixed-location consumers.

## Migration sequence

### Phase 0 — already completed on this branch

- add `HUMAN_READ_THIS/`;
- add `DEV_SOURCE_RESEARCH/`;
- add `AI_START_HERE_DO_NOT_SCAN_REPO/`;
- keep root README unchanged;
- create evidence ledger.

### Phase 1 — inventory

Generate a machine-readable top-level inventory with:

```text
path
blob_or_tree_sha
class
known_consumers[]
text_references[]
runtime_references[]
workflow_references[]
proposed_destination
move_status
```

No move occurs in this phase.

### Phase 2 — safe leaf moves

Move only `SAFE_TO_MOVE` leaf material with zero unresolved consumers. Preserve bytes. Add old→new mapping and link regressions.

### Phase 3 — compatibility-backed moves

For paths with legitimate consumers, land consumers/adapters first, prove them, then move. Keep a minimal compatibility pointer only when necessary.

### Phase 4 — root acceptance

Acceptance is not “root looks clean.” It requires:

- public navigation from README to all three layers;
- GitHub automation still discoverable;
- Claude Code/Codex instruction discovery still works or has a verified adapter;
- imports/workflows/relative links pass;
- current authority pointers resolve;
- no source/evidence bytes silently changed;
- old paths either intentionally gone or explicitly shimmed;
- repository reconstruction remains possible.

## Counterhypothesis

**Hypothesis:** a cleaner public root materially improves human/AI navigation and reduces accidental scanning/authority confusion.

**Counterhypothesis:** aggressive physical relocation creates more compatibility shims and path complexity than it removes, increasing operational ambiguity.

**Discriminator:** measure first-task navigation cost and broken-reference count before/after a dependency-safe candidate migration. Reject a migration that reduces visual clutter but increases broken paths, duplicate pointers, or host-specific exceptions.

## Next exact action

Create and run a deterministic **read-only root inventory/reference audit** on a clean checkout of the current branch. It must emit the inventory above and make zero moves. Review the `UNKNOWN` and fixed-location classes before authorizing Phase 2.
