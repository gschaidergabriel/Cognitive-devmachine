# Drive Enumeration Method Guard — Level 0

Status: ACTIVE_METHOD_GUARD_V2
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
- direct Drive folder `fetch`: returned five JSON task files.

Reproduced case 2:
- Folder: `frank-projects/autocar-hunter/.tasks`
- Folder ID: `1a7O73z14NQfu6K_LInav5BnTTUK9hw7G`
- parent-scoped `search`: returned zero children.
- direct folder `fetch`: returned eight task JSON files.
- direct `list_folder(top_k=1000)` independently returned the same eight identities.

Reproduced case 3:
- Folder: `frank-werkzeuge/genesis-monitor`
- Folder ID: `1xwTAPEWzXOBo8jv6iXSIyFKboFd5D8O0`
- search-derived view exposed two reports.
- direct folder fetch exposed seven files.

The mismatch falsifies parent-scoped search emptiness/counts as exact denominator evidence. The independent agreement of direct folder fetch and direct folder listing on a preregistered discordant identity establishes `list_folder` as the preferred exact child-enumeration surface when configured with a scan ceiling safely above the returned population.

## Binding Level-0 method rule

For Google Drive archive assimilation:

1. `search` MAY be used for discovery, routing, finding candidate identities, or semantic retrieval.
2. `search` MUST NOT, by itself, establish any of:
   - `EXACT_EMPTY`;
   - exact child count;
   - exact recursive denominator;
   - exact Level-0 completion;
   - absence of generated/support files.
3. Preferred exact folder accounting is direct `list_folder` over the stable folder URL/ID with `top_k` intentionally set well above the observed population (normally 1000 for this corpus), recursively for every returned child folder.
4. Direct folder `fetch` remains a valid identity/content crosscheck for small folders. For large folders its readable rendering may be truncated; rendering truncation MUST NOT be converted into a guessed count.
5. A separately frozen/pinned raw snapshot whose complete directory inventory is independently verifiable is also valid exact denominator evidence.
6. If `search` disagrees with `list_folder` or direct folder fetch, the direct folder-enumeration evidence outranks search for structural accounting.
7. If `list_folder` returns exactly `top_k` items, the result is ceiling-ambiguous and MUST NOT be called exact until rerun with a higher `top_k` or independently reconciled.
8. Any prior exact manifest materially dependent on search-derived emptiness/counts must be revalidated or reopened. Preserve the old artifact as historical; do not silently rewrite it.
9. Semantic claims from files previously read remain separate from denominator validity. Invalidating an exact count does not automatically refute the content of a file that was actually read.
10. Exact global Level-0 percentage remains zero until a valid combined denominator is frozen under this guard.

## Immediate affected artifacts

Revalidation remains required for search-derived exact/empty claims created during the 2026-08-09 666 campaign, including the reopened `frank-projects` manifest, the old `synteq-umbau` 55-unit count, and AICORE submanifests whose exactness relied on search-derived absence/counts.

Newer direct-enumeration evidence beats older denominator claims. Old claims remain preserved with provenance and may still contain valid semantic/history evidence.

## Decision trace

Evidence used: identical stable folder IDs queried through search, direct fetch, and direct list-folder paths. Search returned false-empty/incomplete results; fetch and list-folder independently exposed concrete children, and list-folder reproduced the known eight-child direct-fetch count for `autocar-hunter/.tasks`.
Alternative explanations: indexing lag, search-surface filtering, connector behavior differences, or source mutation. None rescues search-negative evidence for exact accounting.
Falsifier: demonstrate across a preregistered representative corpus including known discordant folders that parent-scoped search is completeness-equivalent to direct enumeration under a pinned epoch. Until then, search remains discovery-only for denominator work.
