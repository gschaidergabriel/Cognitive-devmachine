# Root topology migration plan

Target public root:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

This is a **migration plan**, not permission to mass-move the active repository blindly.

## Why additive-first

At the Trigger-3 base (`854f6bc87780f4a5242489a6c807d186b16a8c3d`) the root still contains technical files/directories such as `.claude`, `.github`, `.env.example`, `AGENTS.md`, authority/state helpers and legacy `000_*` entry surfaces. Some are referenced by scripts, imports, hooks, CI, human habits, receipts or evidence paths.

Moving them without a path-dependency inventory could improve appearance while silently breaking execution or reproducibility. That would repeat a known Frankenstein failure class: **surface cleanup deleting a cognitive/runtime path**.

Therefore PR #2050 first adds the three target entry directories and leaves root `README.md` untouched.

## Migration invariant

For each candidate move:

```text
old bytes == new bytes
unless an intentional source edit is separately reviewed and evidenced
```

And:

```text
old path dependency inventory
 -> compatibility decision
 -> move
 -> static reference check
 -> executable non-provider regression where applicable
 -> receipt
 -> only then remove compatibility surface
```

Do not create a second authority by copying an active control file and then letting both copies evolve.

## Destination model

Technical material moves below:

```text
DEV_SOURCE_RESEARCH/repository/
```

Suggested categories are organizational only; exact paths must be chosen after dependency discovery:

```text
DEV_SOURCE_RESEARCH/repository/
  governance-and-authority/
  automation-hooks/
  ci-and-dev-config/
  legacy-entry-surfaces/
  tooling/
  runtime-source/
  evidence-and-receipts/
  historical-donor-material/
```

Large existing source trees such as `research_entity/` and `the artefact/` should not be physically relocated merely to satisfy aesthetics until import/path/evidence consequences are proven and a migration strategy exists. The target is a human-legible public root without sacrificing causal reproducibility.

## Phase 0 — freeze evidence identity

Before any batch:

1. record current `main` SHA and tree SHA;
2. record candidate path, blob SHA and byte size;
3. enumerate direct textual references to the candidate path;
4. enumerate CI/hook/import/runtime references not discoverable by plain text alone where applicable;
5. classify the file as current authority, compatibility pointer, source, test, tool, generated artifact, receipt or historical donor;
6. refuse the move if the authority role is ambiguous.

## Phase 1 — move low-risk documentation/history first

Eligible first wave:

- historical root-only prose that is not a current authority pointer;
- archived dashboards/reports with no runtime importer;
- old compatibility instructions whose references can be redirected safely.

Acceptance:

- byte identity verified;
- all known links updated or compatibility redirect retained;
- no source/runtime import changed;
- Git history remains traceable;
- evidence text preserves the old path as historical provenance when needed.

## Phase 2 — dev/config surfaces

Examples: contributor instructions, non-secret sample config, developer metadata.

Additional acceptance:

- local/CI consumers resolve the new location;
- no secret-loading behavior changes accidentally;
- `.github/` and host-required dot-directories are **not** moved unless the host actually supports relocation. GitHub requires `.github/` semantics at expected repository paths; a visual topology target cannot override host conventions.

Result classification may therefore be `ADAPTED` rather than literal four-entry root if a platform-mandated root/dot path must remain.

## Phase 3 — authority pointers and hooks

High risk. Examples include current authority pointer files and `.claude/` lifecycle hooks.

Rules:

- never duplicate mutable authority;
- if a root pointer is required for boot/reentry, prefer a tiny immutable redirect/pointer over a copied authority body;
- prove real hook firing after any hook-path change;
- prove the hook reads/writes the intended canonical state path;
- preserve fail-closed behavior when the target is absent or stale.

A cosmetically pure root is lower priority than a correct native host contract.

## Phase 4 — source/runtime trees

Do not mass-relocate runtime trees in a documentation curation pass.

A source-tree move requires:

- import/module path map;
- packaging/build map;
- test discovery map;
- shell/script relative-path map;
- CI/workflow map;
- data/receipt path map;
- external consumer compatibility assessment;
- clean exact-head non-provider regression;
- rollback plan.

Prefer leaving a stable mature tree in place and exposing it through `DEV_SOURCE_RESEARCH/README.md` over renaming thousands of paths for aesthetics.

## Root inventory classifications

Use these dispositions:

- `KEEP_PLATFORM_REQUIRED` — host semantics require the path, e.g. `.github/` unless proven otherwise.
- `KEEP_BOOT_POINTER` — tiny root pointer materially reduces dangerous repo scans/reentry ambiguity.
- `MOVE_SAFE_DOC` — documentation/history with no runtime path dependency.
- `MOVE_AFTER_REFERENCE_REWRITE` — static consumers exist but are bounded.
- `MOVE_AFTER_EXECUTABLE_PROOF` — source/hook/runtime path.
- `HISTORICAL_PATH_IMMUTABLE` — evidence/reproducibility cost exceeds cosmetic value.
- `REMOVE_ONLY_AFTER_SUCCESSOR` — obsolete current-facing surface, but deletion waits for a proven successor.

## Dependency manifest format

For each planned batch, write a machine-readable manifest similar to:

```json
{
  "schema": "ROOT_PATH_MIGRATION/v1",
  "base_main": "<sha>",
  "items": [
    {
      "from": "old/path",
      "to": "DEV_SOURCE_RESEARCH/repository/.../path",
      "blob_sha_before": "<sha>",
      "classification": "MOVE_AFTER_REFERENCE_REWRITE",
      "known_references": ["path/a", "path/b"],
      "byte_identity_required": true,
      "compatibility_surface": "none|pointer|redirect",
      "tests": ["exact test command or static gate"],
      "rollback": "revert commit <sha>"
    }
  ]
}
```

## Acceptance for the eventual topology

The migration is accepted only when:

1. the human entry path is obvious;
2. the AI installer can start without scanning root;
3. technical source remains discoverable through the dev/research index;
4. current authority has exactly one mutable source;
5. moved source preserves byte identity unless explicitly edited;
6. all platform-mandated root/dot paths are documented exceptions rather than hidden violations;
7. relevant hooks, tests and runtime paths have executable evidence after the move;
8. old evidence remains reproducible or explicitly records an immutable historical path;
9. root `README.md` is changed only by an explicit user request in that turn.

## Current Trigger-3 decision

`ADDITIVE_SEED + MIGRATION_PLAN`, not destructive cleanup.

Reason: current `main` is active, root has dependency-bearing surfaces, supervisor 9.13 identifies live caller/control gaps, and PR #2050 already contains the high-value safety repair. A mass move now would have lower information gain and higher regression risk than preserving a precise migration contract.
