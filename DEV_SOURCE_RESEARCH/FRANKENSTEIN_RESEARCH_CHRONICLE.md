# Frankenstein Research Chronicle

> **Curated reconstruction, not canonical authority.** Dates below mean **first verified in accessible Git/search evidence used for this curation**, not necessarily the day an idea was originally conceived. Current authority/source/receipts outrank this narrative.

## Reading key

- `CURRENT_SOURCE` — visible in current source/authority surfaces.
- `HISTORICAL_SOURCE` — archived real material, not current authority.
- `PROJECT_MEASUREMENT` — measured project result at a declared scope.
- `EXTERNAL_PRIMARY` — primary paper/spec/vendor documentation.
- `INFERENCE` — synthesis from evidence.
- `OPEN_HYPOTHESIS` — falsifiable proposal.
- `NEGATIVE_RESULT` — blocked, contradicted, zero-yield or falsified result.

## 1. The recurring engineering problem

The project's history can be compressed into one recurring failure pattern:

```text
useful cognition
  -> fragmented state
  -> stale or contradictory memory
  -> model generates a plausible action
  -> request is mistaken for effect
  -> outcome is not re-observed cleanly
  -> next cognition is trained/conditioned on an unverified story
```

The current architecture reverses that failure chain:

```text
typed observation
  -> canonical state/evidence
  -> candidate cognition
  -> deterministic effect gate
  -> effect journal / observed result
  -> verification
  -> memory update
  -> next bounded decision
```

`INFERENCE`: many project subsystems that look unrelated — UnifiedDB, Typed Entry, EffectGate, causal receipts, Hyperposition, HCU, J-Space traces, compiler contracts — converge on the same problem: **keep cognition powerful while preventing it from silently becoming truth authority**.

---

## 2. GWT/workspace lineage — first verified accessible Git: 2026-08-08

Accessible Git search first verifies the FRANK/GWT research line in commits including:

- `15f8f87e` — "Deploy FRANK/GWT domain shard";
- `f3a32d1c` — GWT research trigger protocol;
- `572d7e6b` — causal GWT micro-packet;
- `f1b4ce5f` — GWT causal-closure research run;
- `262136d8` — adaptive workspace experiment results;
- `b1ff9253` — dual-workspace topic packet.

`HISTORICAL_SOURCE`: these commits establish a real research lineage, not modern whole-HCU acceptance.

### External research frame

`EXTERNAL_PRIMARY`: Dehaene & Changeux (Neuron, 2011, DOI `10.1016/j.neuron.2011.03.018`) review experimental/theoretical approaches to conscious processing and the global neuronal workspace family. Project Frankenstein uses workspace/global-broadcast ideas as **engineering inspiration** only. It does not need or make a present claim of consciousness, sentience, subjective experience, or biological equivalence.

Current engineering interpretation:

- a workspace may coordinate candidate state across modules;
- recurrence/broadcast can be measured;
- causal intervention (shuffle/lesion/rescue/control) is needed before calling a specific internal vector/workspace state causal;
- workspace stability cannot mint external truth.

`OPEN_HYPOTHESIS` (confidence 0.68): a useful agentic workspace becomes more reliable when it is coupled to an external substrate carrying typed state, memory, perception, effect receipts and verified outcome re-entry.

**Falsifier:** a matched architecture with substantially weaker external substrate repeatedly achieves equal or better long-horizon task reliability, causal attribution and recovery under state perturbation without hidden equivalent state elsewhere.

---

## 3. UnifiedDB — first verified accessible Git: 2026-08-08

Accessible Git search first verifies the UnifiedDB line in:

- `08793cde` — "Add UnifiedDB research foundation";
- `85b56a7c` — scientific trigger protocol;
- `f23c3d54` — UnifiedDB registered as research trigger;
- subsequent mesh/bootstrap wiring commits on the same date.

Current repository paths include real store/retrieval/prototype material such as:

- `the artefact/clayverse/store.py`;
- `agentZero/code/produkt/store.py`;
- `research_entity/harness/reference/unifieddb_emergent_compact.py`;
- `.../unifieddb_emergent_exact_topk.py`;
- `.../unifieddb_emergent_incremental.py`;
- `.../unifieddb_emergent_cascade.py`;
- `.../unifieddb_claygraph_assembly.py`;
- benchmark and maintenance documents under `research_entity/harness/reference/` and `research_entity/runtime/`.

### Why fragmentation collapsed toward one substrate

`INFERENCE`: multiple databases/services are not bad by definition. The project-specific problem was **authority fragmentation**: if independent stores can each claim current state, recovery and causal lineage become ambiguous. UnifiedDB's architectural value is therefore not "SQLite is magical" but **one durable authority boundary with typed internal structure**.

A UnifiedDB is not a god file. One authority substrate can have many tables, views, indexes, typed journals, policies and projections. Derived graphs/workspaces remain rebuildable; high-rate transient sensor values may remain in RAM.

`EXTERNAL_PRIMARY`: SQLite's official WAL documentation explains that WAL appends committed changes separately while allowing concurrent readers of the original database image, with later checkpointing. This is relevant to the repository's SQLite/WAL fabric design. It is not proof that any particular Frankenstein schema is correct.

### Emergent Retrieval

Project term: relevance that emerges when independently stored evidence dimensions overlap at query time — semantics, time, causal lineage, state, goals, perception, effect history, confidence, provenance, etc.

`CURRENT_SOURCE`: multiple `unifieddb_emergent_*` reference/prototype paths and benchmarks exist.

`OPEN_HYPOTHESIS` (confidence 0.73): multi-dimensional query-time composition can outperform one-dimensional retrieval for stateful agent decisions while preserving provenance.

**Falsifier:** matched evaluation shows no gain or worse calibrated relevance/latency once data leakage, query complexity and index cost are controlled.

---

## 4. GRF + Hyperposition — first verified accessible Git: 2026-08-10

Accessible chronology includes:

- `7367f0e4` — executable C-GRF candidate contract;
- `dba25ad4` — C-GRF synthesis/reentry receipt;
- `7544d636` — HyperMath GRF proof-carrying IR v1.1 candidate;
- `d4ceafc6` — synthetic execution receipt;
- `57a10a4f` — executable HyperMath GRF reference prototype;
- `fc731bbd` — fusion report;
- `4ffce811` — research-mesh reentry.

Important archive paths include:

`research_entity/trigger_runs/hyperposition/hyperposition-20260810T2342p0700-chatgpt-secondary-hypermath-grf-fusion/`

with a proof-carrying `.clay` IR candidate, execution receipt, final report and reentry manifest.

### Engineering interpretation

`HISTORICAL_SOURCE + INFERENCE`: GRF/HyperMath is best read as a typed reasoning/control lineage: represent relations, alternatives, proofs/constraints and generation lineage in a machine-checkable form instead of relying on prose alone.

Hyperposition's durable principle is:

> unresolved alternatives remain unresolved until an evidence-bearing discriminator closes them.

That principle now appears at multiple boundaries: competing hypotheses, causal candidates, route/engine identity, effect outcome, model/checkpoint ancestry and semantic promotion.

`NEGATIVE_RESULT` prevented: majority vote or recurrence must not collapse uncertainty into a fact.

---

## 5. ClayCode — compiler/language line, verified by 2026-08-11

Current source/index paths include:

- `tools/claycode_base_compiler.py`;
- `tools/claycode_base_package_compiler.py`;
- `tools/claycode_compiler_lab.py`;
- `tools/claycode_base_compiler_validation.py`;
- `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`;
- `research_entity/global/CLAYCODE_GENERAL_PURPOSE_COMPILER_ACCEPTANCE_CONTRACT.md`;
- `research_entity/trigger_runs/claycode/claycode-20260811T2243p0700-chatgpt-secondary-first-compiler-lowering/FINAL_REPORT.md`.

The line evolved from "an internal language exists" toward a stricter question: **can a declared ClayCode program lower, execute and preserve semantic/effect/state invariants at an accepted scope?**

Current 9.13 supervisor state still lists broad BASE/release gates as open beyond WP-01/WP-02. Therefore:

`CURRENT_SOURCE`: compiler/runtime artifacts exist.

`NEGATIVE_RESULT`: existence or narrow test success is insufficient for general-purpose release acceptance.

---

## 6. From Frank/Mini Entity/Xeno to EntityOS + HCU

### HCU first verified accessible Git: 2026-08-23

Accessible commits include:

- `201aed23` — owner-directed "Hyperposition Computational Unit" workstream, KVM4 topology and FREE_ONLY feed contract; explicitly source/architecture only, no runtime-performance claim;
- `95c26642` — HCU fused into root routing;
- `77582d2f` — HCU worker-admission fusion, explicitly retaining unverified runtime capacity;
- `b754d51a` / `3b74948d` / `9e0eac16` — capacity-claim guard, poison regressions and bounded evidence.

Naming later converged so HCU is the sole current integrated cognition/compute architecture, while Xeno/XCU are compatibility/research aliases rather than parallel systems.

### Current computer-like decomposition

```text
Typed Entry I/O
  -> deterministic admission/control
  -> canonical UnifiedDB state/evidence
  -> HCU shared-weight/vector/inference/J-Space plane
  -> Hyperposition / workspace candidate set
  -> ActionCandidate
  -> EffectGate
  -> EffectJournal / verified outcome
```

`CURRENT_SOURCE`: this decomposition is present in current authority caches and supervisor-era design.

`OPEN_HYPOTHESIS`: the decomposition is sufficient to support increasingly agentic behavior without granting the model direct truth/effect authority.

**Falsifier:** integrated runtime repeatedly requires hidden competing state/effect authorities to function, or measurable task performance/recovery worsens relative to a simpler architecture after equalizing compute and context.

---

## 7. Global J-Space — from semantic intuition to causal test demand

The project hypothesis is that a low-dimensional/shared vector interface can coordinate modules and eventually bind a small specialized model to HCU state.

The central methodological correction is crucial:

```text
text looks coherent
!= internal vector is causal
!= model state equals J-Space state
!= repeated label is evidence
```

Current promotion target therefore demands exact trace identity and model-specific interventions such as shuffle/lesion/rescue, family-level split discipline, hard negatives and checkpoint/tokenizer/runtime/build binding.

`NEGATIVE_RESULT`: hidden-state/J-Space claims based only on language labels or model self-report do not receive causal credit.

---

## 8. Training: prompt-vs-weight conflict and the interface hypothesis

A recurring project hypothesis is that small models often encode useful semantic distinctions internally but fail to bind those distinctions reliably to the project's exact output identifiers, state variables, J-Space controls or ClayCode atoms. That motivates fine-tuning as **interface installation**, not just style training.

The intended training language should align:

- model-internal representation;
- ClayCode atoms / compiler-visible variables;
- J-Space vector-control ABI;
- HCU module/state variables;
- Hyperposition alternatives;
- causal receipt identities.

But the current evidence law remains strict:

- training completion != behavioral PASS;
- checkpoint ancestry must be explicit;
- train/calibration/holdout family leakage invalidates independence;
- source-generated labels without admitted causal identity do not become canonical training truth.

Current supervisor 9.13: `training_credit = 0` and Together/paid fallback forbidden.

---

## 9. Reflection + action: agency without recursive rumination

`EXTERNAL_PRIMARY`: ReAct (Yao et al., ICLR 2023; arXiv `2210.03629`) studies interleaving reasoning and environment actions. Reflexion (Shinn et al., 2023; arXiv `2303.11366`) studies verbal feedback stored in episodic memory to alter later trials without weight updates.

These are **external analogies**, not project evidence. Frankenstein's stricter engineering formulation is:

```text
inspect -> compare -> correct -> persist/retrieve -> ACT|ASK|WAIT|REOBSERVE
```

The exit condition matters. A reflective system that indefinitely re-evaluates its own text can increase latency/context contamination without improving world-state alignment.

`OPEN_HYPOTHESIS` (confidence 0.81): reflective agency is more reliable when every reflection episode must terminate into a typed measurable transition and later outcome re-entry.

**Falsifier:** matched runs without explicit reflection termination show equal/better task completion, lower error accumulation and no higher rumination/fixation rate across long horizons.

---

## 10. August 27 Frankenstein master cognition concept: useful source-grounding plus a new authority failure

`CURRENT_SOURCE`: `research_entity/topic_packets/frankenstein-master-cognition-concept/CONCEPT.md` is unusually explicit about what exists and what is aspirational. It identifies real SQLite/WAL fabric, regulators, elastic polling and memory-release mechanisms, while rejecting invented external-model suggestions such as an InfluxDB-like store and nonexistent 128-dimensional short-window embeddings.

That source discipline is valuable.

The same topic packet later produced:

- `frankenstein_packages_v1.py` — package/dependency/claim dispenser;
- `frankenstein_orchestrator_v1.py` — Bauleiter continuity/orchestration;
- `frankenstein_bugfix_v1.py` — separate watchdog/rollback role;
- three test files. Commit `854f6bc8` reports 29 tests green.

### But: tests green != authorized architecture

Current supervisor 9.13O records that the orchestration directly calls or walks external provider tiers and retains stale Together availability assumptions. Fresh NVIDIA/Mistral fallback provenance after HARD_OFF demonstrates that this was not merely dead text.

Classification:

- package/orchestration source: `CURRENT_SOURCE`;
- non-network logic tests: bounded source/component evidence;
- provider-running 72h plan under current authority: `NEGATIVE_RESULT / QUARANTINED_NON_OPERATIVE`;
- execution authority: false.

Required engineering move: gate the **actual caller boundary** before secret lookup, provider import, network, Aider or fallback dispatch. Do not modify Frank's own Harness merely to hide the caller.

This is a strong example of why authority and runtime evidence must remain separate from code quality: a well-tested scheduler can still be the wrong thing to run.

---

## 11. GRID10 thread-count falsifier: architecture by measurement, not generic advice

Current supervisor 9.13O retains a measured A/B:

| topology | result |
|---|---|
| 4 concurrent processes, 4 vCPU, 1 torch thread/process | ~8.3197 s/call mean, 12 samples |
| same, 2 threads/process | ~23.1806 s/call mean, 12 samples |
| same, 4 threads/process | zero completed samples within experiment timeouts |

`PROJECT_MEASUREMENT + NEGATIVE_RESULT`: the generic recommendation that 2 threads/process should improve latency was directly falsified for this topology.

This does **not** prove that 1 is globally optimal. It proves the narrower and more useful statement: **for the measured 4-process/4-vCPU surface, retain default=1 until topology changes or a matched experiment overturns it.**

---

## 12. Memory/RAM claims: avoid accounting-class Goodharting

Supervisor steering warns that lower `Private_Dirty` alone does not establish lower physical RAM use or preserved weight sharing. A stronger falsifier should measure RSS/PSS and the full `smaps_rollup` classes plus host-level memory deltas.

`NEGATIVE_RESULT`: moving memory between accounting classes is not a RAM win.

This is an anti-Goodhart pattern worth reusing throughout the project: a metric only earns promotion if it remains linked to the real resource/outcome being optimized.

---

## 13. FreeSwarm / Forge / Distillery: volume is not conversion

Current 9.13O supervisor record keeps Distillery at zero accepted dataset tokens and training credit at zero.

`NEGATIVE_RESULT`: millions of generated/swarm tokens and many worker records do not establish usable training data, semantic independence or product progress.

The meaningful funnel is closer to:

```text
source token
  -> evidence-qualified delta
  -> accepted Forge record
  -> exactly one persistent Distillery packet
  -> accepted_dataset_tokens > 0
  -> replay/idempotence +0
  -> family-safe dataset
  -> model-specific causal evaluation
```

Raw generation volume belongs at the left edge, not at the definition of success.

---

## 14. Unified Memory analogy — useful only at systems-design level

`EXTERNAL_PRIMARY`: NVIDIA's current CUDA programming guide describes Unified Memory as a programming model that makes managed memory accessible across CPU/GPU and supports different hardware/software coherence regimes.

Project use: analogy for reducing ownership/copy boundaries so compute can operate over a coherent substrate.

Do **not** map the analogy too literally:

- CUDA coherence != database semantics;
- page migration != causal provenance;
- one address space != one truth authority;
- hardware coherence does not solve application-level effect identity.

The analogy is useful because it asks the right systems question: *how much complexity is being spent moving/duplicating state between owners?* It is not evidence for UnifiedDB correctness.

---

## 15. Current synthesis: what appears adopted vs. what remains open

| Topic | Current curation status | Evidence boundary |
|---|---|---|
| EntityOS product identity | **ADOPTED** | current authority/current-facing state |
| HCU integrated architecture identity | **ADOPTED** | current authority; full runtime credit still zero |
| UnifiedDB canonical state direction | **ADOPTED** | source/authority direction; exact runtime scopes vary |
| Typed Entry before cognition | **ADOPTED** | authority/design + component evidence only at declared scopes |
| EffectGate/EffectJournal authority | **ADOPTED** | deterministic architecture invariant |
| Emergent Retrieval | **SOURCE-READY / RESEARCHED** | reference/prototype/bench lineage; production claim must be scoped |
| GRF/HyperMath | **HISTORICAL + DONOR / PARTLY EXECUTABLE** | candidate/prototype/synthetic receipts; no blanket modern semantic credit |
| Hyperposition | **ADOPTED PRINCIPLE / ACTIVE RESEARCH** | preserves unresolved alternatives; implementation scopes vary |
| ClayCode compiler | **SOURCE-READY / PARTLY MEASURED** | broad release gate not pass |
| Global J-Space causal interface | **OPEN HYPOTHESIS / INSTRUMENTATION TARGET** | model-specific causal credit zero |
| local ~0.8B specialization | **PREPARED / NOT PROMOTED** | training credit zero |
| persistent provider-backed Frankenstein 72h loop | **QUARANTINED** | conflicts with 9.13 HARD_OFF |
| GRID10 1-thread default for 4proc/4vCPU | **MEASURED / TOPOLOGY-SPECIFIC** | diagnostic component evidence only |
| Distillery usable dataset yield | **BLOCKED / ZERO YIELD** | accepted dataset tokens 0 in current supervisor record |

---

## 16. What should be built next under current authority

Highest-value work is not another layer of narrative. It is a set of discriminators that can turn open claims into bounded evidence:

1. close the real external free-pool caller boundary under HARD_OFF and prove `provider_calls=0` + `secret_lookups=0` before provider-side code can run;
2. independently re-review/re-execute post-HARD_OFF provider-authored GRID10/core changes on a clean non-provider checkout with repository/source identity bound;
3. strengthen memory measurement to PSS/full `smaps_rollup` + host delta before claiming RAM efficiency;
4. preserve thread-count result as topology-specific and rerun only when topology changes;
5. convert one evidence-qualified Forge acceptance into exactly one persistent Distillery packet and nonzero accepted tokens followed by idempotent replay;
6. only then increase confidence in training-readiness or model-specific J-Space experiments.

The architectural story should continue to be written **by the failures that survive verification**, not by the most persuasive model output.

---

## External primary references used as analogies, not project evidence

- Dehaene S, Changeux J-P. *Experimental and theoretical approaches to conscious processing*. Neuron 70(2), 2011. DOI: `10.1016/j.neuron.2011.03.018`.
- Yao S et al. *ReAct: Synergizing Reasoning and Acting in Language Models*. ICLR 2023 / arXiv `2210.03629`.
- Shinn N et al. *Reflexion: Language Agents with Verbal Reinforcement Learning*. arXiv `2303.11366`.
- SQLite official documentation: Write-Ahead Logging (`sqlite.org/wal.html`).
- NVIDIA CUDA Programming Guide: Unified Memory (`docs.nvidia.com/cuda/.../unified-memory.html`).

These sources motivate comparison and falsifiers. They do not establish Frankenstein runtime facts.
