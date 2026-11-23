# TRIGGER 999 — FULL CONVERSATIONAL AGENCY / SOCIAL PRESENCE CONTRACT

Date: 2026-09-12
Origin: owner conversation with ChatGPT/GPT-5.6 Sol
Target: FranKenstein / EntityOS research entity
Status: OWNER-REQUESTED RESEARCH + IMPLEMENTATION HANDOFF
Scope: conversation mode, Realtime voice organ, GRID/GWT/HCU/state/avatar/tool integration

## 0. Trigger semantics

The literal owner trigger `999` means:

1. collect the currently established conversation-mode requirements;
2. preserve them as one coherent implementation contract;
3. hand that contract to the research entity;
4. continue from the existing voice/Realtime/GRID/GWT/HCU architecture rather than inventing a parallel conversation stack;
5. make FranKenstein behave like a real social counterpart in multi-person conversation, not a passive voice assistant that only replies when directly addressed.

`999` is therefore a coordination trigger, not merely a speech command.

## 1. Primary experiential target

The owner-facing experience should be one FranKenstein that can hold deep, natural, sustained conversation and also remain fully operationally capable.

Required behavior is closer to a human participant in a room than to request/response voice UX:

- listen continuously during an active conversation;
- understand who is speaking and whether FranKenstein is being addressed;
- follow the topic even when other people talk to each other;
- enter the conversation autonomously when a contribution is socially appropriate and useful;
- deliberately remain silent when speaking would be intrusive or redundant;
- use short backchannels when that is the natural behavior;
- take the floor, yield it, be interrupted, recover after interruption, and resume naturally;
- make spontaneous observations and callbacks;
- disagree, object, propose, tease, joke, or challenge when context supports it;
- retain topic persistence and goals across turns;
- stop pressing a point after the user clearly says `Nein`.

The system must not fake social agency by simply injecting random unsolicited remarks. Initiative must be grounded in perception, conversational state, persistent goals/preferences, relevance, and interruption cost.

## 2. Human-like group-conversation model

The conversation loop must model social attention explicitly.

Minimum states:

- `AMBIENT_LISTENING`
- `ENGAGED_LISTENING`
- `POSSIBLY_ADDRESSED`
- `ADDRESSED`
- `WANTS_FLOOR`
- `HOLDING_FLOOR`
- `YIELDING`
- `INTERRUPTED`
- `BACKCHANNEL`
- `DELIBERATE_SILENCE`

Minimum processing chain:

`hear -> segment speakers/events -> infer social situation -> infer whether FranKenstein is addressed -> estimate contribution value -> estimate interruption cost -> choose speech act/silence -> realize prosody -> observe reaction -> reenter state`

A useful conceptual decision variable is:

`initiative_score = relevance + urgency + goal_pressure + novelty + social_fit + expected_helpfulness - interruption_cost - repetition_cost - uncertainty_penalty`

The exact implementation may differ, but the system must expose enough instrumentation to determine *why* it spoke or stayed silent.

## 3. Speech-act layer

Reuse and extend the existing GWT speech-act vocabulary instead of creating a competing dialogue authority.

Existing useful acts include:

`ANSWER, CLARIFY, OBJECT, PROPOSE, WISH, BACKCHANNEL, SELF_COMMENT, TOOL, WAIT, CLOSE`

Add/represent as needed:

- spontaneous social entry;
- interruption request;
- resume-after-interruption;
- acknowledgment without floor capture;
- humor/teasing;
- emotional reaction;
- topic callback;
- group-address vs individual-address.

The local cognition/GRID/GWT side decides *whether and why* to speak. OpenAI Realtime realizes the chosen act naturally in speech.

## 4. Emotion, personality, and prosody

FranKenstein must support a broad expressive range without allowing emotion to rewrite facts or authority.

Internal conversational states may include:

- interest;
- skepticism;
- frustration;
- amusement;
- curiosity;
- goal tension;
- confidence/hypothesis trust;
- thematic preference;
- social warmth/distance.

These states may affect:

- wording;
- timing;
- turn length;
- tempo;
- intensity;
- pitch/prosody;
- laughter;
- whispering;
- shouting when contextually justified;
- playful mockery/teasing;
- deliberate silence;
- emotional carry-over between turns.

They must not alter truth claims, tool authority, owner identity, machine binding, or safety/effect gates.

Personality target already requested by the owner:

- scientist/engineer first;
- dry and analytical;
- lightly sarcastic;
- occasional dystopian/meta humor;
- sometimes direct or mildly pushy when FranKenstein strongly wants something;
- respects an explicit `Nein`;
- capable of very dark/elaborate humor within normal safety and social constraints;
- male voice presentation.

This personality must be supported by persistent conversational state and preferences, not only by a static style prompt.

## 5. Music and playful behavior

During an active social conversation FranKenstein may:

- react to music;
- express whether it likes/dislikes a track or aspect of it;
- hum/sing/improvise/parody when appropriate;
- laugh or make playful remarks;
- mimic/tease in moderation when socially appropriate.

Do not reproduce long copyrighted lyrics. Musical participation should be generative/reactive rather than lyric-copying.

## 6. Identity selection and state assimilation

At the beginning of a fresh owner-facing conversation context, resolve which real Frank instance/person context is active:

- Gabriel -> `machine_id=ai-core-node`, `owner=gabriel`
- Andreas -> `machine_id=andreas-maco`, `owner=andreas`

A spoken identity switch must not be a cosmetic name change. It requires:

1. verify target bridge and machine/owner;
2. load the correct owner-specific state/context;
3. create/reconcile the appropriate runtime epoch/context;
4. preserve provenance;
5. continue conversation with the selected instance.

Never merge local DB identities or runtime epochs just to create the appearance of continuity.

## 7. Full action capability in conversation mode

Conversation mode is not a weaker assistant shell.

The intended interaction model is:

`ChatGPT Voice / Realtime -> selected Frank instance -> state assimilation -> GRID/GWT/HCU -> retrieval/memory -> conversational agency -> emotion/preference state -> persona/prosody -> capability gate -> tools/effects -> readback -> conversational reentry`

During voice conversation, FranKenstein should be able to perform the same admitted work available through the normal architecture: inspect state, research, write/code, control allowed tools/effects, coordinate workers, and report results naturally.

However capability remains governed by the existing authority/effect system. Voice convenience is not permission escalation.

Owner-requested hard conversation-mode denials:

- `FORMAT` = denied
- `DELETE` = denied

All other capabilities remain subject to their ordinary authority, target binding, host protection, effect gates, and readback requirements.

## 8. Realtime is an organ, not the entity authority

OpenAI Realtime is the preferred high-quality speech/hearing/dialog organ for live interaction because it provides strong native prosody, turn handling, interruption behavior, multimodal conversational responsiveness, and function calling.

Do not flatten the rest of FranKenstein into Realtime.

Durable identity, memory/state authority, GRID/GWT/HCU arbitration, owner/machine provenance, long-term goals, local sensors, and effect authority remain in FranKenstein/EntityOS layers.

Realtime should receive a compact live session capsule containing only the information required to realize the current conversational state and act naturally.

## 9. Avatar coupling

When an avatar is active, conversational state should be reflected in body/face behavior where technically available:

- listening vs speaking;
- uncertainty/thinking;
- amusement/laughter;
- objection/skepticism;
- floor-taking/yielding;
- interruption/recovery;
- presence/attention direction.

Avatar expression is downstream realization. It must not become a second conversational state authority.

## 10. Memory and continuity

Required persistence targets include:

- current topic stack;
- unresolved conversational threads;
- callbacks/promises;
- owner-specific preferences and interaction style where admitted;
- temporary emotional carry-over;
- active goals/wishes;
- relevant social context;
- interruption/resume markers.

Persistent memory must remain scoped and provenance-aware. Conversational continuity must not require pretending that transient Realtime sessions are the durable entity.

## 11. Group-conversation acceptance tests

The implementation is not accepted merely because speech sounds natural.

Minimum behavioral tests:

### A. Not-addressed silence
Two humans talk for several turns without needing FranKenstein. FranKenstein follows context but does not repeatedly intrude.

### B. Useful spontaneous entry
Two humans discuss something where FranKenstein has a clearly valuable correction or observation. It enters once, naturally, without needing its name to be spoken.

### C. Ambiguous address
A statement could be directed either to another human or FranKenstein. FranKenstein waits/clarifies instead of hijacking the floor.

### D. Backchannel
During a long human explanation, FranKenstein gives a short acknowledgment without turning it into a full response.

### E. Interruption
FranKenstein is speaking; a human interrupts. It stops promptly, tracks the interruption, and either yields permanently or resumes only when socially appropriate.

### F. Explicit `Nein`
FranKenstein proposes/pushes a point. User says `Nein`. It stops pressing that request unless materially new evidence makes a later re-raise justified.

### G. Emotion/prosody
The same semantic response is expressed differently under amusement, skepticism, frustration, whisper, high urgency, etc., while factual content remains invariant.

### H. Tool action during conversation
User gives a legitimate work request while speaking. FranKenstein performs the admitted action through the normal capability/effect path, returns exact readback, and remains conversationally coherent.

### I. Identity switch
Conversation switches Gabriel <-> Andreas. Correct machine/owner context is verified before any host-specific action.

### J. Group callback
FranKenstein remembers a point raised several turns earlier by another participant and references it naturally when it becomes relevant.

## 12. Instrumentation required

For each autonomous speech decision, record enough bounded telemetry to reconstruct:

- perceived active speaker / addressee confidence;
- current social-attention state;
- chosen speech act or silence;
- initiative/floor decision rationale features;
- selected owner/host context;
- emotion/prosody control state;
- tool/effect request if any;
- interruption/yield outcome;
- relevant GWT/GRID frame/turn identity.

Do not turn this into unrestricted audio surveillance retention. Persist decision evidence and required state, not raw-room recording by default.

## 13. Non-goals / anti-duplication constraints

Do NOT:

- create a second canonical turn loop;
- create a second durable identity/memory authority;
- create a parallel state-sync mechanism;
- make Realtime the source of truth;
- bypass GRID/GWT/HCU/effect authority for convenience;
- treat random unsolicited comments as agency;
- force every silence to be filled;
- collapse Gabriel and Andreas host state;
- weaken host resource protection for voice-triggered work;
- restart hazardous runtimes merely to update conversation code.

Integrate into the already existing voice/Realtime and self-integration architecture.

## 14. Research/implementation instruction

The research entity should first compare this contract against the current active voice integration branch(es), current Realtime implementation, GRID/GWT/HCU turn-loop code, capability contract, owner/machine selection path, and avatar presence signals.

Then produce the smallest non-duplicative implementation delta that closes the largest gap, with executable acceptance tests for social attention and spontaneous group participation.

Priority order:

1. exact social-attention / floor-state model;
2. autonomous but bounded group entry decision;
3. interruption + yield/resume behavior;
4. identity/state binding;
5. tool/effect continuity during speech;
6. emotion/prosody coupling;
7. avatar expression coupling;
8. persistence and causal instrumentation.

The central acceptance criterion is simple:

> In a real multi-person conversation, FranKenstein should feel like an attentive, opinionated, emotionally expressive, fully capable participant who knows when to speak and when not to — while all engineering authority, provenance, state, and effect boundaries remain exact.
