# 666 Level-0 Run Report — Project-Frankenstein History k368..k383

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Canonical entity: RAE-8.8 revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`
- Project-Frankenstein frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact ordinal shard: `k368..k383`
- Exact commits materialized: 16/16
- Runtime reproduction: not performed; evidence is historical Git commit/diff evidence.

## Concurrency result

This worker durably claimed the shard at commit `45af63eb7cf40ed3748a11cc36c807126ed36ee3` (13:33:02 +07:00) and leased it at `431bd28380ca9d7b4c4522595c9066a0fad3c6f5`. A competing claim became visible later at `3bf2f2604802a31d78a75d47021d2cc19bf82573` (13:33:37 +07:00). Under the swarm earliest-durable-claim rule, this run owns the ordinal semantic closure; the later worker should pivot or keep only explicitly noncounting replication.

## Terminal disposition

All 16 ordinals were individually resolved to concrete SHAs and assigned explicit terminal dispositions in:

`research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_HISTORY_SEMANTIC_K368_K383_20260809T1336p0700.json`

Uncovered inside shard: **0**.

## Main historical findings

### External-effect authority cannot live in persona/style prompts

The email subsystem expanded into a broad mutating surface: SMTP send, reply/reply-all, forward, CC/BCC, delete/spam, draft, read-state changes and attachments. Nearby revisions also changed the reply prompt into a ghostwriter/"no refusal" policy. That is a historically important unsafe architecture coupling: a generative style prompt was being used to define authority behavior for an external communication channel.

Transfer: user intent, generative style, effect capability, approval/confirmation and execution policy must be separable and enforceable outside the text-generation prompt.

### Optimistic UI requires effect receipts and rollback

The lineage is unusually diagnostic. `k376` introduced an optimistic local blacklist so a deleted/spammed email disappeared immediately, but explicitly rolled that local state back when IMAP failed or the message was absent. `k375` then made the UI even more immediate and removed those rollback paths. The visible surface could therefore report disappearance while the authoritative external effect failed.

Transfer: represent external effects with explicit states such as `PENDING -> COMMITTED | FAILED -> ROLLED_BACK`, and derive durable/visible truth from verified receipts or reconcile optimistic projections against them.

### Remote and local replicas must converge

IMAP mutations and the local Thunderbird mbox were distinct replicas. `k372` added explicit local mbox deletion plus summary-cache invalidation after successful remote delete/spam.

Transfer: any external effect that also has local materialized views needs an explicit convergence/reconciliation contract.

### Untrusted message content is not instruction

The email-body lineage progressively stripped HTML/script artifacts, tracking URLs, base64 blobs, boilerplate and injection-like material before LLM consumption; it also reduced model context to a bounded informational essence and added a separate user-intent step.

Transfer: keep externally supplied message text in an untrusted content class; normalize it before model context and never let it silently acquire instruction/authority status.

### Cross-service contract drift is a real failure mode

At `k380`, the proactive controller called a nonexistent function, passed an unsupported parameter and assumed the wrong return type from the email module.

Transfer: cross-module APIs should be versioned and machine-checkable, with contract/type tests that fail before runtime integration.

### Deployment dependency closure must be executable

At `k381`, components referenced `frank-overlay.service`, but the installer had never created it. At `k383`, native libraries required by QR/screenshot functionality were added only after failure discovery.

Transfer: clean-environment installation must verify every declared service, native library and runtime dependency; dependency closure is part of architecture correctness, not packaging polish.

## Negative results preserved

- Generative ghostwriter prompts attempted to suppress safety/refusal behavior on an effect-capable channel.
- UI-first delete/spam could drift from confirmed IMAP truth after rollback code was removed.
- Remote IMAP state and local Thunderbird state could diverge without explicit synchronization.
- Caller/provider API assumptions drifted without schema enforcement.
- A systemd service referenced by several subsystems was absent from installer output.
- Required native runtime dependencies were absent until a later fix.

## Evidence boundary

No source-reported performance, success or reliability figure was reproduced here. The shard establishes historical implementation lineage and negative-result evidence, not current runtime correctness.

## Earned-work boundary

No new avoided-hours number is assigned. The mechanisms overlap existing Safe-Effect Geometry, capability-gateway, context-routing and deployment-reproducibility research; row-level earned-work dedup was not executed in this shard.

## Current-program implication

The shard strengthens four current contracts without changing their evidence class:

1. external capability/effect gateway;
2. effect lifecycle + rollback/receipt semantics;
3. trusted-state/context separation;
4. executable deployment and cross-service contract validation.

It does **not** change the global Level-0 exact percentage because the combined obligation denominator remains not frozen. `666_RELEASE_GATE` remains `NOT_PASS`.
