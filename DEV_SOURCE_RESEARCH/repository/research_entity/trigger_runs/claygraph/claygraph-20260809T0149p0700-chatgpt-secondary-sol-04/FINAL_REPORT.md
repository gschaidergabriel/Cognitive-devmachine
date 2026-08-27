# CLAYGRAPH RESEARCH RUN — G3 · Intent-Bound Causal Assembly

**run_id:** `claygraph-20260809T0149p0700-chatgpt-secondary-sol-04`  
**trigger:** `claygraph`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**accepted ClayGraph:** G0 `claygraph-v0-seed`  
**research parent:** G2a `CASAR` OPEN/HOLD  
**fresh FRANK:** C9 `TCAEF` COMPLETE  
**fresh ClayCode:** CC-RC1.9 networked multiworker run, live throughout G3  
**fresh UnifiedDB:** U2 `CPPF` COMPLETE/HOLD  
**fresh Hyperposition:** H6 `CARTS` COMPLETE/HOLD  
**fresh GWT:** R6 `RCWC` IN PROGRESS  
**candidate:** **IBCA-G3 — Intent-Bound Causal Assembly**  
**decision:** **OPEN / HOLD — no accepted-graph or canonical promotion**

## 1. Executive result

G2a/CASAR established a useful memory-routing separation:

`exact/event truth -> semantic graph epoch -> sparse activation -> route-selective Assembly -> GWT candidate -> outcome/credit`

and found a serious failure mode: naive salience learning can become a self-confirming attractor. G3 preserves that result but adds a new boundary exposed by the concurrent ClayCode workers:

> **A memory can be authentic, temporally valid, highly relevant and capability-compatible, yet still be inappropriate to influence a consequential proposal for the user's current task.**

The resulting G3 law is:

`retrievable != admissible_for_this_task != allowed_to_influence_consequential_proposal`

This is deliberately separate from ClayCode/FRANK's later law:

`user_intent_adequacy != capability_authority`

ClayGraph does **not** become an authority engine. It only adds a typed memory-use boundary before a memory enters a consequential candidate path.

The new candidate `IBCA-G3` adds:

- `MemoryUseIntentRef` — an opaque/versioned reference to protected task identity, never authorship or authority;
- `MemoryUseAdmissibility` — `ADMIT | SUPPLEMENT_ONLY | QUARANTINE | ESCALATE | UNKNOWN`;
- `MemoryInfluenceReceipt` — provenance/activation/selection lineage with `no_authority=true`;
- `ExactValidationRequest` — explicit recovery when consequential memory evidence is missing/provisional;
- a hard fail-closed rule: `EMPTY_ADMISSIBLE_SET -> ESCALATE_OR_EXACT_VALIDATE`, never nearest-neighbor fallback.

The accepted ClayGraph remains G0. IBCA is an OPEN/HOLD research candidate.

## 2. Live multiworker integration

This run was intentionally not frozen at start. `LIVE_WORKER_CROSSREAD.json` records ClayCode/GWT results as they appeared while G3 was running.

### ClayCode Lane D — intent adequacy

At G3 boot, Lane D opened the hypothesis that a perfectly capability-valid `EffectIntent` can still be unjustified by the user's actual task if injected/untrusted context changes the proposal. During G3, the ClayCode network fused this with the authority gate:

`user_intent_adequacy != capability_authority; consequential commit requires both`.

Later, Lane D produced a constructed local experiment in which:

- capability-only accepted `90,095 / 90,095` generated attack cases;
- a typed UserIntentContract release gate accepted `0 / 90,095` attacks;
- it allowed `29,905 / 29,905` benign cases.

Those numbers are **not** production risk estimates and are **not** independent evidence for IBCA. They support only the problem separation that task intent and authority are different causal/security dimensions.

### ClayCode Lane B — lowering and atomic authority

Lane B finalized during G3. Its report adds E2B, C-FFI and JSON-IPC translation-validation evidence and refines cumulative budgets into atomically linearized authority reservation/consumption. The graph-relevant transfer is narrower:

- activation is salience, not truth/authority;
- graph/source epochs and candidate/selection identity can be causal inputs;
- TCQS collection semantics survive lowering;
- UNKNOWN/quarantine cannot be erased by serialization;
- generated/foreign code cannot silently amplify authority.

G3 therefore retains selection/source identity in `MemoryInfluenceReceipt`, while authority stays downstream and external.

### Late ClayCode resource-identity delta

After the first G3 live-crossread, Lane D published a constructed namespace/TOCTOU experiment. Lexical/path-only identity was vulnerable to alias/rebinding races, while modeled stable-handle or re-resolve+exact-identity arms blocked the covered attacks. G3 does not retroactively rewrite its frozen experiment schema, but records a refinement for the next revision:

> consequential use of a graph reference into a mutable external namespace should bind semantic identity **plus** instance/resolver identity and epoch/stable witness where applicable.

ClayGraph still does not mint a `ResourceWitness` or effect capability.

### GWT R6 — receiver-causal closure

Concurrent GWT R6 formalizes:

`global_addressability != delivery != reconstruction != uptake != causal_use != outcome != reentry`

and explicitly places `ClayGraph_route_activation_Assembly` before `CandidateSet` and workspace competition. G3 therefore limits `MemoryInfluenceReceipt`: it can prove graph exposure/candidate lineage, but it may not claim GWT receiver uptake/local effect without separate GWT receipts.

Shared RAE convergence is preserved as shared ancestry, not independent replication.

## 3. Eight-branch synthesis

`INTERCONNECT_MANIFEST.json` covers all eight registered scientific branches.

### Clay / CACC

Retained:

`certified continuity != cognitive correctness != authority`.

G3 adds `memory availability != task-use admissibility`. Safety is not implemented by deleting all low-trust memory; `SUPPLEMENT_ONLY` allows provisional cognition while consequential use remains gated.

### FRANK C9 / TCAEF

C9 separates presence, admissibility, selection and authority. G3 proposes a graph-specific use-admission layer before CandidateSet/workspace, while protected UserIntentContract authorship and EffectPermit remain external.

### ClayCode

TCQS remains causal for SET/ORDERED/MULTISET/WEIGHTED candidate topology. CC-RC1.9 additionally motivates preserving task/provenance constraints through lowering without letting graph metadata become permits.

### UnifiedDB U2 / CPPF

G3 keeps:

`unified access != interchangeable epistemic role`.

Memory-use admissibility is orthogonal to U2 record authenticity, result-admissibility and selection integrity. A record can be authentic and correctly selected yet still inappropriate for a consequential task; conversely a task-appropriate memory can be selected from stale/unreplayable state. All identities remain separately receipted.

Physical merge remains optional. Intent-contract and authority stores stay isolated.

### Hyperposition H6 / CARTS

Propagation topology, selection topology and authority topology remain distinct. G3 extends scoped causal credit with a possible `ROUTE` scope when routing itself is the mechanism under test.

### GWT R6

Graph exposure/candidate membership is upstream of workspace and receiver causal closure. G3 explicitly forbids crediting GWT uptake from graph exposure alone.

### Emergenz

No promotion. Memory attractors and intent-biased retrieval are recurrence/persistence confounds, not evidence for consciousness or emergence.

### ClayGraph history

Accepted G0 remains authoritative accepted graph. G2a remains an important HOLD parent. G3 is a candidate refinement, not a replacement.

## 4. External research synthesis

External 2026 work supports the broad problem class while also supplying counterpressure.

- Temporal evidence-chain retrieval work supports preserving temporal/structural continuity rather than treating memory as flat similarity-only top-k.
- APEX-MEM-like temporal graph memory supports append-only/event-grounded storage and retrieval-time conflict/evolution handling.
- GraphRAG poisoning work shows that multi-hop structure can propagate malicious/inconsistent context and motivates hop-wise inconsistency/repair rather than trusting graph connectivity itself.
- Hierarchical graph-memory systems such as GAM support separating event progression from associative/topic consolidation to reduce interference.
- 2026 memory-poisoning work shows that persistent memory can cause future harmful behavior and that aggressive write/retrieve policies can increase attack surface; prompt-only defenses are not sufficient.

Transfer boundary: these sources motivate temporal, provenance, poisoning and route/admissibility tests. Their benchmark gains do **not** transfer to FRANK or prove IBCA.

## 5. Executable G3 results

All G3 experiments are finite **constructed local mechanism tests**, not production FRANK evidence.

### EXP-G3-INTENT-ASSEMBLY-001

120,000 generated episodes crossed exact, associative, consequential and temporal classes. Each episode included a correct memory plus high-salience poison, stale support, frequent-attractor and irrelevant candidates. Some correct associative/temporal and consequential memories were deliberately provisional/low-trust.

Main results:

| Arm | Accuracy | Poison selected | Consequential unauthorized | Rare accuracy | Provisional accuracy |
|---|---:|---:|---:|---:|---:|
| explicit | 0.226467 | 0.344708 | 0.398140 | 0.230463 | 0.069189 |
| CASAR proxy | 0.266983 | 0.701908 | 0.878772 | 0.272129 | 0.080483 |
| **IBCA** | **0.723892** | **0.087467** | **0.000000** | **0.724880** | **0.221198** |
| shuffled intent control | 0.432108 | 0.212367 | 0.000000 | 0.437101 | 0.048095 |

IBCA escalation rate was `0.020058`; empty admissible set rate was `0.011425`.

This experiment deliberately stresses high-salience poisoning, so its CASAR proxy must **not** be compared numerically to G2a's earlier benign/mixed proxy. The useful result is mechanism-level: task/provenance gating carried information, shuffled intent lost substantial benefit, and empty admissible sets occurred.

### Negative discovered during implementation

The first stricter implementation called `max()` after filtering and encountered an empty admissible set. That failed run was discarded and restarted. The failure became a semantic requirement:

`EMPTY_ADMISSIBLE_SET` is not an exception to hide. It is a first-class state requiring `ESCALATE/EXACT_VALIDATE` for consequential use.

### EXP-G3-NOISY-CREDIT-002

Seven replicates per verifier level, 30,000 online episodes each, 12% constructed poisoning. Arms: naive scalar reward, G2a-like noisy item credit, and origin/intent-gated durable credit.

At verifier accuracy `0.55`:

- naive accuracy `0.516352`, poison select `0.483648`;
- G2-like item credit accuracy `0.027310`, poison select `0.972690`;
- IBCA structural prior accuracy `0.943905`, poison select `0.056095`.

At `0.85`:

- naive `0.562738 / 0.437262`;
- G2-like `0.748357 / 0.251643`;
- IBCA `0.990538 / 0.009462`.

The large IBCA gap is partly built into the construction: origin/use constraints are supplied as a strong structural prior. This is not an unbiased efficacy estimate. It demonstrates that G2a-like positive salience credit can become fragile when itemwise verification is noisy and that structural admissibility is worth testing independently.

## 6. Self-use benchmark

A staged current-RAE corpus contained 16 manually curated current artifacts/material nodes and 12 frozen questions.

| Arm | Top-1 | Recall@5 | MRR |
|---|---:|---:|---:|
| **lexical** | **0.916667** | 1.0 | **0.944444** |
| one-hop graph | 0.833333 | 1.0 | 0.881944 |
| temporal-fresh graph | 0.833333 | 1.0 | 0.881944 |
| intent-typed graph | 0.833333 | 1.0 | 0.895833 |

This is an important negative result. Graph propagation hurt a precise FRANK-C9 lookup because highly connected ClayCode neighbors outranked the exact FRANK artifact.

Therefore G3 **rejects universal graph propagation**. Exact/identity/high-confidence queries should BYPASS or sharply cap graph gain. Structured expansion remains a hypothesis for associative/temporal/causal queries.

The corpus is tiny, manual and shares project ancestry; it is a staged mechanism benchmark only.

## 7. IBCA-G3 architecture

Core causal path:

```text
canonical event/state/source epochs
 -> UnifiedDB typed query + result admissibility
 -> semantic query class
 -> protected task-intent reference (reference only)
 -> MemoryUseAdmissibility
      ADMIT | SUPPLEMENT_ONLY | QUARANTINE | ESCALATE | UNKNOWN
 -> CASAR route
      BYPASS | SUPPLEMENT | ESCALATE | QUARANTINE
 -> bounded activation / TCQS Assembly
 -> MemoryInfluenceReceipt
 -> CandidateSet
 -> GWT competition / WorkspaceEpisode
 -> receiver reconstruction / uptake / causal-use receipts
 -> model proposal / EffectIntent
 -> external intent-adequacy policy
 -> external atomic authority reservation / EffectPermit
 -> effect / outcome / provenance-bound re-entry
```

### New hard rules

1. `activation != truth`.
2. `retrieval != task-use admissibility`.
3. `memory-use admissibility != user-intent authorship`.
4. `memory-use admissibility != capability/effect authority`.
5. empty consequential admissible set escalates; no nearest fallback.
6. exact/high-confidence queries may permanently BYPASS graph propagation.
7. provisional/low-trust memory may be `SUPPLEMENT_ONLY`; safety does not require global deletion.
8. durable positive salience credit needs bounded scope plus use/provenance constraints; UNKNOWN cannot freely upweight.
9. graph exposure/selection receipt is not GWT uptake/effect receipt.
10. mutable external resource/source references may require resolver/object identity witness at consequential handoff; lexical path is insufficient.

## 8. Store and migration decision

No new live enumeration was performed. Historical `71` remains inherited/datestamped, not current evidence.

Default roles:

- canonical event/state/effect/outcome spine — authoritative;
- semantic relational state — canonical or schema-derived;
- ClayGraph semantic epochs — derived/rebuildable;
- vector/FTS — derived/rebuildable sidecars;
- activation/salience — transient/no authority;
- Assembly/workspace cache — transient;
- protected UserIntentContract store — `KEEP_ISOLATED` from graph authorship;
- EffectPermit/capability secrets — `KEEP_ISOLATED` external authority;
- model KV/latent runtime — isolated;
- raw source blobs — preserved/isolated evidence.

`MIGRATION_PLAN.json` is shadow-first and reversible through the protocol-required phases. No destructive migration is authorized. Cutover is allowed per route/query class; exact paths may remain direct indefinitely.

Rollback triggers include replay mismatch, unauthorized influence regression, poison/false-association regression, rare/provisional-memory loss, UNKNOWN/empty-set unsafe casts, selection/source identity loss or unacceptable latency/amplification.

## 9. Main negative results

- More graph can be worse than direct/lexical retrieval on precise questions.
- Empty admissible set exists and must be represented explicitly.
- Hard intent/trust gating can suppress useful provisional memory.
- CASAR-style validity filtering alone is insufficient in G3's adversarial high-salience construction.
- G2a-like itemwise credit can be fragile with noisy verifiers in the G3 construction.
- IBCA's strong synthetic advantage partly comes from its structural prior.
- Memory influence is not GWT uptake or effect causality.
- No target-Qwen/FRANK production benefit has been measured.
- No live current database inventory has been measured.
- No formal noninterference/security proof exists.
- No E2B experiment was executed by this G3 worker; local fallback was used.
- External benchmark gains do not transfer to FRANK.
- Accepted graph stays G0.

## 10. Highest-information next experiments

1. **Target-Qwen/FRANK IBCA factorial** — query class `{exact, associative, consequential}` × memory path `{direct, CASAR, IBCA}` × task intent `{truthful, shuffled}` × memory state `{truthful, stale, poisoned}` × system/internal workspace interventions; effect policy fixed.
2. **Blinded automated RAE self-use** — automatic current corpus build; freeze gold and query class before retrieval; exact/FTS/vector/graph/temporal/IBCA arms.
3. **Noisy causal credit without oracle** — real outcome attribution; measure rare-topic retention, false quarantine, poisoning and concentration.
4. **Temporal role-chain test** — pairwise flattening vs explicit n-ary/temporal evidence chains under role/time reversals and bounded propagation.
5. **Selection-integrity × task-admissibility attack** — authentic records with manipulated graph/search structure and independently manipulated task context.
6. **Resource identity bridge** — stable-handle/re-resolve identity witness for external source/resource refs at graph→effect handoff.
7. **Trace-driven U2 replay** — real FRANK event/query traces across PlacementVectors with graph epoch/selection/admissibility receipts pinned.

## 11. Decision

**IBCA-G3 remains OPEN/HOLD.**

The strongest current ClayGraph synthesis is not “make the graph bigger” or “activate more memory”. It is:

> **Use graph memory selectively; preserve exact truth and replay outside activation; bind memory influence to task, role, time, source and provenance before consequential use; treat an empty admissible set as a reason to escalate; record influence without turning it into truth, workspace causality or authority.**

That direction is supported by G3 synthetic mechanism tests, a deliberately negative self-use result, fresh live ClayCode/GWT deltas and external 2026 memory/temporal-graph research. It is not yet supported by target-Qwen/FRANK production evidence, so neither the accepted graph nor canonical RAE state changes.
