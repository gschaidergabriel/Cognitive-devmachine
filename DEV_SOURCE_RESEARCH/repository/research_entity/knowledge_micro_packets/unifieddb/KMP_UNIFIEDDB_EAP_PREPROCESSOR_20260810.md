<!-- RAE_META
{
  "packet_id": "KMP-UNIFIEDDB-EAP-PREPROCESSOR-20260810",
  "title": "EAP-1.3 turns UnifiedDB/ClayGraph retrieval into a bounded model-input preprocessor with epistemic propagation gates",
  "domains": ["unifieddb", "claygraph", "retrieval", "gwt", "frank"],
  "topics": ["active_assembly", "possibility_retrieval", "preprocessor", "multi_hop", "negative_space", "epistemic_gating", "latency"],
  "epistemic_class": "MEASURED_CANDIDATE",
  "status_hint": "TESTING",
  "origin_actor": "chatgpt-secondary",
  "provider": "OpenAI",
  "model": "GPT-5.6 Sol",
  "created_at": "2026-08-10T00:22:30Z",
  "source_refs": [
    "research_entity/harness/reference/unifieddb_emergent_preprocessor.py@ec6417e9f7e5766700fdb5edddeeb2794938ac53",
    "research_entity/harness/reference/test_unifieddb_emergent_assembly.py@77c85f931b88ef27f46f31a29212770b90679ca2",
    "research_entity/harness/reference/benchmark_unifieddb_emergent_assembly.py@0efc688ebd4f3a9d75315dbf29fa10da3844c85b",
    "research_entity/runtime/semantic_entity_resolver_v12.py@cecb7447682ddfaa218a677a9aaa25c7f35deecf",
    "research_entity/experiments/unifieddb_claygraph_retrieval/u11_nl_claygraph_cascade_candidate.py@8df4089c1f9054f42d041ed79d6eac938083dff2",
    "https://arxiv.org/abs/2405.14831",
    "https://arxiv.org/abs/2410.05779",
    "https://www.microsoft.com/en-us/research/blog/lazygraphrag-setting-a-new-standard-for-quality-and-cost/",
    "https://www.microsoft.com/en-us/research/blog/benchmarkqed-automated-benchmarking-of-rag-systems/"
  ],
  "confidence": 0.78,
  "verification_required": "Self-hosted Ubuntu receipt plus repo-native/held-out paraphrase/write-rate benchmarks before promotion",
  "falsifier_or_next_test": "EAP fails to beat a matched staged SQL model-input baseline after amortizing structural rebuild cost, or loses accuracy on held-out/repo-native tasks, or U11/U12 plus a simpler online-SQL path dominates it."
}
RAE_META -->

### Atomic result

The current Clay direction is better described as a **model-input preprocessor over canonical UnifiedDB state** than as a replacement physical database engine.

EAP-1.3 (`EmergentAssemblyPreprocessor`) keeps the `StateLedger`/UnifiedDB as source truth and derives an epoch-bound, disposable sparse dependency topology. It performs bounded best-first multi-hop activation to compile the task-conditioned `ActiveAssembly` handed toward GWT/model cognition. It is explicitly non-authoritative and `persistent_second_store=false`.

The implementation preserves:

- semantic epoch and semantic-state hash;
- source row semantic hashes;
- dependency refs, relation type and predecessor (`via_ref`);
- epistemic/status labels;
- bounded frontier/hop budgets;
- deterministic selection hash;
- stale-epoch rejection;
- safe rebuild after dependency mutation;
- incremental refresh after non-structural writes when the cached basis is still exact.

### Local synthetic mechanism benchmark

Workload:

- 12,000 semantic nodes;
- 11,760 dependency edges;
- 240 deterministic multi-hop queries;
- `k=12`, max depth 3;
- exact same target set for EAP and recursive SQL baselines.

Latest local EAP-1.3 measurements before remote validation:

- EAP complete hot Assembly: recall@12 `1.0`, precision@12 `1.0`, nDCG@12 `1.0`, p50 `92.5725 us`;
- staged recursive SQLite closure + row materialization + model-context receipt: recall/precision/nDCG `1.0`, p50 `104.19 us`;
- EAP p50 speedup over that matched staged SQL path: about `1.1255x`;
- naked recursive SQLite refs-only closure: p50 `43.059 us`, so SQLite remains materially faster when the workload asks only for reference IDs and does not require equivalent Assembly materialization/provenance;
- EAP cold topology build + first query: `17.380535 ms`;
- at the measured local medians, cold structural rebuild cost breaks even only after roughly `1496` hot reads (`17.380535 ms / (104.19-92.5725 us)`).

**Boundary:** this is synthetic mechanism evidence. It does not establish universal database superiority, downstream answer-quality superiority, or target-machine acceptance.

### Exactly-one `go` out-of-box experiment

`EXP-GO-EAP-NEGATIVE-SPACE-001` tested an adversarial graph where a high-weight `CONFLICT` node leads to a decoy that would outrank a lower-weight known relevant branch if conflict is merely hidden at final output.

Counterfactual ungated propagation:

- precision@2 = `0.5`.

EAP epistemic propagation gate:

- precision@2 = `1.0`;
- the inadmissible `CONFLICT` node remains observable as blocked/suppressed evidence but cannot relay activation into descendants;
- if `CONFLICT` is explicitly admitted by policy, the path may propagate again.

Interpretation: filtering uncertainty only at output can launder uncertainty through graph topology. Propagation eligibility must itself be epistemically typed.

### External evidence fusion

External work supports the general mechanism but not the Clay-specific superiority claim:

- HippoRAG combines knowledge-graph structure with Personalized PageRank and reports strong multi-hop gains plus lower cost/latency than iterative retrieval in its evaluation.
- LightRAG combines graph and vector structure and emphasizes incremental updates.
- Microsoft LazyGraphRAG combines best-first and breadth-first search using iterative deepening and deliberately avoids expensive full up-front summarization.
- BenchmarkQED demonstrates why local/global query classes and matched quality/cost evaluation are required; one retrieval strategy does not get universal superiority by construction.

Clay-specific implication: keep persistence canonical and conservative, but make model access **budgeted, task-conditioned, topology-aware and precompiled only as far as evidence/cost warrants**.

### Fusion with concurrent U11/U12 work

Parallel current work converges on complementary layers rather than competing stores:

1. U12 evidence-bound resolver: natural-language mention -> exact/evidence alias, otherwise fail closed as `AMBIGUOUS`, `LOW_CONFIDENCE` or `MISS`.
2. U11 coherent semantic fast path: known coherent seed/generation -> very cheap pre-materialized retrieval when coverage exists.
3. EAP: bounded multi-hop expansion for a seed where the current task requires dependency/possibility closure.
4. NL+ClayGraph fallback: only when coherent seed coverage is absent and policy allows broader search.
5. GWT receives the bounded provenance-bearing Assembly, not an unbounded database/graph dump.

Candidate pipeline:

`natural language -> U12 fail-closed resolver -> U11 coherent seed fastpath -> EAP bounded closure when needed -> GWT ActiveAssembly`

with `NL+ClayGraph fallback` for unresolved coverage, never as authority.

### Strongest counterhypotheses still active

1. **Amortization counterhypothesis:** structural dependency updates are frequent enough that EAP rebuild cost erases hot-read gains.
2. **Seed-coverage counterhypothesis:** exact/normalized seeds make synthetic EAP/U11 tests unrealistically easy; held-out paraphrases reduce recall.
3. **Simpler-baseline counterhypothesis:** a strong online SQLite/FTS/metadata/recursive-edge plan is fast and accurate enough that EAP complexity is unnecessary.
4. **Downstream counterhypothesis:** retrieval metrics improve but final answer/tool-choice quality does not.
5. **Memory counterhypothesis:** in-memory row/value/topology amplification costs more RAM than the latency gain justifies on the target system.

### Next discriminating tests

- self-hosted Ubuntu EAP receipt bound to exact SHA and runner metadata;
- held-out paraphrase + ambiguity/OOD seed-resolution benchmark through U12 -> EAP;
- realistic read:nonstructural-write:dependency-write sweeps to measure amortization and structural rebuild duty cycle;
- repo-native Frank retrieval episodes with ground-truth provenance and downstream task outcome;
- matched U11-only, U12+U11, U12+EAP, and strong online-SQL baselines;
- peak RSS/state amplification and recovery/rebuild measurement;
- only after those pass: architecture promotion from `TESTING` to `SUPPORTED`.
