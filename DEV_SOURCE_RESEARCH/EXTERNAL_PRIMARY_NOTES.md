# External primary notes used by Triggerword 3

These are **external references**, not project runtime evidence. They constrain analogies and engineering claims; they do not promote EntityOS/HCU acceptance.

## PyTorch multiprocessing / CPU oversubscription

Primary vendor documentation:

- https://docs.pytorch.org/docs/stable/notes/multiprocessing.html

PyTorch documents CPU oversubscription as a multiprocessing failure mode and recommends bounding per-process threads to approximately `floor(N/M)` for `N` available vCPUs and `M` processes. This is consistent with — but does not independently prove — the project’s measured 4-process/4-vCPU result in which 1 thread/process outperformed 2 threads/process and 4 threads/process timed out.

Evidence label: `EXTERNAL_PRIMARY` for the vendor guidance; `PROJECT_MEASUREMENT` for the project A/B.

## SQLite WAL

Primary SQLite documentation:

- https://www.sqlite.org/wal.html

SQLite’s WAL mode maintains a write-ahead log as part of database state while connections are active; the WAL must be handled as part of the database’s persistent state when copying/moving a live database. This supports disciplined snapshot/backup handling for SQLite/WAL project substrates but says nothing by itself about EntityOS semantics, causal identity or recovery correctness.

SQLite also documents a rare WAL-reset corruption bug in affected SQLite versions and concurrency conditions; any project claim about exposure must first bind the actual SQLite version, journal mode and concurrency pattern rather than infer vulnerability from “uses WAL”.

Evidence label: `EXTERNAL_PRIMARY`.

## NVIDIA CUDA Unified Memory — analogy boundary

Primary NVIDIA CUDA documentation:

- https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html
- https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/unified-memory.html

CUDA Unified Memory provides memory accessible by CPU and GPU, with coherence/migration behavior depending on platform capabilities such as HMM or ATS. Project documentation may use this only as a **systems-design analogy** for reducing ownership/copy boundaries. GPU/CPU memory coherence is not database semantics, provenance, causal identity, or canonical truth authority.

Evidence label: `EXTERNAL_PRIMARY` for CUDA behavior; `INFERENCE/ANALOGY` for architectural transfer into EntityOS.

## Global neuronal workspace lineage

Primary/authoritative literature references:

- Dehaene, Kerszberg & Changeux (1998), *A neuronal model of a global workspace in effortful cognitive tasks*, PNAS 95(24), 14529–14534. DOI: `10.1073/pnas.95.24.14529`.
- Mashour, Roelfsema, Changeux & Dehaene (2020), *Conscious Processing and the Global Neuronal Workspace Hypothesis*, Neuron. DOI: `10.1016/j.neuron.2020.01.026`.

The GNW lineage distinguishes globally available workspace dynamics from specialized processors. It is useful conceptual lineage for modular/global coordination. It is **not** evidence that Project Frankenstein, EntityOS, HCU or Global J-Space implements biological GNW, and the project does not need a consciousness/sentience claim for its engineering architecture.

Evidence label: `EXTERNAL_PRIMARY` for the neuroscience literature; `OPEN_HYPOTHESIS` for transfer into artificial-agent architecture.

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
