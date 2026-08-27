# Root topology migration plan

**Status:** `PREPARED_NOT_RUN`  
**Observed base:** `main@854f6bc87780f4a5242489a6c807d186b16a8c3d`

The intended public root is:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

The current repository root does **not** yet have that shape. This trigger adds the three navigation layers but deliberately does not mass-move technical files and does not rewrite the root `README.md`.

## Why the mass move is deferred

Repository cleanup is not evidence-neutral. A path move can break:

- Python imports and `sys.path` assumptions;
- scripts that derive `REPO_ROOT` from `__file__`;
- shell scripts and systemd units;
- GitHub Actions paths and filters;
- test fixtures and snapshots;
- documentation deep links;
- receipts whose exact historical path is part of provenance;
- local/VPS launch scripts outside the repository;
- artifact hashes and manifests;
- downstream clones or tools that address a path directly.

Moving first and repairing later would make the root prettier by spending reproducibility.

## Migration law

A technical root item may move under `DEV_SOURCE_RESEARCH/repository/` only when all of the following are true:

1. its current blob SHA is recorded;
2. source bytes after the move are identical unless an intentional source edit is separately reviewed;
3. repository references to the path are inventoried;
4. import/launch/CI/automation consequences are identified;
5. historical receipts and evidence links remain resolvable or receive an explicit compatibility pointer;
6. runtime-sensitive paths have a deterministic regression test or are left in place;
7. no second canonical copy is created;
8. the migration commit records old path → new path → blob identity → compatibility action;
9. current authority is re-entered immediately before the move;
10. root `README.md` remains unchanged unless explicitly authorized in that user turn.

## Proposed phases

### Phase R0 — inventory

Generate a machine-readable root inventory containing, per item:

```json
{
  "old_path": "...",
  "blob_sha": "...",
  "kind": "source|config|doc|receipt|entrypoint|generated|unknown",
  "references": [],
  "runtime_sensitive": true,
  "historical_identity_sensitive": false,
  "proposed_action": "MOVE|KEEP_ROOT|COMPAT_POINTER|REVIEW"
}
```

No moves in R0.

### Phase R1 — reference graph

Search exact repository references plus known host/launch surfaces. Classify each reference:

- import/runtime;
- CI/workflow;
- docs/navigation;
- evidence/provenance;
- external/local deployment assumption;
- generated/obsolete.

Unknown references fail closed to `KEEP_ROOT`.

### Phase R2 — low-risk documentation moves

Move only items proven to have no runtime/path identity requirement. Preserve Git rename history and validate links.

### Phase R3 — source/config moves

Move one dependency family at a time. Run the narrowest deterministic regressions that establish path compatibility. Do not combine semantic refactors with topology moves.

### Phase R4 — compatibility cleanup

Only after dependents have migrated, remove temporary pointers/shims that have explicit expiry evidence. Do not delete historical evidence just because the new navigation layer can find it another way.

### Phase R5 — public-root acceptance

Acceptance requires:

- exact four-item public-root target achieved, excluding Git/platform metadata that must remain at root;
- no duplicate current authority;
- required launch/import/test paths green at their stated scopes;
- all technical source remains discoverable from `DEV_SOURCE_RESEARCH/`;
- AI installation does not require a root scan;
- byte/path migration manifest complete;
- no claim that historical files originally lived at their new locations.

## Current trigger-3 delta

Created additively:

- `HUMAN_READ_THIS/`
- `DEV_SOURCE_RESEARCH/`
- `AI_START_HERE_DO_NOT_SCAN_REPO/` when its installer layer is committed

Not performed:

- no mass source move;
- no deletion;
- no root README rewrite;
- no authority-file relocation;
- no provider/runtime execution.

That is a partial topology advance with an explicit safety boundary, not a claim that repository cleanup is complete.