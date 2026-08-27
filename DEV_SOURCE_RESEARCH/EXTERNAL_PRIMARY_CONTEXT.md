# External primary context — Project Frankenstein / EntityOS

**Updated:** 2026-08-28  
**Evidence class:** `EXTERNAL_PRIMARY_RESEARCH_CONTEXT_ONLY`  
**Authority:** non-authority. External literature/specification does not mint Project-Frankenstein, EntityOS, HCU, GRID, Global J-Space, provider, model, training, or whole-product runtime credit.

This file materializes the external-primary node already referenced by the Triggerword-3 research layer. It imports methods, constraints and counterevidence while keeping project evidence separate.

## Adversarial Global Neuronal Workspace / IIT test

Cogitate Consortium et al., *Adversarial testing of global neuronal workspace and integrated information theories of consciousness*, Nature 642, 133–142 (2025), DOI `10.1038/s41586-025-08888-1`.

Primary sources:

- https://www.nature.com/articles/s41586-025-08888-1
- https://doi.org/10.1038/s41586-025-08888-1

The preregistered, theory-neutral adversarial collaboration used fMRI, MEG and intracranial EEG across 256 participants. It reports results compatible with some predictions while substantially challenging key predictions of both IIT and GNWT, including GNWT predictions around stimulus-offset ignition and some prefrontal representations.

**Transfer boundary:** this neither proves nor disproves Frankenstein's engineering workspace, Global J-Space, GWT-inspired coordination, consciousness, or cognition. The useful transfer is test design: define genuinely divergent predictions and pass/fail interpretations before measurement where feasible.

Project discriminator shape:

```text
candidate mechanism
vs simpler countermechanism
vs lesion
vs shuffle
vs rescue
→ fixed task families + exact runtime identity + observed downstream outcomes
```

## ReAct

Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, arXiv:2210.03629 / ICLR 2023.

- https://arxiv.org/abs/2210.03629

ReAct interleaves reasoning traces with actions and observations. It is an external donor for closed observation/action-loop design, not evidence that the project's historical reflection/tool/effect architecture is superior.

Useful discriminator: compare observation/action interleaving with a matched tool-use baseline using the same model, tools, task families, token budget, action budget and outcome verification.

## Reflexion

Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, arXiv:2303.11366 (2023).

- https://arxiv.org/abs/2303.11366

Reflexion uses verbal feedback/reflection and episodic memory to alter later behavior. It supports the plausibility of reflection as a control operation, but does not prove unique causal value for Frankenstein reflection.

Project discriminator: lesion the explicit reflection step while holding model, retrieval, feedback, task family, action budget and token budget fixed. Measure whether corrections survive into later ACT/ASK/WAIT/re-observe transitions.

## Activation engineering / steering vectors

Zou et al., *Steering Language Models With Activation Engineering*, arXiv:2308.10248 (2023).

- https://arxiv.org/abs/2308.10248

Activation engineering demonstrates that inference-time interventions in model activations can alter behavior. This is methodological support for causal vector-intervention experiments only where the relevant activation interface is actually exposed.

Strict Global-J-Space boundary:

```text
external activation steering exists
!=
Frankenstein has activation-level access to Claude Code or another closed model
```

A current J-Space claim must bind exact checkpoint/tokenizer/runtime identity and the actually exposed intervention interface. Text/tool/session interfaces cannot be relabelled hidden-state access.

## SQLite WAL durability counterexample

Primary sources:

- https://www.sqlite.org/wal.html
- https://sqlite.org/releaselog/3_51_3.html

SQLite documents a rare WAL-reset corruption bug discovered and fixed in March 2026. The documented affected range is broadly SQLite 3.7.0 through 3.51.2 under a specific concurrent WAL writer/checkpoint race; the fix is in 3.51.3 and later, with selected backports.

This is **not** evidence that UnifiedDB was affected. It means concrete concurrent-WAL durability claims must bind at least:

- exact SQLite library/runtime version;
- journal mode;
- connection count;
- process/thread topology;
- checkpoint behavior;
- filesystem/runtime environment.

Database brand name alone is not durability evidence.

## NVIDIA CUDA Unified Memory

Primary source:

- https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html

CUDA Unified Memory is useful only as a systems-design analogy for reducing ownership/copy boundaries across compute domains. NVIDIA's documented behavior depends on platform/kernel/GPU/interconnect capabilities and may use hardware or software mechanisms for access and coherency.

Strict boundary:

```text
hardware/system memory coherence
!= SQLite transaction semantics
!= canonical evidence authority
!= model truth
```

The analogy may motivate fewer ownership boundaries; it cannot prove UnifiedDB semantics or HCU correctness.

## Transfer rule

The strongest reusable pattern across these sources is not “use GWT”, “use reflection”, or “use vectors”. It is:

1. bind the exact mechanism and exposed interface;
2. formulate a serious alternative explanation;
3. define predictions that differ;
4. lesion/shuffle/rescue or otherwise intervene where possible;
5. keep task/model/runtime provenance controlled;
6. observe real downstream outcomes;
7. preserve negative results;
8. promote only the scope that survived the discriminator.

Immediate Frankenstein applications:

- **Global J-Space/GWT:** truthful-vector vs shuffled-vector vs lesion vs rescue; no hidden-state claim without an exposed interface.
- **Reflection:** explicit-reflection lesion under matched budgets; measure ACT/ASK/WAIT/re-observe termination and later correction retention.
- **UnifiedDB:** exact SQLite version + WAL/concurrency topology before durability promotion.
- **Editing autonomy:** use the 672→87 direct-dispatch whole-file rewrite as an executable counterexample; compare preimage-bound structured/patch edits with whole-file regeneration on destructive-delta tests.

`EXTERNAL_PRIMARY + METHOD_PRESENT != PROJECT_RESULT_PRESENT`.
