# Triggerword 3 root migration plan

**Status:** `PREPARED_NOT_RUN`

Triggerword 3 wants the human-facing repository root to converge toward:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

The current root does not physically satisfy that target. This protocol prevents “cleaning” the root by breaking GitHub behavior, host-native discovery, imports, workflows, links, or historical reproducibility.

The root `README.md` remains untouched unless the owner explicitly asks for README work.

## Invariants

1. No blind bulk move.
2. Pure relocation preserves file bytes; an edit during relocation is an intentional source change.
3. No duplicate semantic authority.
4. Inventory all active references before moving a path.
5. Preserve historical receipt/source identity even when current-facing navigation changes.
6. Unknown dependency means `BLOCKED_UNKNOWN_DEPENDENCY`.
7. Re-enter current `main` and authority after material parallel movement.

## Root classes

Every top-level path must receive one class:

| Class | Meaning | Default |
|---|---|---|
| `PUBLIC_ENTRY` | Triggerword 3 human navigation | retain |
| `HOST_REQUIRED` | external tool discovers exact root path | retain until verified adapter |
| `GITHUB_REQUIRED` | Git/GitHub convention requires location | retain unless exact replacement exists |
| `SOURCE_RUNTIME` | executable product/research source | move only after dependency audit |
| `EVIDENCE_ARCHIVE` | receipts/history/research state | move/index with provenance mapping |
| `COMPATIBILITY_SHIM` | minimal pointer to moved canonical content | allowed only when explicit/non-authoritative |
| `SAFE_TO_MOVE` | all consumers closed | eligible for relocation |
| `UNKNOWN` | dependency not established | fail closed |

## Known fixed-location risks

Likely blockers include:

- `.github/` — GitHub Actions/workflow conventions;
- `.gitignore` — repository-root ignore semantics;
- `CLAUDE.md` / `.claude/` — Claude Code project discovery/lifecycle surfaces;
- `AGENTS.md` — Codex-style project instruction discovery;
- current authority/bootstrap pointers referenced from scripts/docs.

Therefore there are two distinct goals:

1. **strict physical root** — literally only the four target entries;
2. **canonical public root** — those four are the only human navigation entry points while fixed-location machine-control files remain documented exceptions.

Current evidence favors the second interpretation unless verified adapters eliminate the fixed-location requirements. That is an engineering inference, not an owner-authority rewrite.

## Migration phases

### 0. Freeze source identity

Record current `main` SHA, current root tree identity, and supervisor authority. If `main` changes materially, regenerate the inventory.

### 1. Read-only inventory

Run:

```bash
python3 DEV_SOURCE_RESEARCH/repository/root_migration_inventory.py \
  --repo-root "$(git rev-parse --show-toplevel)" --pretty
```

It makes no changes. It emits root paths, conservative classes, hashes for root files, candidate text references, proposed destinations, and unresolved fail-closed items.

### 2. Disposition

Each non-public root path gets exactly one disposition:

```text
MOVE_BYTE_IDENTICAL
MOVE_AND_INTENTIONALLY_PATCH_REFERENCES
KEEP_TEMPORARILY_COMPATIBILITY_BLOCKER
RETIRE_WITH_EVIDENCE
GENERATED_OR_EXTERNAL_DO_NOT_MIGRATE
UNKNOWN_FAIL_CLOSED
```

### 3. Old→new identity mapping

Preferred technical destination pattern:

```text
DEV_SOURCE_RESEARCH/repository/<old-root-path>
```

Preserve subtrees where possible. For a pure move, bind old path, new path, old blob/hash, new blob/hash, and require byte identity.

### 4. Patch consumers first

For paths that require intentional reference changes, patch and verify consumers before removing the old path. Historical immutable receipts are not rewritten merely to make links prettier.

### 5. Validation

Before deleting an old path:

```text
[ ] no unresolved active source/workflow reference
[ ] relevant Python syntax/import checks pass
[ ] shell syntax checks pass where applicable
[ ] workflow YAML and referenced paths remain valid
[ ] curated Markdown links resolve
[ ] installer/host discovery still works
[ ] historical immutable evidence remains reconstructable
[ ] pure move bytes match
[ ] current authority still matches migration assumptions
```

### 6. Compatibility blockers

If a host truly requires a root file:

1. use an official configurable alternate location if proven;
2. otherwise use a tiny explicit non-authoritative pointer shim if the host supports it;
3. otherwise retain the root file and report strict physical topology as not reached.

Do not duplicate the full current instruction body in two locations.

## Acceptance

Root topology becomes `PASS` only when every non-target entry has a disposition, no unknown dependency remains, verified fixed-location exceptions are resolved or explicitly admitted, moves preserve identity where claimed, and active workflows/installers/tests still function.

Until then:

```text
ROOT_TOPOLOGY = IN_PROGRESS
```

## Counterhypothesis

**Hypothesis:** a cleaner public root reduces human/AI navigation cost and accidental authority confusion.

**Counterhypothesis:** physical relocation creates more shims and fixed-path exceptions than it removes, increasing operational ambiguity.

**Discriminator:** compare first-task navigation cost and broken-reference/compatibility count before and after a dependency-safe candidate migration. Reject a visually cleaner migration if operational ambiguity increases.
