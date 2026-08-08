# Hyperposition H5 — External Evidence Ledger

Run: `hyperposition-20260808T2212p0700-chatgpt-secondary-r3`

Evidence classes are preserved; cross-branch agreement is not counted as independent replication.

## Higher-order semantic representation

- **HyperGraphRAG — NeurIPS 2025, peer reviewed.** AI-specific evidence that binary graph representations can be limiting for n-ary factual relations and that hypergraph retrieval can improve tested retrieval/answer behavior. Transfer: preserve relation-instance/group semantics when they matter. Non-transfer: not proof that FRANK requires native hyperedges.
- **HyperRAG — WWW 2026 / arXiv, peer-reviewed conference record + preprint.** Query-conditioned hypergraph traversal over n-ary relations. Transfer: active topology can be query/context conditioned.
- **Collective dynamics on higher-order networks — Nature Reviews Physics 2026, peer-reviewed review.** Higher-order interactions can change collective dynamics qualitatively. Transfer: group structure can be causally important. Non-transfer: not evidence of FRANK emergence.

## Pairwise reducibility / counterthesis

- **Reducibility of higher-order to pairwise interactions: Social impact models on hypergraphs — Physical Review Research 2026, peer reviewed.** Shows an exact weighted-pairwise mapping for a general class of higher-order node-update models. Transfer: `higher-order` does not imply `native hypergraph execution`; equivalence must be operation-specific.
- **Graphs are maximally expressive for higher-order interactions — 2026 preprint.** Counterargument to simplistic graph-vs-hypergraph dichotomy; graph constructions may encode higher-order phenomena.
- **Adaptive Expansion — 2025 preprint** and **WebConf 2024 information-loss framework** show that graph expansions differ in how much hypergraph information they preserve. Transfer: lowering needs an explicit equivalence/loss contract.

## Propagation / oversmoothing / selectivity

- **From Diffusion to Reaction-Diffusion: Oversmoothing in HGNNs — 2026 preprint.** Multi-way diffusion can intensify representation collapse with depth; reaction terms can preserve variation.
- **FrameHGNN — AAAI 2025, peer reviewed.** Treats oversmoothing as a deep hypergraph-neural-network problem and uses frequency-aware mechanisms.
- **K-hop HGNN — AAAI 2025, peer reviewed.** Long-range propagation can help while oversmoothing/oversquashing remain design constraints.
- **Synapse — ACL Findings 2026, peer reviewed.** Dynamic agent graph memory using spreading activation, lateral inhibition, temporal decay and hybrid retrieval. Transfer: bounded/inhibited activation is independently plausible; not FRANK validation.

## Incremental dependency maintenance

- **Feldera / DBSP — authoritative project documentation/current system.** Incremental maintenance of complex SQL views from deltas supports change-proportional derived topology.
- **Differential Dataflow — authoritative documentation.** Maintains outputs as changing inputs produce differences; supports incremental dynamic-topology implementation class.
- **Salsa — authoritative current Rust crate docs.** Tracks dependencies for incremental on-demand computation. Its untracked-dependency mechanism independently supports conservative behavior when exact dependency tracking is incomplete.

## Physical topology / IPC

- **Apache Arrow C Data Interface — authoritative documentation.** Same-process zero-copy interchange; cross-process sharing/persistence are explicit non-goals. Transfer: same-process data plane candidate only, not a universal IPC protocol.
- **Rethinking IPC with Memory Operation Offloading — 2026 preprint.** Shared-memory/offloaded IPC can improve latency/throughput but depends on synchronization/cache/concurrency design.
- **Zerrow — 2025 preprint.** Shows zero-copy across pipeline boundaries needs explicit memory/lifetime/kernel mechanisms.

## Epistemic conclusion

External evidence supports H5's mechanism class but also its main counterthesis: **explicit higher-order semantics and bounded contextual propagation are useful ideas, yet neither native hypergraphs nor maximum coupling are universal defaults.** The correct architecture is operation-specific, equivalence-tested and benchmarked against physical/failure costs.
