# External research notes — analogies, not project evidence

These sources help frame engineering choices. They do **not** prove that Project Frankenstein implements the corresponding mechanism, and they do not promote any EntityOS/HCU runtime claim.

## Acting, observing, and leaving the reasoning loop

### ReAct — reasoning interleaved with actions

**Class:** `EXTERNAL_PRIMARY`  
Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023 / arXiv:2210.03629.  
https://arxiv.org/abs/2210.03629

ReAct studies interleaving reasoning traces with task-specific actions so that actions can obtain information from an external environment and later reasoning can update the plan.

**Project relevance:** supports the general engineering direction that cognition should not terminate in narration alone. Frankenstein's stronger project-specific requirement is that reflection exits into ACT / ASK / WAIT / re-observe or another measurable state transition and that world effects remain separately verified.

### Reflexion — feedback stored for later decisions

**Class:** `EXTERNAL_PRIMARY`  
Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, NeurIPS 2023 / arXiv:2303.11366.  
https://arxiv.org/abs/2303.11366

Reflexion uses linguistic feedback and an episodic memory buffer to affect decisions on later trials without requiring a weight update for every correction.

**Project relevance:** a useful comparison for self-reflection + memory. It does not establish that any Frankenstein reflection is correct; the project still requires provenance, behavioral effect, and a terminating control transition.

## Global workspace as an architectural analogy

### Global Workspace Theory / IDA

**Class:** `EXTERNAL_PRIMARY`  
Baars & Franklin, *An architectural model of conscious and unconscious brain functions: Global Workspace Theory and IDA*, Neural Networks 20(9), 2007. DOI: 10.1016/j.neunet.2007.09.013.  
https://pubmed.ncbi.nlm.nih.gov/17998071/

**Project relevance:** global-workspace ideas are useful for selective broadcasting / bounded coordination abstractions. They are not evidence that HCU/J-Space is conscious or that a workspace readout is canonical truth. The project treats Global J-Space/GWT as an empirical causal interface hypothesis.

## Canonical state substrate

### SQLite Write-Ahead Logging

**Class:** `EXTERNAL_PRIMARY`  
SQLite official documentation, *Write-Ahead Logging*.  
https://www.sqlite.org/wal.html

SQLite WAL provides a concrete systems mechanism for durable transactional state with concurrent readers and a serialized write path, plus explicit checkpoint behavior.

**Project relevance:** supports SQLite/WAL as a pragmatic building block for a coherent local authority substrate. It does not by itself prove the project's higher-level schemas, provenance, effect authority, Emergent Retrieval, or recovery semantics.

## Unified Memory analogy — use carefully

### NVIDIA CUDA Unified Memory

**Class:** `EXTERNAL_PRIMARY`  
NVIDIA, *CUDA Programming Guide — Unified and System Memory / Unified Memory*.  
https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html  
https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/unified-memory.html

CUDA Unified Memory provides a programming model in which managed memory can be accessed by CPU and GPU, with coherence/migration behavior depending on platform capabilities.

**Project relevance:** only a **systems-design analogy**: reduce ownership/copy boundaries so multiple compute components can operate over a coherent substrate. Hardware virtual memory, page migration, or cache coherence are not database semantics and do not explain UnifiedDB's epistemic or effect rules.

## Possible-world / world-model research already fused in the archive

The existing C-GRF research receipt records primary sources including MuZero, DreamerV3, V-JEPA 2, task-relevant robust world-model representation work, PETS, causal representation work, and uncertainty-aware planning. Its main surviving engineering lesson is deliberately narrower than “simulate reality”:

- task-sufficient latent models can be more useful than full reconstruction;
- generated plausibility can coexist with poor transition/world consistency;
- uncertainty and model disagreement need explicit handling;
- simulation is a costly cognitive action and should be selectively allocated;
- observational, interventional, and counterfactual semantics must not be collapsed;
- generated branches remain non-factual until reconciled with observed outcomes.

See the canonical archive receipt:
`research_entity/trigger_runs/clayresearch/clayresearch-20260810T2324p0700-chatgpt-secondary-generative-reality-framework/RESEARCH_RECEIPT.json`.

## External-source discipline

External literature can:

- motivate a mechanism;
- supply a comparison baseline;
- suggest a falsifier or measurement;
- identify a known failure mode.

It cannot:

- establish that the project source implements the mechanism;
- create runtime evidence;
- convert a historical result into current authority;
- convert a bio-inspired analogy into a consciousness claim;
- waive the project's deterministic state/effect boundaries.
