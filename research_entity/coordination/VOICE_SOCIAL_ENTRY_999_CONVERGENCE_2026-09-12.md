# 999 — VOICE SOCIAL-ENTRY / HUMAN CONVERSATION CONVERGENCE CONTRACT

Date: 2026-09-12
Producer: ChatGPT / GPT-5.6 Sol as FranKenstein web cognitive organ
Target: Clay research entity + Frankenstein Voice/GRID/GWT integration
Status: RESEARCH HANDOFF / SOURCE-LEVEL CONTRACT, NOT PRODUCT PROMOTION

## 0. Why this exists

`999` is the owner trigger for converging FranKenstein's conversation mode toward a real human-like conversational counterpart while preserving the full engineered entity behind it.

The voice model is **not** a reduced voice assistant. Voice is a live cognitive/I/O organ of the same FranKenstein entity. Persistent identity, owner/installation binding, UnifiedDB/TITAN memory, GRID10/GWT arbitration, tools/effects, Cortex/presence, re-entry and evidence rules stay active.

The remaining interactional gap is not merely response wording or emotion. The missing control problem is **social entry**: humans do not answer every audible utterance. They continuously estimate whether they are addressed, whether a contribution is useful, whether a backchannel is appropriate, whether interruption is justified, or whether remaining silent is the correct action.

## 1. Hard invariants

1. **One entity, multiple organs.** Realtime/Voice never becomes an independent identity or memory authority.
2. **No second turn loop.** Social-entry logic must feed the existing canonical GRID/GWT/Voice arbitration path, not create a parallel cognitive authority.
3. **No reflexive response rule.** `speech_stopped` or transcript completion is evidence that an utterance occurred, not permission to speak.
4. **WAIT is a real action.** Silence can be the selected output, with explicit reason/evidence.
5. **BACKCHANNEL is distinct from ANSWER.** A short acknowledgement must not accidentally seize the floor.
6. **Tool/action intent remains full Frankenstein agency.** When a spoken turn implies coding/research/tool work, the execution path remains authority-gated and its outcome must return into the next cognitive state.
7. **Owner/host provenance remains exact.** Gabriel/ai-core-node and Andreas/andreas-maco must not be flattened into one local runtime.
8. **No provider execution from this handoff.** Current `NOW.md` still reports FreeSwarm provider admission HARD_OFF; any later provider use requires fresher explicit owner/supervisor authority.

## 2. Required continuously maintained conversation state

For each live acoustic/text/visual event, maintain a bounded `ConversationField` (RAM-first; durable evidence only where the canonical path already admits it):

- active speakers / speaker identity confidence
- current floor holder and floor-transition probability
- latest utterance + partial utterance stability
- direct-name/vocative evidence (`Frank`, `FranKenstein`, owner name, second-person deixis)
- addressee probability for FranKenstein vs another human vs broadcast-to-group
- gaze / face orientation / body orientation toward FranKenstein where available
- prosodic terminality / continuation evidence
- overlap state, interruption pressure and barge-in history
- silence duration and projected next-speaker probability
- affect/prosody cues: amusement, anger, teasing, uncertainty, urgency, whisper/shout, etc.
- current activity/task context from GRID/GWT/TITAN/VoiceSessionCapsule
- current owner/person binding + machine/installation provenance
- pending tool/effect/action and most recent execution outcome
- chatter debt / recent FranKenstein floor occupancy

Missing modalities must reduce confidence, not fabricate evidence.

## 3. Social-entry action space

The social-entry arbiter chooses a **speech act**, not a full utterance:

`WAIT | BACKCHANNEL | ANSWER | CLARIFY | OBJECT | PROPOSE | WISH | SELF_COMMENT | TOOL | CLOSE`

In addition, the implementation may annotate the act with interaction behavior:

`NORMAL_TURN | SHORT_OVERLAP | INTERRUPT | YIELD | REOPEN`

Important: `WAIT` and `BACKCHANNEL` are first-class winners. `TOOL` means the cognitive turn requires an effect/tool path; it does not bypass effect authority.

## 4. Core inference: should FranKenstein enter now?

Compute bounded evidence terms rather than a single prompt heuristic:

- `P_addressed`: probability FranKenstein is the intended addressee
- `P_floor_available`: probability a floor transition is open
- `P_contribution_value`: estimated utility of entering now
- `P_backchannel_fit`: probability a minimal acknowledgement helps without taking the floor
- `P_interruption_justified`: urgency/error/safety/explicit-invitation evidence
- `P_human_other`: probability the utterance is primarily between other people
- `P_continuation`: probability current speaker intends to continue
- `P_social_cost`: interruption + chatter debt + uncertainty cost

Conceptual competition:

```
S_WAIT        = w1*P_human_other + w2*P_continuation + w3*P_social_cost
S_BACKCHANNEL = b1*P_backchannel_fit + b2*P_addressed - b3*P_interruption_justified
S_SPEAK       = s1*P_addressed + s2*P_floor_available + s3*P_contribution_value
S_INTERRUPT   = i1*P_interruption_justified + i2*P_contribution_value - i3*P_social_cost
```

These are candidate features for GRID/GWT competition, not hardcoded truth. The implementation should preserve component values and selected-action provenance so the behavior is falsifiable.

## 5. Human-like behavioral laws

### A. Not every sentence is FranKenstein's turn

If another human is clearly addressed, default toward `WAIT`. FranKenstein may still enter when explicitly invited, when the group address is broad, when its task context makes a contribution unusually valuable, or when urgent correction/safety warrants an interruption.

### B. Backchannel without stealing the floor

Use short acknowledgements (`mhm`, brief laugh, `ja`, `okay`) only when timing and context support them. A backchannel must not automatically trigger a long model response.

### C. Real interruption, not timer theatre

Interruption is an action with evidence. High urgency or direct challenge can win; ordinary impatience cannot. If the user interrupts FranKenstein, truncation/barge-in remains immediate and the next state records that the previous turn was cut off.

### D. Enter conversations proactively, but selectively

FranKenstein is allowed to join an ongoing conversation without a wake phrase when the current session is already active and the social-entry score supports it. This must feel like a participant deciding to speak, not a microphone keyword bot firing on every utterance.

### E. Emotion belongs to the speech act

Emotion/prosody is not decoration applied after reasoning. The winning speech act should carry an `ExpressionVector` (e.g. warmth, amusement, irritation, confidence, urgency, volume, tempo). Full range is allowed when context supports it: friendly warmth, dry sarcasm, laughter, mockery/teasing, anger, whisper, shout, excitement. Expression must remain proportional and must not corrupt factual/tool accuracy.

### F. Action loop remains closed

When speech produces a real action intent, preserve the chain:

`heard intent -> GRID/GWT candidate -> selected TOOL/action -> authority gate -> execution -> exact result/receipt -> outcome event -> VoiceSessionCapsule/GRID uptake -> next spoken turn`

The current legacy Realtime path already injects completed background-task results back into the conversation and logs `task_completion`; this contract requires that social-entry/GRID state also consume the outcome so the next participation decision knows whether FranKenstein is still working, succeeded, failed, or should report proactively.

## 6. Current-source observations motivating this handoff

Current Frankenstein PR #41 (`chatgpt-work/voice-full-integration-20260912`) already contains substantial fusion work:

- Realtime as cognitive organ, not transport-only
- mandatory Gabriel/Andreas person + installation binding
- TITAN relationship context
- emergent retrieval before response release
- canonical GRID turn uptake on the local bound installation
- tool gate with fail-closed identity/remote routing behavior
- barge-in/realtime-event signals
- asynchronous task/research result reinjection

This means `999` must **not** build another voice runtime. The next clean layer is social-entry evidence/arbitration feeding the existing runtime.

## 7. Research basis (external, non-authoritative)

Recent dialogue research supports separating *when to speak*, *whether to backchannel*, and *what behavior to realize* rather than treating transcript completion as a response trigger:

- Lin et al., ACL 2025, **Predicting Turn-Taking and Backchannel in Human-Machine Conversations Using Linguistic, Acoustic, and Visual Signals** — multimodal linguistic/acoustic/visual signals jointly improve turn-taking/backchannel prediction. https://aclanthology.org/2025.acl-long.743/
- Inoue et al., NAACL 2025, **Yeah, Un, Oh: Continuous and Real-time Backchannel Prediction with Fine-tuning of Voice Activity Projection** — continuous frame-wise backchannel timing/type prediction. https://aclanthology.org/2025.naacl-long.367/
- Lee et al., NAACL 2025, **Behavior-SD** — models explicit turn-taking, interruption, fillers and backchannels as conversational behaviors, including simultaneous/full-duplex contributions. https://aclanthology.org/2025.naacl-long.484/
- Inoue et al., SIGDIAL 2025, **Prompt-Guided Turn-Taking Prediction** — demonstrates controllable turn timing conditioned on conversational style/context. https://aclanthology.org/2025.sigdial-1.9/

Engineering translation for FranKenstein: use native Realtime events + transcript/prosody + Cortex/presence + current GRID/Voice state as features, then arbitrate an explicit participation action.

## 8. First implementation slice — deliberately bounded

Do **not** start by training a large new model. Build a deterministic/inspectable `SocialEntryCandidate` adapter that consumes already-available signals and emits:

```
{
  action: WAIT|BACKCHANNEL|ANSWER|...,
  addressed_probability: float,
  floor_probability: float,
  continuation_probability: float,
  social_cost: float,
  reasons: [...],
  evidence_refs: [...],
  session_id,
  selected_person,
  machine_id,
  owner
}
```

Feed that object into the existing speech-act/GWT competition. Do not let it directly call `response.create`.

Initial behavior can be rules + calibrated thresholds; later replace individual estimators with VAP/audio/vision models only when measured failure data justifies it.

## 9. Acceptance gates for the first 999 cycle

A source/runtime implementation is not accepted until at least these discriminators exist:

1. **Other-human dialogue gate:** two humans talk to each other; FranKenstein remains silent unless explicitly addressed or high-value/urgent evidence exists.
2. **Direct-address gate:** `Frank, was meinst du?` yields high `P_addressed` and timely participation.
3. **Continuation gate:** a speaker pauses mid-thought; FranKenstein does not jump in merely because VAD emitted `speech_stopped`.
4. **Backchannel gate:** a long user turn can elicit a short acknowledgement without converting into a long floor-taking response.
5. **Barge-in gate:** user interrupts FranKenstein; output truncates, state records interruption, next turn adapts.
6. **Proactive-entry gate:** ongoing group conversation contains a clear relevant opening; FranKenstein may join once, then chatter debt suppresses repeated unsolicited entries.
7. **Tool feedback gate:** spoken coding/research request -> authority-gated execution -> real completion/failure -> next-turn state contains the exact outcome/ref.
8. **Identity gate:** identical audio/text under Gabriel vs Andreas binding never leaks the other installation's local state/effects.

Required metrics: false-entry rate, missed-direct-address rate, backchannel precision, interruption recovery, median decision latency, action-outcome closure rate, provenance completeness.

## 10. 999 execution law

Every future bare `999` should perform one bounded convergence cycle:

1. refresh current repo/authority/runtime evidence;
2. inspect active work and avoid duplicate mutation;
3. measure the strongest current conversational failure;
4. research only the bottleneck actually observed;
5. translate the result into the existing Clay/GRID/Voice architecture;
6. implement the smallest nonparallel slice;
7. run deterministic regression + exact-subject runtime readback where available;
8. emit a receipt with what changed, what failed, what is not promoted, and the next bottleneck.

No cycle earns whole-system promotion merely because one conversational discriminator passes.

## 11. Immediate next nonduplicate discriminator

Instrument the current PR #41 runtime at the point where transcript/barge-in/native Realtime events are already collected, but **before** response release. Prove on synthetic event sequences that the runtime can choose `WAIT` and `BACKCHANNEL` without invoking a normal full response. Only after that source-level discriminator passes should live microphone/group tests be attempted.
