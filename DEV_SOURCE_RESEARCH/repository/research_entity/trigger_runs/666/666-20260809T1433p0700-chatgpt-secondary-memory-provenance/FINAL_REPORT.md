# 666 Level-0 Run Report — Project-Frankenstein Memory/Provenance Shard

- **run_id:** `666-20260809T1433p0700-chatgpt-secondary-memory-provenance`
- **trigger:** `666`
- **actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
- **program stage:** `L0_ARCHIVE_ASSIMILATION`
- **canonical parent observed:** revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- **Project-Frankenstein frozen ref:** `abba90a5767d85abc8a1ac340bae92842dab35c1`
- **exact Level-0 coverage credit:** `0.0%` because the combined denominator remains `NOT_FROZEN`

## Work executed

A distinct query-directed Project-Frankenstein historical shard was analyzed around persistent memory, retrieval fusion, compaction, user preferences, identity isolation and provenance.

Primary files:

- `MEMORY&PERSISTENCE-ARCHITECTURE.md`
- `services/memory_hub.py`
- `services/chat_memory.py`
- `services/memory_consolidator.py`
- `services/memory_consistency.py`
- `services/preference_extractor.py`

Durable detailed receipt:

`research_entity/archive_assimilation/receipts/666_20260809T1433p0700_chatgpt_secondary_pf_memory_provenance_lineage.json`

## Main recovered mechanisms

1. Project-Frankenstein already had a real multi-layer memory architecture: chat FTS/vector retrieval, Titan graph retrieval, consciousness retrieval, world-experience context and preference retrieval behind a common MemoryHub.
2. `chat_memory.py` uses actual FTS/vector reciprocal-rank fusion for chat history.
3. Recursive memory compaction existed as live messages -> Tier-2 summaries -> Tier-3 essences using local Qwen 2.5 3B with an extractive fallback.
4. Preference learning was local and fast but not explicitly person-namespaced at the schema level.

## Reproduced negative result

`memory_consolidator._archive_old_messages()` claims original message text remains in FTS5 after message archival. That is contradicted by the actual `messages_fts` `AFTER UPDATE` trigger in `chat_memory.py`.

An isolated in-memory SQLite reproduction using the same external-content FTS5/update-trigger semantics produced:

- before archival: `MATCH durable` -> original row found;
- after `messages.text='[archived]'`: `MATCH durable` -> no row;
- after archival: `MATCH archived` -> marker row found.

**Conclusion:** the original lexical content is removed from FTS5 during archival. The historical code comment is false for this implementation.

A second degradation follows: message embeddings remain, but vector search joins them back to the now-mutated `messages.text`, so a semantic hit may return `[archived]` rather than the evidence-bearing historical content.

## Provenance defect

Tier-3 essences store `source_msg_ids` containing Tier-2 abstraction IDs, then delete those Tier-2 rows. This severs direct dereferenceable Message -> Tier-2 -> Tier-3 ancestry. `turn_start`/`turn_end` preserve only a coarse interval, not full source identity.

## Current architecture implications

### Reuse

- hybrid lexical/semantic retrieval;
- logical multi-layer query surface;
- bounded recursive memory compaction;
- local embedding/compression;
- retrieval-latency metrics and integrity/backfill jobs.

### Must change for current Frank v0.1

- immutable raw event/content storage separated from derived summaries;
- transitive source IDs/hashes preserved through every compaction level;
- exact retrieval-source/scorer attribution instead of heuristic post-fusion labels;
- explicit entity + human-user namespace on all personal memory and preference state;
- auto-extracted preferences remain evidence-linked candidates until confirmed/updated;
- compaction regression must prove lexical/vector retrieval equivalence and source reconstruction.

## Highest-value H1 tests derived

1. **Compaction retention differential:** frozen corpus -> retrieve targets -> compact -> require equivalent evidence-bearing retrieval with intact source hashes.
2. **Andreas/Gabriel isolation:** contradictory synthetic histories -> require zero cross-user memory/profile contamination under lexical, semantic-neighbor and fallback retrieval.
3. **Retrieval attribution:** every injected memory item logs contributing retrievers, ranks and scores and can be deterministically replayed.

## Branch feedback

- **frank:** preserve historical memory ideas but harden identity/provenance boundaries.
- **harness:** add compaction-retention, archived-vector and user-isolation regressions.
- **claycode:** represent immutable raw vs derived state and transitive provenance explicitly.
- **claygraph:** derived memories must retain source ancestry even if intermediate summaries are compacted.
- **unifieddb:** use one logical query plane without collapsing immutable evidence into mutable derived text.
- **gwt:** memory injection should expose exact causal source attribution for uptake/effect/re-entry analysis.
- **hyperposition:** maintain set-valued retrieval candidates and provenance until explicit context selection.
- **emergenz:** no scientific emergence delta from this shard.

## Open obligations

- history-search previous/later revisions for fixes/supersession;
- reconcile with Drive `titan-memory`, recovery trees and current `frankv0.1` state;
- deduplicate earned-work before assigning historical hours;
- complete Project-Frankenstein recursive tree/history denominator through an actually exhaustive read surface.

## Promotion decision

No canonical scientific promotion. This run adds historical evidence, a reproduced implementation defect and current architecture/test deltas while Level 0 remains open.
