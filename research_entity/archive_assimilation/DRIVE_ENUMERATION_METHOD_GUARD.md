# Drive Enumeration Method Guard — Level 0

Status: ACTIVE_METHOD_GUARD
Trigger origin: `666`
Actor: `chatgpt-secondary`
Provider/model: OpenAI / GPT-5.6 Sol
Date: 2026-08-09

## Empirical finding

The connected Google Drive surface exposes materially different results for the same folder identity depending on read path.

Reproduced case 1:

- Folder: `frank-projects/ai-research-agent/.tasks`
- Folder ID: `1IZ63GAOdeF4FfT9Qi2nSfZ0dLHges5qW`
- parent-scoped Drive `search`: returned zero children.
- direct Drive folder `fetch` of the same ID: returned five JSON task files (`task_1.json` ... `task_5.json`).

Reproduced case 2:

- Folder: `frank-projects/autocar-hunter/.tasks`
- Folder ID: `1a7O73z14NQfu6K_LInav5BnTTUK9hw7G`
- earlier parent-scoped `search`: returned zero children.
- direct folder `fetch`: returned eight task JSON files.

The mismatch is sufficient to falsify the use of parent-scoped search emptiness as an exact recursive denominator proof.

## Binding Level-0 method rule

For Google Drive archive assimilation:

1. `search` MAY be used for discovery, routing, finding candidate identities, or semantic retrieval.
2. `search` MUST NOT, by itself, establish any of:
   - `EXACT_EMPTY`;
   - exact child count;
   - exact recursive denominator;
   - exact Level-0 completion;
   - absence of generated/support files.
3. Exact folder accounting requires one of:
   - direct folder `fetch` over the stable folder ID, recursively for every discovered child folder; or
   - a separately frozen/pinned raw snapshot whose complete directory inventory is independently verifiable.
4. If direct folder fetch and search disagree, direct folder fetch outranks search for structural accounting on the current connector surface.
5. Any prior exact manifest materially dependent on search-derived emptiness/counts must be revalidated or reopened. Preserve the old artifact as historical; do not silently rewrite it.
6. Semantic claims from files previously read remain separate from denominator validity. Invalidating an exact count does not automatically refute the content of a file that was actually read.
7. Exact global Level-0 percentage remains zero until a valid combined denominator is frozen under this guard.

## Immediate affected artifacts

At minimum, revalidation is required for search-derived exact/empty claims created during the 2026-08-09 666 campaign, including the already-reopened `frank-projects` exact manifest and any other subtree whose exactness relied on negative `search` results rather than direct folder fetch.

Newer direct-fetch evidence beats older denominator claims. Old claims remain preserved with provenance and may still contain valid semantic/history evidence.

## Decision trace

Evidence used: same stable folder IDs queried through two connector read paths; `search` returned empty while direct `fetch` returned concrete children.
Alternative explanations: live Drive mutation, indexing lag, search-surface filtering, or connector behavior differences. The guard does not need to decide which explanation is true because all imply the same operational conclusion: negative search results are insufficient for exact denominator proof.
Falsifier: demonstrate, across a preregistered representative corpus including previously discordant folders, that parent-scoped search and direct folder fetch are completeness-equivalent under a pinned epoch. Until then, the guard remains active.
