# ClayGraph G1 — Negative / Blocking Results

Run: `claygraph-20260808T0642p0700-chatgpt-secondary-r2`

1. **N-CG1-001 — Naive spreading activation did not beat lexical retrieval in the local self-use proxy.** Parent-like unconstrained two-hop activation and lexical retrieval both produced mean recall@5 `0.6333`; graph precision was slightly lower (`0.32` vs `0.33`). This is a small proxy, but it is direct evidence against assuming that more propagation automatically means better memory.

2. **N-CG1-002 — Physical database monolithization is not supported.** Current FRANK/Clay/Hyperposition evidence distinguishes semantic topology from physical store topology. `71 DB files` does not imply `71 semantic organs`, but neither does it justify one physical graph database. No store is assigned `MERGE` in the current inventory.

3. **N-CG1-003 — Activation cannot serve as truth/evidence strength.** This remains a hard invariant across ClayGraph, Clay, FRANK and ClayCode. A relation being highly active means it is cognitively reachable, not that it is more true.

4. **N-CG1-004 — Complete live FRANK database mapping is unavailable in this worker.** The measured runtime source reports 71 live DBs, but reachable evidence exposes only a subset by current name/schema. Remaining stores are `BLOCKED/UNKNOWN`; migration claims cannot silently fill the gap.

5. **N-CG1-005 — Official full-corpus ClayGraph runtime benchmark is blocked on this surface.** The GitHub connector exposes repository files and writes but cannot execute `tools/claygraph_build.py` / `tools/claygraph_benchmark.py`; `research_entity/claygraph/runtime/current/manifest.json` is not committed/reachable.

6. **N-CG1-006 — Qwen3-4B matched-budget benefit remains unmeasured.** Hugging Face inference is cached as quota exhausted until 2026-09-01 and no local target-model runtime is exposed. No small-model accuracy/token advantage is claimed.

7. **N-CG1-007 — Graph-only current-state authority is not justified.** FRANK C4 already requires exact `CognitiveFrame` consistency/witnesses. ClayGraph generation 1 therefore requires exact-anchor validation for current telemetry, transaction and authority-sensitive decisions.

8. **N-CG1-008 — Broad graph edges are a false-association risk.** `MENTIONS`, broad dependency and branch-membership edges are useful for navigation but are not automatically meaning-bearing evidence links. Generation 1 therefore does not expand them by default without query/target support.

9. **N-CG1-009 — CRDT/event-sourcing/graph technology is not universally appropriate.** External literature supports each as a tool with explicit semantics/trade-offs, not as a blanket replacement for conventional transactional or hot-path stores.

10. **N-CG1-010 — The current interconnection protocol text is stale relative to registries.** The authoritative/current registries list seven scientific branches including `claygraph`; `INTERCONNECTED_RESEARCH_MESH_PROTOCOL.md` still enumerates six. This run follows the newer registries and records the governance inconsistency rather than treating it as scientific evidence.

None of these negative results establishes that ClayGraph is a bad architecture. They constrain what can currently be claimed and which next tests have the highest information value.
