# Root topology migration manifest

Trigger-3 public-root target:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

This branch intentionally does **not** mass-move the current root yet. The base root contains active authority files, host integration files, workflows, runtime/test paths, historical bootstrap files, research trees, receipts, and several anomalous filenames. Moving them without a verified reference map risks breaking current runtime, CI, installers, provenance and authority resolution.

## Base identity

- repository: `gschaidergabriel/clay-global-research-entity`
- base commit: `854f6bc87780f4a5242489a6c807d186b16a8c3d`
- root README modification in this trigger: **forbidden by trigger contract / not performed**

## Observed root classes at the base commit

### Public/host entry files

Examples:

- `README.md`
- `AGENTS.md`
- `CLAUDE.md`
- `CLAUDE_CODE_INTRODUCTION.md`
- `JOIN_RAE_CLAUDE_CODE.txt`

Target treatment: keep only the public README at root; move host-specific technical entry material under `DEV_SOURCE_RESEARCH/repository/host_integration/` **only after** current host loaders/hooks are proven not to require the original root paths, or after compatibility stubs/redirect contracts are explicitly designed and tested.

### Authority/current-state surfaces

Examples:

- `CLAY_EXECUTION_AUTHORITY.md`
- `AUTHORITATIVE_STATE_RESOLUTION.md`
- `000_CLAY_CURRENT.md`
- `PROJECT_AUTO_BOOT_KERNEL_FINAL.txt`
- `PROJECT_SOURCE_SINGLE_BOOTSTRAP*.txt`

Target treatment: do **not** move until every current authority resolver, workflow, external bridge and host integration is mapped. Authority relocation is a control-plane change, not documentation cleanup.

### Historical/compatibility bootstrap material

Examples:

- `000_FRANK_GLOBAL_RESEARCH_ENTITY_AUTOBOOT.txt`
- `CLAYVERSE_CANONICAL_DIRECTIVE.md`
- legacy bootstraps

Target treatment: move under a history/provenance subtree once all exact-path consumers are identified. Preserve byte identity where possible; do not rewrite historical evidence to match newer naming.

### Research/runtime trees

Observed root directories include:

- `research_entity/`
- `research_sources/`
- `receipts/`
- `runtime_checks/`
- `schemas/`
- `tests/`
- `tools/`
- `benchmarks/`
- `governance/`
- `the artefact/`
- `rae_core/`
- `frank_reference/`
- `agentZero/`
- `agentzeroforschung/`
- `dump/`
- `dump archive/`
- `free swarm/`

Target treatment: converge technical/research content beneath `DEV_SOURCE_RESEARCH/repository/` by **tree-preserving moves** only after reference analysis. Do not duplicate these trees into the new layer.

### Root anomalies requiring explicit handling

The base tree includes unusual root filenames such as:

- `gemeinsamer State)`
- `libc.malloc_trim(0)`
- `madvise(ptr, length, MADV_FREE);`

These must be classified before deletion or relocation. A strange filename can still be provenance or an accidentally referenced artifact. No silent cleanup.

## Safe migration algorithm

1. Freeze exact base commit for the migration batch.
2. Enumerate all top-level entries from Git tree, not a truncated UI listing.
3. For every candidate move, search exact path/name references in:
   - source
   - tests
   - workflows
   - shell scripts
   - Python imports/path arithmetic
   - docs/installers
   - governance/authority resolvers
4. Classify each reference as runtime-critical, CI-critical, installer-critical, historical-only, or dead.
5. Move byte-identically where source modification is not intended.
6. Update runtime/CI/installer references in the **same atomic migration change**.
7. Add compatibility shims only when an external consumer cannot be migrated atomically; give every shim an explicit retirement condition.
8. Run static path-reference audit.
9. Run task-relevant tests and host entry probes.
10. Verify authority resolution still selects the same current owner/inbox steering.
11. Compare moved file blob identities where byte preservation is required.
12. Only then remove obsolete root paths.

## Acceptance gates

A root-convergence PR may claim PASS only if all of the following are observed:

- root contains only the approved public entries plus unavoidable VCS/platform control entries whose location is structurally required (for example `.gitignore`/`.github` if GitHub operation requires them; any exception must be explicit);
- no broken current imports/path arithmetic;
- no broken workflows;
- no broken authority resolution;
- no broken Claude/Codex/other host entry route that is intended to remain supported;
- historical evidence blobs preserved or intentionally transformed with a receipt;
- all moved technical content is discoverable from `DEV_SOURCE_RESEARCH/`;
- AI installation does not require a root scan;
- root `README.md` has not been silently rewritten by this trigger.

## Why the move is deferred in this branch

The current repository is moving rapidly and the newest supervisor has an active P0 control/provider boundary problem. A cosmetic mass move now would create a large diff that could hide or break those higher-priority control paths. This Trigger-3 branch establishes the **destination topology and migration contract first**, then makes the destructive reorganization a separately reviewable, reference-verified change.

Status: `PREPARED_NOT_RUN` for the mass relocation. The new entry layers themselves are implemented on this branch.