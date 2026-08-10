# Hypofusion R6 — External Evidence Ledger

Run: `hypofusion-20260810T1631p0700-chatgpt-secondary-r6`

Evidence is used as independent analogue/counterevidence/failure-mode input, never as direct proof of a Clay/Frank mechanism.

## E6-01 — MLIR Dialect Conversion
- Source class: OFFICIAL_TECHNICAL_DOCUMENTATION / independent implementation precedent.
- Source: LLVM MLIR, `Dialect Conversion` documentation, retrieved 2026-08-10.
- Mechanism: explicit legal/dynamic/illegal operation status; partial conversion can retain unknown operations; full conversion succeeds only when all required operations are legalized; conversion can roll back failed legalization paths.
- R6 classification: `IMPLEMENTATION_PRECEDENT | PARTIAL_ANALOGUE`.
- Effect: strengthens H-HF6-01 direction that preservation and executability/legality are distinct obligations. Does not prove ClayCode must copy MLIR's API or class taxonomy.

## E6-02 — SLSA provenance
- Source class: OFFICIAL_SPECIFICATION.
- Source: SLSA v1.2 provenance/build provenance specification, retrieved 2026-08-10.
- Mechanism: artifact subject identity is bound with builder/build-definition/input provenance; verification checks identity and provenance rather than treating one semantic hash as the whole release claim.
- R6 classification: `PARTIAL_ANALOGUE | IMPLEMENTATION_PRECEDENT`.
- Effect: preserves H-HF5-01 multi-layer evidence-identity contract; no further transform required in R6.

## E6-03 — SQLite WAL/checkpoint semantics
- Source class: OFFICIAL_TECHNICAL_DOCUMENTATION.
- Source: SQLite `Write-Ahead Logging` documentation, retrieved 2026-08-10.
- Mechanism: readers and writers can overlap, but there is one writer; checkpoints interact with active readers, can be delayed/starved, and some WAL operations can return `SQLITE_BUSY`; checkpoint/durability policy trades latency against durability/resource behavior.
- R6 classification: `FAILURE_MODE | IMPLEMENTATION_PRECEDENT`.
- Effect: keeps H-HF5-04 observer-passivity and H-HF5-05 measured commit-policy tests open; no architecture choice by citation.

## E6-04 — SparseCL contradiction retrieval
- Source class: PRIMARY_RESEARCH_PREPRINT / later conference-line implementation evidence to be independently checked at promotion time.
- Source: Xu et al., `SparseCL: Sparse Contrastive Learning for Contradiction Retrieval`, arXiv:2406.10746.
- Mechanism: ordinary similarity retrieval is poorly aligned with explicit contradiction retrieval; specialized embeddings/sparsity are evaluated on contradiction-focused corpora.
- R6 classification: `BETTER_MECHANISM_CANDIDATE | PARTIAL_ANALOGUE`.
- Effect: transforms the carried counterevidence-preserving retrieval hypothesis into H-HF6-03: explicit contradiction retrieval/abstention should be tested against relevance-only and diversified baselines.

## E6-05 — Reward prediction-error structure
- Source class: PRIMARY_RESEARCH.
- Sources already independently triangulated in current project state: Lee et al., Nature Neuroscience 2024 feature-specific RPE; distributional PFC work (Nature Neuroscience 2024); Sousa et al., Nature 2025 joint time/magnitude reward structure; Masset et al., Nature 2025 multiple RL timescales.
- R6 classification: `PARTIAL_ANALOGUE`.
- Effect: strengthens plausibility of typed/distributional/multihorizon reward candidates but does not select them for Frank. H-HF5-02 remains baseline-gated against measured historical and simpler scalar causal-outcome baselines.

## E6-06 — Higher-order representation sensitivity
- Source class: PRIMARY_RESEARCH.
- Sources: higher-order-network / hypergraph-simplicial dynamics literature already triangulated in R6 live search.
- Mechanism: pairwise versus higher-order representation can materially alter predicted dynamics; representation is not automatically behavior-neutral.
- R6 classification: `THEORY_CRITIQUE | PARTIAL_ANALOGUE`.
- Effect: strengthens the Hyperposition/backend-equivalence falsifier; no claim that Frank requires a particular hypergraph formalism.

## E6-07 — Directed workspace/broadcast signatures
- Source class: PRIMARY_RESEARCH.
- Source: recent Network Neuroscience work on directed network signatures compatible with Global Neuronal Workspace broadcasting, triangulated in R6 live search.
- Mechanism: generic integration/connectivity is not sufficient evidence of directed global broadcasting.
- R6 classification: `PARTIAL_ANALOGUE | THEORY_CRITIQUE`.
- Effect: strengthens existing Clay GWT separation of selection, delivery, reconstruction, use, effect and re-entry; no new R6 hypothesis required.

## Anti-echo disposition
Project-internal repetition across ClayCode/ClayGraph/UnifiedDB/live-fusion branches is one ancestry unless an execution or independent mechanism source establishes otherwise. External analogues above change falsifiers and test obligations; none promotes a scientific claim or canonical architecture.
