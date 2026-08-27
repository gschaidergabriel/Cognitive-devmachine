# External primary notes used by Triggerword 3

These are **external references, not project runtime evidence**. They constrain analogies and engineering claims; they do not promote EntityOS/HCU acceptance.

## PyTorch multiprocessing / CPU oversubscription

Primary vendor documentation:

- https://docs.pytorch.org/docs/stable/notes/multiprocessing.html

PyTorch documents CPU oversubscription as a multiprocessing failure mode and recommends bounding per-process threads to approximately `floor(N/M)` for `N` available vCPUs and `M` processes. This is consistent with — but does not independently prove — the project’s measured 4-process/4-vCPU result in which 1 thread/process outperformed 2 threads/process and 4 threads/process timed out.

Evidence label: `EXTERNAL_PRIMARY` for the vendor guidance; `PROJECT_MEASUREMENT` for the project A/B.

## SQLite WAL

Primary SQLite documentation:

- https://www.sqlite.org/wal.html

SQLite’s WAL mode maintains a write-ahead log as part of database state while connections are active; the WAL must be handled as part of the database’s persistent state when copying/moving a live database. This supports disciplined snapshot/backup handling for SQLite/WAL project substrates but says nothing by itself about EntityOS semantics, causal identity or recovery correctness.

Evidence label: `EXTERNAL_PRIMARY`.

## NVIDIA CUDA Unified Memory — analogy boundary

Primary NVIDIA CUDA documentation:

- https://docs.nvidia.com/cuda/cuda-programming-guide/02-basics/understanding-memory.html
- https://docs.nvidia.com/cuda/cuda-programming-guide/04-special-topics/unified-memory.html

CUDA Unified Memory provides managed memory accessible by CPU and GPU, with coherence/migration behavior depending on platform capabilities such as HMM or ATS. Project documentation may use this only as a **systems-design analogy** for reducing ownership/copy boundaries. GPU/CPU memory coherence is not database semantics, provenance, causal identity, or canonical truth authority.

Evidence label: `EXTERNAL_PRIMARY` for CUDA behavior; `INFERENCE/ANALOGY` for architectural transfer into EntityOS.

## Global neuronal workspace lineage

Primary literature references:

- Dehaene, Kerszberg & Changeux (1998), *A neuronal model of a global workspace in effortful cognitive tasks*, PNAS 95(24), 14529–14534. DOI: `10.1073/pnas.95.24.14529`.
- Mashour, Roelfsema, Changeux & Dehaene (2020), *Conscious Processing and the Global Neuronal Workspace Hypothesis*, Neuron. DOI: `10.1016/j.neuron.2020.01.026`.

The GNW lineage distinguishes a globally accessible workspace from specialized processors. This is useful conceptual lineage for modular/global coordination. It is **not** evidence that Project Frankenstein, EntityOS, HCU or Global J-Space implements biological GNW, and the project does not need a consciousness/sentience claim for its engineering architecture.

Evidence label: `EXTERNAL_PRIMARY` for the neuroscience papers; `OPEN_HYPOTHESIS` for any transfer into artificial agent architecture.

## Agent reflection/action analogies

Primary research references:

- Yao et al., *ReAct: Synergizing Reasoning and Acting in Language Models*, ICLR 2023 / arXiv `2210.03629`.
- Shinn et al., *Reflexion: Language Agents with Verbal Reinforcement Learning*, arXiv `2303.11366`.

These works are useful external comparison points for interleaving reasoning/action and storing feedback that changes later behavior. They do not prove Frankenstein's reflection loop, memory substrate, effect authority, or long-horizon agency. Project-side claims still require exact state/effect/outcome evidence and bounded exit from recursive reflection.

Evidence label: `EXTERNAL_PRIMARY` for the papers; `INFERENCE/ANALOGY` for project transfer.

## Safe repository editing — Git patch semantics

Primary vendor documentation:

- https://git-scm.com/docs/git-apply

Git documents `git apply` as failing the whole patch without touching the working tree when some hunks do not apply, unless partial application is explicitly requested with `--reject`. The `-C<n>` option can require surrounding context lines to match around each change.

Transfer into Triggerword-3 repository curation:

```text
structural similarity
  patch is applied against a concrete preimage with contextual anchors

structural difference
  Git hunk applicability is textual; it does not prove semantic correctness

assumption that transfers
  stale or mismatched context should fail closed rather than silently reconstruct a whole file

assumption that does not transfer
  successful patch application != behavior preserved

cheapest project-side falsifier
  stale-preimage, out-of-scope-region and >50%-size semantic-corruption negative controls
```

This supports preimage-bound patch/diff mutation as a safer primitive than unconstrained whole-file regeneration after the 2026-08-28 destructive-rewrite counterexample. It does **not** establish that every applicable patch is correct.

Evidence label: `EXTERNAL_PRIMARY` for Git behavior; `INFERENCE/ENGINEERING_TRANSFER` for the project editing contract.

## SWE-agent — Agent-Computer Interface as an engineering variable

Primary research and project documentation:

- Yang et al., *SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering*, arXiv `2405.15793`.
- https://github.com/SWE-agent/SWE-agent/blob/main/docs/background/aci.md

SWE-agent treats the agent-computer interface itself as an experimental design variable. Its paper reports large performance differences from a custom ACI, while the project documentation describes bounded file viewing/editing and syntax validation at edit time.

Transfer boundary for Frankenstein:

```text
external result
  interface design changes software-engineering-agent behavior/performance

project use
  prefer explicit inspect -> bounded edit -> validate interfaces over opaque whole-file reconstruction

non-transfer
  SWE-agent benchmark gains do not prove Frankenstein correctness, safety or repository acceptance

project falsifier
  compare bounded/preimage-bound editing against unconstrained reconstruction on fixed edit families,
  including preservation failures and stale-source controls
```

Evidence label: `EXTERNAL_PRIMARY` for the paper/project docs; `OPEN_HYPOTHESIS` for performance/safety transfer into Project Frankenstein.

## 2026 code-edit interface research — inspection/edit context separation

Current primary research note, checked 2026-08-28:

- Zhang et al., *SWE-Edit: Rethinking Code Editing for Efficient SWE-Agent*, arXiv `2604.26102`.

SWE-Edit identifies context coupling between inspection, modification planning and edit execution as a software-engineering-agent failure mode and evaluates a Viewer/Editor decomposition. The reported benchmark gains are external and model/system-specific.

This is relevant to two Project Frankenstein hypotheses:

1. large mixed contexts can contaminate or dilute edit execution;
2. a narrower edit executor operating from an explicit plan and exact source slice may reduce accidental reconstruction damage.

Counterhypothesis: decomposition can hide important global dependencies or transfer planning errors into a clean editing context. Therefore separation itself is not a safety proof; cross-file dependency and preservation tests remain necessary.

Evidence label: `EXTERNAL_PRIMARY` for the paper; `OPEN_HYPOTHESIS` for transfer into Frankenstein editing architecture.

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
