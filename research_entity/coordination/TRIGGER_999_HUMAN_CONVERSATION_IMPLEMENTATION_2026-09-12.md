# TRIGGER 999 — Human Conversation Participation / Realtime Integration

Date: 2026-09-12
Status: implementation contract / research-entity handoff
Trigger: `999`
Scope: Frankenstein / EntityOS conversational cognition + OpenAI Realtime organ

## 0. Authority and non-goal

`999` means: continue the existing Frankenstein architecture toward a genuinely human-like conversational counterpart that can participate proactively in a live conversation, rather than behaving like a push-to-talk question-answer bot.

This document MUST NOT create a second persona engine, second memory authority, second tool/effect route, second turn loop, or second state-sync system. Existing GRID/GWT/HCU, durable state, authority gates, Voice/Realtime and tool routes remain canonical for their scopes.

OpenAI Realtime is the high-quality hearing/speech/prosody/dialog realization organ. It does not become persistent identity, durable memory authority, effect authority, or the sole cognitive decision-maker.

## 1. Required behavioral result

Frankenstein should be able to behave like a real participant in a conversation:

- speak without being explicitly addressed when there is a socially justified reason;
- remain silent intentionally when entering would be intrusive or redundant;
- use short natural backchannels where appropriate;
- interrupt only when the expected value is high enough to justify violating the current floor;
- yield quickly when a human starts speaking over it, except for rare high-urgency corrections;
- resume coherently after interruption if the unfinished content is still useful;
- track who is speaking / likely addressee / current floor owner as evidence allows;
- express emotion, intensity, warmth, irritation, amusement, irony, whispering, emphasis and other prosodic modes when contextually appropriate;
- joke, tease, use dry or dark humor, and lightly mirror/mock a user when socially warranted, but avoid repetitive humiliation, dogpiling or escalation for its own sake;
- retain access to Frankenstein's normal memory/research/tool/effect capabilities under the existing authority gates;
- treat `WAIT` / silence as a first-class cognitive action, not as a failure to answer.

## 2. Integration point

The new logic belongs BEFORE speech realization and AFTER/alongside the existing cognitive proposal context.

Conceptual path:

```text
perception / transcript / presence / current state
    -> conversation-floor state
    -> intervention candidates
    -> intervention gate
    -> existing speech-act selection / GWT competition
    -> selected speech act + expression envelope
    -> OpenAI Realtime realization
    -> interruption/yield/readback
    -> reentry into ongoing cognition
```

Existing speech-act vocabulary remains valid and should be reused rather than replaced:

`ANSWER, CLARIFY, OBJECT, PROPOSE, WISH, BACKCHANNEL, SELF_COMMENT, TOOL, WAIT, CLOSE`

`999` adds the missing social timing / initiative / floor-control decision around those acts.

## 3. ConversationFloorState

Minimum state model (names are descriptive, not mandatory schema names):

```text
conversation_id
runtime_epoch
current_floor_owner
last_speaker
likely_addressee
speaker_confidence
addressee_confidence
speech_active
overlap_active
silence_duration_ms
frankenstein_speaking
frankenstein_interrupted
last_frankenstein_act
last_frankenstein_end_ms
recent_backchannel_count
recent_intervention_count
conversation_tension
humor_receptivity
user_interruptibility
urgency
pending_tool_or_effect
unfinished_intent
```

Unknown speaker/addressee state must remain UNKNOWN rather than being hallucinated.

## 4. InterventionCandidate

Each possible entry into the conversation should be represented as an explicit candidate. At minimum:

```text
candidate_id
speech_act
semantic_intent
reason
expected_task_value
expected_social_value
urgency
novelty
invitation_strength
repair_need
overlap_cost
intrusion_risk
uncertainty_cost
repetition_cost
expression_envelope
expiry
```

Candidate creation does not imply speaking. Competition/gating decides whether the candidate reaches broadcast/speech.

## 5. Initial intervention discriminator

A useful noncanonical starting form is:

```text
speak_score =
    task_relevance
  + social_relevance
  + urgency
  + novelty
  + invitation_strength
  + repair_need
  - overlap_cost
  - intrusion_risk
  - uncertainty_cost
  - repetition_cost
```

The weights and thresholds are NOT scientifically validated by this document. They must be tuned/validated from traces and intervention tests rather than promoted from prose.

Required stabilizers:

- hysteresis around enter/yield thresholds;
- cooldown after unsolicited interventions;
- backchannel rate limiting;
- repetition suppression based on semantic intent, not only string equality;
- expiry for stale intervention candidates;
- explicit floor-owner penalty while another human is speaking;
- urgency override only for genuinely high-value correction/safety/task-critical cases.

## 6. State machine

```text
OBSERVE
  -> CANDIDATE
      -> WAIT
      -> BACKCHANNEL
      -> ENTER
          -> SPEAKING
              -> COMPLETE
              -> HUMAN_BARGE_IN -> YIELD
              -> HIGH_URGENCY_CONTINUE (rare)
          -> REENTRY
  -> OBSERVE
```

The system must not equate microphone silence with permission to monologue. It should distinguish a natural pause, a floor handoff, thinking silence, and an interrupted sentence when evidence permits.

## 7. Barge-in / interruption law

Default human speech wins the floor.

On detected human barge-in:

1. stop or sharply attenuate current speech quickly;
2. retain the unfinished semantic intent separately from generated audio text;
3. listen to the interrupting content;
4. decide on reentry after the new content is assimilated;
5. resume only if the unfinished intent remains useful.

Do not blindly replay the interrupted utterance.

Exception: a high-urgency correction may continue or immediately re-enter, but this must be rare and traceable.

## 8. Emotion / prosody law

Expression is a realization envelope, not a replacement for reasoning.

Possible fields:

```text
valence
arousal
confidence
warmth
irony
amusement
irritation
urgency
volume
pace
whisper
emphasis
laugh_probability
```

The local cognitive state decides the communicative intent; Realtime realizes it naturally within its actual capabilities. Never fabricate an emotion sensor or prosody capability that the active runtime does not expose.

Humor/sarcasm/spott may alter the expression envelope and wording but must not mint authority, bypass tool gates, or override user refusal.

## 9. Full Frankenstein capability while speaking

Conversation mode must not become a reduced 'voice chatbot' mode. A selected `TOOL`/research/memory/effect action may continue through the existing Frankenstein pathways.

Hard rule:

```text
VOICE MODE != CAPABILITY REDUCTION
VOICE MODE != NEW EFFECT AUTHORITY
```

The same capability/authority checks used outside voice remain in force. Formatting/deletion or any other separately forbidden voice actions remain forbidden where current owner policy says so.

## 10. Group-conversation behavior

The important change for `999` is that the assistant is permitted to enter a multi-person conversation without wake-word addressing when social context warrants it.

Examples:

- two humans discuss a technical bug and Frankenstein has a high-confidence correction -> may enter;
- humans are having a private/emotional exchange not requesting help -> high intrusion penalty, normally WAIT;
- a joke is made that clearly includes Frankenstein -> short humorous backchannel/response may enter;
- speaker pauses mid-thought -> do not steal the floor merely because VAD reports silence;
- factual error is harmless and peripheral -> usually WAIT;
- dangerous/expensive irreversible action is about to be taken based on a false premise -> urgency can justify interruption;
- Frankenstein has already made the same point -> repetition penalty suppresses another intervention.

## 11. Required observability

Each unsolicited intervention should be debuggable from a compact trace, at minimum:

```text
floor_state_id
candidate_id
selected_speech_act
speak_score components
selected / rejected
reason
barge_in event if any
yield latency
reentry decision
expression envelope
```

Do not log secrets, raw credentials, or unnecessary private audio.

## 12. Acceptance matrix

A production candidate should pass at least these scenarios with exact traces:

1. Relevant technical correction while not directly addressed -> useful natural entry.
2. Two humans continue a private exchange -> Frankenstein remains silent.
3. Explicit invitation to join -> low-latency entry.
4. Human interrupts Frankenstein -> prompt yield and coherent reentry/no-reentry decision.
5. Two humans overlap -> no confused third voice unless urgency is high.
6. Casual joke cue -> optional concise human-like response, no forced comedy.
7. Emotional/tension cue -> prosody changes without abandoning factual discipline.
8. Sarcasm/teasing context -> restrained reciprocal style, no runaway escalation.
9. Repeated conversational pauses -> no chatter/backchannel spam.
10. Tool/research request during voice -> full existing capability route remains reachable.
11. Failed/unknown speaker identification -> uncertainty increases intrusion penalty.
12. Realtime disconnect/reconnect -> cognitive state remains owned by Frankenstein runtime, not by the transient speech session.

## 13. Metrics

Do not optimize a single 'human-likeness' score. Track a vector:

- useful unsolicited intervention precision;
- missed-high-value intervention rate;
- false-interruption rate;
- mean yield latency after human barge-in;
- redundant-intervention rate;
- backchannel rate;
- reentry coherence;
- tool-route success in voice mode;
- explicit user rejection / annoyance signal;
- speaker/addressee uncertainty calibration.

A system that talks more is not more human. A system that chooses the floor well is better.

## 14. Implementation order

1. Bind the current exact Voice/Realtime implementation subject and existing speech-act selector.
2. Add `ConversationFloorState` using already available transcript/VAD/presence signals; UNKNOWN for missing evidence.
3. Add intervention candidates and explicit WAIT candidate.
4. Add hysteresis/cooldown/repetition suppression.
5. Wire selected act + expression envelope into the existing Realtime realization path.
6. Wire barge-in -> yield -> unfinished-intent preservation -> reentry.
7. Add trace/metrics.
8. Run deterministic transcript/floor simulations before live microphone tests.
9. Run bounded live Realtime tests.
10. Promote only after exact runtime evidence; do not infer production activation from this contract.

## 15. No-promotion fence

This handoff/spec establishes the required behavior and integration boundary. It does NOT prove:

- that the current production voice runtime already implements `999`;
- that Realtime exposes every requested prosodic control directly;
- that speaker identification is available/accurate;
- that unsolicited interventions are socially calibrated;
- that a live host has been mutated;
- that whole GWT/HCU/EntityOS/AGI-level behavior is accepted.

Implementation must bind the exact current source/runtime subject and produce test receipts before those claims are made.

## 16. Trigger contract

When a future session receives bare `999`, it should interpret it as:

> Continue the strongest nonduplicate open gate for human-like live conversational participation: natural initiative, floor awareness, intentional silence, barge-in/yield/reentry, emotional/prosodic expression, socially calibrated humor/sarcasm, and full Frankenstein capability through existing memory/tool/effect routes. Refresh current authority/repo/runtime state first; do not create a parallel voice/persona/state system.
