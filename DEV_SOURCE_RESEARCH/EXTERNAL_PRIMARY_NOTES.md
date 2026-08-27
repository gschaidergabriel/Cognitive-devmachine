# External primary notes used by Triggerword 3

These are **external references, not project runtime evidence**. They constrain analogies and engineering claims; they do not promote EntityOS/HCU acceptance.

## PyTorch multiprocessing / CPU oversubscription

Primary vendor documentation:

- https://docs.pytorch.org/docs/stable/notes/multiprocessing.html

PyTorch documents CPU oversubscription as a multiprocessing failure mode and recommends bounding per-process thread use relative to available CPU resources. This is consistent with — but does not independently prove — the project's measured 4-process/4-vCPU result in which 1 thread/process outperformed 2 threads/process and 4 threads/process completed no samples in the experiment window.

Evidence label: `EXTERNAL_PRIMARY` for vendor guidance; `PROJECT_MEASUREMENT` for the project A/B.

Transfer boundary: generic oversubscription guidance does not establish a globally optimal thread count for HCU/GRID. The measured result remains topology-specific.

## SQLite WAL

Primary SQLite documentation:

- https://www.sqlite.org/wal.html

SQLite's WAL documentation describes write-ahead logging, reader/writer behavior, checkpointing and recovery constraints. This is relevant to disciplined handling of SQLite/WAL project substrates but says nothing by itself about EntityOS semantics, causal identity, archive completeness or application-level recovery correctness.

Evidence label: `EXTERNAL_PRIMARY`.

Transfer boundary: `SQLite WAL exists` is not equivalent to `UnifiedDB durability is proven`. Bind the exact SQLite runtime/version, journal mode, concurrency topology and project recovery procedure before a concrete durability claim.

## NVIDIA CUDA Unified Memory — analogy boundary

Primary NVIDIA CUDA documentation:

- https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html
- https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/unified-memory.html

CUDA Unified Memory provides managed/system-memory mechanisms for CPU/GPU access with platform-dependent coherence, migration and performance behavior. Project documentation may use this only as a **systems-design analogy** for reducing ownership/copy boundaries.

Evidence label: `EXTERNAL_PRIMARY` for CUDA behavior; `INFERENCE/ANALOGY` for architectural transfer into EntityOS.

Do not equate:

```text
GPU/CPU memory coherence = database semantics
page migration = causal provenance
one address space = one truth authority
hardware coherence = EffectGate/EffectJournal correctness
```

## Global neuronal workspace lineage

Primary literature references:

- Dehaene, Kerszberg & Changeux (1998), *A neuronal model of a global workspace in effortful cognitive tasks*, PNAS 95(24), 14529–14534. DOI: `10.1073/pnas.95.24.14529`.
- Dehaene & Changeux (2011), *Experimental and theoretical approaches to conscious processing*, Neuron 70(2). DOI: `10.1016/j.neuron.2011.03.018`.
- Mashour, Roelfsema, Changeux & Dehaene (2020), *Conscious Processing and the Global Neuronal Workspace Hypothesis*, Neuron. DOI: `10.1016/j.neuron.2020.01.026`.

The GNW lineage distinguishes globally accessible/broadcast workspace dynamics from specialized processors. This is useful conceptual lineage for modular/global coordination.

It is **not** evidence that Project Frankenstein, EntityOS, HCU or Global J-Space implements biological GNW. The project does not need a consciousness, sentience or subjective-experience claim for its engineering architecture.

Evidence label: `EXTERNAL_PRIMARY` for the neuroscience papers; `OPEN_HYPOTHESIS` for any transfer into artificial-agent architecture.

## ReAct / Reflexion — reflection and action analogies

Primary papers:

- Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023, arXiv `2210.03629`.
- Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, NeurIPS 2023, arXiv `2303.11366`.

ReAct is relevant as an external example of interleaving reasoning with environment actions. Reflexion is relevant as an external example of retaining feedback in episodic memory to alter later behavior without weight updates.

Neither establishes Project Frankenstein's stricter engineering claims about typed effect authority, verified outcome re-entry, UnifiedDB, provenance, or mandatory reflection termination into `ACT / ASK / WAIT / RE-OBSERVE`.

Evidence label: `EXTERNAL_PRIMARY` for the papers; `INFERENCE/ANALOGY` for transfer into Project Frankenstein.

## Transfer rule

For every external analogy, record:

```text
external mechanism
-> structural similarity
-> structural difference
-> assumptions that transfer
-> assumptions that do not transfer
-> cheapest project-side falsifier
```

No external paper or vendor document can substitute for exact project source/runtime evidence.
