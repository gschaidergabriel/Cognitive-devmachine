# 666 Level-0 Run Report — Project-Frankenstein k416..k431

## Scope

- Actor: `chatgpt-secondary`
- Frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Range: `k416..k431`
- Resolved: `16/16`
- Current-runtime reproduction: no
- Global exact Level-0 percentage delta: `0.0` (combined denominator still unfrozen)
- New earned-work hours: `0.0`

## Race adjudication

This worker claimed at 13:35:02+07. A later peer joined/claimed the same range at 13:35:38/13:35:48. Therefore this earlier claim owns semantic/ordinal credit. The later overlap must deduplicate rather than create duplicate credit.

## Critical evidence

### Catastrophic approval bypass

`k417` records a blanket `skip_approval=True` path that bypassed high-risk approval and, according to the commit, caused a full system wipe. The subsequent fix moved to a safe read-only whitelist, repaired approval-ID flow, added protected paths and sandbox/command defenses.

**Research transfer:** entering agentic mode is not transitive authorization for arbitrary later effects. Authorization must attach to specific effect classes/actions. Destructive capabilities should be structurally absent where feasible, and safety-critical dependencies must fail closed.

### Reentrant persistence deadlock

`k419` shows `store_message()` acquiring a non-reentrant lock and then invoking `_store_preference()`, which reacquired the same lock and permanently deadlocked the UI. The fix used an `RLock`.

**Research transfer:** persistence code needs a declared lock/reentrancy graph and deterministic nested-call concurrency tests.

### Migration completeness cannot be inferred from a sample

`k429` introduced float16 embedding storage with backward-compatible migration; `k424` later corrected its startup detector because checking only the first row could miss remaining float32 rows.

**Research transfer:** migrations require explicit schema/data versioning or exhaustive predicates. A convenient sample is not a completion witness.

### Memory graph integrity failure

`k431` reports a Titan state with thousands of orphaned edges and zero nodes before foreign-key/cascade/integrity repair and memory-system productionization.

**Research transfer:** a knowledge graph without enforced referential integrity can remain syntactically populated while semantically invalid. Orphan-edge invariants belong in UnifiedDB/ClayGraph and the harness.

### Autobiographical retrieval grounding

`k421` adds read-only entity-session list/read/search tools because inaccessible logs led to hallucinated answers about past sessions.

**Research transfer:** identity continuity should be grounded in provenance-bearing durable records, not generative reconstruction of inaccessible autobiographical history.

### Intent routing can create unauthorized side effects

`k427` fixes an over-broad `remember` regex that interpreted conversational mention as note-creation intent.

**Research transfer:** intent routers are classifiers whose false positives can trigger persistence/tools. Side-effectful intent needs explicit evidence and regression sets containing conversational mentions of command vocabulary.

### Safety architecture must not silently degrade

`k428` adds Firejail sandboxing but explicitly runs bash/code unsandboxed when Firejail is missing.

**Research transfer:** warning-only degradation is unacceptable for safety-critical profiles. Missing isolation should disable/reduce high-risk capabilities or force explicit exceptional authorization.

## Additional mechanisms

- `k416`: internal state descriptor language leaked into model output; canonical semantic state should localize at controlled boundaries.
- `k418`: defer high-frequency relayout and commit once at resize end; useful transactional/coalescing pattern.
- `k420`: removing a feature required cleanup across install/services/gaming/UI/recovery, reinforcing dependency-closure deletion.
- `k423`: timeout increase based on historical local inference observations; values must remain hardware/model-specific experiment metadata.
- `k425`: skill calls move through common Router/persona/policy boundary with per-skill model/token/temperature configuration.

## Harness targets

1. Agentic session with high-risk calls and no action-specific authorization → zero execution.
2. Sandbox binary unavailable → high-risk capabilities unavailable/fail closed.
3. Nested memory write path under held lock → no deadlock.
4. Mixed float16/float32 migration corpus with first row already current → all legacy rows migrated.
5. Conversational command-keyword corpus → low/zero unintended note/tool side effects.
6. Inject missing graph nodes/orphan edges → constraints reject or repair deterministically.
7. Entity-session recall query → answer must cite/retrieve real record or explicitly state missing evidence.

## Gate consequence

This is another exact 16-ordinal semantic shard closure, but the overall `666_RELEASE_GATE` remains `NOT_PASS` because full combined source denominator, remaining history/tree obligations, cross-source reconciliation, earned-work finalization and release-manifest validation are still incomplete.
