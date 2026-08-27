# ATOMIC FINAL REPORT — Authority-Separated Voice Braid (ASVB)

## Why this candidate
The current Frank v0.1 owner surface now explicitly supports portable third-party participation: any client or peer AI with a valid scoped token may attempt interaction, while token possession is never SELF or effect authority and one global execution lease remains authoritative. Current operational MCP evidence also shows authenticated Streamable HTTP with bearer auth, but that research executor is not claimed here as the final Frank production API.

The uncovered semantic gap is inside an admitted interaction: a relay AI can authenticate as a token holder, yet that does not prove that every sentence it forwards or synthesizes originated with the human. Frank therefore needs a way to reason about multiple semantic principals in one request without flattening them into one authenticated voice.

## Candidate
**ATOMIC-CANDIDATE-ASVB-001 / Authority-Separated Voice Braid.** The candidate keeps four distinct ClayCode voice classes:
- `AUTHENTICATED_ORIGIN`: independently origin-bound human/user semantics;
- `RELAY_ACTOR`: semantics introduced by the external AI/bridge;
- `TRANSPORT_METADATA`: routing/session/client data with no instruction authority;
- `RELAY_ASSERTED_ORIGIN`: a relay's claim about what the user said when no independent origin proof exists.

These boundaries must survive DE_TO_CLAY translation, cognition, summarization/memory and effect-gate extraction. Relay context may influence reasoning, but it cannot silently become authenticated user intent.

## Executable discovery that changed the design
The first proxy was wrong. It let each relay sign the scope of its own hop. A relay could therefore widen a previously narrowed incoming scope while retaining a cryptographically valid self-signed chain. The executable test exposed this authority-laundering bug.

The corrected proxy makes each delegation edge **parent/grantor-sealed**. The recipient can only attenuate future scope; it cannot rewrite its own incoming grant. Presenter proof is separate. This synthetic HMAC construction is a discriminator only, not a production cryptographic proposal.

## Measurements
Main run: 50,000 randomized synthetic cases across normal traffic plus scope escalation, subject swap, origin tamper, resource swap, stale epoch, actor reorder/drop, grant-signature tamper and relay injection.

- ASVB: 0 false allows, 0 false denies.
- shared bearer baseline: 38,919 false allows.
- delegated-scope-only baseline: 25,548 false allows.
- local ASVB verifier p50: 14.762 microseconds; p95: 46.179 microseconds.
- median encoded envelope: 1,224 bytes.
- replay control: first consume allowed, second consume rejected as replay.

Five independent 20,000-case replications (100,000 additional cases) also produced 0 ASVB false allows and 0 false denies. At eight relay hops, local median verification was 79.889 microseconds and median encoded size 2,937 bytes.

These are local synthetic semantic-proxy measurements, not target-VPS or network end-to-end performance.

## Prior-art collision and strongest counterhypothesis
The broad authorization idea is not novel. OAuth Token Exchange already models subject and actor delegation; Rich Authorization Requests express structured fine-grained authorization; sender-constrained tokens/proofs and resource indicators constrain presentation and audience; attenuating delegated credentials are established elsewhere too. MCP authorization/security guidance likewise emphasizes proper OAuth resource-server boundaries and rejects token passthrough.

Accordingly, an explicitly idealized `RFC8693 + RAR + sender-constrained` baseline was given exact per-turn claims in the proxy and also achieved 0 false allows / 0 false denies. This is the strongest result of the counterhypothesis: ASVB currently has **no evidence of benefit as a new authorization protocol**.

The surviving hypothesis is narrower: standardized authorization may still need a Frank-native semantic representation that keeps user-origin, relay-added and transport voices distinct after authentication and through the DE_TO_CLAY boundary. That is what must be tested next.

## Decision
**NO ARCHITECTURE PROMOTION.** Status `SUPPORTED_SYNTHETIC_PROXY_RETEST`.

The next falsifier is a real standards-first differential on Frank's actual token API/translator path:
1. build the smallest standards-based subject/actor + fine-grained authorization + sender-constrained envelope;
2. test direct user, user -> AI -> Frank, multi-relay and AI-only traffic;
3. preserve/inspect voice provenance after DE_TO_CLAY, summaries and memory/re-entry;
4. attack token rotation/revocation, audience, replay, relay insertion and origin-label tampering;
5. compose with the owner-fixed single-spawn global-busy lease;
6. compare ordinary signed application provenance against explicit ASVB voice types.

If ordinary standards-based application metadata preserves exactly the same semantic/provenance boundary with lower complexity, ASVB should be recorded as `NO_BENEFIT` rather than promoted.
