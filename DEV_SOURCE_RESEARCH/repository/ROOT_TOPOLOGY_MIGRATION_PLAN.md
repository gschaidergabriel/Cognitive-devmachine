# Root topology migration plan — additive first, destructive later

**Status:** `PREPARED_NOT_RUN`  
**Goal:** eventually make the public repository root human-legible without losing evidence, breaking deep links, or creating duplicate authorities.

Target public root:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

Root `README.md` is deliberately not rewritten by this Trigger-3 pass.

## Current observation

The repository root is not yet at the target topology. At the start of this pass it still contained many technical/current/historical surfaces directly at root (`000_*`, `AGENTS.md`, authority/docs, configuration, directories, etc.).

That is a navigability problem, but a blind `mv` is worse. Some root files are current authority/bootstrap surfaces, some are historical provenance, and many may be referenced by tests, scripts, documentation, external links, or active parallel branches.

## Migration invariant

A topology cleanup is accepted only if it preserves:

1. exact file bytes unless a source edit is intentional;
2. Git lineage/provenance;
3. current authority semantics;
4. executable imports/paths;
5. deep-link discoverability or an explicit redirect/mapping strategy;
6. test behavior at the same scope;
7. no second source of truth;
8. negative evidence and historical receipts.

## Required pre-move inventory

Before moving one existing root item, freeze an exact inventory at an exact `main` SHA:

```text
path
Git blob SHA / tree SHA
size
kind (file/dir/symlink)
current authority role?
known code references
known documentation links
known CI/config semantics
historical/provenance only?
proposed destination
move-safe? yes/no/unknown
```

Directories need a recursive tree identity and a path-reference scan. Generated/vendor/binary material can be classified separately but not silently discarded.

## Proposed destination law

Technical clutter that is not required by GitHub/host conventions should converge beneath:

```text
DEV_SOURCE_RESEARCH/repository/
```

But convention-bound files stay where their host requires them. Examples may include `.github/`, `.gitignore`, tool configuration, or other root-discovered metadata. The four-item target is therefore a **public human-facing target**, not permission to break platform-required control files.

If an exact host requirement conflicts with the aesthetic target, correctness wins and the exception is documented.

## Staged procedure

### Stage A — additive navigation

Already safe to do:

- create `HUMAN_READ_THIS/`;
- create `DEV_SOURCE_RESEARCH/`;
- create `AI_START_HERE_DO_NOT_SCAN_REPO/`;
- create machine-readable source/evidence indices;
- deep-link canonical/historical sources in place.

No old path breaks.

### Stage B — exact root census

At one exact current SHA:

1. enumerate root completely;
2. record blob/tree identities;
3. classify each item;
4. scan current source/tests/docs for exact path references;
5. inspect active branches/PRs touching those paths;
6. derive an old→new mapping.

Output should be machine-readable JSON plus a human review table.

### Stage C — move simulation

Before commit:

- simulate destination tree;
- reject collisions;
- reject duplicate authority surfaces;
- identify path consumers that require edits;
- calculate expected changed-file set;
- verify bytes remain identical for pure moves.

### Stage D — bounded migration commits

Move one coherent family at a time, not the whole root in one opaque commit.

Each family commit should include:

```text
old paths
new paths
old/new blob identity evidence
references updated
tests run
negative/blocked references
scope of acceptance
```

### Stage E — link/import regression

At minimum verify:

- Python/import path consumers where applicable;
- Markdown relative links;
- scripts that use repo-root-relative paths;
- authority/bootstrap discovery paths;
- CI/workflow/config expectations;
- AI installer entry still works without root scan.

### Stage F — final public-root review

Only after staged moves are green:

- verify a human can start at `README.md` / `HUMAN_READ_THIS/`;
- verify technical readers can reach source through `DEV_SOURCE_RESEARCH/`;
- verify AI hosts can start at `AI_START_HERE_DO_NOT_SCAN_REPO/`;
- verify no essential research/evidence became unreachable;
- verify root README changes, if any, are separately owner-requested/reviewed.

## Why this is not done in the current pass

`triggerword 3` demands maximum useful compression and safe repository topology, not maximum file movement. During this pass `main` was moving concurrently and a provider-authority blocker was being repaired in parallel. A mass root rewrite without a frozen exact census would violate the same evidence/provenance discipline the curation is intended to teach.

Therefore current status is:

```text
ADDITIVE_NAVIGATION: ADOPTED
MACHINE_INDEX: ADOPTED
ROOT_MASS_MOVE: PREPARED_NOT_RUN
ROOT_README_REWRITE: NOT_REQUESTED
```

## Acceptance falsifiers

A future migration fails if any of these occurs:

- moved bytes differ without intentional source change;
- current authority discovery breaks;
- tests/imports depend on old path and are not repaired;
- root cleanup creates duplicate current files at old and new locations;
- historical evidence is deleted to make the tree look cleaner;
- links silently rot;
- platform-required root metadata is moved for aesthetics;
- migration claims completeness without a frozen inventory denominator.

The root should become simpler because the evidence graph is better organized, not because evidence disappeared.
