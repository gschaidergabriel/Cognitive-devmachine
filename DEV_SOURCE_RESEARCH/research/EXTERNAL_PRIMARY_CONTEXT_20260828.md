# External primary context — Triggerword 3 research update — 2026-08-28

**Status:** `EXTERNAL_PRIMARY_RESEARCH_CONTEXT_ONLY`  
**Authority:** This file is not Clay authority and grants no Project-Frankenstein, EntityOS, HCU, GRID, Global J-Space, model, provider, training, or whole-product runtime credit.

The purpose of this note is to import current primary-source methods and counterevidence without laundering external results into project facts.

## 1. Adversarial Global Neuronal Workspace / IIT test

**Evidence class:** `EXTERNAL_PRIMARY`  
**Source:** Cogitate Consortium et al., *Adversarial testing of global neuronal workspace and integrated information theories of consciousness*, Nature 642, 133–142 (2025). Published 2025-04-30. DOI: 10.1038/s41586-025-08888-1.

Primary links:

- https://www.nature.com/articles/s41586-025-08888-1
- https://doi.org/10.1038/s41586-025-08888-1

The study used a preregistered, theory-neutral adversarial collaboration with fMRI, MEG and intracranial EEG across 256 participants. It reports results that support some predictions while substantially challenging key predictions of both IIT and GNWT. In particular, the paper reports challenges to GNWT predictions involving stimulus-offset ignition and some prefrontal representations.

### Transfer to Frankenstein

This does **not** prove or disprove the project's engineering workspace, Global J-Space, GWT-inspired coordination, consciousness, or cognition claims. The transferable method is narrower and useful:

> For disputed architecture claims, define divergent predictions, analysis rules and pass/fail interpretations before measurement where feasible.

Project discriminator shape:

```text
candidate mechanism A
vs candidate mechanism B / simpler control
vs lesion
vs shuffle
vs rescue
→ preregistered task families + exact runtime identity + causal outcome receipts
```

This strengthens the existing rule that coherence, recurrence and narrative consensus cannot establish causal workspace value.

## 2. ReAct

**Evidence class:** `EXTERNAL_PRIMARY`  
**Source:** Shunyu Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, arXiv:2210.03629 / ICLR 2023.

Primary link:

- https://arxiv.org/abs/2210.03629

ReAct interleaves reasoning traces with actions and observations. For Frankenstein, this is useful as an external engineering donor for closed observation/action loops. It is not proof that the project's historical reflection, tool, or effect architecture is superior.

Transferable discriminator: compare an observation/action interleaving loop against a matched tool-use baseline with the same model, tool access, token/action budget and outcome verification.

## 3. Reflexion

**Evidence class:** `EXTERNAL_PRIMARY`  
**Source:** Noah Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, arXiv:2303.11366 (2023).

Primary link:

- https://arxiv.org/abs/2303.11366

Reflexion uses verbal feedback/reflection and episodic memory to alter later behavior. This is relevant to the project hypothesis that useful reflection must produce a later measurable transition rather than recurse indefinitely.

It does **not** establish unique causal value for Frankenstein reflection. A proper project test lesions the explicit reflection step while holding retrieval, feedback, model, task family, action budget and token budget fixed.

## 4. Activation engineering / steering vectors

**Evidence class:** `EXTERNAL_PRIMARY`  
**Source:** Andy Zou et al., *Steering Language Models With Activation Engineering*, arXiv:2308.10248 (2023).

Primary link:

- https://arxiv.org/abs/2308.10248

Activation Addition/activation engineering demonstrates that inference-time interventions in model activations can alter behavior. This supports the *methodological plausibility* of causal vector-intervention tests for a model where the required activation interface is actually exposed.

Boundary for Global J-Space:

```text
activation/vector steering exists in external model research
!=
Frankenstein currently has activation-level access to Claude Code or another closed model
```

A current J-Space claim must bind the exact checkpoint/tokenizer/runtime and the actually exposed intervention interface. Text/tool/session interfaces cannot be relabelled hidden-state access.

## 5. SQLite WAL durability counterexample

**Evidence class:** `EXTERNAL_PRIMARY`  
**Sources:** SQLite WAL documentation and SQLite 3.51.3 release notes.

Primary links:

- https://www.sqlite.org/wal.html
- https://sqlite.org/releaselog/3_51_3.html

SQLite documents a rare WAL-reset corruption bug discovered and fixed in March 2026. The documented affected range is broadly SQLite 3.7.0 through 3.51.2 under a specific concurrent WAL writer/checkpoint race; the fix is in 3.51.3 and later, with selected backports.

### Transfer to UnifiedDB

This is **not** evidence that UnifiedDB was affected. It is a concrete reason to refuse generic claims such as “SQLite WAL is safe” without binding:

- exact SQLite library/runtime version;
- journal mode;
- connection count;
- process/thread topology;
- checkpoint behavior;
- filesystem/runtime environment.

Durability acceptance belongs to the exact deployed topology, not the database brand name.

## 6. NVIDIA CUDA Unified Memory

**Evidence class:** `EXTERNAL_PRIMARY`  
**Source:** NVIDIA CUDA Programming Guide, *Understanding Memory*.

Primary link:

- https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html

CUDA Unified Memory is useful only as a systems-design analogy for reducing ownership/copy boundaries across compute domains. NVIDIA's documented behavior depends on platform/kernel/GPU/interconnect capabilities and may use hardware or software mechanisms for access/coherency.

Strict boundary:

```text
hardware/system memory coherence
!=
SQLite transaction semantics
!=
canonical evidence authority
!=
model truth
```

The analogy can motivate fewer ownership boundaries; it cannot prove UnifiedDB semantics or HCU correctness.

## 7. Current research synthesis

The strongest transferable pattern across these sources is not “use GWT”, “use reflection”, or “use vectors”. It is:

1. bind the exact mechanism and exposed interface;
2. formulate a serious alternative explanation;
3. make predictions that differ;
4. lesion/shuffle/rescue or otherwise intervene where possible;
5. keep task/model/runtime provenance fixed;
6. observe real downstream outcomes;
7. preserve negative results;
8. promote only the exact scope that survived the discriminator.

For Project Frankenstein, the immediate high-information applications are:

- **Global J-Space/GWT:** preregister truthful-vector vs shuffled-vector vs lesion vs rescue predictions; no hidden-state claims without an exposed interface.
- **Reflection:** explicit-reflection lesion under matched budgets, with ACT/ASK/WAIT/re-observe termination measured.
- **UnifiedDB:** bind exact SQLite version and WAL/concurrency topology before durability promotion.
- **Editing autonomy:** treat the 672→87 direct-dispatch rewrite as an executable counterexample and compare preimage-bound patch edits against whole-file regeneration on destructive-delta tests.

`EXTERNAL_PRIMARY + METHOD_PRESENT != PROJECT_RESULT_PRESENT`.
