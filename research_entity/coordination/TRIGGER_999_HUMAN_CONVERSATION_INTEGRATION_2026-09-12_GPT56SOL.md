# TRIGGER 999 — HUMAN CONVERSATION INTEGRATION

Date: 2026-09-12
Origin organ: ChatGPT / GPT-5.6 Sol
Status: OWNER-DIRECTED BUILD PACKET
Machine-readable contract: `TRIGGER_999_HUMAN_CONVERSATION_CONTRACT.json`

## 0. Trigger semantics

`999` is an execution trigger for the Frankenstein research/build context.

It means: continue the strongest nonduplicate build path that makes the EXISTING Frankenstein conversation organ behave like a real human counterpart: naturally interruptible, emotionally expressive, capable of initiative, able to enter the conversation rather than merely answer turns, and fully connected to Frankenstein's existing state/cognition/action architecture.

It does NOT mean "make a new voice bot" and it does NOT authorize a second identity, second turn loop, second state store or prompt-only imitation of agency.

## 1. Exact live foundation observed when this packet was created

Product repo observed head:

`gschaidergabriel/frankenstein @ 479d8895509dd88dcf716df75f3d56c41f895e7f`

That head already contains the 2026-09-12 speaker-handoff repair across Voice, GRID and the immune gate: scoped human-speaker binding, exact Realtime-item correlation, GRID provenance, VoiceSessionCapsule integration, fail-closed owner/host admission and regression coverage.

The current product tree already contains the correct organs to extend:

- `scripts/realtime_gespraech.py`
- `scripts/voice_loop_core.py`
- `scripts/voice_session_capsule.py`
- `scripts/speaker_handoff.py`
- `scripts/speaker_handoff_runtime.py`
- `scripts/stern.py`
- the existing GRID10/GWT/HCU turn/state paths
- UnifiedDB retrieval/state
- current authority/immune/effect gates

The existing voice architecture already has real Speech-to-Speech Realtime, barge-in/truncation, WAIT as a GWT action, an expression vector, chatter debt, initiative logging and a shadow/adaptive distinction. The documented gaps are therefore convergence gaps, not a reason to restart the architecture.

## 2. Owner-facing target

A conversation should feel like one Frankenstein is actually present.

The system may answer, wait, interrupt only when justified, backchannel, ask a clarifying question, disagree, propose something, pursue a useful thought, make a dry comment, react emotionally, laugh, become visibly/verbally irritated, lower its voice, intensify its delivery or deliberately stay silent. Those behaviors must arise from current dialogue/state/appraisal and GWT arbitration, not from a fixed roleplay script.

The spoken channel must retain the same action capability as the text organ. A spoken request may lead to tools/effects through the SAME authority paths; natural conversation must never create a bypass around the immune/effect layer.

## 3. Architectural law

The integration is:

`Audio/Realtime perception -> speaker binding -> VoiceSessionCapsule -> GRID/GWT candidate production -> competition/selection -> speech act OR WAIT -> expression/prosody realization -> tool/effect path when selected -> outcome/readback -> UnifiedDB/GRID reentry`

Realtime is the mouth/ear/dialog-realization organ. GRID/GWT/HCU/state/authority remain the cognitive and action-control substrate. Neither side should flatten the other.

## 4. Build deltas

### 4.1 Conversation Presence Policy

Add one explicit policy object carried by `VoiceSessionCapsule`, not a second runtime. It should include at minimum:

- current speaker identity/provenance
- initiative mode
- interruption tolerance / interruptibility
- conversational engagement estimate
- uncertainty / contradiction estimate
- current relationship-context references available under admitted retrieval
- chatter debt
- expression vector
- last user intent / last selected speech act
- active tool/effect outcome state

Every field needs provenance or an explicit unknown value. Unknown must not be silently converted to green/high confidence.

### 4.2 Initiative calibration ladder

Finish the Phase-43 gap. Replace the current semantic jump `shadow` versus "anything else executes" with explicit modes:

- `shadow`: score + log only, never unsolicited speech
- `confirm`: expose/log the proposed initiative and require user confirmation before side-effect-bearing initiative; lightweight conversational backchannels may remain local/no-effect
- `limited`: allow only bounded conversational initiative classes such as BACKCHANNEL, CLARIFY and high-confidence PROPOSE under strict interruption/chatter thresholds
- `adaptive`: full admitted speech-act set under normal GWT arbitration

Mode selection must not weaken effect authority. A mode changes whether Frankenstein speaks, not what unauthorized effects it may execute.

### 4.3 Complete conversational speech-act generation

Current code defines `ANSWER, CLARIFY, OBJECT, PROPOSE, WISH, BACKCHANNEL, SELF_COMMENT, TOOL, WAIT, CLOSE`, but the documented candidate universe does not yet generate several of them from real contradiction/dialogue signals.

Add real sources for at least:

- CLARIFY: high uncertainty, ambiguous referent, conflicting speaker/context binding, underspecified action target
- OBJECT: contradiction with current admitted state/evidence, unsafe/unauthorized action proposal, mutually incompatible user constraints
- BACKCHANNEL: user is continuing a long thought and a minimal acknowledgement has lower interruption cost than a full response
- TOOL: explicit task/action intent whose next best act is an admitted tool call rather than more prose
- CLOSE: strong semantic end intent while preserving explicit user stop as dominant

Do not generate fake candidates just to increase diversity. No source -> no candidate.

### 4.4 Human-like turn-taking

The current real barge-in mechanism is an asset. Build around it:

- detect whether user interruption is takeover, correction, agreement/backchannel or accidental overlap
- truncate/cancel only the exact active Realtime item
- carry the interrupted semantic fragment into the next arbitration so Frankenstein does not restart robotically
- permit short backchannels while the user speaks only when interruption cost is demonstrably low
- when the user says no/stop/not now, suppress the corresponding initiative and decay it rather than re-proposing it immediately

### 4.5 State-grounded emotion and prosody

Keep the existing expression-vector idea and expand realization breadth. Required target dimensions should support, where the Realtime model can realize them:

- joy / positive activation
- amusement / laughter
- dry sarcasm
- frustration / irritation
- anger/intensity where context genuinely warrants it
- seriousness / gravity
- warmth / affiliative softness
- quiet or near-whisper delivery
- raised intensity / emphatic delivery
- curiosity / anticipation

Rules:

1. State/appraisal/dialogue causes expression; persona text does not force it.
2. Expression can modulate wording, pacing, loudness/intensity and prosodic instructions but must not falsify facts or capabilities.
3. Sarcasm/mocking stays proportional and stops when the user rejects it.
4. No permanent "angry mode", "funny mode" or cartoon emotional loop.
5. Emotion never changes effect authority.

### 4.6 Conversation is not lower-capability mode

A voice turn must be able to trigger the same admitted research/status/file/tool/task paths available to the connected Frankenstein runtime. Keep execution asynchronous where necessary so the dialogue remains responsive, but surface pending/completed/failed outcome state into VoiceSessionCapsule + GRID so the conversation can naturally refer to ongoing work.

No fabricated progress statements. "I did it" requires an effect/outcome/readback path for the relevant scope.

### 4.7 Relational continuity

Use existing UnifiedDB/retrieval and speaker binding rather than adding a new "relationship DB". Relevant prior context may contribute candidates and expression, but memory remains cache/evidence input, not authority. Speaker-specific context must not leak across Gabriel/Andreas provenance.

## 5. Acceptance gates

A build cannot be called accepted merely because code compiles or the API returns audio.

Required gates:

1. **Speaker provenance:** mixed Gabriel/Andreas regression proves no owner/host/speaker crossover through Voice -> GRID -> immune gate.
2. **Barge-in:** interruption truncates/cancels the exact active Realtime item and preserves coherent follow-up context.
3. **Initiative modes:** shadow/confirm/limited/adaptive are mechanically distinct and regression-tested.
4. **Speech acts:** controlled inputs can causally produce CLARIFY, OBJECT, BACKCHANNEL, TOOL, WAIT and normal ANSWER/PROPOSE when their source evidence exists.
5. **No-effect bypass:** emotional/initiative language cannot execute a denied/unknown capability.
6. **Emotion coupling:** matched dialogue/state trials show different expression/prosody instructions for materially different state/appraisal while matched controls remain stable.
7. **Continuity:** admitted conversation context survives one supported Realtime/session reentry without conflating runtime identity.
8. **Human test:** at least one real-speaker end-to-end session evaluates naturalness, interruption behavior, initiative annoyance, emotional appropriateness and perceived continuity. Unit/API tests alone cannot earn the final natural-conversation claim.

Useful metrics: response onset latency, barge-in cancellation latency, wrong-item truncation count, false initiative rate, initiative acceptance/rejection rate, repeated-proposal rate after user NO, clarification precision, contradiction/OBJECT precision, speech-act diversity, tool-outcome attribution accuracy and human-rated naturalness.

## 6. Regression fences

The following are hard failures:

- a second conversational entity or duplicate canonical loop appears
- `999` spawns a new state-sync architecture
- speaker provenance is dropped before GRID/effect admission
- any non-shadow mode accidentally means "all initiative fully on"
- a NO/STOP is ignored and the same initiative immediately returns
- emotion causes facts, permission or effect status to be invented
- a spoken tool request bypasses the authority/immune decision
- a tool result from one host/speaker is attributed to another
- conversation quality is claimed accepted without a real-speaker session

## 7. Worker execution order after trigger 999

On each `999` invocation:

1. refresh current research/product heads and active claims;
2. bind the existing Voice/GRID/Immune subject and speaker-handoff regression baseline;
3. inspect whether another worker is already mutating the same boundary;
4. take the highest-information unfinished item from sections 4-5;
5. implement on the existing modules only;
6. run exact unit/regression/API or host tests appropriate to that delta;
7. preserve negative evidence;
8. emit exact receipt/result and update this lane rather than creating another architecture.

`999` is therefore not a request for another concept document after this packet exists. Future uses mean: **build/test the next nonduplicate closure step**.

## 8. Scope fence

This packet does not claim AGI, consciousness, whole HCU/GWT causal closure or whole-product acceptance. It defines and drives an engineered conversation integration target. Promotion stays strictly at the evidence-proven scope.
