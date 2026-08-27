# External primary references — bounded analogy map

This file is deliberately small. External literature can sharpen hypotheses and engineering analogies, but it does not create Project Frankenstein runtime evidence.

## Global Workspace / Global Neuronal Workspace

### Baars, Franklin & Ramsoy (2013)

**Primary source:** Bernard J. Baars, Stan Franklin, Thomas Zoega Ramsoy. “Global workspace dynamics: cortical ‘binding and propagation’ enables conscious contents.” *Frontiers in Psychology* 4:200 (2013). DOI: `10.3389/fpsyg.2013.00200`.

Project use:

- useful external conceptual ancestor for a global workspace as a binding/broadcast coordination mechanism;
- useful for generating architecture hypotheses about distributed specialist modules and a shared workspace.

Boundary:

- `EXTERNAL_PRIMARY`, not project evidence;
- neuroscience claims do not prove a software Global J-Space/GWT mechanism;
- Project Frankenstein does not require consciousness/sentience claims;
- software causality must be established with project-specific lesion/shuffle/rescue/nuisance controls.

### Mashour, Roelfsema, Changeux & Dehaene (2020)

**Primary review / theory source:** George A. Mashour, Pieter Roelfsema, Jean-Pierre Changeux, Stanislas Dehaene. “Conscious Processing and the Global Neuronal Workspace Hypothesis.” *Neuron* 105(5):776–798 (2020). DOI: `10.1016/j.neuron.2020.01.026`; PMID `32135090`.

Project use:

- external background for recurrent processing and broad availability/broadcast ideas;
- useful source of counterfactual experimental thinking around what a workspace mechanism should change.

Boundary:

- biological GNW and software GWT/J-Space are not the same object;
- a biological analogy cannot promote local J-Space/model runtime credit.

## SQLite / WAL

### SQLite official WAL documentation

Official source: `https://www.sqlite.org/wal.html`

Project use:

- primary implementation documentation for SQLite write-ahead logging, commit/checkpoint behavior and concurrency boundaries;
- relevant when evaluating durable UnifiedDB-style SQLite designs.

Boundary:

- WAL provides database transaction/recovery/concurrency machinery;
- WAL does not define Project Frankenstein truth semantics, provenance, causal identity, memory policy, or effect authority;
- SQLite correctness does not make an application schema semantically correct.

### SQLite database file-format documentation

Official source: `https://www.sqlite.org/fileformat.html`

Project use:

- primary source for persistent database/WAL file-format and recovery considerations.

Boundary:

- storage-format guarantees must not be inflated into application-level causal or epistemic guarantees.

## NVIDIA CUDA Unified Memory

### CUDA Programming Guide — Unified Memory

Official source: `https://docs.nvidia.com/cuda/cuda-programming-guide/`

The current CUDA guide documents multiple Unified Memory paradigms, including hardware- and software-coherent cases.

Project use is **analogy only**:

> reduce ownership/copy boundaries so heterogeneous compute can operate over a more coherent accessible substrate.

Boundary:

- CUDA Unified Memory is a hardware/software memory-management model;
- UnifiedDB is a database/application authority design;
- a shared/combined addressability model is not a transaction, provenance, causal-identity, retrieval, or truth model;
- no EntityOS/HCU/Frankenstein performance claim follows from the analogy.

## How external references may be used

Allowed:

- hypothesis generation;
- design vocabulary;
- known mechanism constraints;
- test inspiration;
- counterhypotheses;
- implementation facts about the cited external technology.

Not allowed:

- converting analogy into project measurement;
- citing a neuroscience theory as proof of software cognition;
- citing CUDA coherence as proof of UnifiedDB semantics;
- citing SQLite WAL as proof that current Frankenstein uses UnifiedDB correctly;
- upgrading `OPEN_HYPOTHESIS` to `PROJECT_MEASUREMENT` without project execution evidence.

## Evidence label

Everything in this file is `EXTERNAL_PRIMARY` or a clearly marked project-side `INFERENCE` about how the source may inform engineering. External sources remain outside canonical Clay/EntityOS/Frankenstein authority.