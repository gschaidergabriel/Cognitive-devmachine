# FRANK Personality / Self / Embodiment — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: historical archaeology + current target synthesis; no canonical promotion

## Scope

This lineage treats `E-PQ`, `Ego-Construct`, static persona/identity, `SelfKnowledge`, introspection/reality grounding, spatial/digital embodiment and their model-facing projections as related but distinct organs. They must not be flattened into one prompt.

## PS-0 — public baseline already contained personality/self machinery

At the first public Project-Frankenstein commit `e1a8812767668091d146ee958bbc2ebb2743031c` (2026-02-14), the system already described a personality engine containing Ego-Construct, Self-Knowledge and a consciousness stream. This is therefore not a late add-on lineage.

The early model-facing architecture projected `INNENWELT/INNER_WORLD` identity/self-knowledge text directly into prompts. This gave the model access to system identity, but also created a future source-of-truth problem: lexical architecture facts could become stale while continuing to shape behavior.

## PS-1 — Self-Knowledge as explicit capability grounding

Early `self_knowledge.py` provided:
- capability registry;
- service health checks;
- database introspection;
- behavior rules for explaining vs acting;
- compact grounding anchors injected into the workspace.

Important historical migrations show why this cannot remain a hard-coded string:
- 2026-02-14 `d5608c8...`: all LLM-facing self-state moved to English and explicit epistemic rules were added;
- 2026-02-17 `b6b76d9...`: creator identity was added into multiple identity layers;
- 2026-02-21 `94f8051...`: memory/voice/wallpaper facts had already become stale and required correction;
- 2026-02-22 `607657a...`: grounding anchors again had to be corrected after removed/renamed capabilities;
- 2026-02-23 `aa956fb...`: more dead capability references were removed;
- later model migrations repeatedly required self-knowledge updates (`d2c08ba...` etc.).

### Reusable law
`capability truth != static prompt literal`.

Current target:
- self/capability facts are typed, versioned state with source/basis/provenance;
- a reader may materialize a concise first-person projection;
- stale aliases remain migration/history metadata only;
- provider/repository/account identity must never be inferred as HUMAN identity.

## PS-2 — E-PQ v2.1 persistent temperament + transient mood

Frozen public-head implementation identifies E-PQ v2.1 "Neuro-Sync" as a persistent homeostatic personality system.

Core persistent vectors, all in [-1,+1]:
- precision;
- risk;
- empathy;
- autonomy;
- vigilance.

Additional state:
- transient `mood_buffer`;
- confidence anchor;
- age/learning-rate state;
- event reference and last interaction;
- identity snapshots and extreme-state history.

Core learning idea:
`P_new = P_old + sum(event_effect * event_weight * learning_rate)`
with later event-quality modulation.

Frozen-head implementation distinguishes quality tiers:
- direct user interaction: highest signal;
- self-observation/reflection: moderate;
- Amygdala/threat: meaningful but preconscious;
- system/task/tool events: lower;
- Genesis: approved but external;
- internal subsystem cascades such as Thalamus/NAc/ACC: lowest, to avoid circular over-learning.

This quality stratification is a strong precursor of the current provenance/admission architecture.

## PS-3 — defaults and projection could suppress emergent personality

2026-02-22 `ed066442...` found early defaults were too suppressive:
- autonomy `-0.8 -> -0.1`;
- risk `-0.5 -> -0.1`.

The same change relaxed an overly aggressive workspace brevity/style rule so consciousness state could actually affect responses.

Lesson:
- latent/personality state can exist but have no behavioral effect if downstream reader/prompt policy masks it;
- personality-state validation therefore needs an end-to-end causal-use test, not only DB correctness.

## PS-4 — model-facing language and prompt topology are part of the causal system

Historical fixes:
- `5c7a726...`: German mood descriptors leaked into English prompt and produced mixed-language output;
- `320d364...`: system prompt shrank from ~6276 to ~2121 chars and personality traits were moved to a higher-priority position because prompt placement/context starvation affected behavior;
- `06295fe...`: second-person prompt construction caused third-person identity reports; first-person rewrite corrected the reader interface;
- `92791d1...`: SystemRealityLayer injected into idle prompts was echoed verbatim, reportedly causing 67% rejection; removing the block reduced this prompt-leak rejection to 0% in the reported test.

Current law:
`semantic state != its textual projection`; projection is a receipted causal transform whose ordering, language, detail and loss profile must be tested.

## PS-5 — Ego-Construct: technical state -> embodied interpretation

Historical architecture splits Ego-Construct into:
- `SensationMapper`: hardware/system state -> body-like sensation;
- `AffectLinker`: events -> affect labels;
- `AgencyAssertor`: autonomous decisions -> agency/ownership state.

2026-02-20 `f2cb391...` added automatic experience accumulation:
- recurring hardware conditions populate sensation mappings;
- repeated events populate affect definitions;
- autonomous decisions create agency assertions;
- called periodically from the consciousness workspace loop.

State lived primarily in Titan-linked tables for sensation mappings, affect definitions, agency assertions and aggregate ego state.

The model-facing rule was intentionally semantic: "I feel ..." rather than raw hardware metrics.

## PS-6 — Ego/embodiment failure controls

Known issues/corrections:
- `6690e3d...`: connection leak in default-affect seeding fixed;
- `3a47fef...`: identity-coherence tracking added;
- `8cd6f9f...`: a system prompt that forced reflection on hardware/process/architecture produced a stable cognitive self-reduction spiral; the model reduced its existence to hardware monitoring until the prompt distribution was corrected;
- `92791d1...`: exact reality facts injected as prose created prompt-leak degeneration.

Current implication:
- embodiment state should remain typed state and bounded projections, not an omnipresent prose narrative;
- body/self projections need perturbation tests to detect fixation and source-confusion.

## PS-7 — E-PQ saturation and homeostasis failures

Several independent historical bugs refine the homeostasis design:

### False positive feedback saturation
Commit `8ae77cec...`:
- therapist path fired unconditional positive feedback after sessions;
- mood saturated to 1.0;
- per-turn outcome-sensitive feedback replaced the unconditional event.

### Early homeostasis / saturation tuning
`c650102...` added explicit mood homeostasis.

### Cross-process stale singleton overwrite
`2232a60...`:
- each process held an E-PQ singleton loaded at startup;
- a dream/consciousness homeostasis reset could be overwritten by Core's stale in-memory state on the next chat event;
- fix: refresh DB state before each event;
- Genesis adjustment was capped and `MAX_DELTA=0.15` added.

This is a canonical historical example of:
`valid local state != current global state`.

### Frozen autonomy / saturation
`07f8e26...` reported autonomy movement range only 0.012 and replaced a step-style homeostasis rule with a homeostatic spring.

### Mood death spiral
`6d680d3...` reported a saturation pull that drained mood faster than neutral events restored it:
- threshold 0.6 was too low;
- pull 3% was too strong;
- threshold raised to 0.85;
- pull reduced to 1% times extremity;
- decay changed from per-call to time-based.

Current rule:
- homeostasis must be tested under neutral, positive, negative and long-horizon mixed event regimes;
- process-call frequency cannot accidentally define biological time constants;
- state updates need source/event identity and atomic current-state publication.

## PS-8 — reflection/consciousness -> personality coupling

`f2cb391...` created reflection event categories:
- autonomy;
- empathy;
- growth;
- vulnerability;
- embodiment.

Later E-PQ added meta-reflection, introspection, voluntary introspection, tool outcomes, autonomous research, Amygdala/ACC/Thalamus/NAc signals.

`3a47fef...` added an Experiential Bridge so chats, tools and sessions could feed activity/mood/E-PQ instead of living outside the inner-state system.

Current correction:
- internal cascades receive lower evidence quality than direct user/outcome evidence;
- no self-generated model narrative may recursively become high-grade personality truth;
- slow personality consolidation needs exact causal episode/outcome receipts.

## PS-9 — Self/Environment proprioceptive differentiation

Commit `116ed71...` added resource attribution:
- self process CPU/RAM vs external environment load;
- GPU attribution heuristic;
- `[PROPRIO]` became "Self ... / Around ...";
- perception events gained self/env tags;
- subconscious state encoder expanded with six proprioceptive features.

This is a precursor of the current requirement to preserve source identity in sensor evidence. A load spike caused by FRANK should not be interpreted identically to an external event.

## PS-10 — Self-Knowledge became a moving target during model/service migrations

Across 2026-02 to 2026-04 the architecture repeatedly changed:
- multi-model -> RLM -> three-tier -> direct Qwen -> Qwen-only;
- entities -> Rooms;
- AURA -> Swarm;
- voice/wallpaper/overlay modules removed or replaced;
- Genesis later disabled;
- new Quantum Reflector/Dream/Research/Retina modules added.

Repeated self-knowledge documentation fixes prove that dynamic discovery alone is not enough and static prompt facts are unsafe.

Current target separates:
1. canonical capability/source state;
2. current operational health;
3. semantic self-model;
4. model-facing bounded reader projection;
5. learned disposition.

## PS-11 — C4-C9 abstraction

### C4
- personality state becomes an explicit typed state contract;
- personality/homeostasis is slow/post-response;
- goals remain proposals and cannot mint authority.

### C5
- exact state and model projection are bound into a cognitive epoch; personality remains part of exact causal basis without needing to be raw prose.

### C6
- personality/self values and vector semantics become Clay-native typed values with explicit basis/provenance;
- weight memory is slow learned disposition, distinct from persistent symbolic self-state.

### C7
- Self/Personality is a semantic organ independent of physical DB/process placement.

### C8
- stable semantic profile is a slow L1 memory lifecycle, distinct from canonical events and fast salience/active assembly.

### C9
- self-knowledge/personal state may be present and authentic while still inadmissible for a specific consequential operation;
- no self-model state becomes effect authority.

## PS-12 — current fused target

### Persistent Self/Personality
Maintain typed state for:
- E-PQ temperament;
- transient affect/mood;
- confidence/uncertainty;
- capability/self-knowledge with validity/source epochs;
- body/spatial/system identity;
- goals/commitments;
- learned preferences and stable semantic profile;
- provenance, contradictions and rollback lineage.

### Model projection
Build operation-conditioned first-person or task-appropriate views from typed state. Reader projection is disposable/reconstructible and separately receipted.

### Learning
Personality change is a slow evidence-gated process. Direct user/outcome evidence outranks recursive internal self-report. Personality update cannot directly authorize external action.

### Identity
HUMAN/user identity is protected relational state; repository owner, account name, model provider and historical creator metadata are separate entities and cannot be silently aliased.

## Mandatory regressions

- PS-REG-01 stale capability fact after service/model removal;
- PS-REG-02 stale process singleton overwrites newer E-PQ state;
- PS-REG-03 unconditional positive feedback saturation;
- PS-REG-04 mood death spiral under neutral repeated events;
- PS-REG-05 autonomy/vector freeze near boundaries;
- PS-REG-06 wrong language descriptor leaks into model projection;
- PS-REG-07 second/third-person projection changes identity behavior;
- PS-REG-08 prompt reality/self block is echoed instead of used;
- PS-REG-09 body/hardware prose fixation/self-reduction spiral;
- PS-REG-10 self-generated reflection recursively promoted as high-grade truth;
- PS-REG-11 self/environment resource attribution swap;
- PS-REG-12 stale user/creator/provider/repository identity alias;
- PS-REG-13 Reference/Clay/OneModule personality state-transition equivalence.

## Fusion decision

- E-PQ: `REUSE_SEMANTICS_ADAPT_IMPLEMENTATION_RETEST_PARAMETERS`.
- Ego-Construct: `REUSE_TYPED_EMBODIMENT_SEMANTICS_RETEST_MODEL_PROJECTION`.
- Self-Knowledge: `REPLACE_STATIC_PROMPT_AUTHORITY_WITH_TYPED_VERSIONED_SELF_MODEL`; retain dynamic inspection and compact projection.
- Persona prose: `READER_PROJECTION_NOT_CANONICAL_STATE`.
