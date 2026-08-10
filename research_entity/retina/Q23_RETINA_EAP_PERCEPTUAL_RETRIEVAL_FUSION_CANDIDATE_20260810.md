# Q23 Retina–EAP Perceptual Retrieval Fusion Candidate — 2026-08-10

**Status:** USER-PROPOSED HYPOTHESIS / CANDIDATE / NOT PROMOTED  
**Field:** q23 maximum-depth multimodal perception research  
**Scope:** Retina/Qwen native vision, MVC, UnifiedDB Emergent Assembly Preprocessor (EAP), ClayGraph, ActiveAssembly, GWT, Frank 4B.

## 1. Starting proposal

Explore whether UnifiedDB's emergent ActiveAssembly preprocessor can act as a memory/retrieval reflex attached to visual perception:

`incoming visual evidence -> Retina/Qwen processing -> evidence-bound memory anchor(s) -> EAP possibility compilation -> compact relevant ActiveAssembly -> Frank/Qwen reasoning`

This is explicitly a hypothesis, not an owner-fixed architecture requirement.

The project evidence does **not** justify calling EAP literally latency-free. Current synthetic/local measurements are microsecond/sub-millisecond class for important subpaths, which is potentially negligible relative to multimodal 4B encode/decode but still non-zero and must be measured end-to-end on Frank hardware.

## 2. Existing UnifiedDB/EAP evidence

Current EAP is already implemented as a disposable, epoch/hash-bound multi-hop access/assembly preprocessor over canonical UnifiedDB state. It is not a second database. It compiles bounded `ActiveAssembly` context from seed refs/query text, derived sparse dependency topology, epistemic/status gates and a frontier budget. Returned items remain `authority=CONTEXT_ONLY`; graph activation cannot mint truth.

Current research receipts report, on synthetic workloads:

- complete EAP assembly path around ~92.57 us p50 versus ~104.19 us for a matched staged recursive SQLite model-input path; naked recursive SQL refs-only remained faster (~43.06 us), so EAP is not universally the fastest query primitive;
- incremental topology update + next-query reconstruction around ~29.6 us versus ~8661 us full rebuild in one reconstruction benchmark (~292x), with exact selection equality;
- compact EAP cache retained retrieval semantics while reducing transient hot-cache memory by discarding dependency row bodies after topology compilation;
- a separate natural-language hybrid retrieval candidate measured around ~1.0 ms mean on its synthetic workload and showed that naïve always-expand graph retrieval destroys precision (~1.3% Top-1), while intent-bounded graph expansion can recover strong accuracy.

These measurements are evidence for a potentially very cheap precompiled possibility layer, not target-PC or production proof.

## 3. Candidate mechanism: Perceptual Assembly Reflex (PAR-1)

### 3.1 Familiar visual fast path

`screen/camera frame`
` -> deterministic change/provenance gate`
` -> Qwen native vision encode selected region`
` -> MVC raw/projected Qwen familiarity readout`
` -> if KNOWN_HIGH_CONFIDENCE: resolve bound UnifiedDB entity/state refs`
` -> EAP compile bounded ActiveAssembly around those visual seed refs`
` -> combine current visual representation + compact ActiveAssembly`
` -> either local state update / decoder bypass OR one Qwen semantic decode when task/uncertainty requires`

This creates a possible perceptual-memory reflex:

**seeing a known thing activates its currently relevant relational memory before full language decoding.**

### 3.2 Unknown/ambiguous visual path

`Qwen vision encode`
` -> MVC UNKNOWN / AMBIGUOUS / CONFLICT`
` -> Qwen semantic visual decode / active sensing`
` -> typed PerceptualField candidate(s)`
` -> evidence-bound seed resolver maps only supported entities/relations into current UnifiedDB refs`
` -> EAP compile ActiveAssembly`
` -> further reasoning/action if needed`

Unknown perception must not be forced into existing memory anchors merely to gain retrieval speed.

### 3.3 Action-verification path

`pre-action perceptual seeds + ActiveAssembly`
` -> action`
` -> post-action capture + deterministic delta`
` -> current Qwen/MVC perceptual evidence`
` -> EAP retrieves expected/related outcome state only as context`
` -> compare expected memory against observed evidence`
` -> close or escalate outcome`

Memory prediction is never substituted for observation.

## 4. Key architecture insight

The potentially useful fusion is not:

`Retina -> database query -> Qwen`.

It is closer to:

`native visual representation`
` -> evidence-bound perceptual anchor`
` -> emergent possibility compilation`
` -> task-conditioned ActiveAssembly`
` -> native multimodal reasoning`

This lets UnifiedDB/ClayGraph function as a **precompiled associative possibility field** around current perception rather than as a conventional post-hoc database lookup.

The strongest version is available only if the visual fast path can produce stable, trustworthy entity/state refs before full semantic decode. That links this candidate directly to q23's Qwen-feature/MVC research.

## 5. Bidirectional extension: memory-guided active perception

A second, more dangerous hypothesis is a controlled feedback loop:

`visual seed -> EAP ActiveAssembly -> expected relevant relations/states -> choose next ROI/resolution/question -> new visual evidence`.

Potential benefit:

- memory can tell Retina/Qwen *where to look next*;
- only task-relevant crops/high-resolution reads may be purchased;
- current knowledge can disambiguate which visual relation is worth verifying.

Critical rule:

**EAP output may guide sensing but may never overwrite or pre-validate sensor truth.**

Every memory-guided expected state must remain tagged as prior/context until independently observed.

## 6. Main hypotheses

### H-PAR-01 — visual-seed associative retrieval

High-confidence MVC/Qwen visual identities can seed EAP directly and retrieve useful related context before full 4B semantic decoding.

Counterhypothesis: visual identity errors cause associative cascades that amplify false familiarity and corrupt downstream reasoning.

### H-PAR-02 — near-negligible retrieval overhead

Incrementally maintained EAP ActiveAssembly compilation adds negligible end-to-end latency relative to Qwen visual encode/decode while materially improving context relevance.

Counterhypothesis: seed resolution, state synchronization, serialization and cache maintenance dominate the nominal microsecond EAP traversal and erase the advantage in the real Frank path.

### H-PAR-03 — retrieval improves decoder efficiency

Visual-seeded ActiveAssembly reduces prompt/context search and/or semantic decode work enough to reduce total sensor-to-decision cost while preserving task correctness.

Counterhypothesis: adding retrieved context increases prompt tokens and attention cost more than it saves.

### H-PAR-04 — relational memory improves perception

Bounded EAP relational context improves visual disambiguation, action selection and outcome verification on recurring user-specific environments.

Counterhypothesis: memory priming produces confirmation bias and hallucinated continuity, especially after environment changes.

### H-PAR-05 — memory-guided active sensing

EAP-derived uncertainty/relation gaps can select higher-value crops/resolution/rechecks and reduce visual tokens per verified action.

Counterhypothesis: a direct uncertainty/ROI policy from current visual evidence performs equally well with less coupling and lower failure risk.

### H-PAR-06 — one shared associative substrate

The same UnifiedDB/EAP possibility compiler can serve visual perception, textual queries and action/recovery context without modality-specific memory databases.

Counterhypothesis: visual-temporal retrieval has sufficiently different similarity/recency/topology requirements that a specialized transient visual index is necessary for performance and correctness.

## 7. Mandatory anti-confirmation controls

Because perceptual memory can create a dangerous self-confirming loop, PAR-1 is invalid without:

- shuffled visual-entity seed control;
- wrong-but-high-confidence MVC seed injection;
- stale room/UI layout fixtures;
- changed object identity with similar appearance;
- missing/contradictory ClayGraph edges;
- stale EAP epoch/hash rejection;
- no-EAP lesion;
- direct exact/FTS route baseline;
- EAP query-blind fanout negative control;
- memory prior vs observed sensor evidence separation;
- post-action mismatch fixtures;
- unknown visual entities that have tempting nearest known neighbors.

A correct architecture should make wrong memory **easier to falsify**, not easier to perceive as true.

## 8. Candidate data contract

A visual fast-path seed should never be a naked semantic name. Suggested receipt:

`PerceptualMemorySeed = {`
` frame_id, source_epoch, roi_hash, visual_feature_version,`
` candidate_ref, candidate_state_ref?, confidence, open_set_score,`
` evidence_tier, prototype_support, contradiction_flags,`
` observed_at, model_hash, mmproj_hash, pooling_projection_hash`
`}`

Only seeds satisfying the current evidence/open-set gate may enter EAP as direct seed refs. Ambiguous seeds become alternatives/hypotheses or trigger deeper perception.

The compiled ActiveAssembly preserves:

- source UnifiedDB epoch/hash;
- EAP/index version;
- selection hash;
- hop/relation/dependency provenance;
- blocked/suppressed negative-space evidence;
- `authority=ASSEMBLY_CONTEXT_ONLY`.

## 9. Most valuable matched experiment

Freeze identical visual/action episodes and compare:

A. `QWEN_ONLY`: current visual encode/decode, no UnifiedDB associative retrieval.

B. `QWEN + DIRECT_MEMORY`: direct exact/FTS retrieval from current percept label/state.

C. `PAR_RAW`: Qwen/MVC visual seed -> EAP -> ActiveAssembly -> Qwen.

D. `PAR_PROJECTED`: tiny projected Qwen MVC seed -> EAP -> Qwen.

E. `PAR_ACTIVE`: D + EAP-guided active sensing.

F. `PAR_WRONG_SEED`: deliberately wrong visual seed to test amplification/fail-closed behavior.

Measure:

- sensor->ActiveAssembly latency p50/p95/p99;
- sensor->decision/action latency;
- EAP compilation only and complete seed-resolution+EAP overhead;
- Qwen visual encode/decode time;
- prompt/visual/text tokens per successful action;
- task/action success;
- visual identity accuracy and false familiarity;
- relevant-memory precision/recall;
- stale/wrong-memory override rate;
- memory-induced hallucination/confirmation errors;
- GWT false ignition;
- CPU/RAM/VRAM/cache update cost;
- crash/restart/replay equivalence.

## 10. Promotion rule

PAR-1 is promoted only if it gives matched end-to-end benefit over both `QWEN_ONLY` and a simpler direct-memory baseline.

Specifically it must show:

1. useful context/task gain or compute reduction;
2. end-to-end latency benefit, not just fast internal EAP microbenchmarks;
3. no increase in false familiarity or stale-memory acceptance;
4. wrong-seed and shuffled-topology controls collapse the claimed associative benefit;
5. current visual evidence remains epistemically dominant over retrieved memory;
6. exact/cheap routes remain available and EAP is conditional where simpler retrieval suffices;
7. recovery/version/provenance guards survive restart and model/mmproj changes.

If these fail, retain EAP as a general ActiveAssembly preprocessor without coupling it tightly to Retina.

## 11. Research disposition

This proposal is scientifically valuable because it connects two already-existing project directions without assuming the connection is correct:

- q23: native Qwen multimodality + Retina temporal/control fabric + MVC;
- UnifiedDB/EAP: precompiled, bounded, evidence-aware model-input possibility assembly.

The candidate should enter q23 as a high-information cross-branch hypothesis and be attacked adversarially before architectural promotion.
