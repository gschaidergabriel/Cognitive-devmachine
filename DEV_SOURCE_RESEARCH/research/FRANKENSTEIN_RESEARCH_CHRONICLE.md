# Project Frankenstein — research chronicle and dependency map

**Scope:** evidence-bounded synthesis of the accessible research archive.  
**Do not read this as a complete Git history.** The current archive manifest for the historical `gschaidergabriel/Project-Frankenstein` repository is explicitly `PARTIAL_NOT_FROZEN`, with exact tree/history enumeration still incomplete.

This document therefore uses the phrase **first verified in accessible Git/evidence** where chronology is incomplete. It does not convert a retrieved commit window into a creation date.

---

## 0. Evidence vocabulary

- `CURRENT_SOURCE` — source or authority present on current canonical repository state.
- `HISTORICAL_SOURCE` — preserved source from an older Project Frankenstein / Frank / Zero generation.
- `PROJECT_MEASUREMENT` — exact measured result at a named evidence surface.
- `NEGATIVE_RESULT` — measured contradiction, failure or blocked path that constrains the design.
- `EXTERNAL_PRIMARY` — original paper, standard or vendor-primary technical documentation.
- `INFERENCE` — interpretation supported by project evidence but not directly measured.
- `OPEN_HYPOTHESIS` — proposed causal/general claim with a falsifier.

Status verbs used here:

`attempted · source-ready · measured · reproduced · contradicted · blocked · prepared-not-run · adopted · retired`

---

# Part I — what historical Frankenstein actually contains

## 1. The old system was already more than a model wrapper

`HISTORICAL_SOURCE`

The archive manifest deep-reads a historical Project Frankenstein head and identifies real runtime code for:

- persistent cognition / multi-timescale loops: `services/consciousness_daemon.py`;
- persistent state/personality/homeostasis: `personality/e_pq.py`;
- sensory gating / attention / habituation / prediction error: `services/thalamus.py`;
- global broadcast / salience: `services/global_workspace.py`;
- memory, claims, graph, vector retrieval and forgetting: `tools/lcme/lcme_core.py`;
- reward prediction / motivation / habituation: `services/nucleus_accumbens.py`;
- actor-critic / PPO / idle policy / hallucination tracking: `services/subconscious.py`;
- persistent spatial/world/body state: `services/spatial_state.py`;
- replay / synthesis / consolidation / interrupt-resume: `services/dream_daemon.py`;
- persistent projects, goals, strategies and tool learning: `services/project_engine.py`;
- hypothesis lifecycle, experiments and evaluation: `services/hypothesis_engine/`;
- LoRA training and before/after probes: `services/soma/micro_trainer.py`;
- several visual backend generations: adaptive vision, visual pipeline, FrankEye and native vision.

The point is not that all of these modules were correct, necessary, or still current. The point is that the historical project already treated agency as a **system property spanning state, memory, gating, action, learning, perception and control**, not as a single prompt.

### Architectural consequence

`INFERENCE`

The later move toward EntityOS/HCU can be read as a compression/reformulation problem: preserve useful cognitive functions and measured couplings while removing accidental service boundaries, duplicated state authorities and biologically named modules that are no longer useful implementation units.

That interpretation is now explicit in the current owner target: reproduce the cognition that made Zero/EntityOS work, but do not require the old monolithic module boundaries.

---

## 2. Global workspace: from broadcast bus to causal interface question

`HISTORICAL_SOURCE`

The archive identifies `services/global_workspace.py` as runtime code implementing a broadcast bus / salience mechanism and a GWT precursor.

`EXTERNAL_PRIMARY`

Global workspace / global neuronal workspace literature is useful context for broadcast, competition and widespread availability. Dehaene & Changeux (2011), for example, survey experimental/theoretical approaches to conscious processing and global-workspace-like ignition. That literature is **not** proof that the software is conscious and is not required for the engineering architecture.

`CURRENT_SOURCE`

Current EntityOS/HCU work narrows the engineering problem to observable operations:

```text
competition / selection
    -> broadcast
    -> uptake
    -> state change
    -> re-entry
```

The important promotion test is causal: did the transferred workspace state change downstream cognition at the exact supported interface?

`NEGATIVE_RESULT / LAW`

Textual coherence, recurrence, model self-report, majority vote and semantic interpretation alone do not establish model-internal causality.

### Failure -> next move

Historical broadcast semantics were useful, but current work requires **receipted re-entry** and model/runtime-specific intervention evidence. That is the conceptual bridge from `global_workspace.py` to the current **Global J-Space** research interface.

---

## 3. E-PQ / state / homeostasis: personality becomes state transition

`HISTORICAL_SOURCE`

The archive classifies `personality/e_pq.py` as persistent personality state, homeostasis and event learning.

`INFERENCE`

A useful lesson from that line is that stable behavior should not depend only on a prose persona. Persistent state, feedback, homeostatic variables and event-linked updates give the system something observable that can survive model/context changes.

Later project language makes this sharper: **generate/maintain the state first; realize personality linguistically later.**

This is an engineering claim about state control, not a claim about human-like personality.

---

## 4. Perception lineage: replacement matters as much as capability

`HISTORICAL_SOURCE`

The archive manifest explicitly records multiple visual paths and their supersession relationships:

```text
adaptive routing / visual pipeline
    -> FrankEye / Retina artifact consumer
    -> native multimodal vision direction
```

The archive also notes documentation drift and cross-reconciliation obligations.

### Failure -> next move

`INFERENCE`

Perception research repeatedly exposes a systems problem: an architecture can accumulate several partially overlapping backends while documentation continues to describe all of them as if they were current. The curation rule is therefore to preserve old backends as provenance while naming the active replacement only when current source/runtime evidence supports it.

The same rule applies to `Frank`, `ClayVerse`, `Mini Entity`, `Xeno`, `GRID10` and other names: provenance is not authority.

---

## 5. Training lineage: LoRA / IAPT / SOMA before the 0.8B cognitive-module target

`HISTORICAL_SOURCE`

The Project Frankenstein manifest points to:

- `papers/IAPT_METHOD.md` — training method report, historical measurements and negative-result methodology;
- `services/soma/micro_trainer.py` — LoRA training, feedback weighting, before/after probes.

This matters because the current training program is not starting from the abstract idea "fine-tune a model". The archive already contains attempts to connect feedback, state and measured before/after behavior.

`CURRENT_SOURCE`

The current owner target changes the object being trained. The Qwen3.5-0.8B-class model is intended as a reusable **cognitive-process substrate** for a variable grid, not as a miniature Claude Code and not as a personality clone.

Training families should therefore derive from a cognitive-process census and include state interpretation, DB-vs-simulation decisions, planning, alternatives, uncertainty, workspace uptake/re-entry, coordination independent of fixed `N`, compact state transfer and hard negatives against false state/authority/memory.

`OPEN`

Training completion alone is not acceptance. The model must improve intended cognitive behavior without unacceptable loss of protocol, logic, DB interaction, coordination or workspace-bridge behavior.

---

# Part II — why persistent state collapsed toward UnifiedDB

## 6. The multi-store problem

`INFERENCE grounded in historical/current source`

Historical cognitive systems naturally grow specialized state stores: memory, graph, projects, effects, perception caches, training state, identity state, snapshots and service-specific databases. Specialization helps local implementation but creates a harder question:

> Which store is authoritative when they disagree?

EntityOS research moved toward one canonical deterministic substrate while allowing rebuildable derived projections.

The principle is **one authority substrate, many typed structures**, not "one god table".

High-rate transient sensor state can still live in RAM. Derived Graph/FTS/vector structures can still exist. Their job is to accelerate or organize cognition, not silently become a second truth authority.

---

## 7. UnifiedDB negative run: six green failures

`PROJECT_MEASUREMENT + NEGATIVE_RESULT`

A deeper UnifiedDB run deliberately constructed six discriminators on an accepted target. All six discriminators succeeded in reproducing their intended design gaps while canonical state and external effects remained untouched.

That is a useful kind of green test: green means **the bug hypothesis was reproduced**, not "the product passed".

### 7.1 Source certificate != live schema

A rogue table could be added or a required view removed while source/pair certificate and SQLite integrity still looked acceptable.

**Forced move:** separate executable migration identity from normalized live-schema attestation.

### 7.2 Derived Graph must not gate canonical truth availability

Changing expected Graph source identity could make canonical UnifiedDB open fail even while UnifiedDB itself was healthy.

**Forced move:** make the dependency acyclic: canonical DB -> projection, never projection -> canonical DB authority.

### 7.3 Stale projection read gating was insufficient

A globally stale Graph could still return current-looking nodes/edges.

**Forced move:** explicit projection certificates with semantic source root, graph epoch, materializer identity, content digest and state such as `ADMITTED|STALE|RETRACTED|REBUILD_REQUIRED`.

### 7.4 Ambient clock + mixed text formats can create false current

Python-style offset timestamps and SQLite `CURRENT_TIMESTAMP` text could compare incorrectly under raw lexical ordering.

**Forced move:** canonical time representation plus an explicit replay/as-of clock in query receipts.

### 7.5 Snapshot receipt could invalidate its own hash

The flow could hash the live DB, then write the snapshot receipt into that same DB; Graph epoch and Graph file hash could also describe different logical instants.

**Forced move:** materialize an immutable snapshot artifact first, then hash/verify it, and keep receipt semantics outside or explicitly excluded.

### 7.6 Git HEAD was too broad an authority identity

An unrelated repository-head change could invalidate canonical state even while semantic dependencies and DB state were unchanged.

**Forced move:** authority binds a content-addressed minimal semantic dependency manifest; full Git HEAD remains useful audit provenance.

### 7.7 Measured schema digest overhead

The exact target run measured normalized materialized-schema digest cost around:

```text
p50  91.17 µs
p95 126.77 µs
p99 148.112 µs
```

That measurement constrains the cost of stronger open-time/live-schema verification at that target identity.

---

## 8. Emergent Retrieval after the authority split

`PROJECT_TERM + INFERENCE`

Once canonical truth is separated from projections and indexes, retrieval can become richer without becoming more authoritative.

Project **Emergent Retrieval** means candidate relevance can emerge from overlap among independently stored dimensions:

```text
semantic match
+ time
+ causal lineage
+ current state
+ goal relevance
+ effect/outcome history
+ confidence
+ provenance
+ graph context
+ explicit constraints
```

The combination can produce a better candidate set than any single dimension.

But the UnifiedDB result imposes a hard boundary:

```text
candidate ranking != canonical admission
```

Graph, FTS, vector search, Hyperposition and learned rankers may help select what cognition should inspect. They do not mint facts.

---

# Part III — reflection, action and outcome re-entry

## 9. Why reflection without an exit is a bug

`INFERENCE + engineering requirement`

Historical persistent-cognition systems make it easy to build loops that keep generating internal state. A loop becomes useful only when it changes an observable transition.

The current engineering definition of self-reflection is:

1. inspect state/outcome;
2. detect mismatch, surprise or uncertainty;
3. generate a correction or alternatives;
4. compare with evidence/constraints;
5. persist/retrieve correction when appropriate;
6. alter later behavior;
7. terminate into `ACT`, `ASK`, `WAIT`, `RE-OBSERVE` or another measurable transition.

`NEGATIVE_RESULT category`

Rumination/fixation is the case where steps 1-6 recurse without a useful exit or new evidence.

`EXTERNAL_PRIMARY`

ReAct (Yao et al., ICLR 2023) and Reflexion (Shinn et al., NeurIPS 2023) are useful external comparisons because they respectively study interleaved reasoning/action and storing feedback/reflection for later trials. Their benchmark results do not become Frankenstein evidence; the transferable idea is the importance of coupling internal reasoning to observable action/feedback.

---

## 10. Effect authority: intent, effect and observed outcome are different events

`CURRENT ARCHITECTURE LAW`

A safe persistent agent cannot treat these as synonyms:

```text
I decided to call the tool
I submitted the call
it may have executed
I received a response
I verified the world changed
```

Each transition needs causal identity/provenance appropriate to its risk.

Unknown external outcomes remain unknown until reconciled. Repeating an external effect after an ambiguous transport failure can create duplicates.

This is why EntityOS retains deterministic effect gating/journaling even while cognition becomes more model-driven.

---

# Part IV — GRF, Hyperposition, HyperMath and ClayCode

## 11. GRF / HyperMath: make transforms explicit

`PROJECT RESEARCH LINE`

The repository contains a HyperMath/GRF fusion run and proof-carrying Clay artifacts such as:

`research_entity/trigger_runs/hyperposition/hyperposition-20260810T2342p0700-chatgpt-secondary-hypermath-grf-fusion/architecture/HYPERMATH_GRF_PROOF_CARRYING_IR_V11.clay`

The durable idea is to represent important cognitive/system transforms in a compact, typed, inspectable form rather than relying entirely on prose reconstruction.

This should be judged by executable invariants and compression/transfer behavior, not by the elegance of the notation.

---

## 12. Hyperposition: unresolved alternatives are a state, not an error

`PROJECT RESEARCH LINE`

Hyperposition preserves competing hypotheses/candidates instead of forcing an early single answer.

A minimal useful form is:

```text
alternatives = [h1, h2, ...]
for each alternative:
    provenance
    supporting evidence
    contradicting evidence
    uncertainty
    proposed discriminator
```

A recurrence, vote or model confidence score cannot itself collapse alternatives into truth.

The useful collapse event is an evidence-bearing discriminator.

---

## 13. ClayCode: cognitive protocol rather than literary language

`CURRENT TARGET / OPEN IMPLEMENTATION`

ClayCode is most valuable when it makes cognitive state transfer:

- typed;
- compact;
- composable;
- deterministic where possible;
- explicit about alternatives and evidence;
- independent of fixed grid size;
- suitable for DB storage/replay;
- translatable into the strongest interface available to Claude Code.

The owner target explicitly includes `CLAYCODE_COGNITIVE_PROTOCOL` before Global Workspace / Claude Code bridge / Global J-Space re-entry in the implementation chain.

The open question is not whether ClayCode can serialize a structure. The harder question is whether trained small modules can **use the protocol as cognition** and whether the bridge can preserve enough semantics to alter downstream strong-model behavior efficiently.

---

# Part V — HCU: from GRID10 implementation to variable cognitive grid

## 14. GRID10 was useful, but it is not the identity

`CURRENT_SOURCE`

Current code and tests contain a real GRID10 fabric and node runtime. Recent Frankenstein concept work describes real SQLite/WAL fabric operations, CAS claims/leases, regulators, elastic polling and memory release. It also carefully distinguishes real mechanisms from aspirational web UI, permanent boot service, external sensors and Claude bridge work.

`CURRENT_OWNER_CORRECTION`

The final architecture is **variable `N`**. Ten modules are one benchmark configuration.

That changes documentation and testing obligations:

- do not call ten the architecture;
- module-role identities must not be fixed personalities;
- coordination should survive changes in `N`;
- physical concurrency must be measured separately from logical module count;
- state that must survive grid resize/restart belongs in the DB;
- scaling claims require exact hardware/runtime/topology evidence.

---

## 15. Current 4-vCPU thread diagnostic

`PROJECT_MEASUREMENT`

Current supervisor steering records an exact tested topology:

```text
4 processes / 4 vCPU
1 thread/process: ~8.3197 s/call
2 threads/process: ~23.1806 s/call
4 threads/process: zero completed within tested timeout window
```

This is strong evidence against blindly increasing per-process inference concurrency on that exact environment.

It is **not** evidence that the variable grid cannot scale. The grid can scale by logical work distribution, process count, scheduling, model/runtime changes or larger hardware; those need their own measurements.

---

# Part VI — Global J-Space and vector binding

## 16. The strongest allowed claim

`CURRENT_SOURCE`

The current target is:

```text
GRID GLOBAL WORKSPACE
    <-> translate / bridge
    <-> CLAUDE CODE workspace/state at strongest exposed interface
```

Candidate bridge forms include typed ClayCode packets, structured shared-state slices, semantic Hyperposition state, compressed workspace summaries, embeddings/vectors, and model-specific activation/J-Space controls where genuinely accessible.

`OPEN_HYPOTHESIS`

The desired endpoint is deeper than prompt handoff: state should re-enter and causally influence later cognition.

### Required discriminator

A useful bridge test needs at least:

1. an exact transferred state identity;
2. a matched control where the state is absent/shuffled/lesioned;
3. same task family without trivial label/codebook cues;
4. measured downstream behavior/state difference;
5. rescue or counter-intervention where feasible;
6. model/runtime/site identity;
7. failure-closed claim scope.

Without those controls, "the model mentioned the injected concept" may be prompt/schema recurrence rather than internal causal binding.

---

# Part VII — the newest Frankenstein master concept and why it is quarantined

## 17. Source-ready mechanisms

`CURRENT_SOURCE`

The newest Frankenstein concept/source line includes:

- real GRID SQLite/WAL fabric primitives;
- regulator state;
- elastic polling;
- a proposed alignment regulator;
- proposed deterministic reflex layer;
- proposed Claude Code bridge;
- proposed web "cognitive Lego" UI;
- package decomposition / CAS-safe work claiming;
- Bauleiter continuation/orchestrator source;
- independent Bugfix-Frankenstein watchdog source and rollback/checkpoint ideas.

The concept itself does a useful thing: it labels several features as **NEW/aspirational rather than already existing**, including permanent boot operation, physical sensor integration, web UI and Claude bridge.

---

## 18. Provider hard-off makes source and operation diverge

`CURRENT_SOURCE + NEGATIVE_RESULT`

After provider authority switched to 9.13 HARD_OFF, fresh fallback/provider-calling paths still appeared. Current supervisor steering treats this as evidence that the caller boundary was not sufficiently gated before secret lookup/import/network/fallback.

Therefore the recent 72-hour Frankenstein provider orchestration is currently:

```text
QUARANTINED_NON_OPERATIVE
```

This does not erase the source or its tests. It changes the claim:

```text
source component exists and can be reviewed
!=
currently authorized autonomous provider runtime
```

The recovery path is independent non-provider review/re-execution plus hard caller-boundary closure and runtime quiescence before any future provider authority could be considered.

---

# Part VIII — FreeSwarm / Forge / Distillery as a Goodhart warning

## 19. Token production was not the objective

`PROJECT_MEASUREMENT + NEGATIVE_RESULT`

The project observed large FreeSwarm token accumulation while Forge/Distillery accepted output remained at or near zero for important periods. Current steering also reports a snapshot with:

```text
88,774 collected source tokens
0 accepted dataset tokens
```

The lesson is not "free models are useless." The lesson is that **input volume and useful admitted training signal are different metrics**.

A system optimized for token generation can Goodhart the wrong counter.

### Forced move

Training readiness must be measured in admitted, de-duplicated, causally grounded, leak-resistant dataset families with deterministic hard negatives — not raw swarm volume.

---

# Part IX — architecture codependencies

## 20. What cannot be solved independently

| Line | Depends on | Why |
|---|---|---|
| Variable cognitive grid | cognitive-process census + ABI | Otherwise modules are arbitrary roles instead of preserved functions. |
| Cognitive ABI | DB-vs-simulation boundary | Must know what is state vs generated cognition. |
| UnifiedDB | provenance/root/time/snapshot/effect rules | One file without proof surfaces still has ambiguous authority. |
| Emergent Retrieval | canonical/derived split | Ranking must not mint truth. |
| Global workspace | typed state identity | Broadcast without identity cannot be audited or replayed. |
| Global J-Space | exact bridge + interventions | Coherence alone cannot prove causal coupling. |
| ClayCode | cognitive ABI | Language must encode actual functions/state, not decorative syntax. |
| Hyperposition | evidence/discriminator semantics | Alternatives need principled collapse conditions. |
| 0.8B training | causal traces + family splits | Generated narration alone is a leakage/hallucination risk. |
| Claude Code bridge | observable interface + re-entry receipt | Cannot claim activation access the product does not expose. |
| Effect loop | reconciliation / unknown-outcome law | Retry after ambiguity can duplicate real effects. |
| Reflection | measurable exit transition | Otherwise recursive self-commentary can masquerade as agency. |

---

# Part X — open hypotheses, confidence and falsifiers

The scores below are **engineering confidence scores, not calibrated probabilities**. They are intended to force explicit uncertainty and a next discriminator.

## H1 — rich external substrate is necessary for useful persistent reflective agency

**Status:** `OPEN_HYPOTHESIS`  
**Engineering confidence:** `0.78 / 1.00`

Hypothesis: state, durable memory, perception, arbitration, effect receipts and verified result re-entry provide capabilities that cannot be reliably replaced by recursive model reflection alone.

**Support:** historical architecture repeatedly introduced external state/control; current EntityOS design keeps deterministic DB/effect authority; ReAct/Reflexion provide external methodological analogies for action/feedback coupling.

**Falsifier:** a matched end-to-end benchmark where a stripped model-only reflective loop matches or exceeds the rich-substrate system on long-horizon state consistency, recovery, effect correctness and outcome adaptation under context resets.

---

## H2 — Zero/EntityOS cognitive functions can be reproduced by a variable small-model grid

**Status:** `OPEN_HYPOTHESIS`  
**Engineering confidence:** `0.55`

**Support:** functions can be enumerated; shared state and modular work distribution are implementable; GRID source provides an initial fabric.

**Counterhypothesis:** key functions depend on strong-model latent capabilities or old runtime coupling that 0.8B modules cannot reproduce economically.

**Falsifier:** cognitive-process ABI benchmark where variable-grid implementations systematically fail critical processes or require Claude Code for nearly every transition, eliminating the intended grid benefit.

---

## H3 — canonical DB + rebuildable projections reduces authority failure

**Status:** `ADOPTED DIRECTION / STILL OPEN END-TO-END`  
**Engineering confidence:** `0.86`

**Support:** UnifiedDB negative run directly reproduced failure from symmetric authority and motivated acyclic DB->projection direction.

**Counterhypothesis:** specialized stores with a strong transactional/causal protocol may be simpler or more robust than a central canonical SQLite substrate.

**Falsifier:** target A/B showing a specialized-store architecture has equal or better crash/replay/authority correctness and materially better operational cost without reintroducing ambiguous ownership.

---

## H4 — Emergent Retrieval improves relevance without increasing truth authority

**Status:** `OPEN_HYPOTHESIS`  
**Engineering confidence:** `0.64`

**Support:** multi-dimensional candidate selection is structurally plausible and aligns with existing semantic/time/graph/provenance data.

**Counterhypothesis:** combining many dimensions mostly amplifies correlated noise or stale projection bias.

**Falsifier:** family-held-out retrieval evaluation where overlap-based retrieval fails to improve relevant-evidence recall/precision after controlling for candidate-universe leakage and stale derived indexes.

---

## H5 — semantic J-Space control can be made label-independent

**Status:** `OPEN_HYPOTHESIS`  
**Engineering confidence:** `0.36`

**Support:** internal/vector intervention mechanisms and J-Space research artifacts exist.

**Counterhypothesis:** observed steering is primarily lexical/codebook/readout coupling rather than abstract internal-state control.

**Falsifier / promoter:** disjoint, label-free, counterbalanced, family-held-out intervention with lesion/shuffle controls and rescue showing semantic behavior transfer beyond prompt/codebook cues.

---

## H6 — ClayCode can reduce state-transfer cost while preserving cognitive semantics

**Status:** `OPEN_HYPOTHESIS`  
**Engineering confidence:** `0.48`

**Counterhypothesis:** structured JSON/state slices plus conventional code are sufficient; a new IR adds compiler/protocol burden without net gain.

**Falsifier:** matched tasks showing ClayCode has no improvement in token/byte cost, parse reliability, replayability, transfer accuracy or module coordination after implementation overhead is included.

---

## H7 — grid <-> Claude Code can become meaningfully deeper than prompt handoff

**Status:** `OPEN_HYPOTHESIS`  
**Engineering confidence:** `0.40`

**Counterhypothesis:** Claude Code's exposed interface limits the bridge to well-engineered text/tool/session context; "Global J-Space" on the Claude side adds no distinct mechanism.

**Promoter:** causal re-entry experiments showing structured/typed/compressed state transfer improves downstream strong-model behavior over matched textual baselines at lower or equal context cost.

---

## H8 — a low-refusal/abliterated 0.8B module can retain required cognitive abilities

**Status:** `PREPARED-NOT-PROVEN`  
**Engineering confidence:** `0.30`

**Counterhypothesis:** refusal suppression or checkpoint modification damages instruction/protocol fidelity, reasoning stability or safety-critical state discrimination.

**Falsifier:** frozen baseline and post-training evaluation showing unacceptable regression on cognitive-process ABI, DB semantics, ClayCode, uncertainty handling, coordination or hard-negative authority tests.

---

# Part XI — external primary references

These sources provide context only. Project evidence must come from Project Frankenstein/EntityOS source and measured receipts.

1. SQLite — **Atomic Commit in SQLite**  
   https://www.sqlite.org/atomiccommit.html
2. SQLite — **Write-Ahead Logging**  
   https://www.sqlite.org/wal.html
3. NVIDIA — **CUDA Programming Guide: Unified Memory**  
   https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/unified-memory.html
4. Dehaene, S. & Changeux, J.-P. (2011). **Experimental and theoretical approaches to conscious processing.** *Neuron*, 70(2), 200-227. DOI: `10.1016/j.neuron.2011.03.018`
5. Yao, S. et al. (2023). **ReAct: Synergizing Reasoning and Acting in Language Models.** ICLR 2023.
6. Shinn, N. et al. (2023). **Reflexion: Language Agents with Verbal Reinforcement Learning.** NeurIPS 2023. DOI: `10.52202/075280-0377`

---

# Part XII — exact next research obligations

1. Finish/freeze exact historical Project Frankenstein tree/history obligations before claiming complete chronology.
2. Convert historical module names into a **cognitive-process census**, preserving source anchors and measured behavior rather than names.
3. Stabilize the **Cognitive Process ABI** and explicit DB-vs-simulation boundary.
4. Generalize current GRID implementation/tests from fixed-ten assumptions to variable `N` where final semantics require it.
5. Keep provider HARD_OFF enforced at the earliest caller boundary; prove `provider_calls=0` and `secret_lookups=0` while off.
6. Independently re-review/re-execute quarantined post-hardoff core changes on non-provider paths before promotion.
7. Build Global Workspace re-entry receipts and compare structured bridge forms against matched text-only baselines.
8. Close the J-Space abstraction gap with label-free, disjoint, counterbalanced intervention controls.
9. Turn source-token collection into accepted family-split dataset yield with deterministic hard negatives.
10. Keep every effect/result path causally bound so request, execution, response and verified world outcome remain distinct.

The research story should be updated when these tests move a claim between `attempted`, `measured`, `contradicted`, `reproduced`, `adopted` and `retired`. It should not be updated merely because a new model wrote a more persuasive paragraph.
