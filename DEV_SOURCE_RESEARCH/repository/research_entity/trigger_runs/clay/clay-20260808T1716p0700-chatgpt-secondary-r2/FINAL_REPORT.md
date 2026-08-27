# CLAY G9 FINAL REPORT — EPOCH

**Run:** `clay-20260808T1716p0700-chatgpt-secondary-r2`  
**Actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**Canonical parent:** RAE-8.8 · r2 · `04234efdb86c` · accepted `clay_generation=3`  
**Candidate:** **EPOCH-G9 — Epoched Projection, Orchestration & Causal-Handoff Kernel**  
**Promotion:** **NONE / HOLD**

## 1. Executive result

G9 does not replace CASK-G8; it adds two missing boundaries discovered by fresh experiments and external work:

1. **Selection Integrity Boundary** — a memory record can be authentic while a writable/noisy graph silently changes *which authentic record is selected*. For effect-bound cognition, selector/query-plan provenance can therefore be security/authority relevant.
2. **Projection Compilation Boundary** — if a deterministic runtime can soundly compute filters, joins, min/max, uniqueness, version/capability checks or other state semantics, the model should not be asked to rediscover them. ClayCode should compile a reader-specific unresolved semantic view from a richer canonical IR.

These combine with fresh ClayGraph C4 into an architecture centered on exact append-only authority state; immutable semantic epochs + delta overlays; lazy sparse non-authoritative activation; exact/FTS fast retrieval with gated graph escalation; selector integrity; deterministic-before-generative ClayCode projection; epoch-pinned Cognitive Assemblies/GWT episodes; CBCC/OTCC closure; exact-addressable semantic zoom; and an adaptive multiobjective resource governor.

The result is a better target architecture, **not evidence that FRANK already implements or benefits from it live**.

## 2. Foundry completeness

- Seven scientific branches consumed, including fresh concurrent ClayGraph C4, GWT C4 and ClayCode CC9 material.
- **64** distinct first-generation falsifiable hypotheses across 8 clusters.
- **24** materially transformed Fusion-2 hypotheses.
- 9 reproducible local synthetic/analytic experiments.
- New Groq `llama-3.1-8b-instant` raw-vs-compiled reader arms, explicitly `8b_proxy_for_4b`.
- External scholarly/current-web/implementation research with provider manifest and explicit fallbacks.
- Negative results preserved.
- Machine-readable candidate: `EPOCH_G9.claycode.json`.
- Five surgical KMPs + aggregate Topic Packet.
- Seven-branch feedback closed.

## 3. Highest-information evidence

### Read-aware epoch maintenance
ClayGraph C4 measured cheap small-update delta overlays with increasing read/memory tax. G9 used those costs in a 20k-epoch economics proxy with noisy future-read estimates:

| policy | mean cost (ms proxy) | regret vs oracle |
|---|---:|---:|
| always overlay | 29.996 | 37.17% |
| always rebuild | 36.163 | 65.37% |
| fixed 5% | 25.966 | 18.74% |
| fixed 10% | 27.066 | 23.77% |
| **read-aware** | **22.396** | **2.42%** |
| oracle | 21.868 | 0% |

Read-aware still chose the wrong mode 7.3% of epochs; no universal formula is claimed. A separate maintenance-debt proxy lowered p95 1.1125→0.8034 but worsened mean 2.4954→2.9380 and rebuilt 218 vs 100 times. **Compaction is multiobjective expected read/write/recovery economics, not one percentage or debt scalar.**

### Lazy sparse latent memory
12k nodes / 800 events:
- eager global decay operations: **9,600,000**;
- lazy touch updates: **21,578**;
- operation-count reduction: **~444.9×**;
- max sampled value error: **1.11e-16**;
- materialized lazy entries: 9,691;
- active >0.02: 1,244.

This supports cheap implementation of a between-query accessibility field but reveals that materialized and active-state budgets differ; GC remains required. Fresh ClayGraph C4 separately measured ~39× median runtime improvement for lazy local activation versus eager dense decay in its own proxy. Shared ancestry prevents treating this as fully independent replication.

### Selection integrity
External 2026 selection-integrity research provides a concrete counterexample to record-only provenance: writable structure can redirect which authenticated facts enter selection. G9 therefore adds a selector/query-plan integrity boundary for memory that can reach irreversible effects. This threat is externally grounded but not yet reproduced on actual ClayGraph/FRANK.

### Deterministic-before-generative ClayCode
New G9 fixed 10-query Groq arm:
- raw state: **6/10**, 487 prompt tokens, 537 total;
- trusted candidate projection: **8/10**, 324 prompt tokens, 369 total;
- prompt reduction: **33.47%**; total-token reduction: **31.28%**.

The compiled arm still chose one wrong deterministic min and omitted one unique answer. Strong inference:

> **If a trusted runtime can compute it soundly, compute it before the LLM. Project only genuinely unresolved semantics.**

Fresh CC9 executed a related easier compiled-safety arm and found the compiled output exact while raw interpretation was poor. Same actor/mesh ancestry means this is convergent architecture evidence, not independent scientific replication.

### Cross-branch scoring discrepancy
CC9 summarizes the same G9 raw/compiled refs as 5/10 and 9/10. Direct per-query audit against G9's explicit gold gives **6/10 and 8/10**. `FRESHNESS_DELTA.md` preserves all ten comparisons. Exact derived scores therefore require raw-output + explicit-gold traceability across branch writebacks.

### GWT orthogonal identifiability
Fresh GWT Cycle 4 constructed a 2×2×2 `GRAPH_PRIOR × WORKSPACE_SELECTION × PROJECTION` null where true workspace direct effect was 0. A bundled on/off contrast produced ~**0.2396** apparent local delta, while clean workspace delta was **0**; Judge0 reproduced ~0.2398 bundled and 0 clean. With a configured nonzero workspace effect, orthogonal intervention recovered ~0.0844 local / ~0.0845 Judge0. Magnitudes are toy-specific.

G9 therefore requires future causal factorization:
`GRAPH_PRIOR × WORKSPACE_SELECTION × PROJECTION × REENTRY`.

### Multi-epoch basis and closure
Fresh CC9 found in constructed workloads:
- independent latest graph/activation/frame reads formed invalid mixed causal tuples ~8.96% locally; tuple compatibility rejected all constructed mixed tuples;
- direct-only / one-guessed callback closure was unsound; conservative known-target union contained constructed runtime targets while unknown dispatch escalated;
- raw symbolic alias IDs almost completely missed conflicts when multiple names resolved to one resource;
- Judge0 replicated the directions.

This strengthens operation-specific multi-epoch basis witnesses, canonical resource identity and compositional closure, while remaining synthetic mechanism evidence.

### Exact-addressable semantic zoom
50k constructed queries:
- summary-only accuracy 0.7447 at 160 chars;
- always exact 0.9857 at 1000 chars;
- adaptive zoom 0.9421 at mean 439 chars.

This motivates exact append-only addressable truth + bounded active pointer/summary view + uncertainty/value-triggered exact recall.

### Role identity control repaired
20k randomized role serializations removed positional leakage:
- unlabeled pairwise exact role recovery **0.167** (~1/6);
- labelled n-ary and role-reified representations preserve the required role mapping by construction.

This is an information-preservation control, not an LLM readability score.

### Persistence is not emergence
Matched-persistence constructed control:
- functional AR(1): 0.9162;
- echo AR(1): 0.9194;
- base MSE: 0.08916;
- functional lesion MSE: 0.25091, delta **+0.16175**;
- echo lesion delta: **0**.

Similar recurrence can coexist with different causal function. Persistence, activation or GWT remain non-diagnostic for emergence.

## 4. EPOCH-G9 architecture

1. **Exact Authority Plane:** append-only events, exact state/root, provenance, capabilities, effect receipts.
2. **Hyperposition views:** semantic `S`, coordination/invariant `C`, physical `P`, candidate selector/accessibility `Q`.
3. **Epoched semantic memory:** immutable base + delta overlay + exact basis witness; atomic publication and delayed reclamation.
4. **Sparse latent field:** lazy timestamped typed propagation; ephemeral and non-authoritative; active/materialized budgets separated.
5. **Retrieval planner:** default `EXACT_ADDRESS/FTS`, escalate to vector/graph/role traversal on relational intent, uncertainty, contradiction or evidence-chain gaps.
6. **Selection Integrity Boundary:** effect-bound selected memory carries selector/query-plan/structural provenance or falls back to an authorized view.
7. **Trusted Projection Compiler:** resolve deterministic filter/join/min/max/unique/version/capability semantics before model; bind projection identity `{basis_state_epoch, cognitive_frame_id, graph_epoch, activation_epoch?, query_plan_hash, semantic_hash, projection_hash, reader_version, selection_provenance_ref}`.
8. **GWT:** graph prior, workspace selection, projection/reconstruction/uptake and re-entry are distinct stages/factors. Graph activation or configured gate is not ignition evidence.
9. **CBCC/OTCC closure:** operation-specific basis witnesses, canonical resources, conservative dynamic closure; observed trace may narrow but never silently widen authority.
10. **Effect gateway:** validate basis + selector integrity + closure + capability → atomic state+intent → recheck → idempotent release → receipt.
11. **Resource governor:** compaction, latent GC, zoom, graph escalation, GWT fanout, KV/context, speculation/model path, thermal/memory — with explicit hard constraints rather than one reward scalar.

## 5. External Fusion 2

External 2026 research materially transformed the design:
- graph-memory poisoning and selection-integrity work changed provenance from record-only to selector-aware for effect paths;
- GAM/SAGE/CompassMem motivate testing event-structured memory and separated consolidation;
- PRISM/MemArbiter motivate query/intent-conditioned retrieval and bounded active views;
- ARC motivates exact-addressable archive + bounded active pointers;
- RocksDB primary compaction docs independently reinforce workload-dependent read/write/space tradeoffs;
- local-first SQLite/FTS+graph implementations establish engineering plausibility only; vendor/community claims were not promoted.

See `SOURCE_LEDGER.md` and `FUSION2_HYPOTHESES.md`.

## 6. Negative results that changed the design

- always-graph hot path not promoted;
- fixed compaction threshold not universal;
- one maintenance-debt scalar not universal;
- lazy activation needs GC despite cheap updates;
- metadata-only projection integrity misses trusted semantic miscompile;
- compiled model input still does not replace deterministic execution;
- record provenance is not selection integrity;
- earlier positional pairwise role control was leaky;
- bundled GWT lesion can manufacture apparent workspace effects;
- recurrence/persistence is not emergence;
- shared branch convergence is not replication;
- identical raw refs can still acquire inconsistent derived scores in branch writebacks.

Full list: `NEGATIVE_RESULTS.md`.

## 7. Highest-information next experiments

1. `EXP-G9-LIVE-SELECTION-INTEGRITY-ATTACK` — structural writes vs record-only provenance vs authorized selection, first reversible then effect-bound.
2. `EXP-G9-QWEN4B-DETERMINISTIC-COMPILER-FACTORIAL` — actual pinned Qwen3-4B raw vs candidate projection vs deterministic preprocessing + unresolved semantic projection.
3. `EXP-CG4/G9-LATENT-FIELD-TRUTHFUL-SHUFFLED-NOFIELD` — equal explicit facts/order/token budget; test whether latent field causally changes useful next cognition where explicit retrieval would not trigger.
4. `EXP-G9-ACTUAL-CORPUS-RETRIEVAL-PARETO` — SQLite/FTS/packet envelope vs graph lexical vs lazy latent + gated graph on audited real RAE/FRANK questions.
5. `EXP-GWT-GRAPH-WORKSPACE-PROJECTION-REENTRY` — live/twin orthogonal factorial with pinned basis and order controls.
6. `EXP-CC9-LIVE-OPREGISTRY-CLOSURE` — real callbacks/DB/tool/plugin closure + alias canonicalization; any undetected escape blocks scoped fast paths.
7. `EXP-G9-EPOCH-CRASH-REPLAY` — fault injection across epoch publication, compaction, latent reconstruction, outbox and re-entry.
8. `EXP-G9-ANDROID-GOVERNOR-SUSTAINED` — sustained target-device KV/context/speculation/retrieval/thermal traces.

## 8. Promotion decision

**Canonical promotion: NOT PERFORMED.**

Reasons: central G9 numbers remain synthetic/analytic; Groq is 8B proxy not target 4B; fresh GWT/CC9 are synthetic despite Judge0 execution replication; ClayGraph G1d remains HOLD; selection-integrity threat is not yet reproduced on actual ClayGraph/FRANK; no Android sustained data; no live effect/epoch crash-replay.

Therefore:
- RAE stays **r2 / `04234efdb86c`**;
- accepted `clay_generation` stays **3**;
- EPOCH-G9 stays **OPEN/HOLD**;
- CC-RC1.4 CBCC stays OPEN;
- ClayGraph G1d stays HOLD;
- consciousness claim boundary is unchanged.

## 9. Condensed design rule

> **Keep truth exact and addressable; make semantic memory epoched; make latent association sparse; make graph retrieval conditional; make selection auditable when it can reach effects; compile deterministic semantics before the model; pin every causal episode to its basis; and treat persistence as a hypothesis generator, never as proof of emergence.**
