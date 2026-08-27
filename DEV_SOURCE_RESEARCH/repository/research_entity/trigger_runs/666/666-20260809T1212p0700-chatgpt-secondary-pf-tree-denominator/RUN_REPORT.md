# 666 Level-0 Run Report — Project-Frankenstein Frozen-Tree Denominator Attempt

## Run identity
- trigger: `666`
- actor: `chatgpt-secondary`
- provider/model: OpenAI / GPT-5.6 Sol
- canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- stage: `L0_ARCHIVE_ASSIMILATION`
- target: exact recursive repository tree at frozen ref `abba90a5767d85abc8a1ac340bae92842dab35c1`

## Why this lane
The current Project-Frankenstein manifest still marks `exact_tree_enumerated=false` and `denominator_frozen=false`. A prior worker had already shown that commit-history search is not an exact Git-DAG walk. This worker tested whether the missing frozen-head tree denominator could be closed through another exposed read surface without overlapping active Titan, Drive new-root or PF semantic-lineage workers.

## Attempts and results
1. **GitHub connector directory read at frozen ref** — failed explicitly because `fetch_file` accepts files and rejects directory paths.
2. **GitHub connector capability discovery** — tree-matching actions exposed only write-side `create_tree` / `create_commit`; no read/list recursive tree action was available.
3. **Exact-SHA GitHub archive ZIP** — web retrieval could not authorize/fetch the archive URL, so the controlled downloader could not obtain it.
4. **GitHub Git Trees REST endpoint** — direct web opening of `/git/trees/<sha>?recursive=1` was blocked by safe-URL restrictions and search could not surface the exact API endpoint.
5. **Local network fallback** — direct urllib access to `api.github.com` failed DNS resolution.

## Negative result
The current execution surface cannot prove the complete frozen-head Project-Frankenstein tree. Therefore:
- `exact_tree_enumerated = false`
- `denominator_frozen = false`
- exact Level-0 credit from this task = `0.0`
- no partial code-search/file-fetch set may be promoted to a complete denominator.

This is a tool-surface blocker, not evidence that the repository tree itself is unavailable.

## Required future closure evidence
A future worker may close this obligation only with at least one of:
- recursive Git Trees API output at the exact frozen SHA with explicit completeness / `truncated=false` evidence;
- an exact-SHA repository archive or clone plus a local complete `git ls-tree -r -t` / equivalent walk;
- a connector-native complete recursive tree listing tied to the frozen ref.

## Durable outputs
- `research_entity/archive_assimilation/receipts/666_20260809T1214p0700_chatgpt_secondary_pf_frozen_tree_surface_blocker.json`
- `research_entity/rooms/center_events/20260809T1214p0700_666_pf_frozen_tree_surface_blocker.json`
- this report

## Completion judgment
The task's fallback completion test is satisfied: the exact denominator was **not** fabricated, and the execution-surface blocker is reproducibly recorded. `666_RELEASE_GATE` remains `NOT_PASS`; post-Level-0 stochastic field spawning is still forbidden.
