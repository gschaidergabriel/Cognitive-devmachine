# Root topology migration

## Goal

Triggerword 3 defines a human-legible public root:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

This branch implements that topology as a reviewable tree transformation rather than editing the root README.

## Byte-preservation rule

All base-root entries except `README.md` are placed under `DEV_SOURCE_RESEARCH/repository/` using their existing Git blob/tree SHAs. Their content bytes are therefore unchanged by the relocation itself.

The original root `README.md` remains at root with its exact base blob SHA:

`4d39dbfaeace5843d4bfc6901e3ea3d8b566ec84`

New curation files are separate blobs and do not overwrite historical/source material.

## What changes semantically

Paths change. That is operationally significant even when bytes do not.

Likely path-sensitive surfaces include:

- GitHub Actions discovery (`.github/` moves below `DEV_SOURCE_RESEARCH/repository/`);
- imports or scripts that assume repository-root `tools/`, `tests/`, `research_entity/`, `the artefact/`, etc.;
- package paths, relative file opens and shell scripts;
- documentation links;
- install/bootstrap commands;
- any external runner that clones the repository and expects old root layout.

Therefore this curation tree is **not** merge-ready merely because every relocated blob is byte-identical.

## Required pre-merge gate

Before merging this topology into canonical `main`, one of these strategies must be chosen and tested:

### Strategy A — public-root branch / publication view

Keep this topology as a publication branch or generated view while operational `main` retains executable paths.

**Advantage:** lowest runtime risk.  
**Cost:** two views need a deterministic generation/sync rule.

### Strategy B — real canonical move with path adaptation

Move technical source under `DEV_SOURCE_RESEARCH/repository/` on canonical main and update all path-sensitive tooling.

Minimum acceptance:

1. enumerate path-sensitive references to old root paths;
2. update workflows/installers/imports/configs intentionally;
3. prove all intended source blobs survived relocation;
4. run repository tests from the new root;
5. verify actual hooks/workflows fire from their new or deliberately retained locations;
6. verify durable state writes and effect/result receipts where those are part of the claimed install/runtime;
7. classify install result as `NATIVE`, `ADAPTED`, `DEGRADED` or `BLOCKED`;
8. do not grant whole-product runtime credit from topology tests.

### Strategy C — generated clean distribution

Keep canonical engineering layout intact, but generate a clean public distribution artifact with exactly the four top-level entries.

**Advantage:** preserves engineering paths while satisfying human/public navigability.  
**Cost:** generated distribution must carry exact source identity and reproducible mapping back to canonical main.

## Recommended next discriminator

Prefer **Strategy C** unless there is a strong reason to make the canonical engineering repository itself adopt the new physical paths. It delivers the intended public experience with less risk of breaking runtime/import/workflow assumptions.

This branch still implements the literal tree transformation because Triggerword 3 requires a concrete, reviewable topology result. The PR should be treated as a curation candidate / reference implementation until path-sensitive execution is revalidated.

## No hidden rewrite

- Root README changed: **NO**
- Relocated source bytes changed by move: **NO**
- Path semantics changed: **YES**
- Runtime after path change verified: **NO**
- Whole EntityOS/HCU credit added: **0**