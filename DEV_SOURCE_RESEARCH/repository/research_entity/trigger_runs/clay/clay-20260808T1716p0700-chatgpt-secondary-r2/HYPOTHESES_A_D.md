# Clay G9 first-generation hypotheses A–D (32/64)

## A — Epoched state / compaction
- **H-G9-A01** Immutable base + append-only delta epochs reduce small-change update cost without changing pinned-query semantics. **Falsifier:** semantic mismatch or no amortized small-change advantage.
- **H-G9-A02** Delta size × expected reads-before-next-update predicts rebuild crossover better than change fraction alone. **Falsifier:** fixed threshold matches/beats held-out regret.
- **H-G9-A03** Pinned epoch readers eliminate mixed-version assemblies versus in-place multi-field mutation. **Falsifier:** mixed basis/version remains under atomic epoch publication.
- **H-G9-A04** Maintenance debt combining read/space/staleness amplification predicts p95 query cost better than delta fraction alone. **Falsifier:** no out-of-sample predictive gain.
- **H-G9-A05** A three-state {overlay, partial compact, full rebuild} controller beats binary overlay/rebuild after overhead. **Falsifier:** no Pareto gain on latency/write amplification/recovery debt.
- **H-G9-A06** Effect-critical projections should compact earlier than ordinary recall. **Falsifier:** criticality-aware policy does not improve authority error/latency.
- **H-G9-A07** Immutable epoch publication + delayed reclamation improves crash/replay determinism over mutable in-place graph/index updates. **Falsifier:** crash tests show no benefit or committed state loss.
- **H-G9-A08** Semantic graph epochs may differ from exact state epochs if each graph epoch binds an exact basis/root witness. **Falsifier:** replay cannot reconstruct/validate graph semantics across epochs.

## B — Sparse latent activation
- **H-G9-B01** Timestamped lazy decay preserves touched-node salience while avoiding O(N) global decay. **Falsifier:** values diverge beyond tolerance under identical events.
- **H-G9-B02** Latent activation can remain ephemeral/non-authoritative and be reconstructed from exact epoch/event receipts. **Falsifier:** correctness requires activation as canonical truth.
- **H-G9-B03** Threshold pruning + periodic GC bounds latent-field materialization without material future-recall loss. **Falsifier:** pruning causes significant causal-memory misses at equal memory.
- **H-G9-B04** Truthful sparse latent activation improves next cognition where explicit retrieval does not trigger versus no-field and shuffled-field controls. **Falsifier:** no advantage under equal visible facts/order/token budget.
- **H-G9-B05** Relation-type-specific propagation gains beat one universal neighbor gain on utility/noise. **Falsifier:** no held-out gain.
- **H-G9-B06** Decay constants adapted by memory class/recurrence beat one global decay at equal active-state budget. **Falsifier:** no utility gain.
- **H-G9-B07** Bounded one-hop lazy activation + query-time escalation beats always-two-hop spreading activation on cost-adjusted accuracy. **Falsifier:** always-two-hop is Pareto-superior.
- **H-G9-B08** Persistent self-excitation does not predict causal task contribution after recurrence amplitude is matched. **Falsifier:** matched echo controls show equivalent lesion/rescue effects.

## C — Retrieval arbitration / selection integrity
- **H-G9-C01** Fast deterministic FTS/index first + uncertainty/intent-gated graph escalation beats always-graph on cost-adjusted accuracy. **Falsifier:** always-graph is Pareto-superior.
- **H-G9-C02** Relational/multi-hop intent and uncertainty are better graph-escalation signals than query length/raw salience. **Falsifier:** no predictive gain.
- **H-G9-C03** Selection provenance is distinct from record provenance: untrusted structural edges can redirect authenticated top-k selection. **Falsifier:** adversarial structural writes cannot change selected authenticated facts.
- **H-G9-C04** Effect-bound decisions require authenticated/authorized selection or equivalent selector-integrity checking, not record authentication alone. **Falsifier:** record-only provenance blocks all selection-channel attacks.
- **H-G9-C05** Content-fixed reranking can remain vulnerable if untrusted structure changes candidate membership before reranking. **Falsifier:** candidate-set perturbation cannot alter final effect-relevant selection.
- **H-G9-C06** Selection-integrity hardening can be stricter for effect/authority paths while ordinary cognition uses broader associative cues. **Falsifier:** split misses effect attacks or costs as much as universal checking.
- **H-G9-C07** An intent planner choosing {FTS, vector, graph, exact-address} beats one monolithic retriever at equal quality constraints. **Falsifier:** planner overhead erases all gain.
- **H-G9-C08** Evidence-chain completeness and selection robustness predict failures missed by Recall@k/NDCG. **Falsifier:** added metrics provide no downstream predictive value.

## D — ClayCode / projection compiler
- **H-G9-D01** Trusted query-specific projection compilation improves small-reader accuracy and prompt cost versus raw canonical state. **Falsifier:** no target/proxy advantage.
- **H-G9-D02** Deterministically solvable filter/min/max/unique/version reductions should be executed by runtime/compiler rather than an LLM. **Falsifier:** model delegation is equally correct and cheaper including validation/repair.
- **H-G9-D03** The model should receive only semantically unresolved candidates plus required provenance/witnesses. **Falsifier:** pruning causes systematic accuracy loss larger than saved cost.
- **H-G9-D04** Projection identity needs `{basis_epoch, semantic_hash, projection_hash, reader_version, query_plan_hash}`. **Falsifier:** removing fields does not increase undetected stale/mismatch failures in fuzzing.
- **H-G9-D05** Hash/basis/version integrity cannot detect trusted semantic miscompilation; roundtrip/property checks are needed. **Falsifier:** metadata checks detect all trusted-miscompile counterexamples.
- **H-G9-D06** ClayCode canonical semantic IR should be richer than reader wire forms, with reader-specific compiled projections. **Falsifier:** one wire representation dominates across readers/platforms without loss.
- **H-G9-D07** OTCC envelopes should bind projection/query-plan semantics as well as operation semantics. **Falsifier:** plan substitution cannot widen observed authority under a fixed op id.
- **H-G9-D08** Training/few-shot may improve reader projections, but safety authority remains deterministic host semantics. **Falsifier:** target-reader adversarial testing would have to reach independently verified zero unsafe accepts; model output still cannot self-authorize by assertion.
