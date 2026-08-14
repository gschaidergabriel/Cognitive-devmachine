# GO — V16 idle-handoff release-epoch fence

## Result

This run identified a narrow stale-consent race in the current Frank v0.1 V16 idle-handoff confirmation path and produced a bounded repair candidate. The finding is a **SUPPORTED CANDIDATE / TESTING** result, not a promotion or whole-Frank acceptance claim.

## Current contract assembled

The owner-fixed single-spawn/global-busy contract requires interactive release to enter `AWAITING_USER_IDLE_CONFIRMATION`; silence, timeout or disconnect are not consent; a new explicit authenticated interactive request may still acquire while that handoff is pending; a later release supersedes the older pending handoff; autonomous work is admitted only when the current handoff is `CLEAR`.

The current V16 schema already records `released_lease_epoch`, but the confirmation path inspected at run start matched only the released session/client hashes. Because the same legal session/client may complete more than one sequential release, those hashes identify the actor but not the release generation.

## Hypothesis and counterhypothesis

**Hypothesis:** Confirmation must carry and match the exact `released_lease_epoch`; clearing should use a pending-state + epoch conditional update. This turns the release epoch into a fencing token against delayed or duplicated acknowledgement.

**Counterhypothesis:** Session/client identity alone is enough because a valid acknowledgement cannot arrive after another release by the same session.

The current owner behavior allowing fresh explicit user work while a prior handoff is pending makes the repeated-generation case legal, so the counterhypothesis requires an executable discriminator rather than assumption.

## Exactly one GO out-of-box experiment

`ABA_STALE_IDLE_CONFIRMATION_FENCE` is the sole unusual experiment in this GO invocation.

Sequence:
1. Same authenticated session performs interactive release A.
2. Without clearing A for autonomy, the same explicit session starts valid new work and releases B.
3. A delayed confirmation for epoch A arrives after B has superseded the singleton handoff row.
4. Required behavior: reject A, retain B pending, keep autonomous acquisition blocked.
5. Confirmation for epoch B may then clear the handoff and allow autonomous acquisition.

The experiment deliberately maps the ABA/stale-update generation problem from concurrent systems to Frank's idle-handoff receipt. It changes no owner policy and performs no external effect.

## Build/test evidence

The first candidate (#178, now closed and superseded) executed on the accepted self-hosted Linux/X64 target lane in run `31406944484`: the normal V16 continuity regression passed and the single ABA discriminator passed. A later repository-wide static-integrity step failed, so that stale branch was not promoted or merged.

Rapid concurrent mainline development added the separate required rule that explicit authenticated user work may outrank a pending handoff. The repair was reconciled with that behavior and moved to current replacement PR #195, head `b0b48e13c514e929aea44db5c2106b5b7ff372a4`. Its target-VPS run `31408572649` was queued at report write time.

## Proposed architecture delta

At the token/API boundary require a positive `released_lease_epoch`. In V16 confirmation, validate session hash + client hash + exact pending release epoch. On mismatch return a rejection while preserving pending state. On match, clear only with a conditional update constrained by `AWAITING_USER_IDLE_CONFIRMATION` and that epoch, and verify exactly one row changed.

The epoch is not a new authority source. It is a generation/fencing witness attached to already-authenticated user confirmation.

## External mechanism check

Current Kubernetes Lease/API optimistic-concurrency mechanisms and etcd transactions both use version/compare predicates to prevent stale concurrent updates from silently overwriting newer state. That is mechanism-level support for generation fencing only; these systems do not determine Frank's user-consent semantics.

## Limits / non-claims

- No executable pre-fix ABA failure was promoted; the pre-fix weakness is a source-control-flow finding.
- First-candidate target execution supports the narrow repair but does not prove current-main equivalence.
- PR #195 remains unpromoted until exact-head target execution and merge-safety re-check complete.
- No real provider/external effect was performed.
- No Harness self-mutation authority was granted.
- No final training was authorized or started.
- No whole Frank v0.1 acceptance is claimed.

## Next falsifier

Execute PR #195 exact head on the accepted Ubuntu target lane and require: normal V16 regression PASS, same-session ABA discriminator PASS, repository-integrity diagnostic adjudicated, then refresh `main` and compare the exact five-file delta before any merge.
