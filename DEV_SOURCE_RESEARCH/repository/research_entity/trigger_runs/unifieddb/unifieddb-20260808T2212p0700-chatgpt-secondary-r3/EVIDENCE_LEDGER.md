# UnifiedDB U2 — External Evidence Ledger

Run: `unifieddb-20260808T2212p0700-chatgpt-secondary-r3`

This ledger separates peer-reviewed/conference, preprint, official documentation, implementation and practitioner evidence. External convergence supports mechanism classes; it does not independently replicate FRANK/Clay/UnifiedDB end-to-end.

## High-value database/systems evidence

### Selection integrity — preprint, direct mechanism convergence

- Fei et al., **Selection Integrity for LLM Graph Memory: An Accumulability Criterion for Information-Flow-Blind Retrieval**, arXiv:2606.12290, 2026.
- URL: https://arxiv.org/abs/2606.12290
- Relevance: record provenance can remain authentic while mutable graph structure changes which records are selected. `AuthSelect` recomputes selection on authenticated structure and reports 2–3% latency in the authors' evaluated systems.
- Boundary: this is external preprint evidence. U2's E2B PPR-like test reproduces only the mechanism class under a constructed selector; it is not independent replication of the paper's systems/results.

### PostgreSQL-V — CIDR 2026 + open implementation

- Liu et al., **Fast Vector Search in PostgreSQL: A Decoupled Approach**, CIDR 2026.
- Proceedings: https://www.vldb.org/cidrdb/2026/fast-vector-search-in-postgresql-a-decoupled-approach.html
- Implementation: https://github.com/purduedb/PostgreSQL-V
- Relevance: one integrated relational query surface can coexist with a vector index physically decoupled from the core page-oriented engine; the paper reports specialized-level vector performance and up to 8.9x over pgvector in its experiments.
- Transfer: physical placement must separate query composition from index storage placement.

### DecoupleVS / vector-index storage decoupling — 2026 preprint

- Ren et al., **Decoupling Vector Data and Index Storage for Space Efficiency**, arXiv:2604.09173.
- URL: https://arxiv.org/abs/2604.09173
- Relevance: co-locating vector data and auxiliary index metadata can cause storage/read/write amplification; the authors report up to 58.7% storage reduction with their decoupled framework.
- Transfer: even inside one logical vector subsystem, vector payload and index metadata need not share physical placement.

### AkasicDB — SIGMOD 2026 demo / counterevidence toward physical fusion

- **AkasicDB: Demonstrating Omni RAG with a Unified Vector-Graph-Relational DBMS**, SIGMOD 2026 demo.
- Program: https://2026.sigmod.org/sigmod_demos.shtml
- Relevance: demonstrates the opposite design pressure: vector, graph and relational operators can be integrated into one DBMS and one query plan.
- Boundary: this is a demo publication and does not establish that physical fusion is universally better. It prevents UnifiedDB from treating decoupling as dogma.

### Cephalopod — CIDR 2025

- Loughlin & Pirk, **Cephalopod – Virtual Data Model Composition through Partial Query Translation**, CIDR 2025.
- Program: https://www.cidrdb.org/cidr2025/program.html
- Relevance: supports partial/virtual query translation rather than requiring full physical transformation. This is close to U2's per-subplan placement direction.

### Graph-relational typed query semantics — 2025 preprint

- Sullivan et al., **Querying Graph-Relational Data**, arXiv:2507.16089.
- URL: https://arxiv.org/abs/2507.16089
- Relevance: formally typed graph-relational semantics can compile to PostgreSQL rather than requiring the semantic model to equal the physical store.

### Cross-model query equivalence — 2025 preprint

- He et al., **Graphiti: Bridging Graph and Relational Database Queries**, arXiv:2504.03182.
- URL: https://arxiv.org/abs/2504.03182
- Relevance: query equivalence can be checked across graph and relational models modulo a transformer; experiments found subtle bugs in examples/tutorials.
- Transfer: UnifiedDB lowerers should be validated against typed reference semantics instead of trusting translation by construction.

### Living Databases — 2026 preprint

- Deshpande, **Living Databases: A Unified Model for Continuous Schema Evolution, Versioning, and Transformations**, arXiv:2605.00676.
- URL: https://arxiv.org/abs/2605.00676
- Relevance: proposes one abstraction for evolving data, transformations, versions, provenance, dependent views and derived artifacts.
- Transfer: derivation-program/version identity should be first class in replay and view evolution.

### DBSP / incremental view maintenance — peer-reviewed lineage

- Feldera/DBSP documentation and publications: https://docs.feldera.com/literature/papers/
- Relevance: rich query views can be maintained incrementally from input deltas rather than recomputed from full history.
- Transfer: graph/vector/FTS/materialized cognitive views should be evaluated as incremental derivations where applicable.

### FoundationDB transaction semantics — authoritative documentation

- FoundationDB Java API transaction docs: https://apple.github.io/foundationdb/javadoc/com/apple/foundationdb/Transaction.html
- Relevance: explicitly models a transaction as a mutable snapshot with atomicity, isolation and durability at commit.
- Transfer: supports a clearly defined authoritative commit domain, not pretending all derived stores are atomically synchronized.

### SQLite attached-database crash atomicity — authoritative documentation

- SQLite `ATTACH DATABASE`: https://sqlite.org/lang_attach.html
- Relevance: cross-file transactions are not crash-atomic in all modes; under WAL, files can diverge if a host crash occurs mid-commit.
- Transfer: a logical unified API must not overstate cross-store atomicity.

### Apache Arrow C Data Interface — authoritative documentation

- https://arrow.apache.org/docs/format/CDataInterface.html
- Relevance: supports zero-copy sharing between independent runtimes/components **in the same process**; distinct-process sharing and persistence are explicit non-goals.
- Transfer: same-process compute/data exchange and cross-process IPC remain separate placement dimensions.

### Vector-database benchmark — peer-reviewed 2026

- **A unified benchmarking framework for vector databases in scalable embedding-based image retrieval systems**, Frontiers in Computer Science, 2026.
- Relevance: no single evaluated vector system dominated all lifecycle dimensions; workload-aware benchmarking matters.
- Transfer: UnifiedDB must not select one physical vector implementation from semantic arguments alone.

## Practitioner / implementation evidence — anecdotal, not promotion evidence

- 2026 Android/embedded database discussions show active work on LSM/WAL/mmap/vector designs and embedded graph stores.
- A July 2026 Reddit project reports recreating a fused vector+graph+relational Postgres design with one WAL/query plan. This is useful implementation exploration but is explicitly treated as anecdotal/self-reported until independently reproduced.

## External synthesis

The strongest external pattern is not `monolith` or `polystore` alone. The literature now contains credible systems on both sides:

- integrated query/compute and shared transaction domains can reduce cross-system coordination;
- decoupled indexes/data can reduce legacy-engine overhead, storage amplification and update cost;
- typed semantic models can compile across physical backends;
- partial query translation can choose virtual versus physical transformation by subplan;
- selector integrity and derived-view provenance must be explicit.

Therefore U2 treats placement as a **multi-axis, workload- and risk-constrained decision** while keeping semantic identity/query contracts unified.
