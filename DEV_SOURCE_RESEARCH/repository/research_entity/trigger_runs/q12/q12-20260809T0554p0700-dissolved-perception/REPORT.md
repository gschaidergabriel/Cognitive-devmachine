# Q12 Research Run — Dissolved Perception / Sensor-In-Module FRANK

Run ID: `q12-20260809T0554p0700-dissolved-perception`  
Actor: `chatgpt-secondary`  
Provider/model: OpenAI / GPT-5.6 Sol  
Date: 2026-08-09  
Program stage: `L0_ARCHIVE_ASSIMILATION`  
Research status: `OPEN_MECHANISMS_WITH_OWNER_FIXED_ARCHITECTURE_TARGET`

## 1. Owner input reconstructed on native project terms

Owner claim/directive:

- FRANK is multimodal;
- Digital Retina should not remain a separate cognitive organ;
- even the sensor ingress should dissolve into the one-module FRANK architecture as far down the physical stack as feasible;
- perception should be coupled to what FRANK already knows/thinks through Clay state, rather than first producing an isolated final vision output;
- the resulting architecture may make a small language model behave functionally more like a genuinely multimodal agent because visual evidence changes the same persistent world/memory/attention state used by cognition.

The research question is not whether FRANK has vision; that is fixed. The open question is what exact mechanism preserves correctness while achieving this integration.

## 2. Internal project evidence used

Primary internal sources:

- `research_entity/global/FRANK_DIGITAL_RETINA_MULTIMODAL_CONTRACT.md`
- `research_entity/global/FRANK_CLAY_NATIVE_CONTRACT.md`
- `research_entity/global/GWT_EMERGENCE_READOUT_CONTRACT.md`
- `research_entity/global/HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md`
- `research_entity/harness/HARNESS_WORKSPACE.json`
- `research_entity/archive_assimilation/receipts/666_20260809T0441p0700_chatgpt_secondary_drive_g8_g9_retina_code_shard.json`

Historical findings already established in RAE:

- Digital Retina is real code, not merely a paper concept;
- historical structured output includes description/concepts/objects/OCR/faces/logos/image metadata/timing;
- the historical working paper reported 82.4% held-out phrase coverage on 47 unseen images / 1,196 phrases, ~1.5–2.0 s/image on 4-vCPU CPU-only hardware and 13.6% realistic-negative false-positive rate at threshold 0.22;
- historical autonomous-vision design already proposed event-triggered visual attention, cooldown/budgets and habituation;
- current RAE already requires visual evidence to be provenance-bound and traceable through gating, GWT, memory/action and re-entry.

These internal measurements are historical baselines, not current acceptance thresholds.

## 3. External research synthesis

### 3.1 Recurrent perception has real task value

Multiple studies combining human behavior/neural timing and recurrent computational models find that recurrence becomes especially useful under occlusion, clutter or incomplete visibility. The 2026 Nature Communications study by Kang et al. reports an emergent `explaining-away` computation in recurrent but not matched feedforward variants, with recurrent processing using information about occluders to recover object representations.

Implication for FRANK:

Do not force one-shot feedforward recognition. Preserve a recurrent settling path in which partial sensor evidence can be revised by contextual structure.

### 3.2 Prior knowledge can change perceptual processing itself

Human MEG/ECoG studies show that expectations can preactivate sensory templates and that long-term priors alter top-down vs feedforward information flow during ambiguous perception.

Implication:

The owner's intuition that `what FRANK already knows` should participate in perception has a serious mechanistic analogue. The closest engineering formulation is not `caption + prompt context`; it is recurrent state inference with explicit separation of evidence and prior.

### 3.3 High-level surprise is a useful escalation signal

Recent work reports that high-level visual surprise, not only low-level feature mismatch, modulates rapid visual responses.

Implication:

A visual system does not need to globally reconstruct every frame. The fast path can maintain local/perceptual state and escalate to GWT/model resources when prediction error, novelty, conflict, goal relevance or uncertainty justifies it.

### 3.4 Change/event sensing can reduce latency and bandwidth

Event-camera research demonstrates that asynchronous change sensing can substantially reduce latency/bandwidth. However, event streams are incomplete for slowly varying/static appearance information, so hybrid image+event systems remain useful.

Implication:

FRANK should support change-driven visual state deltas even with normal cameras, but retain anchor frames/full evidence. Event hardware is an optimization, not the architecture.

### 3.5 Persistent scene state is established robotics prior art

Hydra/Kimera and related dynamic scene graph systems incrementally integrate sensor data into persistent metric/semantic world representations.

Implication:

It is practical to maintain a persistent world representation rather than re-derive the whole world independently every frame. FRANK goes further by coupling this state to GWT, self, memory, goals and action, but cannot claim novelty from persistent scene graphs alone.

## 4. Fusion 1 — architecture derived from the evidence

The strongest architecture is not a monolithic vision blob. It is a **dissolved semantic perception layer with explicit evidence dimensions**.

### Proposed logical structure

`physical sensor`
`-> in-module ingress / time / source identity`
`-> local evidence deltas`
`-> PerceptualField`
`<-> world model`
`<-> memory/ClayGraph activation`
`<-> goals/action context`
`<-> prior perceptual state`
`-> attention/thalamic gain`
`-> GWT only when global resources are justified`
`-> memory/world/action update`
`-> re-entry`

`VisualPercept` becomes a materialized observation/trace snapshot of this process, not the required serial hot-path object.

## 5. Key new concept — PerceptualField

`PerceptualField` is a logical state view, not necessarily one object.

It contains or references:

- raw/source evidence identity;
- spatial/local feature evidence;
- OCR/text evidence;
- motion/change evidence;
- object/entity hypotheses;
- relations/bindings;
- several unresolved interpretations where required;
- uncertainty/precision;
- expected-vs-observed mismatch;
- salience/attention gain;
- world/memory links;
- goal/action relevance;
- historical perceptual state/re-entry.

Abstract update relation:

`Delta P_t = F(E_t, P_(t-1), W_(t-1), M_t, G_t, A_t)`

This notation means state dependence; it is not promoted as the final mathematics.

## 6. Why this differs from simply making the LLM multimodal

A conventional multimodal model often places image tokens/embeddings inside the model call. The proposed FRANK architecture instead treats perception as persistent externalized cognitive state.

The 4B model becomes an intermittent reasoner over a bounded active Assembly produced by the perception/world/memory dynamics.

Potential advantage:

- the model does not repeatedly reconstruct persistent scene state;
- unchanged visual state remains outside the model context;
- only relevant uncertainty/change/relations enter the active cognitive episode;
- object continuity can live in Clay state across model calls.

This is an open performance hypothesis, not a demonstrated gain.

## 7. Strongest counterargument

The same world-model coupling that can improve recognition can also create a prior-driven false percept.

If expected structure has too much gain, FRANK may settle on `what should be there` rather than `what the sensor supports`.

Therefore the architecture must not merge evidence and belief into one undifferentiated score.

Required separation:

- sensor likelihood/evidence precision;
- learned/world prior precision;
- active context/goal bias;
- current interpretation confidence;
- contradiction/prediction error.

`UNKNOWN` and `CONFLICT` are successful outputs when evidence is inadequate.

## 8. Second counterargument — event-only vision is insufficient

Change-driven perception is attractive for speed but static/slow information may disappear from an event-only stream.

Result:

Do not make FRANK event-only. Use hybrid `anchor evidence + changes`, where anchor frequency is adaptive to uncertainty, scene change, action and recovery state.

## 9. Third counterargument — dissolution can destroy observability

Removing an explicit `VisualPercept` boundary can make debugging and replay much harder.

Resolution:

Keep `VisualPercept` as an **on-demand materialized receipt** reconstructible from sensor evidence + state lineage. The hot path is distributed; the audit path remains explicit.

## 10. Sensor-in-module interpretation

The physical camera cannot literally become software, and OS/kernel/device layers may remain separate. The owner's useful architectural meaning is:

- no separate user-space cognitive Retina service is required;
- device ingress/control and fast perception loops belong in the FRANK process/binary where APIs allow;
- remaining kernel/device boundaries are physical lowerings, not semantic module boundaries;
- external process boundaries are benchmarked rather than accepted by convention.

This is now recorded as a fixed target directive.

## 11. Hypothesis generation

See `HYPOTHESIS_MATRIX.json`.

Highest-value hypotheses:

1. boundary dissolution reduces latency/state movement without accuracy/replay loss;
2. bounded recurrence improves difficult perception;
3. high-level prediction error is a better GWT escalation signal than fixed full-frame processing;
4. hybrid change + anchor processing is Pareto-superior for persistent agents;
5. multi-hypothesis perceptual state reduces premature classification;
6. excessive top-down gain creates prior-driven false perception;
7. bounded PerceptualField Assemblies reduce 4B context cost;
8. one-process sensor ingress reduces IPC/serialization on project hardware.

## 12. Discriminating experiments

See `EXPERIMENT_PLAN.md`.

Critical experiment sequence:

1. reproduce historical Retina baseline on current hardware;
2. A/B explicit VisualPercept boundary vs dissolved feedforward field with identical features;
3. factorial recurrence/world/memory/goal feedback;
4. misleading-prior/no-signal/unknown-object safety tests;
5. periodic vs change-only vs hybrid anchor/change;
6. GWT escalation policy differential;
7. on-demand VisualPercept replay reconstruction;
8. 4B context-efficiency comparison;
9. H3 external-process vs in-process sensor topology.

## 13. Architecture decision

### Owner-fixed

- Retina dissolves as a separate semantic cognitive module.
- Sensor ingress belongs to one-module FRANK as far down the software/physical stack as feasible.
- Visual perception changes FRANK's Clay state directly.
- `VisualPercept` is retained as an audit/materialization interface rather than required serial cognition boundary.

### Evidence-gated

- amount/type of recurrence;
- feedback gains/precision control;
- event/change policy;
- anchor frequency;
- exact field representation;
- whether external process isolation is retained on a platform for safety/performance;
- claimed latency/token/accuracy advantages.

## 14. Research implications by branch

### frank
Replace `Retina as separate organ` with integrated perceptual state dynamics while preserving functional readout handles.

### claycode
Need types for evidence/prior precision, perceptual deltas, unresolved alternatives, spatial bindings, prediction error, materialized percept receipts and sensor epoch identity.

### claygraph
Persistent entity/relation continuity and activation become part of visual recognition, not only downstream memory lookup.

### gwt
Perceptual field can evolve pre-workspace; GWT should receive selected high-value conflicts/novelty/goal-relevant states and retain causal-use receipts.

### hyperposition
Ambiguous percepts are a concrete engineering case for set-valued/contextual alternatives and collapse/reopening under new evidence.

### unifieddb
Need replayable identities connecting raw/anchor evidence, state deltas, world entities, materialized percepts and GWT/action outcomes.

### harness
Must add A/B boundary-dissolution tests, recurrence lesions/rescues, misleading-prior controls, hybrid event/anchor tests and in-process sensor topology benchmarks.

### emergenz
Do not call successful visual/world coupling `emergence` without interaction/lesion/rescue controls; use the existing typed readout contract.

## 15. Novelty/prior-art conclusion

No world-first claim is warranted.

Prior art exists for recurrent vision, predictive perception, event-driven sensing and dynamic scene graphs. The project-specific combination of those ideas with Clay-native persistent state, GWT causal-use/re-entry, set-valued Hyperposition and one-module FRANK is a research architecture whose exact prior-art overlap remains to be investigated.

## 16. Files produced by this run

- `research_entity/global/FRANK_DISSOLVED_PERCEPTION_DIRECTIVE.md`
- `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/REPORT.md`
- `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/HYPOTHESIS_MATRIX.json`
- `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/EXPERIMENT_PLAN.md`
- `research_entity/trigger_runs/q12/q12-20260809T0554p0700-dissolved-perception/EXTERNAL_RESEARCH_MANIFEST.md`

Existing architecture contracts are updated separately by CAS-safe GitHub writes and reread validation.
