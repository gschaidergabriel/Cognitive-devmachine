# Root migration map

## Goal

Final public root target:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

The target is desirable, but **root aesthetics are lower priority than executable compatibility and authority resolution**.

## Current observed root at Trigger-3 re-entry

Observed at `main@854f6bc87780f4a5242489a6c807d186b16a8c3d`.

The root contains, among other entries:

- `.claude/`, `.github/`, `.env.example`, `.gitignore`
- `000_CLAY_CURRENT.md`
- `000_FRANK_GLOBAL_RESEARCH_ENTITY_AUTOBOOT.txt`
- `000_FREE_SWARM_LIVE_DASHBOARD.md`
- `AGENTS.md`
- `AUTHORITATIVE_STATE_RESOLUTION.md`
- `CLAUDE.md`
- `CLAUDE_CODE_INTRODUCTION.md`
- `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`
- `CLAYVERSE_CANONICAL_DIRECTIVE.md`
- `CLAY_EXECUTION_AUTHORITY.md`
- `JOIN_RAE_CLAUDE_CODE.txt`
- `PROJECT_AUTO_BOOT_KERNEL_FINAL.txt`
- `PROJECT_SOURCE_SINGLE_BOOTSTRAP*.txt`
- `RAE_VNEXT_RUNTIME.md`
- `ZZZ_FREE_SWARM_RESULTS.md`
- `agentZero/`, `agentzeroforschung/`, `benchmarks/`, `dump/`, `dump archive/`
- `frank_reference/`, `free swarm/`, `governance/`
- `rae_core/`, `receipts/`, `research_entity/`, `research_sources/`
- `runtime_checks/`, `schemas/`, `tests/`, `the artefact/`, `tools/`
- unusual root artifacts such as `gemeinsamer State)`, `libc.malloc_trim(0)` and `madvise(ptr, length, MADV_FREE);`

This list is an observed high-value root sample, not a claim that the full tree has been exhaustively classified by this document.

## Why not move everything now?

Several root paths are active compatibility/authority entry points. Examples include `CLAY_EXECUTION_AUTHORITY.md`, `AGENTS.md`, `CLAUDE.md`, bootstrap files and workflow/tool paths that may be referenced by:

- GitHub Actions;
- scripts using repository-relative hard-coded paths;
- external/local launchers;
- ChatGPT/Claude/Codex project boot instructions;
- receipts that bind exact historical paths;
- tests and schemas;
- current operator habits.

A mass move without a consumer audit could create a repository that **looks** clean while boot, evidence resolution, tests or runtime callers silently fail.

## Migration law

A root item may move only when all relevant gates pass:

1. **Classify** — CURRENT_AUTHORITY, CURRENT_RUNTIME, CURRENT_TOOLING, CURRENT_DOC, HISTORICAL_EVIDENCE, GENERATED/DERIVED, or UNKNOWN.
2. **Search consumers** — exact repository references, workflows, imports, shell paths, docs, tests and external bootstrap contracts where observable.
3. **Choose compatibility strategy** — direct move, wrapper/shim, generated pointer, or historical immobility.
4. **Preserve evidence** — do not rewrite historical receipt paths/hashes merely to make the tree pretty.
5. **Test old entry path** if compatibility is promised.
6. **Test new entry path**.
7. **Verify current authority resolution** from a clean checkout.
8. **Verify no duplicate authority** was created.
9. **Move one dependency cluster at a time**, not the whole root in one opaque rename.
10. **Re-enter main** after each cluster because parallel work can add new consumers.

## Proposed destination classes

| Current class | Target under `DEV_SOURCE_RESEARCH/repository/` | Rule |
|---|---|---|
| historical bootstraps/directives | `history/bootstraps/` | move only with compatibility pointers if still consumed |
| technical top-level reports/dashboards | `reports/` | preserve source identity; generated publishers must be updated first |
| runtime/tool source directories | `source/` or retained compatibility shim | do not move until imports/workflows are proven safe |
| research archives | `research_archive/` | preserve historical paths when hashes/receipts depend on them; an index may be preferable to a move |
| governance/authority | `governance/` | **do not hide authority behind an undocumented move**; update every resolver atomically |
| tests/schemas/runtime checks | `verification/` | only after path consumers and CI are updated together |
| obvious accidental root artifacts | `quarantine/root_artifacts/` | first prove no current consumer/reference |

## First safe migration tranche

This Trigger-3 change itself is additive:

- create `HUMAN_READ_THIS/`;
- create `DEV_SOURCE_RESEARCH/`;
- create `AI_START_HERE_DO_NOT_SCAN_REPO/`;
- leave `README.md` unchanged because Trigger-3 explicitly forbids silent root README rewriting;
- leave existing root entries unchanged until reference audit.

This improves navigability without changing any existing path contract.

## Next exact repository-topology gate

Generate a **complete root consumer manifest** from an exact current checkout:

```text
for every root entry R:
  classify R
  list exact in-repo consumers
  list workflow consumers
  list boot/authority consumers
  mark path-hash/receipt sensitivity
  select MOVE | SHIM | INDEX_ONLY | RETAIN
```

Acceptance for the final four-entry root requires:

- clean checkout authority resolution PASS;
- CI/path tests PASS;
- installer entry PASS without scanning the old root;
- no missing historical evidence;
- no second authority created;
- `git diff --no-index` or blob-identity proof for source trees meant to remain byte-identical;
- explicit migration receipt mapping every old path to new path/shim/status.

Until then, root migration status is **PREPARED_NOT_RUN**, not COMPLETE.
