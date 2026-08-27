# Triggerword 3 — root topology constraints before relocation

**Date:** 2026-08-27  
**Organ:** GPT-5.6 Sol / ChatGPT  
**Canonical main re-entered for this check:** `3c3dbe5020f57065f47bd4d0a2dce3c537128797`  
**Branch:** `trigger3/frankenstein-curation-20260827-gpt56sol`

## Result

The Triggerword-3 target

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

is a sound **human/public navigation target**, but it is **not currently safe as a literal four-entry filesystem-root invariant**.

At least one hard external platform constraint and several live project-discovery/runtime constraints require root-resident compatibility surfaces. Therefore the repository must distinguish:

```text
PUBLIC_NAV_ROOT_TARGET
```

from

```text
FILESYSTEM_ROOT_REQUIRED_EXCEPTIONS
```

rather than deleting/moving required machinery to make a directory listing look clean.

**Disposition:** `CONTRADICTED_AS_LITERAL_FILESYSTEM_INVARIANT / ADOPTED_AS_PUBLIC_NAVIGATION_INVARIANT`.

---

## 1. Hard external constraint: GitHub Actions

GitHub’s current official documentation states that workflow definitions live in `.github/workflows` and that GitHub searches the `.github/workflows` directory **in the root of the repository** when matching repository events to workflow files.

Primary source:

- https://docs.github.com/en/actions/concepts/workflows-and-actions/workflows
- https://docs.github.com/en/actions/reference/workflows-and-actions/workflow-syntax

Therefore:

- moving `.github/workflows` under `DEV_SOURCE_RESEARCH/repository/` would disable ordinary GitHub workflow discovery;
- a literal root containing only four public entries is incompatible with retaining native GitHub Actions unless the project intentionally abandons/replaces that integration;
- `.github/` must be treated as a `FILESYSTEM_ROOT_REQUIRED_EXCEPTION`, not documentation clutter.

**Evidence class:** `EXTERNAL_PRIMARY`  
**Confidence:** 1.00 for GitHub Actions workflow-location requirement.  
**Falsifier:** current GitHub primary documentation or verified repository execution demonstrates workflows are discovered from the proposed non-root replacement path without a root `.github/workflows` surface.

---

## 2. Live root runtime entrypoint: `rae.py`

At current main, root `rae.py` is only six executable lines and is explicitly documented in its source as the stable entry point:

```python
#!/usr/bin/env python3
"""Stable entry point for the FRANK Global Research Entity runtime."""
from rae_core.cli import main

if __name__ == "__main__":
    main()
```

Blob identity observed at current main:

```text
e911bc9cf3253c08fb82194053920568bd82a456
```

A repository code-search result indexed at parent head `854f6bc…` returned **5** files containing the literal `rae.py` reference:

1. `RAE_VNEXT_RUNTIME.md`
2. `.claude/hooks/rae_hook.py`
3. `research_entity/runtime/claude_state_bridge.py`
4. `research_entity/provenance/RAE_VNEXT_PROVENANCE.jsonl`
5. `.github/workflows/research-entity-verify.yml`

This result is useful evidence of live path coupling, but because GitHub code-search indexing was still serving the parent head rather than `3c3dbe5…`, it is **not** claimed as a complete current-reference denominator.

Consequence:

- moving `rae.py` without a root shim would break a documented stable invocation path and at least historically indexed hook/workflow/provenance references;
- the correct migration class remains `MOVE_WITH_COMPAT_SHIM`;
- the cheapest safe topology cleanup is to leave a tiny stable root shim and move implementation beneath the technical layer only after all callers are rebound/tested.

**Evidence class:** `CURRENT_SOURCE` + bounded indexed code-search evidence.  
**Confidence that a compatibility shim is required if implementation moves:** 0.99.  
**Falsifier:** exact-current reference census plus host/runtime tests prove no caller requires the root path and a replacement invocation contract is admitted everywhere.

---

## 3. Root host-discovery surfaces are not ordinary clutter

The current root also contains host/tool-facing surfaces such as:

- `.claude/`
- `CLAUDE.md`
- `AGENTS.md`
- `.env.example`
- `.gitignore`
- authority/bootstrap pointers

The existing migration manifest already classifies these conservatively as `MOVE_WITH_COMPAT_SHIM` or historical preservation candidates rather than deleting/moving them blindly.

Triggerword 3’s installer requirement is stronger than cosmetic minimalism: host-specific routes must actually fire hooks, write durable state and produce effect/result receipts before being called native. Therefore a host-discovery file that must remain at root for native behavior is a legitimate compatibility exception.

No claim is made here that every listed host surface **must** remain at root forever. The claim is narrower: its discovery contract must be verified before relocation.

---

## 4. Revised topology contract

### Human-facing navigation invariant

A person or AI installer should need only:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

to understand and enter the project.

The root README remains untouched in this Triggerword-3 pass unless explicitly requested by the owner.

### Filesystem compatibility exceptions

Additional root entries may remain only when one of these is proven:

```text
PLATFORM_REQUIRED
HOST_DISCOVERY_REQUIRED
STABLE_RUNTIME_SHIM_REQUIRED
AUTHORITY_POINTER_REQUIRED
BUILD_PACKAGE_CONVENTION_REQUIRED
HISTORICAL_PATH_IDENTITY_TEMPORARILY_REQUIRED
```

Every exception should be as small as practical and should point inward to `DEV_SOURCE_RESEARCH/repository/` or the canonical implementation rather than duplicate authority.

### Technical relocation target

Large implementation/archive trees can still converge beneath:

```text
DEV_SOURCE_RESEARCH/repository/
```

but only through byte/provenance-preserving moves, compatibility shims or formally migrated canonical paths as appropriate.

---

## 5. Migration acceptance algorithm

For every current root entry other than the four public navigation surfaces:

1. classify semantic role;
2. enumerate exact-current text/import/workflow/hook references;
3. inspect external platform discovery rules when applicable;
4. bind current blob/tree SHA;
5. choose one disposition:
   - `KEEP_PLATFORM_REQUIRED`
   - `KEEP_STABLE_SHIM`
   - `MOVE_BYTE_IDENTICAL`
   - `MOVE_WITH_COMPAT_SHIM`
   - `ARCHIVE_HISTORICAL_BYTE_IDENTICAL`
   - `DELETE_ONLY_IF_PROVEN_GENERATED_REDUNDANT`
   - `UNKNOWN_BLOCK`;
6. specify old path → new path;
7. specify compatibility mechanism;
8. run exact import/link/workflow/host-discovery tests;
9. preserve receipt/provenance references or provide an explicit migration mapping;
10. do not reduce `UNKNOWN_BLOCK` by assertion.

Mass relocation is admitted only when no unresolved entry can break authority, runtime, workflow, installer, provenance or historical reconstruction.

---

## 6. Immediate topology consequence

The previous wording “root reduced to four public entries” should be read as **public navigation convergence**, not as permission to move `.github/workflows` out of GitHub’s required location or to break stable root shims.

This is not weakening Triggerword 3. It applies its own higher-priority requirements:

- installation reliability;
- exact evidence;
- no duplicate authority;
- byte/provenance preservation;
- root scan unnecessary for users/agents;
- failures and contradictions remain visible.

A clean-looking root that silently disables workflows or hooks would be a Goodhart failure.

---

## 7. Next exact dependency gate

Build a machine-readable exact-current census for all remaining `MOVE_WITH_COMPAT_SHIM` and `UNKNOWN_BLOCK` entries with:

```text
path
current_blob_or_tree_sha
internal_reference_count
internal_reference_paths
workflow_reference_paths
host_discovery_contract
runtime_import_contract
receipt_provenance_contract
required_root_location
new_path
compatibility_mechanism
validation_command_or_test
status
```

The census must record the Git commit/ref used for each search so stale code-search indexing cannot masquerade as exact-current completeness.

**Current acceptance:** `TOPOLOGY_CONSTRAINTS_PROVEN / MASS_RELOCATION_BLOCKED_PENDING_EXACT_CENSUS`.