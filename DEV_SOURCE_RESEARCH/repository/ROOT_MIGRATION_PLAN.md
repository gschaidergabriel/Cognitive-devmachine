# Root migration plan — Trigger 3

Status: `PREPARED_NOT_RUN` beyond creation of the three new entry-layer directories.

Goal: make the repository human-legible without breaking executable paths, authority pointers, imports, CI, historical receipts, or reproducibility.

Target public entrance:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

Hidden Git/GitHub infrastructure may require root placement for semantics (`.gitignore`, `.github/`). Treat that as infrastructure, not public navigation clutter.

## Current problem

The current root mixes human docs, worker boot files, current authority pointers, historical authority text, dashboards, source trees, tests, tools, archives, research trees and accidental-looking artifacts. Examples include `000_*`, `AGENTS.md`, `CLAUDE*.md`, compiler/boot manifests, `agentZero/`, `benchmarks/`, `dump*`, `frank_reference/`, `free swarm/`, `governance/`, `rae_core/`, `receipts/`, `research_entity/`, `research_sources/`, `runtime_checks/`, `schemas/`, `tests/`, `tools/`, `the artefact/`, plus suspicious root names such as `gemeinsamer State)`, `libc.malloc_trim(0)` and `madvise(ptr, length, MADV_FREE);`.

Do **not** delete or move suspicious names merely because they look accidental. First prove whether they are referenced and whether their bytes are historical evidence.

## Migration laws

1. Use `git mv` or equivalent lineage-preserving moves.
2. For files whose content need not change, verify byte identity before/after.
3. Search all tracked references before moving a path.
4. Update imports, scripts, workflows, docs and receipts only where current-facing references must move.
5. Historical receipts may retain historical paths; add resolution metadata rather than rewriting history.
6. Never create a duplicate current authority to make a move easier.
7. Never move `.github/` or `.gitignore` for cosmetic compliance if that changes platform behavior.
8. Root `README.md` is not rewritten by Trigger 3 unless explicitly requested by the owner.
9. Move one dependency domain at a time and run its exact regression suite before the next domain.
10. No mass move receives runtime/product credit merely because Git accepts it.

## Phases

### Phase 0 — front doors

**Status: SOURCE_READY in this Trigger-3 pass.**

Create:

- `HUMAN_READ_THIS/`
- `DEV_SOURCE_RESEARCH/`
- `AI_START_HERE_DO_NOT_SCAN_REPO/`

No existing path moved. No root README rewrite.

### Phase 1 — classify every root entry

Produce a machine-readable inventory with:

- path
- blob/tree SHA
- type
- current references
- authority role
- executable/path-sensitive role
- proposed destination
- `MOVE_SAFE`, `MOVE_REQUIRES_REWRITE`, `ROOT_REQUIRED`, `HISTORICAL_FREEZE`, or `UNKNOWN`

Acceptance: every current root entry classified; zero `UNKNOWN` before bulk moves.

### Phase 2 — low-risk standalone documentation

Move standalone non-authority docs and dashboards whose readers can follow updated links. Keep redirect/index stubs only when an active consumer still requires the old path; remove stubs when consumers migrate.

Acceptance: byte identity for content-only moves, all references updated, no duplicate authority.

### Phase 3 — historical archives

Move historical/donor collections beneath `DEV_SOURCE_RESEARCH/repository/history/` only after proving no executable loader depends on their current top-level path.

Historical names and embedded paths remain untouched inside receipts unless a separate mapping accompanies them.

### Phase 4 — executable source trees

Highest risk. Candidate trees such as `tools/`, `tests/`, `schemas/`, `research_entity/`, `the artefact/` and runtime directories have many code/import/path dependencies.

Before each move:

- enumerate imports and shell/path references;
- identify packaging and `sys.path` assumptions;
- identify GitHub Actions/workflow references;
- freeze source tree SHA;
- run baseline tests;
- move one domain;
- run same tests;
- compare generated artifacts/receipts where determinism is expected.

Do not use symlinks as a universal compatibility trick: cross-platform behavior and archive/ZIP handling differ.

### Phase 5 — authority/boot surfaces

Move only after every consumer resolves the new path dynamically. Authority pointers must have a single canonical successor and successor-dynamic tests.

### Phase 6 — root acceptance

Acceptance checklist:

- public navigation is only README + the three entrance directories;
- hidden root infrastructure retained only where platform semantics require it;
- no competing authority copy;
- no broken imports/workflows/installers;
- historical evidence remains reproducible;
- exact current authority re-entry works from every supported installer route;
- clean checkout regression suite passes at the claimed scope;
- root scan is unnecessary for human or AI onboarding.

## Why not do it all in one commit?

Because a repository is not a cupboard. Moving a file can change Python imports, shell scripts, CI, relative links, historical evidence interpretation and installer behavior. Trigger 3 optimizes navigability **and** reconstruction fidelity; breaking the machine to make the directory tree prettier would fail the trigger.
