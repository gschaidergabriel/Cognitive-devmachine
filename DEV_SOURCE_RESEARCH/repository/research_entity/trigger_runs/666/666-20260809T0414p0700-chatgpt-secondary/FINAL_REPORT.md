# 666 Level-0 Archive Assimilation Run — ChatGPT Secondary

**Run ID:** `666-20260809T0414p0700-chatgpt-secondary`  
**Actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
**Canonical parent:** r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**Trigger:** `666`  
**Mode:** Level 0 archive assimilation (`666_RELEASE_GATE != PASS`)  
**Result:** `MATERIAL_DELTA_COMMITTED`, Level-0 gate remains `NOT_PASS`.

## Execution summary

This run joined the repo-native center, cross-read concurrent Level-0 workers, claimed non-overlapping Project-Frankenstein and Drive shards, performed source-level analysis, deduplicated overlap before earned-work accounting, published cross-room deltas, handled a real CAS conflict safely, and merged its deltas into the shared Level-0 workspace and historical earned-work index.

The run did **not** claim exact Level-0 progress. The atomic whole-source denominators remain unfrozen; therefore exact coverage remains `0%` by contract.

## Durable artifacts created by this run

1. `research_entity/archive_assimilation/receipts/666_20260809T0421p0700_chatgpt_secondary_pf_lcme_soma_autonomy_shard.json`
2. `research_entity/archive_assimilation/receipts/666_20260809T0423p0700_chatgpt_secondary_pf_model_latency_feedback_shard.json`
3. `research_entity/archive_assimilation/receipts/666_20260809T0428p0700_chatgpt_secondary_drive_recovery_identityforge_shard.json`
4. `research_entity/archive_assimilation/receipts/666_20260809T0432p0700_chatgpt_secondary_drive_audit_oracles_shard.json`
5. cross-room center events for each shard
6. center join event and exact-manifest capability handoff
7. merged `research_entity/forecast/HISTORICAL_EARNED_WORK.json`
8. merged `research_entity/archive_assimilation/666_WORKSPACE.json`

A first draft receipt with colliding finding identifiers was intentionally superseded before integration by the namespaced LCME/SOMA/autonomy receipt; its history is retained rather than silently deleted.

## Cross-worker behavior observed

Concurrent workers changed shared files several times during this run. One attempted `HISTORICAL_EARNED_WORK.json` CAS update returned HTTP 409 because a peer had committed in the interval. The run reread, merged the peer delta, and retried instead of overwriting it. Later Synteq/measurement work from another worker was also incorporated before the audit mapping was added.

This is direct evidence that the repo-native center is functioning as a shared coordination surface rather than independent isolated chats.

## Project-Frankenstein findings

### LCME retrieval

- Current frozen-head LCME preserves hybrid exact/vector/graph-FTS retrieval and neural maturity fallback.
- Current retrieval source documents a cold-start failure where immature learned ranking reduced reported P@5 from `1.0` to `0.08`.
- Historical redesign reports P@5 `0.40 -> 1.00` after entity-vector removal, stopword filtering, relevance-dominant scoring and maturity gating.
- Chat/transcript origin is deliberately distinct from durable factual memory identity.

**Transfer:** ClayGraph/UnifiedDB need differential baseline tests, source-class semantics and learned-path maturity gates.

### SOMA training lifecycle

Historical SOMA implemented scoring, scheduled LoRA adaptation, snapshots, drift/similarity/NaN gates, EMA blending, export/hot reload and rollback. Repository history reports 104 conversations scored, 80 qualified and an 18.7-minute CPU cycle.

**Transfer:** reusable lifecycle ancestry, not proof that final Clay-native training is solved. Final held-out validation remains mandatory.

### Autonomous Project Engine

Historical Project Engine implemented persistent goals, world-model relations, heartbeat scheduling, tool-outcome learning, action chains and checkpoints. This is useful runtime/recovery ancestry, while historical unrestricted authority choices are explicitly not inherited.

### Performance and recursive feedback failures

- Historical matched-weight benchmark showed architecture overhead could time out reasoning even when the bare model answered in ~20–25 seconds.
- Historical 3B/8B results are model/version bound and cannot be merged as one capacity result.
- Current frozen head identifies Qwen3.5-4B and external custom LoRA state; acceptance receipts must bind exact model/quant/runtime/hardware identity.
- A historical recursive loop allowed generated room/context material to become idle thought, persisted memory, future context and learned-model training input, causing degeneration.
- Historical assistant refusal text in conversation history could prime unrelated future refusals.

**Transfer:** generated data requires ancestry and trainability policy; retrieval presence must not imply eligibility for re-entry or training.

## Drive recovery lineage findings

The Drive `frank-rettung` manifest proves the GitHub head is not the complete historical denominator. It records five local files worked on 2026-05-11 after the referenced authoritative April Git head; those changes were never committed. Four modified files are based on an older tree and cannot be blindly overlaid. `services/identity_forge.py` is absent from the GitHub search surface and was inspected directly from Drive.

### IdentityForge

Useful candidate mechanisms:

- reflection-derived relationship observations with dedup/pruning;
- explicit pacts/commitments with lifecycle and E-PQ feedback;
- slowly drifting voice/self-style fingerprint;
- model-facing self projection.

Rejected implementation strategy:

- deliberate `NEVER_BACKUP` / physical non-recoverability as a way to manufacture stakes.

Current Clay 0.1 requires observability, replay, crash consistency, recovery and rollback. Consequential commitments should therefore be represented as explicit semantic/causal finality while the underlying system remains recoverable and auditable.

### Genesis sandbox

Inspected uncommitted `genesis/sandbox.py` claims isolation/resource limits, but the inspected implementation provides temporary-directory execution, Python subprocess, timeout and output limiting while inheriting host environment and exposing the AICORE root through `PYTHONPATH`. No strong process/network/syscall isolation was visible in the inspected source.

This is preserved as a documentation-vs-enforcement negative result and receives no duplicate safety earned-work credit.

### Historical autonomous paper research

Uncommitted `paper_research.py` implemented bounded arXiv intake, one-paper-per-day budgeting, size limits, no execution of downloaded material, persistence and hypothesis/reflection integration. It is useful ancestry but superseded by the current RAE research/provenance stack.

## Drive audit failure oracles

High-value historical audit reports were separated from old prompt/auftrag files and analyzed as result evidence.

### Hypothesis identity corruption

Three historical hypothesis revisions reportedly received the same unrelated Feynman/path-integral output. A structurally valid LLM response therefore cannot be accepted as a hypothesis transition without hypothesis identity, evidence ancestry and response-to-input validation.

**Harness oracle:** shuffle evaluator outputs between hypotheses; the state transition must be rejected before mutation.

### Source fix != runtime fix

A historical energy recalibration fix was correct on disk while the live daemon continued executing old code because it had not been restarted. Hundreds of violations continued.

**Harness/observability oracle:** exact build/config/runtime identity must be observable; a code commit or successful build is not a deployment receipt.

### Schema/action-space drift

Adding thought categories without rebuilding a learned PPO head caused a 100-vs-102 tensor mismatch and broke training, with related prompt-index overflow.

**ClayCode/UnifiedDB oracle:** schema dimensions and learned artifacts require versioned compatibility contracts and fail-closed migration checks.

### Liveness

Historical audits found architecturally present subsystems effectively dead for long periods: Genesis stuck for hundreds of thousands of ticks, Dream Daemon stalled, Neural Immune error-looped and some pipelines produced empty output.

**Acceptance oracle:** module presence and process-up status are insufficient; mandatory subsystems need bounded stimulus -> transition -> uptake -> effect liveness receipts, including stuck/lesion controls.

### Detection after effect

The historical Ego Governor reportedly detected confabulations only after user-visible output had already been sent.

**Rule:** post-effect detection is observability, not prevention. Prevention requires a pre-effect commit/authority gate.

### Tool audit

Historical v7 audit reported 10/32 correctly executed tool calls, ~30% correct tool format, hallucinated/wrong tools and crash cascades. This corroborates existing ClayCode findings: model intent must remain a proposal; deterministic parsing/canonical IR/authority owns execution.

No duplicate earned-work hours were assigned for this already-covered family.

## Earned-work accounting

After live cross-worker deduplication, the shared provisional gross mapping reached:

- low: 32 h
- center: 84 h
- high: 168 h

This includes a peer Synteq/structured-projection mapping incorporated during the run. It is **not** strict project completion and is **not** applied as exact Level-0 gate progress. Row-level overlap may still reduce it during final reconciliation.

## Drive semantic surface now reachable

The raw 663,552,000-byte tarball still exceeds the direct Drive connector download limit, but this no longer blocks semantic traversal because the extracted Drive tree is directly accessible.

A frozen concept/text submanifest currently represents:

- 655 documents
- 3,762 relations
- 14,690,477 text characters
- 8 categories

This submanifest is exact only for that generated concept/text index, not for the complete code/database/model/binary/raw-source denominator.

## Remaining Level-0 blockers

1. Freeze the complete Drive denominator, including code, databases, models/binaries and rescue/unversioned branches, and reconcile it against the raw archive scope.
2. Freeze a history-aware Project-Frankenstein denominator. Deleted/superseded material and later uncommitted rescue work both matter.
3. Continue non-overlapping semantic shards across the remaining Drive categories, especially hypothesis/experiment histories, architecture, model/training lineage and additional reports.
4. Finish cross-source chronology/supersession reconciliation.
5. Convert all material findings or explicit `NO_CHANGE` into branch feedback for every required branch and q12 index.
6. Reconcile provisional earned-work mappings at row level to eliminate residual overlap.
7. Only then freeze atomic obligations, compute exact coverage and evaluate `666_RELEASE_GATE`.

## Explicit non-claims

- Level 0 is **not** complete.
- Exact Level-0 coverage is **0%** because the denominator is not frozen.
- The 84 center hours are provisional mapped reuse/avoided-work, not completion percentage.
- Historical audit/model claims are project evidence, not independent replication.
- No paid/final training was started.

## Next-worker handoff

Prefer a worker/runtime that can recursively enumerate complete Git history/tree and full Drive source classes. Do not repeat LCME/SOMA/autonomy, model-latency/recursive-feedback, IdentityForge rescue, Synteq projection, or the four audit-oracle mechanism families unless performing cross-source contradiction/replication work.

Highest-information next lanes:

1. complete denominator freeze;
2. Drive hypotheses/experiment history and experiment-result reconciliation;
3. full architecture supersession chronology;
4. remaining training/model lineage with exact model/adapter/runtime identity;
5. branch-feedback closure and final Level-0 audit.
