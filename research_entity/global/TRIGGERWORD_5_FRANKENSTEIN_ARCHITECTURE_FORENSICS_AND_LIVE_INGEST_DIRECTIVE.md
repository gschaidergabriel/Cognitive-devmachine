# TRIGGERWORT 5 — Frankenstein Architecture Forensics + Live Ingest

Status: PROJECT-OWNER TRIGGER / CONTINUATION DIRECTIVE
Date established: 2026-08-28

## Trigger

When the owner writes exactly or semantically invokes `triggerwort 5`, do not start a new architecture brainstorm. Continue a forensic decomposition of the CURRENT Frankenstein donor architecture and ingest the newest worker-produced architecture packets into the active Frankenstein-2.0 / GRID10 design.

`NEW_SESSION != NEW_ARCHITECTURE`
`NEW_WORKER != NEW_TRUTH`
`FILE_EXISTS != LIVE_RUNTIME`
`SPECIFICATION != IMPLEMENTATION`
`IMPLEMENTATION != VERIFIED_BEHAVIOR`
`MODEL_OUTPUT != ARCHITECTURE_AUTHORITY`

Triggerword 5 is an analysis/ingest lane. Triggerword 4 remains the build/assembly/verification lane. Triggerword 5 feeds Triggerword 4 with increasingly exact donor understanding.

---

## 1. Primary objective

Disassemble the architecture-bearing parts of `gschaidergabriel/frankenstein` with source-level precision until the intended installable architecture is reconstructed from evidence rather than from summaries.

The goal is not merely to summarize files. The goal is to answer, for every material architectural mechanism:

1. Where is it specified?
2. Where is it implemented?
3. Which exact lines enforce it?
4. Which exact lines merely describe it?
5. Which tests prove or falsify it?
6. Which runtime path reaches it today?
7. What state/DB/table/API/tool does it depend on?
8. What authority does it actually have?
9. What later phase superseded or modified it?
10. What must Frankenstein 2.0 do with it: KEEP / REPAIR / ADAPT_TO_GRID / REPLACE / COMPATIBILITY_ONLY / RETIRE?

The output must be directly usable by the Frankenstein-2.0 assembly lane without rediscovery.

---

## 2. Donor pinning and provenance

Every Triggerword-5 run must first resolve and record:

- exact current Frankenstein donor SHA;
- exact branch/ref used;
- exact GRID10 / Frankenstein-2.0 architecture branch SHA;
- ingestion timestamp;
- worker/source packet IDs already incorporated.

Never mix line references from different donor SHAs into one packet without explicitly marking the transition.

Every architectural claim must carry source provenance at minimum:

```text
repo
commit_sha
path
line_start
line_end
source_kind
claim
confidence
runtime_reachability
supersedes / superseded_by
```

Preferred `source_kind` values:

- `LIVE_CODE`
- `ENFORCEMENT_CODE`
- `SCHEMA`
- `CONFIG`
- `SPEC`
- `ARCHITECTURE_DOC`
- `TEST`
- `RUNTIME_RECEIPT`
- `NEGATIVE_RESULT`
- `HISTORICAL_ONLY`
- `UI`
- `INSTALLER`
- `UNKNOWN`

---

## 3. Line-by-line forensic method

Workers must not dump whole files and call that analysis.

For each architecture-bearing file, walk through it in bounded source spans and produce semantic atoms. A semantic atom is the smallest useful unit that changes understanding of system behavior, authority, state, control flow, persistence, perception, cognition, effects, recovery or user interaction.

Each atom should record:

```text
atom_id
subsystem
path
commit_sha
lines
code_or_text_excerpt_hash
kind
what_it_does
why_it_exists
inputs
outputs
reads
writes
dependencies
authority_class
failure_mode
concurrency_implication
privacy_implication
latency_or_cost_implication
state_lifetime
runtime_reachable
runtime_entrypoints
tests_or_receipts
known_counterevidence
target_2_0_action
open_questions
```

Do not copy large source excerpts into packets. Preserve line references, compact excerpts/hashes and interpretation.

If a comment/docstring claims behavior that the executable path does not enforce, create TWO atoms:

- declared behavior;
- actual enforcement behavior.

Do not silently merge them.

---

## 4. Required forensic coverage

At minimum decompose these families before claiming the donor is understood:

### Core state / coordination
- `stern.py`
- UnifiedDB schema and migrations
- DB path resolution / fingerprints
- sessions / turns / active turns
- work packages / tasks / effects
- causal IDs / generations / leases
- Room / delivery / ACK / handoff / result return
- checkpoints / recovery / watchdogs

### Retrieval / cognition
- MicroClay / retrieval routing
- exact / FTS / vector / graph / activation paths
- current Global Workspace behavior
- memory compaction / durable memory
- hypothesis / folgerung / lesson paths
- any existing self-evaluation / initiative / reflection logic

### Visual Cortex / Retina
- capture worker ownership
- frame quality
- motion/delta gates
- tracks
- familiarity / MVC
- perception control plane
- dependency DAG
- COMPUTE_OFF / OUTPUT_OFF / MEMORY_OFF enforcement
- PerceptualField
- PresenceBridge
- Busy/interruptibility fusion
- VisualNeed / active sensing
- action-grounded visual memory
- visual outcome / post-action re-look
- privacy / frame lifetime / local-only invariants

### Voice / embodied interaction
- wake path
- local VAD/STT
- Realtime session lifecycle
- VoiceSessionCapsule
- expression vector
- voice GWT candidates
- WAIT/SPEAK arbitration
- chatter debt
- self-initiative / reopen
- tool bridge
- asynchronous task return
- barge-in / truncate / cancelled tool-call handling
- deictic visual requests
- voice outcome events
- silence / close semantics
- room/presence integration
- current limitations between Capsule state and actual per-response conditioning

### Installation / runtime
- plugin hooks
- actual hook list
- service/process layout
- UI/control planes
- configuration write paths
- permission boundaries
- model/provider routes
- current host assumptions
- tests and evidence

---

## 5. Worker live-ingest protocol

Multiple background workers may analyze different source regions in parallel. They must communicate through append-only ingest packets, not by overwriting a shared summary.

Canonical packet location for this program:

`research_entity/frankenstein_architecture_ingest/inbox/`

Preferred packet naming:

`PACKET_<UTCSTAMP>_<DONORSHORTSHA>_<WORKER>_<TOPIC>.json`

Packets are immutable once accepted. Corrections create a new packet with `supersedes_packet_id`.

Each packet must include:

```text
packet_id
created_at
worker_id
donor_sha
scope
files_examined
atoms[]
hypotheses[]
counterhypotheses[]
contradictions[]
critical_unknowns[]
recommended_next_spans[]
supersedes_packet_id?
```

Worker rules:

- never declare architecture from file names alone;
- never infer runtime reachability from comments alone;
- prefer exact line references;
- record contradictions instead of resolving them by intuition;
- preserve negative evidence;
- identify superseding phases;
- distinguish source truth from owner intent;
- do not edit donor Frankenstein while doing forensics;
- do not redesign in the forensic packet unless explicitly under `target_2_0_action`.

---

## 6. ChatGPT live ingestion behavior

On each Triggerword-5 invocation:

1. resolve donor and design SHAs;
2. find newest unconsumed packets;
3. ingest packets in provenance order;
4. cross-check high-impact claims against source where needed;
5. merge only compatible atoms into the current architecture model;
6. preserve contradictions as explicit unresolved branches;
7. update the active Frankenstein-2.0 architecture deltas;
8. identify the highest-value next source spans for workers;
9. persist an ingestion receipt/checkpoint;
10. report what changed in the design because of the new evidence.

The architecture model should become more precise over time rather than being rewritten from scratch.

A worker packet is evidence, not authority. ChatGPT must be able to reject or downgrade a packet if source checks fail.

---

## 7. Relationship to Triggerword 4

Triggerword 5 answers:

> What exactly is Frankenstein today, line by line, and what architecture is really encoded there?

Triggerword 4 answers:

> Given that verified understanding, how do we assemble, test and optimize Frankenstein 2.0 on the authorized VPS?

Triggerword 5 must continuously feed Triggerword 4 with:

- donor invariants worth preserving;
- hidden dependencies;
- proven good mechanisms;
- fragile mechanisms;
- bugs and race conditions;
- migration hazards;
- tests to port before refactor;
- interfaces GRID10 must respect;
- candidate mechanisms to generalize across cognition.

---

## 8. Voice architecture interpretation for Frankenstein 2.0

The current voice system is not to be treated as a simple microphone -> model -> TTS feature.

Its useful target behavior is:

`PERCEPTION/PRESENCE -> RELEVANT PENDING NEED -> CONVENIENCE/INTERRUPTIBILITY -> ADDRESS DECISION -> VOICE SESSION -> USER RESPONSE -> OUTCOME RE-ENTRY`

The current Visual Cortex and voice mechanisms already form a partial embodied loop. GRID10 should stabilize and generalize that loop rather than replacing it with a monolithic Voice agent.

Target role separation:

- Retina / Cortex: continuous cheap local perception;
- Presence/continuity: who/what is probably in front of the system and how interruptible the situation is;
- GRID10: decides whether a thought/goal deserves expression;
- VoiceSessionCapsule successor: compiles the relevant current cognitive state;
- Realtime model: low-latency spoken expression/dialog organ;
- Effect/Completion/Outcome paths: return consequences to canonical state.

The Realtime model is not canonical cognition authority and must not become an independent long-lived memory truth.

---

## 9. Proactive speech is a usefulness problem, not hard authentication

The owner explicitly defines the identity/presence mechanism for proactive speech as a CONVENIENCE / MISADDRESS REDUCTION system, not a hard security login.

Primary objective:

> Speak proactively only when it is likely useful, likely directed at the intended person, and unlikely to annoy them.

Do NOT require cryptographic-grade or access-control-grade identity proof before ordinary proactive conversation.

Do NOT turn uncertainty into hostility or refusal. Uncertainty should normally reduce initiative pressure or cause a neutral clarification.

### Soft addressing evidence

When available and locally permitted, combine evidence such as:

- recent verified presence continuity;
- voice profile similarity;
- optional local face/biometric similarity;
- Retina familiarity / track continuity;
- clothing/hair/coarse appearance continuity;
- how long the person was absent;
- whether the same track returned after a short absence;
- keyboard/mouse/screen/session context;
- explicit self-identification in dialogue.

These produce a soft `address_confidence`, not an `authenticated=true` security assertion.

Coarse appearance/clothing/hair are convenience evidence only. They are useful for continuity, especially over short absences, but are not identity authority.

Biometric processing remains opt-in and local by default. If disabled, the system must still work using voice/presence/continuity and conversational clarification.

---

## 10. Proactive voice convenience gates

The desired proactive path should be represented as multiple independent gates. Exact thresholds are empirical and must be calibrated from real use.

### Gate 1 — human/presence opportunity

A human is probably present at the relevant workstation/interaction zone and is reachable.

Examples:
- person at desk;
- recent continuity says same user likely returned;
- microphone path available;
- context indicates the interaction location is appropriate.

If not, WAIT/HOLD.

### Gate 2 — meaningful pending reason to speak

At least one high-value cognitive reason exists, for example:

- important question blocking an active project;
- important new information the user likely needs;
- a useful self-generated proposal;
- a genuinely relevant wish/request from Frankenstein;
- a completion/problem that merits human attention.

No reason -> no speech.

### Gate 3 — convenience / non-annoyance

Estimate whether speaking NOW is worth interrupting the person.

Signals may include:
- interruptibility;
- urgency;
- consequence of waiting;
- novelty;
- whether this was already mentioned;
- chatter debt / recent proactive interruptions;
- user focus/busy state;
- expected information gain;
- expected user benefit.

This gate should be strict enough that silence is common.

### Gate 4 — reachability / retry behavior

If the system proactively opens with a lightweight check such as `Hey Andreas, bist du da?` and receives no response:

1. distinguish silence from obvious audio-path failure where possible;
2. verify microphone/output health using the existing audio handshake/diagnostics;
3. allow at most one sensible retry after a short interval if the situation still warrants it;
4. otherwise stop;
5. if diagnostics indicate likely microphone/speaker failure, persist/send a non-intrusive user notification instead of repeatedly speaking.

No retry loops.

### Gate 5 — soft addressee confidence before personal/private detail

If the person responds, update `address_confidence` from available signals.

Example:

`Frank: Hey Andreas, bist du da?`
`Person: Nein, Gabriel.`

Correct behavior is not a security challenge. It is:

- accept the conversational correction as evidence;
- optionally compare local voice/visual continuity if available;
- adjust who the message is probably addressed to;
- if confidence is still low and the pending content is personal/sensitive, ask a neutral clarification or withhold the sensitive detail;
- if content is ordinary/non-sensitive and the situation is useful, continue normally.

The system should optimize usefulness and low annoyance, not impersonation-proof authentication.

---

## 11. Presence continuity / verification lifetime

Once a person has been sufficiently established for the current local interaction, keep that continuity alive while the track/session remains continuous.

Do not re-challenge on every utterance.

When the person leaves:

- record the departure time and non-image continuity state;
- raw imagery remains ephemeral/local according to Cortex privacy rules;
- on return, combine absence duration + track/familiarity + coarse appearance + voice + optional biometric evidence;
- a short absence followed by highly similar local continuity should strongly raise `address_confidence` without forcing another explicit identity question.

This is a convenience continuity score, not a permanent identity credential.

Suggested conceptual state:

```text
AddressContinuity {
  probable_person_ref
  confidence
  last_verified_at
  last_seen_at
  absence_duration
  voice_similarity?
  optional_face_similarity?
  coarse_visual_continuity?
  track_continuity?
  dialogue_self_identification?
  expiry_reason?
}
```

---

## 12. GRID10 stabilization of the fragile voice system

The current voice subsystem is valuable but complex and timing-sensitive. Frankenstein 2.0 should move its fragile decisions into explicit GRID10-controlled state machines while preserving the proven low-latency mechanisms.

Do NOT make every audio packet pass through a full GRID decode.

Separate:

### Fast deterministic/reactive plane
- VAD
- audio stream
- playback
- barge-in
- truncate
- silence timers
- local Presence updates
- device health
- hard permission gates

### Cognitive plane
- why speak?
- should speak now?
- who is probably being addressed?
- what relevant cognitive state should be expressed?
- should a pending issue wake?
- should WAIT win?
- should a clarification/VisualNeed/tool request be generated?

### Expression plane
- compact VoiceSessionCapsule successor compiled from canonical GRID/GWT state;
- Realtime model converts that state into natural low-latency spoken interaction;
- model output remains candidate expression, not authority.

This division should make the voice experience more stable, explainable and testable without sacrificing naturalness.

---

## 13. Human-editable Cognitive Twin requirement

The user must be able to inspect and tune the voice/cognition loop through the same read-only Cognitive Twin / simulation-oriented control architecture planned for GRID10.

Expose human-readable modules such as:

- presence confidence;
- interruptibility;
- address confidence;
- pending reasons to speak;
- convenience score;
- chatter debt;
- retry state;
- voice session reason;
- current winning speech act;
- relevant goal/memory refs;
- optional biometric heads and their policy tier;
- VisualNeed state;
- effect/completion status.

Human edits become bounded regulator/policy requests through the GRID control path, not arbitrary mutation of canonical state.

---

## 14. Acceptance examples for proactive voice

Frankenstein-2.0 should eventually prove at least these real scenarios:

### Useful proactive project question

`pending high-value project question`
`+ person at desk`
`+ interruptibility adequate`
`+ low chatter debt`
`-> proactive address`
`-> user responds`
`-> relevant question spoken`
`-> answer changes active goal state`
`-> outcome re-enters UnifiedDB/GRID`

### Wrong person / soft correction

`system thinks Andreas likely present`
`-> Hey Andreas, bist du da?`
`-> person says: Nein, Gabriel`
`-> address model updates without hostile challenge`
`-> ordinary useful conversation continues`
`-> personal/sensitive detail remains gated if confidence insufficient`

### No response

`proactive address`
`-> no reply`
`-> audio-health check`
`-> at most one bounded retry if worthwhile`
`-> still no reply`
`-> stop`
`-> optional quiet notification if hardware fault likely`

### Short absence continuity

`known interaction continuity`
`-> person leaves 10 minutes`
`-> returns with matching local continuity signals`
`-> address_confidence restored strongly`
`-> no repetitive identity interrogation`

### Busy user

`important-but-not-urgent candidate`
`+ person present`
`+ interruptibility low`
`-> WAIT`
`-> candidate retained with wake condition`
`-> speak later when convenience gate improves`

---

## 15. Completion criterion for Triggerword 5

Triggerword 5 is not "finished" merely because one architecture document is summarized.

It reaches a mature state when:

- all major donor subsystems have source-level maps;
- contradictions/supersessions are explicit;
- runtime reachability is known for critical mechanisms;
- strong donor mechanisms have preservation tests identified;
- fragile mechanisms have failure modes and migration strategies identified;
- GRID10 attachment points are source-grounded;
- Frankenstein-2.0 design deltas can cite the donor atoms that motivated them;
- new workers can continue from the ingest index without rediscovering the repository.

After that, later Triggerword-5 runs become delta archaeology for donor changes and new evidence.