# Hyperposition H2 Source Ledger

## Canonical / RAE
- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json` — r2 / `04234ef...`
- `research_entity/triggers/HYPERPOSITION_RESEARCH_PROTOCOL.md`
- predecessor: `hyperposition-20260808T0526p0700-chatgpt-secondary/FINAL_REPORT.md`
- `research_entity/global/EXTERNAL_RESEARCH_TOOL_REGISTRY.json`
- `tools/research_provider_router.py`

## Scholarly / preprint
- Budiu, McSherry, Ryzhyk, Tannen — *DBSP: Automatic Incremental View Maintenance for Rich Query Languages*, arXiv:2203.16684.
- Haas et al. — *LoRe: A Programming Model for Verifiably Safe Local-First Software*, arXiv:2304.07133.
- Zeng, Wu, Krishnan — *A Simple and Fast Way to Handle Semantic Errors in Transactions*, arXiv:2412.12493.
- Chmielewski et al. — *The Role of Semirings in Incremental View Maintenance*, arXiv:2606.07795.
- Lu, Tupikina, Alam — *Two-dimensional Taxonomy for N-ary Knowledge Representation Learning Methods*, arXiv:2506.05626.
- Chan et al. — *HyperPatch: Sequential Knowledge Editing Under n-ary Structural Drift*, arXiv:2606.03179.
- Lien et al. — *HyperRAG: Reasoning N-ary Facts over Hypergraphs for Retrieval Augmented Generation*, arXiv:2602.14470.

## Primary implementation / systems evidence
- Feldera documentation — DBSP incremental tables/views, inserts/updates/deletes, signed changes, no concurrency control in DBSP query engine.
- OSDI 2026 — Yu et al., *Efficient and Scalable Synchronization via Generalized Cache Coherence* (Soul/GCP).
- OSDI 2026 — Hu et al., *SBB: Eliminating Centralized Bottlenecks in Userspace Network Runtime*.
- OSDI 2026 — Yang et al., *FORGE: Mitigating Synchronization Amplification for Memory-Disaggregated Caching Systems*.
- OSDI 2026 — Luo & Shen, *No Buffer, No Bottleneck: Efficient Zero-Copy KV Cache Offloading for Long-Context LLMs*.
- OSDI 2025 — Huang et al., *Tigon: A Distributed Database for a CXL Pod*.
- TimelyDataflow/differential-dataflow GitHub implementation evidence retained from H1.
- eclipse-iceoryx/iceoryx2 GitHub implementation evidence retained from H1.

## Practitioner / anecdotal
- Reddit r/highfreqtrading — SPSC ring-buffer discussion on separating producer/consumer atomics to avoid false sharing.
- Reddit r/cpp / r/cpp_questions 2026 — lock-free SPSC discussions emphasizing cache-line bouncing, batching and tail-latency tradeoffs.
- Reddit r/localfirst 2026 — recovery-contract discussion emphasizing visible conflicts/history; anecdotal only.

## Executable evidence
- `EXP-HYP-H2-SCOPE-001` — synthetic global-vs-scoped closure + mis-scope safety test.
- `EXP-HYP-H2-REVOKE-002` — exact incremental invalidation vs rebuild crossover.
- `EXP-HYP-H2-RELATION-003` — pairwise flattening ambiguity vs relation-instance identity.