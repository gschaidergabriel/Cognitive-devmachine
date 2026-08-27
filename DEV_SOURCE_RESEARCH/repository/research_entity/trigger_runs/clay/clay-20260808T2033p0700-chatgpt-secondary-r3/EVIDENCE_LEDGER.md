# Clay G11 Evidence Ledger — MOSAIC / UnifiedDB / MRSC

**run_id:** `clay-20260808T2033p0700-chatgpt-secondary-r3`

Evidence is classified by source and transferred only to the mechanism actually supported.

## Database / query architecture

- **PostgreSQL-V — Fast Vector Search in PostgreSQL: A Decoupled Approach (CIDR 2026).** Primary proceedings source. Decouples vector indexes from the relational engine while preserving consistency and reports up to 8.9x over pgvector. **Transfer:** strong architecture precedent for logical integration with physically specialized sidecars. Not evidence for Clay/FRANK performance.
- **Cephalopod — Virtual Data Model Composition through Partial Query Translation (CIDR 2025).** Primary proceedings source. Proposes a bridge representation and cost-based subplan choice between virtual query translation and physical transformation. **Transfer:** supports UnifiedDB/MOSAIC choosing translation vs physical colocation per subplan/workload rather than globally.
- **DortDB — Bridging Query Languages for Multi-Model Data Ponds (PVLDB 2025).** Primary proceedings source. Uses a unified algebra for multi-model query processing. **Transfer:** independent precedent for one logical algebra over heterogeneous representations.
- **Querying Graph-Relational Data / Gel (arXiv 2025).** Formal graph-relational model and typed query semantics lowered into PostgreSQL. **Transfer:** supports high-level semantic identity independent of physical relational lowering.
- **Meta Engine (arXiv 2026).** Unified semantic query engine routing over heterogeneous specialized LLM query systems; reports 3–6x higher F1 in most evaluated cases. **Transfer:** query-router/adapters can outperform a forced all-in-one semantic-query system; task is not FRANK storage.
- **Samyama (arXiv 2026).** Single Rust graph-vector engine with MVCC and broad integrated functionality. **Transfer:** physical unification is technically feasible enough to benchmark. Preprint claims are not taken as proof that monolithic unification is superior.
- **DuckDB VSS + FTS primary docs.** Shows vector and full-text indexes can coexist in one engine, but VSS persistence/index lifecycle has explicit limitations and stale-delete/compaction concerns. **Transfer:** derived-index lifecycle must remain explicit even in a single physical DB.
- **PostgreSQL 18 MVCC docs.** Primary documentation for transaction isolation and serialization handling. **Transfer:** basis/snapshot consistency is an explicit runtime contract, not a timestamp assumption.

## Incremental / low-latency dataflow

- **Feldera / DBSP primary docs + VLDB lineage.** Maintains arbitrary SQL incrementally from changes rather than recomputing full historical state. **Transfer:** strong feasibility precedent for Clay derived-view maintenance; exact target dependency graphs remain unmeasured.
- **Apache Arrow v25 primary format docs.** Defines cross-language columnar memory, IPC and same-process zero-copy C data interface plus extension types. **Transfer:** physical Clay payloads may use zero-copy/shared buffers and typed extension metadata without making Arrow itself canonical semantics.

## Compiler / representation

- **MLIR primary docs.** Multiple typed dialects model different abstraction levels and can be extended/lowered. **Transfer:** one semantic architecture need not imply one literal representation.
- **E-Graphs as a Persistent Compiler Abstraction (arXiv 2602.16707).** Maintains equality information across multiple IR levels in an MLIR flow. **Transfer:** Clay may preserve alternative equivalent representations, but semantic equality must remain separate from provenance/authority identity.
- **Fresh project E2B compiler-lab v0.1/v0.2.** Verified isolated executable evidence. v0.1 conflated executable semantic identity with provenance-bound contract instance; v0.2 split `semantic_hash` from `contract_hash`. **Transfer:** direct new RAE evidence for multi-axis identity and typed collection semantics.

## Agent memory / ClayGraph

- **Synapse (Findings ACL 2026).** Dynamic graph memory using spreading activation, inhibition, temporal decay and hybrid retrieval; reports improved temporal/multi-hop performance. **Transfer:** supports bounded associative activation as retrieval mechanism, not truth/GWT evidence.
- **GAM (ACL 2026).** Separates an event progression graph from topic associative consolidation. **Transfer:** supports distinct fast episodic encoding and slower semantic consolidation.
- **MAGMA (ACL 2026).** Represents memory across orthogonal semantic, temporal, causal and entity graphs with policy-guided retrieval. **Transfer:** supports multiple specialized views rather than one monolithic embedding space.
- **Query-Aware Spreading Activation (arXiv 2606.30133).** Single-query Cypher implementation; reports gate-driven F1 gains and 1.5–4.9x retrieval-latency reduction versus ungated structural variant in tested tasks. **Transfer:** query intent should affect graph propagation/routing.
- **SeedER (arXiv 2605.23753).** Low-cost seed-and-expand retrieval with controlled candidate growth. **Transfer:** graph escalation can be conditional and bounded rather than universal.
- **Reddit RAG/agent-memory reports (2026).** Community systems report practical value from hybrid dense+lexical+graph+temporal signals and frustration with passive query-only memory. **Class:** anecdotal/community evidence only; useful for failure-mode discovery, never promotion.

## GWT / emergence / causality

- **PEID (arXiv 2605.03267).** Intervention-grounded effective-information decomposition for unique/synergistic causality. **Transfer:** emergence measurements should bind exact intervention basis and multivariate source identity.
- **Emergent Coordination in Multi-Agent Language Models (ICLR 2026 submission).** Uses information decomposition and randomized interventions to distinguish temporal coupling from performance-relevant coordination. **Transfer:** recurrence/synergy alone is insufficient.
- Current RAE GWT R4 remains stronger project-specific method evidence for stage orthogonality: graph prior, workspace, projection and re-entry are separate causal factors.

## Security / authority

- Current RAE H4 and CC11 supply the active boundary: semantic classes/roles may share Clay syntax but cannot implicitly cast to truth/authority/effect. Fresh NVIDIA embedding negative controls show dense similarity is unsafe for directed role/class identity.
- Community agent-security discussions emphasize traceability, permissions and context poisoning, but these are secondary evidence only. Hard effect authority remains a deterministic capability gateway.

## Edge / embodiment

- **MLC LLM Android primary docs.** Supports compiled Android runtime/model libraries, estimated VRAM metadata and physical-device execution. **Transfer:** same high-level model/semantic contract can have Android-specific physical lowering.
- **llama.cpp Android primary repository docs.** Provides Android bindings and hardware-aware kernels. **Transfer:** local inference path is technically feasible.
- **2026 Reddit Qwen3 Android reports.** Community reports Qwen3-4B Q4_K_M running around 4–6 tok/s on a Pixel 7 with ~6 GB minimum RAM in one implementation. **Class:** anecdotal, hardware-specific; motivation only, not target evidence.

## Evidence boundary

No external source proves MOSAIC-G11, FRANK consciousness, target-Qwen Clay internalization, a universal database winner, or production latency/security. External literature establishes feasibility classes, independent failure modes and comparison architectures; current-run numbers remain synthetic/local unless explicitly inherited from verified NVIDIA/E2B runtime receipts.
