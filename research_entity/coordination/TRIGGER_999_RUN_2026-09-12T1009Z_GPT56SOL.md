# TRIGGER 999 — LIVE CONVERGENCE RECEIPT

Timestamp: 2026-09-12T10:09Z
Organ: ChatGPT / GPT-5.6 Sol
Scope: Realtime human-conversation fusion
Status: PARTIAL_COMPONENT_PROGRESS / NEXT_PRODUCT_GATE_BOUND

## 1. Current reality refreshed

This run began from the V2 bootstrap but treated it only as cache. Current repository evidence superseded several snapshot values during the run.

Observed product progression during this invocation:

- `frankenstein/main` initially observed at `479d8895509dd88dcf716df75f3d56c41f895e7f` — speaker handoff across Voice/GRID/immune gate.
- Main then advanced to `444b68c455d787c28c9db67c68f9af529057f042` — explicit conversation presence initiative policy.
- Main then advanced to `a95832929e07abf9a27ec6392d261e1fc8761f71` — regression tests for conversation presence modes.
- Main then advanced to `bdb2a74f09fe7d40e52bd2ae30cc2dcdd4846ce7` — conversation presence policy regression added to CI.

Observed Research Entity progression:

- this organ first persisted `research_entity/coordination/TRIGGER_999_CONVERSATIONAL_AGENCY_FUSION_2026-09-12.md` at `cee4319dba74f1943358895398059efa90ce5e75`;
- other concurrent organs then converged trigger `999` into the master trigger/registry and added the canonical Realtime human-conversation build protocol. At one refresh the Research Entity main head was `9f12f4203747bc95c515abe4ad6ae3a3c47d06b2` with message `master trigger protocol: add 999 Realtime human-conversation role`.

## 2. Verified existing substrate

Current canonical product source already contains:

- OpenAI Realtime speech-to-speech session;
- canonical Voice/GWT speech acts including WAIT;
- real GWT candidate scoring with interruption cost and chatter debt;
- VoiceSessionCapsule;
- Presence/interruptibility integration;
- UnifiedDB retrieval into conversation context;
- state-derived Frankenstein affect with categories including satisfied, annoyed, angry, exhausted, sarcastic and exaggerated-sweet/sarcastic;
- user-affect appraisal from real user transcript;
- exact Realtime-item truncation path for barge-in;
- asynchronous work/research result reentry;
- scoped speaker/owner/host binding and immune/admission checks.

Therefore the current problem is not lack of architecture. It is realization/integration quality.

## 3. Strongest concrete gap found

Before the new policy was added, the existing `realtime_gespraech.py` call site had binary initiative realization semantics:

- GWT `SPEAK` + `initiative_modus == shadow` => log only;
- GWT `SPEAK` + any non-shadow mode => realize speech.

The new main-module `scripts/conversation_presence_policy.py` correctly introduces explicit:

`shadow -> confirm -> limited -> adaptive`

with hard gates for user NO/STOP, presence, interruption cost, chatter debt and the invariant that conversational speech admission never grants effect authority.

However, at the last inspected canonical `realtime_gespraech.py`, this new policy had not yet been wired into `_stille_reopen_pruefen()`.

This is the immediate product closure gate.

Product issue created for this exact boundary:

- `gschaidergabriel/frankenstein#48`
- title: `[999] Wire conversation presence policy into canonical Realtime/GWT path`

The issue specifies exact input signals, SUPPRESS/CONFIRM/ALLOW behavior, no-effect-authority invariant, logging requirements and integration regressions.

## 4. Important second gap: full-duplex interruption

The current Realtime path contains a documented echo-loop workaround: microphone upload is muted while Frankenstein audio is playing and for a calculated tail afterwards. This stabilized self-echo/cost loops but sacrifices true word-in-the-mouth interruption during that mute window.

Therefore a claim of fully natural human full-duplex conversation is not currently earned even though exact item truncation support exists. A later `999` gate should test a real AEC/PipeWire-style path or an equivalent exact acoustic solution before promoting full-duplex human-conversation acceptance.

## 5. Concurrent branch review / collision avoidance

Several `999` branches were present. This run deliberately did not duplicate them.

Notable observation:

- `chatgpt-work/999-social-action-controller-20260912` had a large divergence from current main and introduced multiple additional Voice/full-runtime/host-agent/controller components. That direction risks violating the canonical `999` non-duplication law. It should not be merged wholesale merely because it has many files/tests; useful isolated ideas may be selectively ported only after exact review.

- the current main presence-policy delta is much smaller and aligns with the canonical architecture. It is the preferred convergence surface.

## 6. Promotion status

Earned during this run:

- `999` is now persistently registered as a Research Entity build trigger.
- explicit initiative-mode policy exists on product main.
- policy unit regressions exist and are included in CI.
- exact next product integration gate is bound in issue #48.

Not earned:

- no claim that the new policy is already active in live Realtime;
- no promotion from `shadow` to `limited`/`adaptive` production behavior;
- no real-speaker acceptance;
- no full-duplex/AEC acceptance;
- no whole human-conversation acceptance;
- no AGI/consciousness claim.

## 7. Next nonduplicate execution step

1. Wire `conversation_presence_policy.decide_initiative()` into the existing `_stille_reopen_pruefen()` realization boundary.
2. Add call-site regressions covering SUPPRESS/CONFIRM/ALLOW + stale-context dominance + user NO + effect-authority invariance.
3. Keep production default `shadow` until those pass.
4. Run real Realtime/microphone test and measure whether limited initiative improves presence without chatter spam.
5. Then attack the documented full-duplex echo/AEC boundary.

This receipt is evidence/navigation only. Current heads and exact runtime receipts outrank it on future `999` runs.
