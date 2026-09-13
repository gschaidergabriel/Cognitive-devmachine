# VOICE999 — Human Conversation / Social Presence Coordination Packet

Date: 2026-09-12
Status: CURRENT_RESEARCH_PACKET
Trigger: exact user input `999`
Target: existing Frankenstein voice/conversation stack; no second voice loop

## Owner intent

When `999` is entered, the research entity must treat the whole Frankenstein conversation system as an active engineering target. The user-facing goal is not merely correct answers or a persona prompt. Frankenstein should behave like a coherent, capable conversational counterpart: temporally fluid, willing to enter the conversation on its own when useful, able to interrupt/backchannel/recover naturally, emotionally expressive when state supports it, technically agentic, and continuous across tools/state/reentry.

The observed defect to attack first is the owner's direct report that the current voice interaction feels strongly robotic / chopped-up. Do not optimize around this wording; falsify concrete mechanisms.

## Existing target — reuse, do not duplicate

Canonical implementation candidate currently exists in `gschaidergabriel/frankenstein` PR #41:

- branch: `chatgpt-work/voice-full-integration-20260912`
- head observed during this 999 activation: `dfff97231a65ff87fec832df077c4e24e1245189`
- contract: `VOICE_FULL_INTEGRATION_2026-09-12.md`
- runtime controller: `scripts/voice_full_integration.py`

That work already defines/implements:

- Gabriel/Andreas person + host binding separation;
- real host-switch semantics;
- GWT/GRID/retrieval/state integration target;
- voice-only proactive agency/persona;
- explicit-no pressure stop;
- Realtime event telemetry for speech, transcripts, barge-in, tool intents and response release;
- FORMAT and DELETE voice-gate denials while preserving canonical authority for other effects.

Do not create a replacement voice controller, second GWT/GRID loop, voice-only DB, second effect authority or duplicate watcher.

## 999 engineering contract

Frankenstein branch:

- `chatgpt/voice-999-generative-reality-20260912`
- Clay contract after this activation: `clay/voice_999_generative_reality.clay`
- commit: `04e8046345e9e2cb68504ce04d0982efbee0502c`

The Clay contract now binds human-conversation quality as a vector rather than a single score and explicitly reuses the existing full-voice integration target.

## First discriminator family

Measure before changing production. Highest-information initial candidates for the reported robotic/choppy behavior:

1. false turn cutoffs — Frankenstein releases/ends turns before the user's utterance or thought is actually complete;
2. response-onset jitter — inconsistent or excessively delayed onset creates mechanical cadence;
3. barge-in recovery — interruption works technically but loses conversational intent/context;
4. post-tool context drop — tool/action handoff breaks the social/conversational thread;
5. repetitive template language — structurally correct but predictably patterned replies create robot feel;
6. initiative mismatch — either irrelevant unsolicited speech or missing initiative when a high-value conversational opening exists;
7. affect without grounded state — prosody/emotion appears random or detached from conversation state;
8. action-followthrough gap — voice sounds agentic but does not actually carry authorized actions through canonical effect paths;
9. pressure-after-no — explicit refusal does not terminate pressure on the rejected proposal.

## Measurement vector

Do not collapse quality into one scalar. Preserve at least:

- turn_fragmentation_rate
- false_cutoff_rate
- awkward_silence_rate
- overlap_error_rate
- response_onset latency/distribution
- barge_in_recovery latency
- post_tool_continuity
- cross_turn_semantic_continuity
- initiative_relevance
- initiative_overreach_rate
- explicit_no_pressure_violations
- affect_grounding
- affect_range
- repetition/template rate
- action_followthrough
- user_correction_rate

Every value needs exact sample provenance. Owner subjective ratings are valid outcome evidence but not the only discriminator.

## Behavioral target

Operational definition of “real counterpart”:

`temporal continuity + semantic continuity + relevant initiative + interruption recovery + grounded affect + action followthrough`

It is NOT:

- more verbosity;
- random emotion;
- constant joking;
- constant initiative;
- constant agreement;
- pretending the Realtime model itself is persistent entity authority.

Realtime-native strengths (prosody, barge-in, audio context, turn dynamics, fast tool intent) should remain in Realtime. Durable identity, state, memory, authority, GRID/GWT and effect verification remain Frankenstein-owned.

## Execution order for the research entity

1. Bind exact current PR #41 / current main / current Voice999 branch before work.
2. Observe a bounded real conversation sample with exact runtime/host/person provenance.
3. Reconstruct social-presence episodes from existing Realtime/GRID/initiative telemetry.
4. Rank the strongest measurable failure, starting with turn cutoff / onset / interruption / post-tool continuity.
5. Generate competing hypotheses and counterhypotheses.
6. Run the cheapest discriminator that can separate them.
7. Express accepted semantics in ClayCode before promotion.
8. Implement only in isolated workspace/branch; preserve active WIP.
9. Require tests + independent review + measured pre/post readback.
10. Propose uptake through existing GRID/canonical paths only.

## Promotion fence

This packet and the Voice999 Clay change are research contracts, not proof that the live voice runtime is fixed. No production activation or humanlike-conversation PASS is claimed here. Promotion requires real conversation evidence on the exact runtime subject.
