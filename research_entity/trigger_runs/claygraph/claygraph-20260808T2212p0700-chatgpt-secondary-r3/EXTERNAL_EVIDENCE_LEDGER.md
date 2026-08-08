# ClayGraph G2a — External Evidence Ledger

Run: `claygraph-20260808T2212p0700-chatgpt-secondary-r3`

Evidence classes are preserved. External systems are mechanism analogues/implementation evidence, not FRANK validation.

## Active / multi-view graph memory

- **SYNAPSE (2026)** — dynamic graph memory with spreading activation, lateral inhibition, temporal decay and hybrid retrieval. Transfer: active memory is technically/scientifically plausible; non-transfer: its task gains are not ClayGraph gains.
- **MAGMA (ACL 2026)** — separates semantic, temporal, causal and entity graph views with query-adaptive traversal. Transfer: relation purpose should remain typed/orthogonal rather than one undifferentiated similarity graph.
- **GAM (ACL 2026)** — separates event progression from associative/topic consolidation. Transfer: short-lived event sequence and longer associative structure can be distinct semantic views without requiring separate physical stores.
- **Temporal Semantic Memory (ACL Findings 2026)** — distinguishes semantic time from dialogue time and retrieves duration-consistent memory. Transfer: use-time temporal validity should participate in activation/Assembly eligibility.
- **APEX-MEM / LiCoMemory / Hindsight (2026)** — current graph/hierarchical/temporal hybrid memory systems provide implementation precedents for incremental memory evolution and multifactor retrieval.
- **Graphiti/Zep** — temporal KG implementation with validity windows, episode provenance, incremental updates and hybrid search. Transfer: exact source lineage and temporal validity should remain first-class.

## Bounded active context / dual path

- **Cognitive Scaffold (ACL 2026)** — fluid working context + persistent graph + dual retrieval path. Mechanism convergence with persistent-rich / active-small architecture.
- **Context Rot / long-context degradation studies** — longer context can degrade effective use; supports bounded Assembly as a serious baseline, not a proof of ClayGraph.
- **STITCH / intent grounding** and **reasoning-aware memory reranking** — query intent/temporal/causal structure can matter beyond raw semantic similarity.

## Propagation failure / attractors

- Current GNN/hypergraph oversmoothing work analyzes message-passing convergence/homogenization and mitigation through signed/structural mechanisms. Transfer: representation richness and propagation strength are separate variables; spreading activation needs gain/depth/diversity controls.

## Memory poisoning / contextual safety

- **SMSR (2026)** — certified/runtime memory-poisoning defense line.
- **systematic memory-poisoning studies (2026)** — aggressive write/retrieve policies can increase exploitability.
- **MemSecBench (2026)** — memory-security lifecycle and backend differences.
- **MemPoison (2026)** — direct, compositional and context-triggered memory corruption; write-time checks alone can miss dormant context-activated attacks.

Transfer: source authenticity/provenance is necessary but does not prove use-time cognitive safety. CASAR therefore keeps query-time role/time/context/utility/poison gates.

## Main external synthesis

The evidence supports the mechanism class:

`rich persistent typed/temporal relational memory -> selective query/activation -> bounded working Assembly`

but also supplies the counterthesis:

`more propagation / more context / more reinforcement != better cognition`.

This motivates CASAR-G2a's route-selective field and anti-attractor governor while leaving target-Qwen/FRANK benefit OPEN.
