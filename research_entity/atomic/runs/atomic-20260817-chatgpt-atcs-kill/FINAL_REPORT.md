# ATOMIC — ATCS-001 Active-Turn Capability Seal

## Final classification

**KILL AS RUNTIME ORGAN / RETAIN THE AUTHORITY LAW.**

The candidate was a per-turn cryptographic capability/seal bound to user, session, turn, causal identity, generation and effect target. It was generated after an earlier source slice exposed a real composition defect: the MCP effect path was reconstructing current authority from a selected workspace/history row plus turn provenance while hook-owned `active_turns` already carried the current turn identity and generation.

During the same ATOMIC cycle, current main converged on the simpler architecture before this worker wrote product code:

- MCP effect requests now enter the same `TurnLifecycle` used by the automatic Claude hooks;
- effect admission reads the hook-owned `active_turns` row directly;
- expected generation is carried into `EffectGate` and checked against the live session generation;
- verified effect re-entry is checked against the predeclared causal identity;
- `entityos.exec` receives an automatic target-scoped lease;
- duplicate hook lifecycle implementation was removed.

This makes the extra ATCS credential a duplicated second authority path unless a future exact isolated discriminator proves a safety property that the canonical active-turn/generation/lease composition cannot express.

## Hypothesis field

### H1 — ATCS
Issue a short-lived per-turn MAC/token and require it at every effect request. Bind it to `(user, session, turn, causal_id, generation, capability, target)`.

Prediction: stale, sibling, replayed or transplanted effect requests fail even if surrounding mutable state looks plausible.

### H0 — canonical database fence
Do not mint a second credential. Define current effect authority as the unique hook-owned `active_turns` record joined to the live session generation, plus the existing target lease where collision exclusion is required.

Prediction: the same stale/sibling/replay classes are rejected with less state, fewer expiry/synchronization failure modes and no second authority lifecycle.

### H2 — historical workspace reconstruction
Infer current effect authority from the newest selected/open workspace plus copied provenance fields.

Prediction: stale completed rows, mismatched generation, wrong episode selection and provenance drift can create false admission or false denial.

## Synthetic discriminator

A deterministic 20,000-episode synthetic model compared the three mechanisms. It is **not target evidence** and its ground truth was intentionally aligned to the current-turn authority contract.

- historical-workspace/provenance proxy: 71.435% accuracy, 3,367 false accepts and 2,346 false rejects;
- canonical active-turn join: 20,000/20,000 matched the modelled authority law;
- active-turn join plus extra seal: zero additional false-accept reduction and 31 synthetic false rejects from seal propagation/freshness mismatch.

Targeted stale-selected, wrong-generation and wrong-workspace cases were accepted by the historical reconstruction proxy and rejected by the canonical active-turn baseline.

This does not prove the current code is correct. It only shows that, under the hypothesized failure family, an extra credential is not the cheapest discriminator.

## Prior-art collision

The mechanism family is not novel enough to justify architectural promotion by novelty:

- RFC 9449 DPoP is established proof-of-possession/sender-constrained token machinery with replay-oriented binding properties.
- Macaroons are established contextual authorization credentials with caveat attenuation.
- Database transaction/fencing patterns already provide serialization and current-state admission without minting a parallel capability object.

Therefore ATCS can only survive on measured ClayVerse-specific necessity, not conceptual novelty.

## Strongest counterhypothesis

The strongest counterhypothesis is that a database-backed active turn is insufficient across process crash/restart or multi-process writers, while a self-contained capability object could survive or detect those transitions more cleanly.

That counterhypothesis remains **UNTESTED at exact container runtime**. A token does not automatically solve it: token validity itself needs a current revocation/generation authority, and accepting the token without consulting current state would weaken fail-closed recovery.

## Kill test / promotion gate

Keep ATCS killed unless an exact isolated ClayVerse container test demonstrates a concrete case where all of the following are simultaneously true:

1. `active_turns` + live session generation + causal identity + target lease admits an unsafe effect or cannot distinguish the stale/sibling case;
2. a seal detects that case without becoming a second canonical authority;
3. crash/restart, lease expiry, dual-user collision and stale-generation tests remain fail-closed;
4. the seal does not introduce token propagation, revocation, storage or recovery ambiguity;
5. the gain survives live Claude Code hook -> MCP -> EntityOS execution rather than only a synthetic proxy.

## Durable law retained

**Current effect authority must derive from the one hook-owned active turn plus live generation; historical workspace/provenance rows are evidence, not current admission authority. Collision exclusion belongs to the existing effect/target lease rather than to a second capability system.**

## Architecture decision

`NO_PRODUCT_CODE_CHANGE_BY_THIS_ATOMIC_RUN`

`ATCS-001 = REJECT_AS_RUNTIME_ORGAN`

`ACTIVE_TURN_GENERATION_LEASE_LAW = RETAIN`

The useful outcome is negative knowledge plus a narrower executable falsifier. Concurrent main already implemented the simpler composition, so writing another product mechanism would duplicate the canonical path.

## Next exact discriminator

On the then-current exact ClayVerse image in an authorized isolated executor:

- start both canonical user sessions;
- begin a hook-owned turn for each;
- collide both on the same admitted EntityOS target;
- force one stale session generation and one lease expiry/reacquisition boundary;
- crash/restart between journal PENDING and verified completion;
- require exactly one valid current causal lineage, no stale effect completion, no duplicate external execution, and fail-closed recovery for ambiguous outcomes.

No Vercel Sandbox/OCI/live-Claude result is claimed by this ATOMIC packet.
