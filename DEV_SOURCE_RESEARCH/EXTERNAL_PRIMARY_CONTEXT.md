# External Primary Context — What Transfers, What Does Not

This page keeps external literature separate from project evidence. It is here to improve hypothesis design, not to decorate internal claims with citations.

**Rule:** an external paper can justify a discriminator or analogy. It cannot convert Project Frankenstein / EntityOS / HCU source into measured runtime evidence.

## ReAct — observation/action interleaving

**Primary source:** Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023 / arXiv:2210.03629.  
`https://arxiv.org/abs/2210.03629`

The paper studies interleaving model-generated reasoning traces with task actions and new observations. Actions provide additional environment information that can update later plans.

### Transferable structure

```text
reason / plan
  -> act
  -> observe result
  -> update next decision
```

That supports the engineering value of **outcome re-entry**.

### Does not transfer automatically

ReAct does not establish Project Frankenstein's EffectGate semantics, canonical-state rules, UnifiedDB design, HCU architecture, or model-internal J-Space causality. It also does not turn a requested action into evidence that the action succeeded.

## Reflexion — feedback and episodic reflection

**Primary source:** Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, 2023 / arXiv:2303.11366.  
`https://arxiv.org/abs/2303.11366`

Reflexion studies agents that turn task feedback into linguistic reflections and keep those reflections in episodic memory to influence later trials.

### Transferable structure

```text
trial
  -> feedback
  -> bounded reflection artifact
  -> later retrieval
  -> changed next trial
```

This is relevant to the project hypothesis that reflection is useful when it changes later measurable behavior.

### Project-specific extension

Project Frankenstein's `reflection must have an exit` rule is stronger and operationally different. The project additionally requires a terminal transition such as ACT / ASK / WAIT / RE-OBSERVE and preserves effect/result evidence separately. Reflexion is background for the memory-feedback pattern, not evidence that the project's reflection architecture works.

### Counterhypothesis retained

An explicit reflection subsystem may add no causal value once retrieval, feedback, token budget and action opportunities are matched. The appropriate project test remains a lesion/control study, not citation count.

## Activation engineering — inference-time vector intervention

**Primary source:** Turner et al., *Steering Language Models With Activation Engineering*, 2023 / arXiv:2308.10248.  
`https://arxiv.org/abs/2308.10248`

The paper studies inference-time interventions on model activations, including Activation Addition (ActAdd), to steer model outputs.

### Transferable structure

It establishes that **activation-level intervention is a legitimate experimental method** for testing causal control of model behavior.

### Does not transfer automatically

It does not prove that the project's Global J-Space exists as an internal model variable, that one project's steering vector has the intended semantics, or that a multi-cell HCU fabric is causally coordinated through such a vector.

The project therefore still needs exact checkpoint/runtime identity and label-free, counterbalanced, disjoint intervention families with shuffle/lesion/rescue controls.

## Global Workspace / Global Neuronal Workspace

**Primary/review sources:**

- Bernard J. Baars, *Global workspace theory of consciousness: toward a cognitive neuroscience of human experience*, Prog Brain Res. 2005. DOI `10.1016/S0079-6123(05)50004-9`.
- Stanislas Dehaene & Jean-Pierre Changeux, *Experimental and Theoretical Approaches to Conscious Processing*, Neuron 70(2), 2011. DOI `10.1016/j.neuron.2011.03.018`.

The useful engineering analogy is **global availability / broadcast among distributed specialist processes**.

### Boundary

Current EntityOS/HCU does not require a claim of consciousness, subjective experience, or biological equivalence. Historical neuroscience-inspired names remain provenance. The project question is narrower: can a measurable shared coordination interface improve bounded computational behavior, and can that effect be causally isolated?

## SQLite WAL — storage semantics and current concurrency risk

**Primary source:** SQLite official WAL documentation.  
`https://www.sqlite.org/wal.html`

WAL changes SQLite's commit/checkpoint behavior and supports readers concurrent with a writer on the same host. The official documentation also records the **WAL-reset bug**, a rare multi-connection write/checkpoint race present through SQLite 3.51.2 and fixed in 3.51.3 (with selected earlier backports).

### Transferable requirement

Any release-grade project claim involving concurrent SQLite/WAL should bind the actual SQLite library version and the measured connection/checkpoint topology.

### Boundary

This is an external risk condition. Triggerword 3 has not established that EntityOS/GRID10 encountered this bug.

## NVIDIA CUDA Unified Memory — analogy only

**Primary source:** NVIDIA CUDA Programming Guide, Unified Memory.  
`https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/unified-memory.html`

Unified Memory reduces explicit CPU/GPU ownership and copy boundaries through a coherent memory programming model and managed migration/access behavior.

### Transferable analogy

Reducing ownership/copy boundaries can simplify a compute system.

### Non-transfer

GPU memory coherence is **not** SQLite semantics, evidence provenance, retrieval, canonical truth, or cognition. UnifiedDB may use the analogy only at the systems-design level: fewer competing state owners and fewer reconciliation boundaries.

## Research-method synthesis

These sources motivate five discriminators, none of which is already a project PASS:

| Project question | External method signal | Required project discriminator |
|---|---|---|
| Does verified outcome re-entry improve agency? | ReAct | matched action tasks with/without observed result re-entry |
| Does explicit reflection add unique value? | Reflexion | reflection lesion under matched retrieval/feedback/token/action budget |
| Can a vector channel causally steer the target model? | activation engineering | exact-runtime label-free shuffle/lesion/rescue intervention |
| Does a shared workspace improve coordination? | GWT/GNW | measured broadcast/uptake/re-entry with non-workspace controls |
| Is the canonical state substrate safe under concurrency? | SQLite WAL | exact-version/topology concurrency and recovery tests |

`EXTERNAL_PRIMARY + METHOD_PRESENT != PROJECT_RESULT_PRESENT`.
