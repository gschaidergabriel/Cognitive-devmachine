# UnifiedDB + ClayGraph -> Possibility Preprocessor Fusion Handoff

Date: 2026-08-10 +07:00  
Origin actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Identity: `RESEARCH_ENTITY_TEMPORARY_WORKER`  
Status: `MEASURED_CANDIDATE / TESTING`  
Canonical promotion: `NONE`

## Atomic synthesis

The current evidence does **not** support replacing conventional persistence/index engines with a novel physical database. It supports a stronger and more specific architecture:

> UnifiedDB remains the canonical transactional/provenance state plane; ClayGraph remains derived/rebuildable topology; the model-facing surface becomes an epoch-coherent **possibility/context preprocessor** that chooses the cheapest validated access primitive, returns a precompiled sufficient semantic field when one exists, and deepens through query-aware/gap-controlled topology only when explicit evidence remains unresolved.

This means the cognitive hot path should increasingly see a bounded `PossibilityCapsule`/`ActiveAssembly`, not perform a generic `retrieve -> top-k -> prompt` database decision.

## What survived falsification

### 1. Ordinary database primitives remain part of the winning architecture

A strong exact-key counterbaseline refuted universal speed superiority. On 112 exact-key queries / 22,400 operations per mode, plain SQLite `WITHOUT ROWID` B-tree lookup retained perfect retrieval quality with p50 `3.755 us`; U13 cycle-pinned semantic access narrowed the overhead to p50 `4.256 us` but did not beat it. Therefore already-resolved trivial keys should use ordinary indexed lookup.

Evidence: `research_entity/experiments/unifieddb_claygraph_retrieval/NEGATIVE_RESULT_EXACT_KEY_BASELINE_AND_ALIAS_FALSIFIER_20260810.json`.

### 2. Semantic sufficiency-stop is a causal mechanism candidate

The first 12-query claim benchmark was too easy: SQLite FTS5/BM25 already reached Recall@5/MRR/nDCG `1.0`, and the proposed counterevidence-reserve experiment showed no gain. That benchmark was explicitly rejected as discriminating evidence.

A harder current-Clay snapshot stress then used 11 semantic-family queries, the current 17-claim ledger and 225 real project-source chunks as distractors. Against a strong claims-only SQLite FTS5/BM25 baseline:

- filtered FTS5: precision `0.4985`, recall `1.0`, MRR `0.8485`, nDCG `0.8874`, median `0.07206 ms`;
- compiled semantic field + sufficiency-stop: precision/recall/MRR/nDCG `1.0`, median `0.01087 ms`.

Padding the already-complete semantic field back to top-k reduced precision to `0.3273`, so `sufficient -> stop; do not fill spare top-k slots` is retained as a causal architecture candidate.

Evidence: `research_entity/benchmarks/possibility_preprocessor/REAL_CLAY_SNAPSHOT_STRESS_20260810T0714P0700.json`.

### 3. Coherent generations and cycle pinning are required, not optional cache details

U11 introduced staged/verified/current semantic access generations with atomic head publication. U13 pins one coherent generation/epoch/hash per cognitive cycle so a thought cannot mix old/new possibility projections. Stale, ambiguous or unverified topology fails closed to fallback/abstention rather than being silently reused.

Relevant implementation/evidence ancestry includes:

- `69febf0808aec8197e69edc49ae2b01c32f49682` — coherent access generations;
- `f02ea048440994d0888ea91cc72e2e283d191c93` — cycle-pinned semantic runtime;
- `f69f05be0f4f3f2a82dd5cc90c9804fdbcc4a3b5` — epoch-bound UDB/ClayGraph assembly gate;
- `c51a8b93634464362c7a4f2a8708907a8459aa0a` — every V14 fast path bound to verified epochs.

### 4. Precomputation helps where the task is genuinely semantic/compositional

Repeated 1-2 hop intent/entity retrieval on a synthetic 6,000-query, three-seed workload preserved Top-1 `1.0` for both strategies while compiled V14 access reduced mean hot-read latency from about `60.8 us` online SQL to `4.29 us` (resolved-ID mode), and from about `61.0 us` to `4.82 us` in alias mode. Build cost remained explicit at roughly `62-72 ms` per derived generation.

The compositional Pareto frontier addressed a different task class: multi-hop routes with cost, latency, reliability, authority, freshness, locality and lineage. On 409 valid synthetic route queries, direct V9-like lookup found a feasible route only `49.39%` of the time and the exact best route `27.87%`; the compiled frontier reached `100%` on both in that fixture, with a hot-read median around `0.0030 ms` versus `26.78 ms` for the recursive SQL oracle. Median compile cost was about `3.39 s` and therefore remains an amortization/resource constraint.

These results support moving repeated possibility composition off the model hot path; they do not establish universal database superiority.

### 5. EAP is best understood as model-input compilation, not a second store

`EmergentAssemblyPreprocessor` derives a disposable, epoch-bound sparse topology over canonical UnifiedDB/StateLedger state, performs bounded best-first multi-hop activation, preserves provenance/epistemic labels and emits a deterministic active assembly. `CONFLICT`/inadmissible nodes may remain observable as suppressed evidence but cannot relay activation into descendants, preventing uncertainty from being laundered through topology.

On the matched synthetic 12,000-node assembly benchmark, EAP and staged recursive SQLite both reached recall/precision/nDCG `1.0`; EAP p50 was `92.57 us` versus `104.19 us` for SQL closure + row materialization + model-context receipt (~`1.13x`). Naked recursive SQL returning refs only was faster at `43.06 us`. Cold EAP topology build + first query cost about `17.38 ms`, giving a measured local break-even near 1,496 hot reads at those medians.

Therefore the claimed value is `ready provenance-bearing model context`, not faster raw ID lookup.

### 6. Natural-language resolution and graph propagation must fail closed

The no-internal-ID synthetic control refuted exact-logical-ID anchoring as a general solution. Evidence-bound alias resolution + graph retrieval reached Top-1 `1.0` in the synthetic fixture where FTS5 was `0.3333`; ambiguous controls abstained `1.0` across the later three-seed alias workload. Real aliases/misspellings/pronouns remain an open gate.

### 7. More graph is not automatically better

A fixed depth-2 synthetic relational benchmark reached Recall@10 `1.0` at p50 `1.23 ms`; adaptive depth-3 kept the same recall but increased p50 to `2.31 ms`. Python-decoded facet sets also lost to SQL until replaced by direct compact bit tests. The architecture therefore keeps bounded expansion and compact filtering; depth is earned only by unresolved information pressure.

## Current fused model-facing pipeline

```text
canonical UnifiedDB transactions/provenance
  -> incremental Pulse / targeted invalidation
  -> build VERIFY-able semantic generations + derived ClayGraph projection
  -> atomic publish
  -> V13 cycle pin (one thought = one coherent generation)
  -> V14 adaptive read plane
       exact resolved key -> ordinary B-tree/index
       verified complete semantic family -> COMPILED_SUFFICIENT + STOP
       compositional capability question -> Pareto possibility frontier
       unresolved mention -> fail-closed evidence-bound resolver
       explicit residual evidence gap -> U15 gap-controlled query-aware EAP/ClayGraph deepening
       unsupported/missing/stale -> conventional fallback or ABSTAIN
  -> provenance-bearing PossibilityCapsule / ActiveAssembly
  -> GWT/model cognition
  -> outcome / causal credit / provenance-bound re-entry
  -> targeted invalidation / next generation
```

The fused Python orchestration ancestor is `ea297b73e4528e9b88dd401165ad97f2bdf70f43`; the Clay architecture candidate is `a83090790ffa4ac15de3607c758152e0fb80b67d`.

## New U15 delta from this cycle

U15 `semantic_gap_controller_v15.py` (`4fd81671412b64e279c446e65167982acd1a73a2`) implements deterministic typed sufficiency gaps:

- a complete compiled field causes exactly zero deepening;
- only missing evidence tags/refs can drive expansion;
- invalid provenance cannot close a gap;
- no novel evidence stops recurrence immediately;
- max rounds/items are bounded;
- activation remains `ASSEMBLY_CONTEXT_ONLY_NO_EFFECT_AUTHORITY`.

Falsifier tests are committed at `cc46aa42bf6c6314edcf5246b221fa2a3a734ca2`; a three-seed mechanism benchmark is at `87f0c22baf5ac066756da12a6aaf4aafccf9f157`; Hostinger self-hosted Ubuntu execution workflow is at `686abeeb47a67d0fe1469e24224dabe5db93d1d4`.

At handoff time there is **no persisted U15 `LATEST.json` receipt**, so U15 execution remains unverified remotely.

## External research fusion

Fresh primary research strengthens the mechanism without proving Clay-specific superiority:

- Makarov & Glybovets, *Query-Aware Spreading Activation for Multi-Hop Retrieval over Knowledge Graphs*, arXiv:2606.30133: per-step query-aware gating prunes low-information branches and their ablation reports simultaneous F1 and latency gains.
- *PAR2-RAG: Planned Active Retrieval and Reasoning for Multi-Hop Question Answering*, arXiv:2603.29085: separates high-recall coverage from deeper commitment/refinement.
- *S2G-RAG: Structured Sufficiency and Gap Judging for Iterative Retrieval-Augmented QA*, arXiv:2604.23783: explicitly represents insufficiency/gaps to control subsequent retrieval.
- *Mitigating KG Quality Issues: A Robust Multi-Hop GraphRAG Retrieval Framework*, arXiv:2603.14828: motivates constraint/sufficiency checks when graph edges are imperfect.

Clay consequence: propagate only when the unresolved requirement justifies it; make the gap/query influence each expansion step; keep propagation epistemically typed; and preserve a conventional fallback when the compiled field is stale/missing/insufficient.

## Exactly-one `go` out-of-box experiment in this worker lane

`COUNTEREVIDENCE_RESERVE`: reserve one context slot for the strongest relevant REFUTED/NEGATIVE/SUPERSEDED neighbor.

Result on the initial 12-query current-claim suite: **NO MEASURED BENEFIT**. Precision/recall/MRR/nDCG did not improve and latency increased. The experiment is not promoted. Counterevidence remains preserved through explicit conflict/suppression semantics rather than a forced reserved slot.

## Strongest counterhypothesis

The apparent wins may be mostly materialization/caching plus benchmark-aligned semantic anchors. A well-tuned conventional relational/search/vector/graph stack implementing the **same semantic safety, entity resolution, sufficiency and provenance contracts** may match or beat Clay while having lower rebuild/update/memory complexity. High write churn, stale/noisy topology, real alias ambiguity or lack of downstream answer/tool-choice improvement may erase the preprocessing advantage.

## Promotion gates / next falsifiers

1. Independently adjudicated, held-out real Clay natural-language retrieval/possibility tasks, including misspellings, pronouns and genuine ambiguity.
2. Matched same-semantics conventional baselines: SQLite/FTS, PostgreSQL+FTS/pgvector where available, dense/late-interaction retrieval, and a graph engine only when current tooling/cost justifies it.
3. Real Clay/Frank capability-route fixtures rather than generated worlds.
4. Stale/noisy/contradictory/untrusted edge injections, concurrent writer + generation swap, crash/restart/replay/last-known-good recovery.
5. Read:nonstructural-write:structural-write sweeps, compile/update duty cycle, peak RSS, state amplification, storage/IO and token/context savings.
6. Downstream answer accuracy, tool-route correctness, calibration, causal-use/outcome and token-budget improvement.
7. Self-hosted Hostinger Ubuntu receipts for EAP/U15/Pulse and final Andreas Ubuntu target acceptance.

## Remote truth at handoff

The GitHub self-hosted workflows have been materialized, but neither
`research_entity/state/system/unifieddb_eap_benchmark/LATEST.json` nor
`research_entity/state/system/unifieddb_u15_gap_benchmark/LATEST.json` exists at this handoff. Therefore no EAP/U15 VPS PASS is claimed.

## Architecture adjudication

- `UNIFIEDDB_AS_NOVEL_PHYSICAL_DB_REPLACEMENT`: **REFUTED / NOT THE TARGET**.
- `CONVENTIONAL_STORAGE + CLAY_SEMANTIC_POSSIBILITY_PREPROCESSOR`: **SUPPORTED_CANDIDATE**.
- `ALWAYS_GRAPH_EXPAND`: **REFUTED**.
- `ALWAYS_FILL_TOP_K`: **REFUTED WHEN VERIFIED FIELD IS SUFFICIENT**.
- `EXACT_KEY_ALWAYS_THROUGH_CLAY_LAYER`: **REFUTED**.
- `ADAPTIVE_CHEAPEST_VALIDATED_READ_PRIMITIVE`: **SUPPORTED_CANDIDATE**.
- `GAP_CONTROLLED_QUERY_AWARE_DEEPENING`: **TESTING; REMOTE RECEIPT PENDING**.

No canonical architecture promotion is authorized from this handoff alone.
