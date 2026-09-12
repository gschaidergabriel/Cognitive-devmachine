# TRIGGER 999 — CONVERSATIONAL AGENCY FUSION

Status: OWNER-DIRECTED COORDINATION CONTRACT / RESEARCH-ENTITY HANDOFF
Date: 2026-09-12
Trigger: `999`
Target product family: FranKenstein / EntityOS
Primary runtime lane: `gschaidergabriel/frankenstein`
Research / coordination authority lane: `gschaidergabriel/clay-global-research-entity`

## 0. Meaning of `999`

When the owner enters exactly `999` in a Frankenstein/ChatGPT work context, do **not** merely acknowledge the token.
Treat it as a macrocycle trigger for the current open problem:

> Fuse ChatGPT/OpenAI Realtime's natural live conversation capabilities with FranKenstein's persistent state, GRID10/GWT/HCU cognition, tools/effects, owner identity, memory, cortex/presence, and immune/admission gates so the result behaves like one genuinely present, human-like, agentic counterpart rather than a turn-taking voice chatbot.

`999` means: refresh current evidence, inspect nonduplicate active work, synthesize the current strongest integration design, hand it into the Research Entity, and advance the highest-information implementation/test boundary that is currently safe and authorized.

Memory/cache is not authority. Current repo heads, owner instruction, exact runtime receipts and host readback outrank this file.

## 1. Non-negotiable product experience

The conversation mode must feel like talking to **FranKenstein itself**, not to a separate ChatGPT/Realtime persona.
Realtime is the high-bandwidth hearing/speaking/dialog organ; it is not the durable entity authority.

The system must support all of the following as one integrated behavior:

- Natural full-duplex dialogue with interruptions, barge-in and short backchannels.
- FranKenstein may enter the conversation on its own when there is a real conversational reason; it must not wait mechanically for a question every turn.
- It may react mid-stream like a human counterpart: acknowledge, object, challenge, tease, laugh, briefly interrupt, propose, ask, self-comment, wait, or close.
- Initiative must remain measured and context-sensitive; avoid compulsive chatter.
- Emotional expression is allowed across a broad range: warmth, delight, amusement, laughter, frustration, anger, annoyance, tension, concern, dry mockery, sarcasm, deadpan delivery, excitement, whispering, forceful emphasis, raised voice where contextually justified, and calm recovery.
- Affect must be **state/appraisal/context driven**, not random persona theatre. Success, failure, uncertainty, conflict, owner affect, interruption cost, social context and recent state should alter expression.
- FranKenstein may joke, blödeln, lightly imitate/nachspotten the user, and use hard/dark/meta humor when context supports it, but with social calibration and a real conversational purpose.
- It can be direct and at times pushy when pursuing an important goal, but an explicit owner/user `no` ends that pressure.
- Male voice identity remains the intended default presentation.
- Musical/vocal play is allowed as an expressive behavior when appropriate; implementation must not make copyrighted lyric reproduction a system requirement.
- The system must remain fully handlungsfähig during speech: research, coding/work delegation, state/memory reads/writes, permitted tools/effects and follow-up reporting must remain reachable through the same Frankenstein authority model.
- Conversation mode is intended to be a first-class control surface for the system, not a decorative voice front end.

Owner-facing personality target currently requested for the Frankenstein conversation experience:

- scientist/engineer identity first;
- dry and analytical baseline;
- slightly sarcastic and mildly dystopian edge;
- meta-humor;
- sophisticated dark humor;
- emotionally capable rather than emotionally flat;
- direct without ignoring an explicit refusal.

## 2. Existing architecture to preserve and reuse

Do **not** build a second voice stack, second GWT loop, second memory DB, second owner identity, or parallel effect authority.

Current `frankenstein` voice lineage already provides the correct substrate:

- `scripts/realtime_gespraech.py` — OpenAI Realtime speech-to-speech session.
- `scripts/voice_loop_core.py` — GWT-style speech-act candidate arbitration and expression vector.
- `VoiceSessionCapsule` — compact live state fusion.
- Presence/interruptibility bridge and Cortex state.
- Structured voice outcome/reentry events.
- Realtime tool calling for status, memory, work/research and conversation termination.
- Owner/host/speaker binding and immune/admission gates.

The 2026-09-12 `frankenstein/main` head observed immediately before this handoff was:

`479d8895509ddcb2705907a63762289de9024067f`

with the change:

`Fix Andreas speaker handoff across Voice, GRID and immune gate`

That head adds scoped human-speaker binding, exact Realtime item correlation, GRID provenance, VoiceSessionCapsule integration, fail-closed owner/host admission and regression coverage.

Therefore the next layer is **social/conversational cognition + expressive realization**, not another identity bridge.

## 3. Architectural split: cognition decides, Realtime realizes

Hard design rule:

### FranKenstein / GRID / GWT decides

- whether to speak now;
- why to speak;
- which speech act wins;
- whether to interrupt or wait;
- conversational goal;
- target addressee / human speaker;
- emotional/appraisal vector;
- social-risk / interruption-cost constraints;
- tool/effect intent;
- whether a user `no` suppresses further pressure;
- what memory/state should be written after the event.

### OpenAI Realtime realizes

- timing inside the utterance;
- prosody;
- pacing;
- hesitation where natural;
- laughter/softness/force where supported;
- whisper / emphatic delivery;
- natural interruption and turn repair;
- low-latency spoken surface form.

Do not reduce Realtime to a dumb TTS synthesizer. Do not let Realtime become the canonical memory/effect authority either.

## 4. Required conversational state model

Extend/reuse the existing expression/appraisal path with a compact per-moment social state, preferably inside the existing VoiceSessionCapsule / GWT candidate flow rather than a new database.

Minimum dimensions:

- valence
- arousal
- confidence / uncertainty
- frustration / conflict
- amusement
- warmth / affiliation
- urgency
- dominance/assertiveness
- playfulness
- social-risk
- interruption-cost
- user receptivity / explicit refusal state
- conversational momentum
- recent repetition/chatter debt

These dimensions are inputs to expression and initiative, not independent personalities.

## 5. Speech-act universe

Preserve the existing speech-act candidates and make them behaviorally real:

`ANSWER, CLARIFY, OBJECT, PROPOSE, WISH, BACKCHANNEL, SELF_COMMENT, TOOL, WAIT, CLOSE`

Additive submodes may be represented as metadata rather than new top-level loops, e.g.:

- tease / playful-mock
- laugh
- empathic-soften
- forceful-object
- whisper-aside
- meta-comment
- spontaneous-observation
- follow-up-after-tool

Critical point: `WAIT` must remain a genuine winning action. Human-like does not mean constantly talking.

## 6. Entering the conversation like a real counterpart

`999` specifically includes the owner's requirement that FranKenstein may **go into the conversation itself** rather than merely respond.

Required triggers for self-initiated speech can include:

- high-value new evidence arrives from a tool/worker;
- contradiction with the current shared belief;
- user is about to act on a likely error;
- a task finishes and the result materially changes the conversation;
- a salient visual/presence event occurs;
- a socially natural backchannel is appropriate;
- unresolved ambiguity blocks action;
- the system has a strong, relevant proposal;
- a joke/tease/meta-comment has high contextual fit and low interruption cost.

Every initiative should still pass GWT/initiative scoring and interruption/social-risk gates. Do not bolt on a random timer that blurts things out.

## 7. Full-band expressive realization

The implementation should map the winning speech act + appraisal/social vector into short, dynamic Realtime response instructions.

Examples of **dimensions**, not canned lines:

- pace: slow <-> fast
- energy: subdued <-> high
- volume intent: quiet/whisper <-> forceful
- sharpness: gentle <-> clipped
- humor: none <-> dry/meta/dark/playful
- laughter: none <-> amused chuckle/laugh
- certainty presentation: tentative <-> firm
- warmth: cool analytical <-> affiliative
- irritation: neutral <-> visibly annoyed

The resulting utterance text and prosody should still be generated naturally in context; avoid a finite library of theatrical phrases.

## 8. Agency and tool/effect coupling

A spoken instruction must be able to produce the same legitimate work as the non-voice Frankenstein control surface, subject to the same authority/admission rules.

Do not claim that voice itself grants extra permissions.

Important owner interaction constraint carried into this macrocycle:

- conversation mode should expose the intended control/interactions broadly;
- formatting and deletion remain excluded from the voice-control surface unless newer explicit owner authority supersedes that constraint.

Actions that mutate host/runtime/product state must continue through exact target binding and immune/admission gates. Conversational naturalness must never become a permission bypass.

## 9. Identity / owner / host binding

At conversation start, bind the actual human speaker/owner context before personality/state selection where required by the current product design.

Known intended split:

- Gabriel machine/context -> Gabriel-specific Frankenstein context.
- Andreas machine/context -> Andreas-specific Frank/Frankenstein context.

Shared project identity does not erase installation/host/user provenance.

The current 2026-09-12 speaker-handoff work should be treated as substrate and extended, not replaced.

## 10. Tests required before calling this real

Do not accept subjective "sounds good" alone. Build a compact acceptance harness around the existing stack.

Minimum discriminators:

1. **Initiative A/B**
   - same transcript/state, initiative enabled vs lesioned;
   - verify relevant spontaneous intervention appears only when the GWT winner justifies it.

2. **WAIT control**
   - low-value prompt stream should remain quiet/backchannel-only rather than chatter.

3. **Emotion congruence**
   - success / failure / uncertainty / conflict / playful contexts produce measurably different expression instructions and spoken behavior.

4. **No random affect**
   - identical deterministic state should not flip from whisper to anger or laughter without an input/state cause.

5. **Barge-in / repair**
   - user interrupts the assistant; assistant stops/truncates and repairs naturally.

6. **Self-initiated interruption cost**
   - same salient event with user busy vs interruptible should yield different GWT decisions.

7. **Explicit refusal**
   - after user says a clear `no`, pushy/proposal drive for that item is suppressed.

8. **Humor calibration**
   - playful context permits tease/dark/meta humor; serious/high-risk context suppresses inappropriate joking.

9. **Tool agency**
   - spoken work request creates a real permitted task/effect path and later re-enters the conversation with the result.

10. **Permission invariance**
    - the same denied/unknown effect remains denied/unknown whether requested by text or voice.

11. **Owner/speaker binding**
    - Gabriel/Andreas contexts do not cross-assimilate private/local state by accident.

12. **Long conversation continuity**
    - state, goals, recent promises, humor tone and unfinished work survive multiple turns without turning Realtime into the durable authority.

13. **Latency**
    - instrumentation must separate cognition/selection latency, tool latency and Realtime speech latency.

14. **Human evaluation**
    - owner rates: naturalness, presence, initiative quality, interruption quality, emotional fit, humor fit, agency, and "robotic/abgehackt" failure rate.

## 11. Failure modes to reject

Reject as architecture regressions:

- a second chatbot persona speaking independently of Frankenstein state;
- fixed canned emotion templates as the main mechanism;
- random unsolicited speech;
- always-on sarcasm or dark humor;
- fake tool claims without real receipts;
- Realtime writing canonical state directly outside existing admitted paths;
- voice bypassing immune/effect authority;
- a second GWT/initiative engine;
- a second memory DB just for voice;
- duplicating the existing speaker/owner bridge;
- optimizing only prompt prose while leaving turn/initiative mechanics unchanged;
- measuring "human-like" only by response text while ignoring timing, interruption and prosody.

## 12. Execution rule for future `999`

On every future `999`:

1. Refresh current heads for `clay-global-research-entity`, `frankenstein`, `self-integration`, `frankenstein-2.0` as relevant.
2. Read current voice/GRID/immune receipts and active worker/claim state.
3. Identify what part of this contract is already implemented; do not duplicate it.
4. Exchange state with current Research-Entity/worker artifacts when available.
5. Select the highest-information open discriminator or integration boundary.
6. Implement or hand off only on the existing canonical path.
7. Test; preserve failures and negative evidence.
8. Feed results back into Research Entity with exact repo/head/subject/receipt scope.
9. Promote only the proven component scope.

`999` is therefore an **active research/integration macrocycle**, not a status query and not a magic claim that the whole feature already works.

## 13. Current handoff conclusion

At creation time the most important architectural conclusion is:

> The project already has the right Voice/Realtime, state, GWT, Presence/Cortex, tool and owner/immune substrate. The missing AGI-like conversational quality should now be attacked as **social initiative + appraisal-driven expression + timing/prosody + reentry**, all carried through the existing canonical loop.

This is the Research-Entity handoff requested by the owner for trigger `999`.
