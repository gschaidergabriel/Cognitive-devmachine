# Frankenstein research chronicle

This chronicle reconstructs the engineering lineage without turning archive prose into truth. “First verified” means first verified in the accessible evidence named here, not necessarily the day an idea was originally invented.

## 0. Evidence frame

Current curation re-entry: `clay-global-research-entity/main@854f6bc87780f4a5242489a6c807d186b16a8c3d`.

Historical Project-Frankenstein archive scope is bounded by the current Level-0 scope law:

- inclusive base: `e1a8812767668091d146ee958bbc2ebb2743031c`
- frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- compare distance after base: 544 commits
- exact scope obligations: 545 commits
- ordered 545-SHA inventory: still not established by the cited scope artifact
- exact complete frozen-head tree denominator: still open in the cited manifest

The current archive manifest is `PARTIAL_NOT_FROZEN` and indexes 25 deep-read units. Therefore this chronicle is a high-value reconstruction, not a claim of exhaustive historical closure.

---

## 1. Historical Frank: cognition as cooperating services

**HISTORICAL_SOURCE.** The current archive manifest verifies deep reads of a modular Frank architecture at frozen historical Project-Frankenstein head `abba90…`.

Representative modules:

- `services/consciousness_daemon.py` — persistent/multi-timescale cognition loop and workspace precursor;
- `services/global_workspace.py` — broadcast/salience workspace;
- `personality/e_pq.py` — persistent E-PQ/personality/homeostatic state and event learning;
- `services/thalamus.py` — sensory gating, attention, habituation and prediction error;
- `tools/lcme/lcme_core.py` — claims, graph/vector retrieval, memory and forgetting;
- `services/nucleus_accumbens.py` — reward prediction/motivation/habituation;
- `services/subconscious.py` — actor-critic/PPO-style idle policy and hallucination tracking;
- `services/spatial_state.py` — persistent world/body/spatial projection;
- `services/dream_daemon.py` — replay/synthesis/consolidation with interrupt/resume;
- `services/project_engine.py` — projects, goals, strategies, tasks and tool learning;
- `services/hypothesis_engine/*` + `services/experiment_lab.py` — hypothesis lifecycle, experiments, relevance/budget gates and revision;
- `services/soma/micro_trainer.py` and `papers/IAPT_METHOD.md` — historical adaptation/training lineage;
- visual lineage: adaptive routing → FrankEye / Retina artifacts → native multimodal path, with source drift explicitly preserved in archive notes.

### Architectural value

The historical design treated cognition as a federation of specialized loops around persistent state. That provided rich behavior, but it also created many ownership, synchronization and integration boundaries.

### Failure pressure

**INFERENCE, grounded in the later architecture and preserved project failure corpus:** when state, memory, prediction, reward, perception, goals and action live behind many separate services/databases, every boundary creates opportunities for stale state, duplicate authority, timing drift, partial recovery and ambiguous provenance.

**Engineering move forced by the failure:** converge durable authority, make projections rebuildable, and bind causal identity across the path instead of allowing each cognitive subsystem to behave like an independent truth store.

---

## 2. GRF, state and measured coupling

Historical Frank research repeatedly tried to turn internal state into something measurable rather than relying only on persona text. GRF/related state mechanisms belong in this lineage as engineering attempts to couple internal variables, memory and behavior.

The important current interpretation is not a metaphysical claim. It is a measurement law:

`state → trigger/input → model/process behavior → action/outcome → re-observed state`

Short, source-bound windows are stronger evidence than a vague statement that “the agent ran for a long time.” A long stable run can coexist with a broken causal mechanism; a short controlled lesion/rescue can discriminate a mechanism directly.

**OPEN_HYPOTHESIS:** state-space controls become useful when their variables align with real interfaces and when nuisance/prompt shortcuts are excluded.

**Falsifier:** matched interventions fail to cause selective downstream behavior under label-free, counterbalanced, family-disjoint controls.

---

## 3. Workspace / GWT lineage without a consciousness claim

Historical Frank contained a global-workspace-style broadcast module. Current EntityOS/HCU preserves a workspace/J-Space research direction as a computational coordination hypothesis.

External Global Workspace literature is useful here as an architecture analogy: distributed specialists can compete/cooperate around globally available information. It does **not** establish that Project Frankenstein, EntityOS, HCU or any model is conscious.

Current rule:

- workspace recurrence = observation/candidate evidence;
- model self-report = model output;
- majority/consensus = not truth;
- internal-vector causality requires model/runtime-specific intervention evidence;
- canonical durable truth remains deterministic and external to model-generated cognition.

---

## 4. Memory fragmentation → UnifiedDB

The project term **UnifiedDB** captures the convergence toward one canonical durable state/evidence substrate.

This does not mean one table or one monolithic file API. A coherent authority may have:

- typed state tables;
- event and admission identities;
- memory records and indexes;
- effect journal;
- policy/capability tables;
- provenance and recovery metadata;
- rebuildable graph/workspace projections;
- high-rate transient state outside the DB in RAM.

### Emergent Retrieval

`Emergent Retrieval` means relevance produced by the **intersection of stored evidence dimensions at query time**: semantic similarity can combine with recency, causal ancestry, current state, goals, perception, effect history, confidence and provenance.

It explicitly does not mean that missing information is created by the retrieval system.

### Systems analogy only

NVIDIA Unified Memory is a useful systems analogy for reducing explicit ownership/copy boundaries between compute domains. Hardware memory coherence is **not** database semantics and does not validate UnifiedDB by itself.

---

## 5. From named cognitive services to EntityOS + HCU

Current authority names the product **EntityOS** and the integrated cognition/compute architecture **HCU**.

The current conceptual machine decomposes into:

- canonical durable state/evidence substrate;
- Typed Entry admission for new observations;
- deterministic control plane;
- HCU candidate compute / vector / inference / workspace plane;
- typed causal interconnect;
- Hyperposition for unresolved alternatives;
- deterministic candidate-to-effect translation;
- EffectGate + EffectJournal as the real-effect authority.

The direction is deliberately less anthropomorphic than the historical service names. Function is retained where useful; biological naming is not treated as scientific evidence.

### Hyperposition

Hyperposition is a control rule for **keeping alternatives unresolved** until an evidence-bearing discriminator closes them. It is the opposite of turning recurrence, confidence or majority vote into truth.

A minimal form is:

`{candidate_i, evidence_i, provenance_i, unresolved_reason_i}`

Resolution must cite the discriminator that changed the epistemic state.

---

## 6. GRID / HCU compute: logical modules are not physical models

GRID10 is an important reference/benchmark configuration but logical cell count must never be reported as equal resident-model count or equal physical decode concurrency.

### 2026-08-27 thread-count discriminator

**PROJECT_MEASUREMENT, topology-specific diagnostic.** Current supervisor evidence records a matched four-process / four-vCPU A/B:

| Torch threads per process | Result |
|---:|---|
| 1 | 8.3197 s/call average, 12 samples |
| 2 | 23.1806 s/call average, 12 samples |
| 4 | 0 completed samples within experiment timeouts |

This falsified the recommendation that two threads/process would improve latency on that exact measured topology and supports retaining the one-thread default there.

It does **not** promote Physical-GRID10, BASE, HCU or EntityOS. If process/core topology changes, the A/B must be repeated.

The result is consistent with PyTorch’s documented CPU-oversubscription guidance, which recommends bounding per-process threads by available vCPUs divided by process count. External documentation is method context, not project runtime evidence.

---

## 7. Global J-Space and vector binding: transport is not semantics

The J-Space research line asks whether internal/vector state can become a useful causal interface between small models and the external workspace.

A recurring project lesson is that three different achievements must be separated:

1. **READ** — an internal feature is decodable/readable;
2. **BIND/ROUTE** — a semantic state can be dynamically bound to the correct episode-local variable/code/situation;
3. **WRITE/CONTROL** — intervention on the internal carrier causes selective downstream behavior.

Strong READ or even successful vector transport does not imply successful dynamic binding or semantic control.

### Shortcut pressure

Current training-research lanes explicitly attack:

- fixed label/code associations;
- prompt/order shortcuts;
- demo/input-label prior shortcuts;
- lexical leakage;
- split/family leakage;
- nuisance-variable control failures;
- checkpoint/model-family ancestry leakage;
- one-phase provenance that confuses content identity with execution occurrence.

External primary research on demonstration shortcuts and systematic variable binding motivates these controls but cannot mint Qwen/Clay evidence.

---

## 8. ClayCode and protocolization

ClayCode represents the attempt to make cognition/control variables explicit enough to be typed, serialized, replayed and eventually trainable rather than living only in natural-language prompts.

The important current direction is protocol alignment:

`Typed Entry identity → cognitive/work packet → state placement → workspace/HCU candidate → result packet → optional strong-model/tool handoff → reconciliation → effect proposal → deterministic effect gate → journal receipt`

Training should learn the **cognitive/process protocol**, not a second truth database or a hidden effect path.

---

## 9. Training lineage: LoRA/IAPT/SOMA → causal protocol training

Historical Project Frankenstein contains IAPT/SOMA/micro-training artifacts. Current training research is stricter about promotion:

- model/checkpoint/tokenizer/runtime identity must be exact;
- train/validation/holdout must be family/provenance safe;
- hard negatives must reject authority and evidence mistakes;
- dynamic binding must be counterbalanced;
- behavior must be tested, not inferred from representation movement;
- model-family/checkpoint ancestry must stay explicit;
- completed training alone is not PASS.

The current selected supervisor reports `training_credit = 0`.

### Current negative conversion result

**PROJECT_MEASUREMENT / NEGATIVE_RESULT.** The selected 9.13O steering reports `0 accepted dataset tokens / 88,774 collected source tokens` for the Distillery utility path. This is a conversion/quality frontier, not a reason to celebrate raw token generation.

The architectural consequence is correct: optimize evidence-qualified conversion and replay identity before scaling raw generation.

---

## 10. Claude / strong-model bridge

The architecture benefits from a stronger model/tool/code partner only if the boundary is typed and observable.

A bridge should make explicit:

- handoff identity;
- capability scope;
- exact context/state digest;
- request provenance;
- returned result identity;
- reconciliation into current state;
- what authority the return **does not** possess.

Text handoff does not prove activation-level access. A model/tool result is a candidate until deterministic state/effect rules admit it.

---

## 11. 2026-08-27 Frankenstein master-cognition concept: useful ideas plus a live negative result

The recent `frankenstein-master-cognition-concept/CONCEPT.md` is unusually valuable because it records both design and correction.

It explicitly says an external Free-Pool consultation invented structures that were not in the real GRID10 source (including an InfluxDB-like store, 128-dimensional embeddings and a weighted graph). Those details were rejected rather than copied into the concept.

That is a **NEGATIVE_RESULT** with direct methodological value:

`external model consensus/design advice → source inspection → contradiction → discard invention → retain only source-compatible structural idea`

The same concept distinguishes existing SQLite/WAL Fabric/regulator mechanisms from aspirational boot persistence, physical sensorics and a web UI.

---

## 12. 72-hour Bauleiter/Bugfix orchestration: source-ready is not operative

The current main head added:

- `research_entity/topic_packets/frankenstein-master-cognition-concept/frankenstein_packages_v1.py`
- `.../frankenstein_orchestrator_v1.py`
- `.../frankenstein_bugfix_v1.py`
- three corresponding test files.

The commit message reports 29 tests green across the three suites.

However, the same current head’s provider path directly imports/calls the external fallback pool. The selected 9.13O supervisor state says current provider authority is HARD_OFF and explicitly quarantines this 72-hour provider orchestration.

Therefore:

**CURRENT_SOURCE:** implementation exists.  
**SOURCE TEST CLAIM:** commit records unit-test success.  
**CURRENT AUTHORITY:** provider-calling deployment is non-operative.  
**RUNTIME CREDIT:** zero.  
**Required repair:** gate the **caller/orchestration** boundary before secret lookup, provider import, network, Aider or fallback dispatch; do not rewrite Frank’s own Harness to get around the control boundary.

The commit itself is also valuable provenance evidence: Git records the author/committer as `harness-mistral-small`, so a later clean non-provider re-review matters even though the message describes direct coordinator authorship.

---

## 13. Failure → engineering move map

| Failure / negative evidence | Engineering move it motivates |
|---|---|
| state split across services/stores | one canonical durable substrate + rebuildable projections |
| rumination / recursive reflection | explicit reflection exit into ACT / ASK / WAIT / re-observe |
| prompt/context contamination | typed state and bounded context provenance |
| prompt-vs-weight / label shortcut | dynamic binding, counterbalance, nuisance controls, family splits |
| internal feature moves but behavior does not | separate READ / BIND / WRITE; require behavioral causal gate |
| model consensus repeats same error | source/runtime evidence outranks consensus |
| component test passes | scope-bound credit; no whole-product promotion |
| provider route bypasses authority | fail-closed caller gate before secret/import/network boundary |
| Free-Swarm produces raw volume but no accepted dataset tokens | optimize Forge/Distillery conversion before more scale |
| thread oversubscription hurts latency | matched topology-specific resource A/B, no extrapolation |
| external consultant invents nonexistent structures | source-adversarial review before adoption |
| unknown external effect outcome | journal UNKNOWN; never blind replay |

---

## 14. Current frontier after this Trigger-3 synthesis

1. Preserve 9.13 HARD_OFF at every external Frankenstein caller before credentials/import/network/fallback.
2. Independently review/re-execute post-HARD_OFF provider-authored Frankenstein/GRID changes on clean non-provider source before runtime promotion.
3. Keep provider execution, whole EntityOS/HCU, full HCU, model-specific J-Space and training credits at zero until exact receipts establish only their measured scope.
4. Continue Project-Frankenstein Level-0 reconstruction: ordered history obligations and exact frozen-head tree remain incomplete in the current archive manifest.
5. Migrate the repository root only after path-reference, workflow, bootstrap and consumer audits prove each move compatibility-safe.
6. Keep converting historical failures into tests, evidence labels and causal discriminators rather than narrative cleanup.

This is the practical meaning of Frankenstein synthesis: preserve the organs that worked, preserve the scars that explain why they changed, and refuse to call the assembled system alive merely because the documentation is coherent.
