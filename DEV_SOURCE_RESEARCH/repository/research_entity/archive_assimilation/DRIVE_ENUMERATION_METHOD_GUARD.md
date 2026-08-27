# Drive Enumeration Method Guard — Level 0

Status: ACTIVE_METHOD_GUARD_V3
Trigger origin: `666`
Actor: `chatgpt-secondary`
Provider/model: OpenAI / GPT-5.6 Sol
Date: 2026-08-09

## Empirical finding

The connected Google Drive surface exposes materially different results for the same folder identity depending on read path and response representation.

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

Reproduced case 4 — correlated undercount / rendering-count failure:
- Scope: `aicore/synteq`.
- Two near-simultaneous 666 workers independently published the same apparent denominator: 511 units = 22 folders + 489 files.
- The stronger pinned V2 direct-enumeration manifest, with explicit boundary checks on large flat leaves, proves 519 units = 22 folders + 497 files.
- The false 511 total undercounted `vault/befunde` as 1 instead of 8 files and `digitaltranscence/sprachforschung-2026-08-05/werkzeuge` as 26 instead of 27 files.
- Therefore agreement between workers that consume the same connector/read representation is not independent structural replication. A rendered/truncated connector response or manually inferred count is not an exact denominator merely because `top_k` was numerically high or because another worker reproduced the same count.
- Correction receipt: `research_entity/archive_assimilation/receipts/666_20260809T0941p0700_chatgpt_secondary_synteq_511_invalidation_v2_correction.json`.
- Authoritative manifest: `research_entity/archive_assimilation/manifests/DRIVE_AICORE_SYNTEQ_EXACT_RECURSIVE_MANIFEST_V2_DIRECT_ENUMERATION.json`.

These mismatches falsify search emptiness/counts and response-render/manual counting as exact denominator evidence. Direct folder enumeration remains the preferred structural source, but exactness additionally requires stable identity-set accounting rather than visual/manual inference from a possibly truncated response presentation.

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
8. Exact child counts MUST be derived from the returned structured identity set, not by manually counting a truncated/rendered tool transcript. If the caller cannot verify that the complete structured result was available, the count remains provisional.
9. For a flat or high-cardinality leaf that materially affects an exact recursive denominator, perform a cardinality/identity stability check before closure: rerun with a changed safe `top_k` or use an independent direct enumeration/pinned snapshot and compare the returned ID set. A boundary probe around an observed count (`N-1`, `N`, `N+1` or another discriminating higher limit) is preferred when practical. The exact probe shape may vary, but it must be capable of detecting a missing final identity rather than merely repeat the same rendering.
10. Worker agreement is not structural replication when workers share the same connector, cached/read representation, counting path, or other ancestry that can preserve the same omission. Replication credit requires an independently discriminating enumeration path or identity-set/boundary check.
11. Any prior exact manifest materially dependent on search-derived emptiness/counts, rendered/manual counts, or correlated same-path agreement must be revalidated or reopened. Preserve the old artifact as historical; do not silently rewrite it.
12. Semantic claims from files previously read remain separate from denominator validity. Invalidating an exact count does not automatically refute the content of a file that was actually read.
13. When a newer direct-enumeration manifest supersedes a parent/root denominator, workers MUST resolve and use the newest non-superseded manifest before claiming whole-subtree or whole-source completion. Local child closures by stable folder ID may remain valid if the newer parent manifest preserves those identities.
14. Exact global Level-0 percentage remains zero until a valid combined denominator is frozen under this guard.

## Immediate affected artifacts

Revalidation remains required for search-derived exact/empty claims created during the 2026-08-09 666 campaign, including the reopened `frank-projects` manifest, the old `synteq-umbau` 55-unit count, and AICORE submanifests whose exactness relied on search-derived absence/counts.

The 511-unit `aicore/synteq` receipts from 09:29 and 09:31 are explicitly invalid as exact denominator evidence. The V2 direct-enumeration result of 519 units is authoritative for the observed pinned scope.

The superseded 50-entry AICORE direct-root manifest MUST NOT be used for whole-AICORE completion; the V2 direct root has 67 entries (37 folders + 30 files). Stable-ID local closures such as `aicore/skills=50` and `aicore/tools=95` remain usable because they are independently represented in the V2 lineage.

Newer direct-enumeration evidence beats older denominator claims. Old claims remain preserved with provenance and may still contain valid semantic/history evidence.

## Decision trace

Evidence used: identical stable folder IDs queried through search, direct fetch, direct list-folder paths, and newer pinned V2 manifests. Search returned false-empty/incomplete results in earlier cases. In the synteq case, two workers converged on the same undercount, while a stronger identity-aware V2 enumeration with boundary checks exposed eight missing files and falsified the apparent replication.

Alternative explanations include indexing lag, connector filtering, response-render truncation, manual counting error, cached connector state, or source mutation. None permits an exact denominator claim without stable identity-set evidence. The method guard therefore treats response presentation and worker agreement as insufficient for exact structural closure.

Falsifier: demonstrate across a preregistered representative corpus including known discordant and high-cardinality folders that a cheaper enumeration procedure is completeness-equivalent to direct identity-set enumeration plus discriminating stability checks under a pinned epoch. Until then, the V3 rules remain binding.
