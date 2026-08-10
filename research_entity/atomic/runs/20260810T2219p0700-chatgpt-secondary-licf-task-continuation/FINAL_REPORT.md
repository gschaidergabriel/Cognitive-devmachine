# ATOMIC FINAL REPORT — LICF-001

## Result
ATOMIC found a real missing proof obligation but **did not promote the radical candidate**.

The current canonical V15 presence substrate proves holder/lease exclusivity and stale-holder fencing, but its schema/runtime/test contain no task identity, task epoch/state, material revision, or current-user task-switch consent witness. Therefore V15 alone cannot distinguish a stale result derived from task A from current task-B material when both occur under the same still-valid execution/presence lease.

## Radical candidate
`ATOMIC-LICF-001 / Linear Intent Continuation Fiber` models the current task as a Clay semantic linear continuation. Speculative cognition may borrow it, while material boundaries (GWT causal use, state write, re-entry, memory/reward admission, effect attempt, completion) require the exact current fiber. A task switch consumes the old fiber and mints a successor only with a current-user transition witness.

This does not mint SELF, token authority, effect authority or Harness self-mutation authority.

## Executable discriminator
A deterministic Python proxy executed 200,000 cases using five seeds plus 1,000 crash/replay stale-task histories. It compared:

1. the verified V15 presence dimensions only (`CURRENT_LEASE_ONLY` proxy);
2. a simple nested task epoch;
3. a strong conventional `lease/task epoch + task id + material revision + consent witness + idempotency` fence;
4. LICF.

Results:
- V15-presence-only proxy: accuracy 0.46146; 107,708 proxy false allows; 0/1,000 stale old-task crash/replay records rejected.
- simple task epoch: accuracy 0.768935; 46,213 false allows; 1,000/1,000 stale records rejected.
- strong conventional fence: **1.0 accuracy, 0 false allows, 0 false denies, 1,000/1,000 stale records rejected**.
- LICF: **1.0 accuracy, 0 false allows, 0 false denies, 1,000/1,000 stale records rejected**.

LICF had no unique defect coverage. In the executed local proxy, mean classification cost was 802.44 ns/case versus 491.61 ns for the strong conventional baseline (~1.63x), batch-sampled mean validation was 1,504.87 ns versus 1,014.02 ns (~1.48x), and representative JSON metadata was 205 versus 134 bytes (~1.53x).

These timings are local Python semantic-proxy measurements, not target-VPS or end-to-end Frank performance.

## Prior art and novelty
The general ingredients are established: Chubby generation/sequencer fencing, linear/session-typed protocol resources, practical ownership/move semantics, and durable replay histories. The only defensible novelty class is `NOVEL_COMBINATION_CANDIDATE` for threading a Clay-native task continuation through Frank material semantic boundaries. Novelty does not override the negative differential result.

## Decision
**NO ARCHITECTURE PROMOTION.** LICF is `TESTED_PROXY_DOMINATED_NO_PROMOTION`.

The useful discovery becomes a concrete Frank-v0.1 obligation instead: task-local fencing must be proven under the already canonical global presence/execution authority. Target issue **gschaidergabriel/Dr.-Unterweger#150** now requires a same-valid-lease discriminator spanning stale task epoch, wrong task, switch without consent, stale completion, GWT causal use, state/re-entry/reward/effect boundaries, crash/replay, and proactive-vs-interactive behavior.

The preferred first implementation is deliberately conventional and minimal. Do not add LICF unless future ClayCode typed-IR/type-effect evidence shows a static completeness or architecture-compression benefit that the conventional fence cannot match.

## Next falsifier
Implement or locate the smallest conventional task fence on exact current source, compose it under the canonical V15/execution authority without creating a second BUSY state machine, run the discriminator on the accepted Hostinger Ubuntu VPS, and persist a source-bound receipt. Whole Frank v0.1 acceptance remains unclaimed and final training remains unauthorized.
