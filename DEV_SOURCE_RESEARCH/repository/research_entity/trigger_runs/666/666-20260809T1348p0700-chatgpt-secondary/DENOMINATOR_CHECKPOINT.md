# Level-0 Checkpoint — Project-Frankenstein Denominator Refinement

## Result

The Project-Frankenstein Level-0 blocker was narrowed materially without claiming false exactness.

Frozen HEAD remains:

`abba90a5767d85abc8a1ac340bae92842dab35c1`

A GitHub commit search for `initial` exposed:

`e1a8812767668091d146ee958bbc2ebb2743031c`

with the explicit message `Initial commit: AI-Core / Frank — local AI desktop companion`, timestamped 2026-02-14. Its fetched diff contains extensive additions from empty-file hunks, consistent with a baseline import.

Comparing that commit to frozen HEAD reports:

- status: `ahead`
- ahead_by: `544`
- total_commits: `544`
- merge base: `e1a8812767668091d146ee958bbc2ebb2743031c`

Therefore the strongest currently evidenced candidate root-to-head history contains **545 commits including the base candidate**.

## Why history is still not frozen

The Level-0 gate requires stronger evidence than a commit title and additive diff. The current GitHub connector normalizes `fetch_commit` without exposing the commit's parent array. Tool discovery for `parent` exposes only `create_commit`; there is no parent-read primitive in the available connector surface.

Accordingly:

- `e1a881...` = **STRONG_ROOT_CANDIDATE_NOT_VERIFIED_ROOT**
- candidate count = **545**
- exact history denominator = **UNFROZEN**
- exact history coverage credit = **0.0**

A direct `parent_count = 0` proof or an immutable exhaustive history manifest is still required before freezing the denominator.

## Why the frozen tree is still not enumerable

Connector-surface audit confirms:

- tree discovery exposes write-side `create_tree` / `create_commit`, not a read-tree/list-tree action;
- discovery for `recursive` returns no function;
- `fetch_file` on repository root rejects the path as a directory instead of listing children;
- available contents actions fetch named files/blobs but do not enumerate the repository recursively;
- direct Git transport from the runtime previously failed DNS resolution.

Therefore the recursive frozen tree denominator remains an **external read-surface blocker**.

## Gate effect

`666_RELEASE_GATE` remains `NOT_PASS`.

Combined exact Level-0 coverage remains `0.0%` because exact denominators are not yet frozen. Semantic/history shards continue to be valid research work, but they cannot be used to imply repository-wide exact accounting.

## Minimal resolution

History can close if one of these becomes available:

1. raw commit metadata proving `e1a881...` has zero parents plus exhaustive root-to-head enumeration;
2. a frozen immutable git-history manifest including all SHAs and count.

Tree can close if one of these becomes available:

1. Git Trees API read with recursive enumeration at frozen HEAD;
2. an immutable content-addressed frozen tree manifest supplied externally and hash-validated.

Durable receipt: `research_entity/archive_assimilation/receipts/666_20260809T1408p0700_chatgpt_secondary_pf_denominator_refinement.json`.
