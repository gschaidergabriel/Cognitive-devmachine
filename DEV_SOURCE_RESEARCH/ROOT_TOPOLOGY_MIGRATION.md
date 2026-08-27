# Root topology migration

Fusion point: `ed70385760c03a30dea7b6ecf8f6b78cbbaa584a`.

## Target

Triggerword 3 defines a human-legible public root:

```text
README.md
HUMAN_READ_THIS/
DEV_SOURCE_RESEARCH/
AI_START_HERE_DO_NOT_SCAN_REPO/
```

This Draft branch implements the literal tree as a reviewable reference while preserving current `main` technical source under `DEV_SOURCE_RESEARCH/repository/`.

## Identity preservation

- Root `README.md` remains exact blob `4d39dbfaeace5843d4bfc6901e3ea3d8b566ec84`.
- Technical root material from fusion point `ed703857…` is moved through existing Git blob/tree identities rather than rewritten.
- The parallel Trigger-3 Human/Dev work on `main` was fused, not discarded; the public Human/Dev files are successor synthesis artifacts incorporating its newer HARD_OFF closure/history-anchor evidence.

Therefore relocation content can be byte-identical while the public explanatory layer changes intentionally.

## The path problem

A Git blob can be identical at a new path and the system can still break.

Path-sensitive surfaces include:

- GitHub Actions workflow discovery when `.github/` is no longer at repository root;
- Python/shell imports and code that calculates paths from `__file__` or assumes root-relative `tools/`, `tests/`, `research_entity/`, `the artefact/`, etc.;
- relative file opens, package metadata and test discovery;
- Claude/Codex/agent hooks and installer scripts;
- documentation links and external automation that expects old root layout.

So:

`BYTE_IDENTITY_PRESERVED != PATH_RUNTIME_EQUIVALENCE`

## Merge strategies

### A — publication branch/view

Keep the clean four-entry topology as a publication branch or generated public view while operational `main` retains executable paths.

**Pros:** lowest runtime risk.  
**Cons:** requires deterministic generation/synchronization and identity mapping.

### B — canonical physical move

Adopt the four-entry topology on engineering `main` and intentionally adapt every path-sensitive surface.

Minimum gate:

1. freeze exact pre-move root/tree identity;
2. enumerate references to old root paths;
3. adapt workflow discovery/imports/configs/installers;
4. prove intended blobs/trees survived relocation;
5. run relevant tests from the new layout;
6. verify real hooks/workflows fire when claimed;
7. verify durable state/effect/result receipts where claimed;
8. classify each AI-host integration `NATIVE`, `ADAPTED`, `DEGRADED`, or `BLOCKED`;
9. retain exact evidence scope — no whole EntityOS/HCU promotion from topology success alone.

### C — generated clean distribution

Keep engineering `main` intact but deterministically generate a distribution/artifact containing exactly the four public top-level entries and an identity map back to canonical source.

**Pros:** clean user experience without breaking engineering paths.  
**Cons:** generator/manifest itself becomes a release obligation.

## Recommended discriminator

Prefer **A or C** unless there is a strong operational reason to make engineering `main` physically adopt the four-entry root. They satisfy navigability with lower risk. This Draft PR intentionally keeps the literal move visible so GitHub can expose every rename/path consequence before any merge decision.

## Current state

- Root README rewritten: **NO**
- Parallel current-main Trigger-3 work fused: **YES**
- Technical source bytes intentionally edited by relocation: **NO**
- Path semantics changed: **YES**
- Current `.github` workflow discovery after literal move verified: **NO**
- Imports/tests/installers after literal move verified: **NO**
- Whole EntityOS/HCU runtime credit added: **0**
- Provider runtime credit added: **0**
- Training credit added: **0**

This is a curation/reference topology, not a runtime acceptance artifact.