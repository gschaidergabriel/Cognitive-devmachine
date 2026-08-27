# Root topology migration — evidence-preserving convergence

## Target

The canonical public root target for Triggerword 3 is deliberately small:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

At the base head used for this pass (`854f6bc87780f4a5242489a6c807d186b16a8c3d`) the actual repository root is still much larger and contains historical/current control files, source trees, automation configuration and research artifacts.

**Status:** `NOT_YET_PHYSICALLY_CONVERGED`.

This trigger pass creates the three missing public layers but does **not** mass-move existing root content. That is intentional: path moves can break imports, workflows, bootstrap contracts, GitHub links and exact evidence identities. A prettier root is not worth silently damaging reproducibility.

---

## Migration invariant

A root cleanup is accepted only when all of the following are true:

1. byte identity of moved historical/source artifacts is preserved unless a source edit is intentional;
2. every executable/import/workflow path affected by a move is enumerated;
3. dynamic/relative path replacements are tested before deleting the old path;
4. canonical authority remains singular — no copied second `BOOTSTRAP`, `PROGRAM_STATE`, DB or effect journal becomes authoritative;
5. old commit/blob links remain valid through Git history;
6. current in-repo links are rewritten and link-checked;
7. AI installers do not require scanning the whole root;
8. rollback is one Git revert, not an undocumented manual restoration;
9. README changes happen only under an explicit README-scoped instruction;
10. evidence receipts distinguish `MOVE_ONLY_BYTE_IDENTICAL` from `SOURCE_MODIFIED`.

---

## Proposed physical layout

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
  README.md
  research/
  repository/
    archive/
    authority/
    continuity/
    legacy-root/
    automation/
  source/
    entityos/
    hcu/
    agentzero/
    tools/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

This is a **curation target**, not a declaration that those exact subdirectory names already own canonical runtime authority.

---

## Why no bulk move in this commit

`CURRENT_SOURCE`

The current root contains bootstrap/authority/control surfaces and source paths consumed by existing scripts/workflows. Current history also contains fast-moving parallel commits.

`INFERENCE`

A bulk move without a path-dependency census would create a high probability of "documentation cleanup broke the machine" failures and would reduce rather than increase reconstructability.

Therefore physical convergence is split into explicit phases.

---

## Phase A — entry layers (this Triggerword 3 pass)

- [x] Create `HUMAN_READ_THIS/`.
- [x] Create `DEV_SOURCE_RESEARCH/`.
- [x] Create `AI_START_HERE_DO_NOT_SCAN_REPO/`.
- [x] Add machine-readable archive pointers instead of copying the whole evidence store into prose.
- [x] Add explicit current authority/evidence snapshot.
- [x] Preserve root README unchanged.

Acceptance: new readers and AI tools can start without a whole-repo scan while historical/current paths remain intact.

---

## Phase B — path dependency census

Before moving any existing root item, generate a machine-readable table with at least:

```text
old_path
blob_sha
kind = source|authority|config|doc|workflow|archive|generated
importers[]
workflow_references[]
doc_links[]
runtime_string_references[]
canonical_authority_role
move_target
compatibility_shim_required
byte_identical_move
validation_command
```

Required searches:

- Python imports and `Path(...parents...)` assumptions;
- shell scripts and hard-coded relative paths;
- GitHub Actions paths;
- package/build configuration;
- bootstrap/authority path literals;
- internal Markdown links;
- external/public links where a compatibility redirect is impossible;
- tests that use repository-root fixture locations;
- tools that derive `REPO_ROOT` by parent count.

Recent Frankenstein source is one reason this matters: the current bugfix/orchestrator code derives repository roots and imports by explicit relative locations.

---

## Phase C — move-only technical clutter

Move only entries classified `MOVE_ONLY_BYTE_IDENTICAL` with no unresolved canonical-path role.

Preferred destination:

`DEV_SOURCE_RESEARCH/repository/legacy-root/` for legacy root docs/config that must remain discoverable but are not active public entry points.

For each batch:

1. record pre-move blob SHA;
2. move with Git rename semantics where possible;
3. update references;
4. verify post-move bytes/hash;
5. run path/import/link tests;
6. write a move receipt;
7. only then remove compatibility shims if no longer needed.

---

## Phase D — source-tree relocation

Source relocation is higher risk than documentation relocation.

Do not move `agentZero/`, `research_entity/`, `tools/`, `the artefact/`, governance or runtime trees merely to satisfy a visual target until:

- all imports and runtime string paths are known;
- workflow/test coverage exists for the new locations;
- exact evidence references can continue resolving;
- canonical authority files have one unambiguous location;
- any compatibility symlink/shim behavior is supported on intended hosts.

A source tree may remain below a technical subroot longer than the public docs if moving it would damage evidence or compatibility.

---

## Phase E — root reduction gate

Only when Phases B-D are green should the physical root be reduced to:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

At that point the root README can be revised **only if the owner/user explicitly requests README work**, because Triggerword 3 itself forbids silently rewriting it.

---

## Required validator before final root reduction

The future validator should fail closed on:

- broken imports;
- missing workflow paths;
- changed byte hashes on move-only files;
- duplicate canonical authority surfaces;
- missing historical evidence pointers;
- broken AI start route;
- root entries outside the four allowed entries;
- README modified without an explicit README-scoped trigger/receipt;
- old path removed before all current references migrate.

Suggested final output:

```text
ROOT_TOPOLOGY: PASS|FAIL
public_root_entries: [...]
move_only_hash_matches: n/n
imports: PASS|FAIL
workflows: PASS|FAIL
internal_links: PASS|FAIL
authority_uniqueness: PASS|FAIL
ai_bootstrap_without_root_scan: PASS|FAIL
readme_scope_authorized: true|false
```

The objective is not minimal page count. It is **minimal public surface with maximal reconstructability**.
