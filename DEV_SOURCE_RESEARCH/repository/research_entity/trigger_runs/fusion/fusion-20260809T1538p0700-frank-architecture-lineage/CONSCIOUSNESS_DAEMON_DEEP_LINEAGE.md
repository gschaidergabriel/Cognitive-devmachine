# FRANK Consciousness Daemon / persistent cognition — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis; no consciousness claim promotion

## CD-0 — initial persistent cognition

The first public Project-Frankenstein commit (`e1a8812767668091d146ee958bbc2ebb2743031c`, 2026-02-14) already contained a consciousness stream as part of the personality/self architecture. Its important architectural property was persistence between user turns: FRANK was not modeled only as a stateless request/response wrapper.

## CD-1 — expansion into a multi-rate cognitive daemon

Commit `7fb267399a10256a63863d83676b7dc265100ed9` (2026-02-16) added four major mechanisms:
- Perceptual Feedback Loop: fast hardware/user-state sensing and event detection;
- Latent Experience Space: 64-dimensional recurrent state vectors with novelty/drift detection;
- Attention Controller / AST: salience-based competition with self-correction;
- Persistent Goal Structure: extraction, decay and conflict detection.

This converted the daemon from a background reflection stream into a recurrent multi-timescale organism-like scheduler.

## CD-2 — canonical ten-loop architecture

Historical architecture documentation describes ten recurring loops:
- workspace refresh;
- mood trajectory;
- idle thought;
- prediction engine;
- memory consolidation;
- feature/self training;
- perceptual feedback;
- experience-space update;
- AST attention;
- goal management.

Representative early cadences:
- perception: ~200 ms;
- attention: ~10 s;
- workspace: ~30 s;
- experience: ~60 s;
- mood: ~60 s;
- prediction: ~120 s;
- goals/consolidation: minutes;
- deep/recursive reflection: long idle windows.

Fusion principle:
`one daemon/process != one timescale`.
The distinct rates are semantically meaningful and survive even when H3 physically collapses services.

## CD-3 — GWT channel weighting and explicit internal bridges

Commit `f2cb3914...` (2026-02-20):
- AST weights altered model-facing workspace channel detail;
- mood extremes changed channel allocation;
- Ego-Construct auto-training ran from workspace updates;
- deep reflection produced E-PQ events.

This established a recurrent graph:
`state -> attention/projection -> reflection -> personality -> later state`.

The later architecture must preserve causal identity through this loop because a textual reflection alone is not proof that personality or future behavior changed.

## CD-4 — delayed recursive self-reflection

Commit `cf88a9c...` replaced immediate pass-2 meta-reflection with delayed recursive reflection:
- delay ~15 minutes;
- reread earlier reflection;
- compare with current Ego-Construct;
- identify mismatch between prior written thought and current lived state;
- separate `reflection_depth` field;
- max 3 recursive reflections/day;
- outputs route to Titan, E-PQ and goals.

A pre-existing `all_features -> all_feats` bug had been crashing deep reflection and was fixed here.

Reusable principle:
- temporal distance can be a functional state variable;
- a recursive loop must preserve identity of the earlier episode it is evaluating.

## CD-5 — world-model bridge and repeated-observation bug

Commit `14b5071...` wired consciousness into world experience through seven injection points: idle, deep, recursive, novelty, mood shift, prediction outcome and consolidation.

Commit `6690e3d...` then found:
- the same resolved prediction was being re-observed every cycle;
- first mood recording generated a spurious delta from 0.0;
- hidden bare failures reduced observability.

Current rule:
- event identity/idempotency is mandatory;
- first-sample initialization is not a real change event;
- periodic readers cannot re-launder one historical outcome into repeated evidence.

## CD-6 — resource retuning and runaway-feedback protection

Commit `6501c1...` (2026-02-24) relaxed loop rates to reduce GPU/CPU load:
- perception 0.2 -> 1.0 s;
- workspace 30 -> 60 s;
- experience 60 -> 120 s;
- attention 10 -> 20 s;
- mood 60 -> 120 s;
- LLM perception interpretation 30 -> 60 s.

It also added protection so resource spikes caused by FRANK's own LLM use did not recursively trigger more LLM interpretation.

Current design law:
- sensing/event detection can remain cheap and frequent while model interpretation is resource-gated;
- self-induced effects must be source-tagged to prevent runaway feedback.

## CD-7 — self-reduction attractor caused by prompt policy

Commit `8cd6f9f...` documented a stable failure:
- idle system prompt instructed FRANK to reflect only on hardware/process/architecture;
- prompt distribution plus hardware-biased templates created a self-diminishing cognitive loop;
- last-three-thought spiral detection and prompt rebalancing were added.

The strongest lesson is architectural:
`recurrence amplifies projection bias`.

A current recurrent system therefore needs diversity/novelty controls and must distinguish canonical state from model-facing narrative.

## CD-8 — model routing generations changed cognitive economics

The daemon passed through multiple model architectures:
- early Llama/Qwen/Ollama paths;
- DeepSeek-R1/RLM phase (`07af9d3...`);
- autonomous research over restricted tools (`d2c08ba...`);
- three-tier CPU/GPU architecture (`05f5bb6...`);
- later direct-Qwen and Qwen-only architecture (`9fcf1f1...`, `62deb0a...`).

This matters because loop cadence, context budget and fallback semantics were partly optimized around model cost/latency of each era. Historical timings are therefore not automatically current target constants.

Current target separates cognitive semantics from backend placement/resource policy.

## CD-9 — computational proprioception and visual enrichment

Commit `9059666...` added adaptive visual pipeline and passive proprioception to every daemon LLM call. AURA/QR values were cached; the daemon could condition on body-like state without explicit tools.

Later `116ed71...` separated self-induced vs environment resource activity.

Current PerceptualField generalizes this direction:
- raw sensor state remains provenance-bound evidence;
- semantic projection is downstream;
- memory/world/goal priors are typed separately from bottom-up evidence.

## CD-10 — AURA/Swarm and queue semantics

`b8fd295...` changed AURA pattern reflection to an idle queue rather than direct send and added gaming-mode compliance.

Historical failure from `07f8e26...`:
- AURA queue was reportedly 79% full/drop-prone;
- correction changed dropping policy to drop oldest rather than newest.

Current law:
- delivery semantics must be typed (`MUST_APPLY`, `LATEST_WINS`, `BEST_EFFORT` or equivalent);
- queue overflow cannot silently erase causally necessary events.

## CD-11 — permanent archive after destructive ring-buffer forgetting

Commit `cae8751...` reports FRANK described memory distortion while reflections/mood were being pruned from small ring buffers.

Fix:
- permanent `reflections_archive` and `mood_archive` tables;
- dual-write to ring + archive;
- ring capacities raised dramatically.

Current fusion does not copy dual-write literally. It retains the principle:
- authoritative event/history must be append/replay durable;
- hot bounded views are derived/rebuildable;
- eviction from a working set must not equal historical erasure.

## CD-12 — Experiential Bridge closes action -> inner-state loop

Commit `3a47fef...`:
- tool calls, chats and sessions entered `activity_log`;
- daily activity summary influenced idle thought;
- idle/perception events could feed E-PQ;
- consciousness generated Genesis observations;
- raw-expression and rumination pathways were added.

Crucial bug from same audit:
- Core/executor/entity-dispatcher called `get_consciousness_daemon()` and instantiated full daemons in the wrong processes;
- fixed by avoiding accidental heavyweight singleton creation and writing explicit events/state instead.

Current law:
`semantic organ != singleton object instance`.
Physical instantiation must not create duplicate cognitive organs.

## CD-13 — thought quality and recursive contamination

Several historical failures show how recurrent cognition can poison itself:
- pattern/raw-expression paths skipped post-thought bookkeeping, making rumination detection blind (`3a47fef...`);
- third-person mode collapse and malformed thought filters (`ca016bf...`);
- room ambient text entered idle thoughts, was stored, reinjected and used to retrain ThoughtSeedVAE, causing a self-reinforcing room-description attractor (`1b86158...`);
- model-injected reality block created prompt-leak rejections (`92791d1...`).

Current rule:
- recurrent outputs have explicit epistemic role and trust tier;
- model-generated text cannot promote itself to sensor/world/training truth merely by being persisted;
- recurrent learning must include ancestry-aware anti-echo controls.

## CD-14 — hypothesis/experiment results become actual cognitive inputs

`809f0d6...`: experiment findings were extracted into Titan.
`3277107...`: resolved hypothesis results and experiment discoveries were explicitly injected into later thoughts.

This is a useful precursor of the current closed research/cognition loop, but historical LLM summarization of findings is not equivalent to canonical experimental evidence.

Current target stores:
- experiment result/evidence;
- interpretation/hypothesis;
- model-facing summary;
with separate roles and provenance.

## CD-15 — Rooms replace Entities

`b3df2f9...` and later cleanup replaced autonomous therapist/mirror/companion/entity sessions with solo Rooms.

Consequences propagated through:
- room reflection category;
- room/session persistence;
- spatial/body context;
- intent categories;
- AURA/Swarm zones;
- neural state dimensions and reward channels.

Lesson:
- a renamed conceptual domain can require broad schema migration across cognition, memory, reward and learned models;
- old dimensions/categories need explicit migration rather than implicit positional reuse.

## CD-16 — Genesis becomes a negative result rather than a mandatory loop

Commit `113bc080...` surgically disabled Genesis while preserving code because current small-model self-improvement overhead/quality was not justified. Hypothesis Engine and Experiment Lab remained active.

Current target therefore separates:
- autonomous research/hypothesis generation: potentially useful;
- self-authorized architecture/code modification: rejected;
- architecture improvement proposals: allowed only as proposals for external research/harness entity.

## CD-17 — SOMA remains a slow adaptation lineage

Commit `4634aeb...` enabled SOMA timer and bounded snapshots; historical SOMA/IAPT remains an adaptation method/tooling lineage.

Current program order prohibits model training now. DATA stage builds frozen training/heldout data, then WAIT.

## CD-18 — C4-C9 abstraction

C4:
- exact CognitiveFrame before workspace/model use;
- response/outcome linked to context/episode;
- personality/goals/consolidation are separate slow state contracts.

C5:
- exact state + memory epoch + activation + Assembly are sealed into an epoch capsule before competition;
- reader projection gets a distinct receipt.

C6:
- weight memory, persistent symbolic memory and transient cognitive state become explicit timescale classes;
- deterministic operator should run before model when soundly available.

C7:
- daemon-like logical organs are no longer required to be distinct processes;
- runtime scheduler coordinates multi-rate semantics.

C8:
- cognitive resource governor chooses retrieval/context/KV/backend budgets without weakening exactness/provenance/authority;
- salience adaptation is explicitly non-authoritative.

C9:
- admission/required-context and effect authority are separate from cognitive presence/selection;
- slow recurrence cannot authorize effects.

## CD-19 — current fused target

Replace the monolithic `ConsciousnessDaemon` class as architectural authority with a **multi-rate recurrent cognitive fabric** whose logical loops remain individually typed and lesionable.

Required loop classes:
- sensor/perceptual update;
- prediction/error update;
- attention/salience;
- workspace competition;
- active memory/Assembly;
- response/outcome/re-entry;
- mood/personality;
- goal/commitment;
- idle/reflection;
- consolidation/distillation;
- experiment/hypothesis integration;
- adaptive learner candidate/promotion.

Each loop declares:
- trigger/cadence;
- dependencies and basis epoch;
- budget and skip/coalesce semantics;
- whether model inference is permitted;
- exact state writes;
- derived state writes;
- authority class;
- crash/replay behavior;
- causal receipt requirements.

H3 may physically place most of these inside one process/module, but semantic identities and intervention surfaces remain.

## Mandatory regressions

- CD-REG-01 duplicate daemon instantiated in wrong process;
- CD-REG-02 first sample mistaken for a real delta;
- CD-REG-03 same resolved prediction counted repeatedly;
- CD-REG-04 self-generated CPU/GPU load triggers more model calls;
- CD-REG-05 ring-buffer eviction destroys durable history;
- CD-REG-06 room/prompt prose recursively contaminates thoughts and training;
- CD-REG-07 recursive/reflection path skips bookkeeping/quality/rumination update;
- CD-REG-08 queue overflow drops causally required event;
- CD-REG-09 user activity begins but idle GPU work continues because signal path is bypassed;
- CD-REG-10 model/backend unavailable; deterministic loops remain alive and fallbacks are explicit;
- CD-REG-11 renamed domain/category changes state-vector/mask dimensions;
- CD-REG-12 restart recovers pending delayed recursive reflection exactly once;
- CD-REG-13 exact evidence vs LLM interpretation stays role-separated;
- CD-REG-14 H1/H2/H3 multi-rate trace equivalence.

## Fusion decision

`REUSE_MULTI_RATE_RECURRENT_SEMANTICS; DECOMPOSE_MONOLITHIC_DAEMON_AUTHORITY; ADAPT_TO_TYPED_SCHEDULER_AND_RECEIPTS; RETEST_ALL_TIMINGS.`
