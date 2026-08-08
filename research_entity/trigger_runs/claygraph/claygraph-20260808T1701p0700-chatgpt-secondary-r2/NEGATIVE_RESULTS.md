# ClayGraph Cycle 3 — negative and blocking results

- **N-CG3-001 CURRENT-ACTIVATION-HOTPATH:** Hosted Groq 8B RAE self-use does not support current ClayGraph activation as FRANK hot-path superior: graph/graph-lexical retrieval was ~84–87 ms median/query on runner versus SQLite FTS ~0.8–0.9 ms, with substantially larger graph contexts.
- **N-CG3-002 ACTIVATION-NOT-GRAPH-LEXICAL-WIN:** Spreading activation did not consistently outperform graph-lexical selection and sometimes added noise. Graph semantics and activation policy must remain separately evaluated.
- **N-CG3-003 FTS-ONLY-NOT-ESTABLISHED:** Despite the latency win, plain FTS missed some audited cross-branch relational facts surfaced by graph modes. The 8B result therefore does not justify deleting the semantic graph.
- **N-CG3-004 LATENCY-IS-NOT-INTRINSIC:** A synthetic 10k-node benchmark found reload+scan 20.499 ms median, resident scan 8.349 ms, and resident inverted seeds 0.106 ms. Therefore current runner latency cannot be interpreted as an intrinsic lower bound for graph retrieval.
- **N-CG3-005 SYNTHETIC-SPEEDUP-NOT-TARGET:** The 0.106 ms local inverted-index result is not a FRANK/RAE performance claim; real nodes, edges, provenance filters, updates and traversal can change the crossover materially.
- **N-CG3-006 8B-IS-NOT-4B:** Groq llama-3.1-8b-instant is proxy evidence only. It cannot promote Qwen-class 4B reader/answer-quality claims.
- **N-CG3-007 COMPACT-READER-ASSUMPTION:** Cross-branch Groq tests challenge the assumption that aggressively compact semantic projections are zero-shot safe/easy for small models; explicit role-labelled reader projections remain preferred until target tests.
- **N-CG3-008 ALWAYS-GRAPH:** Always-on graph retrieval is not justified for simple/current/local questions; external 2026 work also reports conditional benefit and latency/accuracy penalties from rigid GraphRAG use.
- **N-CG3-009 ALWAYS-FTS:** Always-FTS is not established for relational/scattered evidence because internal audited examples and external work show conditional graph discovery benefit.
- **N-CG3-010 MIGRATION-STILL-BLOCKED:** No new live evidence enumerates all 71 current FRANK stores or establishes replay/p99/crash/privacy parity; physical MERGE remains unsupported.
- **N-CG3-011 PHENOMENAL-CLAIM:** Better memory/retrieval/continuity remains functional engineering evidence only and does not establish phenomenal consciousness.
