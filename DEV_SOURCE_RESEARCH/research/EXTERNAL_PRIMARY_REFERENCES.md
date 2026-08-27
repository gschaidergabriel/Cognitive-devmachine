# External primary references

These sources are **methodology or systems analogies**. They are not Clay/Frankenstein runtime evidence and cannot promote EntityOS, HCU, J-Space or training claims.

## Global Workspace architecture

### Baars, 2005

Bernard J. Baars, “Global workspace theory of consciousness: toward a cognitive neuroscience of human experience.” *Progress in Brain Research* 150 (2005), 45–53. DOI: `10.1016/S0079-6123(05)50004-9`.

Primary index: https://pubmed.ncbi.nlm.nih.gov/16186014/

**Why it is useful here:** the paper places Global Workspace Theory in a cognitive-architecture / blackboard tradition where distributed knowledge sources can cooperate around globally available information.

**What it does not establish:** that Project Frankenstein, EntityOS/HCU or any language model is conscious or sentient. The project uses workspace ideas as an engineering coordination hypothesis only.

## CPU multiprocessing / oversubscription

### PyTorch multiprocessing best practices

Official documentation: https://docs.pytorch.org/docs/stable/notes/multiprocessing.html

PyTorch documents CPU oversubscription as a contention problem and recommends bounding subprocess thread count; for `N` available vCPUs and `M` processes, it gives `floor(N/M)` as the maximum per-process thread guideline in the illustrated CPU multiprocessing case.

**Project use:** this is method context for the 2026-08-27 GRID10 matched thread A/B. It is not a substitute for the project’s measured 4-process/4-vCPU result and must not be extrapolated to unmeasured topologies.

## SQLite write-ahead logging

### SQLite WAL

Official documentation: https://www.sqlite.org/wal.html

SQLite documents that WAL permits readers and a writer to proceed concurrently, while only one writer can exist at a time. WAL relies on same-host shared memory and is not intended for use over a network filesystem.

**Project use:** storage/concurrency facts relevant to SQLite/WAL Fabric and UnifiedDB implementation choices.

**Boundary:** SQLite’s storage semantics do not by themselves establish EntityOS causal identity, capability authority, effect safety or distributed multi-host correctness.

## NVIDIA Unified Memory

### CUDA Programming Guide — Unified Memory

Official documentation: https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html

CUDA Unified Memory allows managed memory to be accessible by CPU and GPU, with coherence/migration behavior depending on system capabilities.

**Project use:** analogy for reducing explicit ownership/copy boundaries between compute domains.

**Boundary:** hardware memory coherence is not database semantics. It does not prove UnifiedDB correctness and must never be cited as evidence that a database fact is true.

## Variable binding

### Wu, Geiger & Millière, ICML 2025

Yiwei Wu, Atticus Geiger, Raphaël Millière, “How Do Transformers Learn Variable Binding in Symbolic Programs?” *Proceedings of ICML 2025*, PMLR 267:67284–67299.

Primary: https://proceedings.mlr.press/v267/wu25j.html

The studied Transformer progressed from random prediction through a heuristic phase to a systematic variable-binding mechanism; causal interventions implicated residual-stream memory and attention-based routing.

**Project use:** motivates explicit tests for dynamic variable/code binding rather than assuming correct binding from aggregate accuracy.

**Boundary:** this is not Qwen-, Clay- or HCU-specific causal evidence.

## Demonstration shortcuts / input-label relations

### Jang et al., NAACL 2024

Joonwon Jang, Sanghwan Jang, Wonbin Kweon, Minjin Jeon, Hwanjo Yu, “Rectifying Demonstration Shortcut in In-Context Learning.” NAACL 2024, pp. 4294–4321. DOI: `10.18653/v1/2024.naacl-long.242`.

Primary: https://aclanthology.org/2024.naacl-long.242/

The work studies a failure mode where models rely on semantic priors in demonstrations rather than the intended input-label relationship, and evaluates calibration under ordinary and semantically unrelated-label settings.

**Project use:** motivates episode-local remapping, opaque labels/codes, nuisance controls and counterbalanced binding tests.

**Boundary:** it does not prove that any current Frankenstein training corpus is shortcut-free.

## Reference law

External literature may:

- suggest a mechanism;
- suggest a counterhypothesis;
- motivate a control;
- provide a systems constraint;
- help design a discriminator.

It may not:

- turn a project hypothesis into an observation;
- replace exact current source inspection;
- replace an exact project runtime receipt;
- promote component evidence to whole-product PASS;
- turn an analogy into implementation truth.
