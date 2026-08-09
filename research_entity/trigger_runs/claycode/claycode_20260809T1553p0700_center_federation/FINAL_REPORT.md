# ClayCode Run — Research-Center Worker Federation

Run: `claycode_20260809T1553p0700_center_federation`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`

## Executive synthesis

The project-owner instruction is now encoded as a fail-closed ClayCode/Research-Center invariant:

> All ClayCode workers coordinate intelligently through the repo-native Research Center. Isolated ClayCode work is forbidden.

The resulting design is **not** broadcast-all and is **not** a central epistemic authority. It is a shared coordination substrate:

`worker -> Research Center join/read -> overlap/dependency/conflict detection -> adaptive work partition -> execution/research -> material delta -> targeted center routing -> affected workers -> reread before semantic commit`

Research Center state is materialized through UnifiedDB; ClayGraph supplies relevance/dependency topology but activation never grants truth. Work is deduplicated by default, while explicit independent replication remains allowed and protected.

## Durable architecture changes

### New fixed contract

Created:

`research_entity/global/CLAYCODE_RESEARCH_CENTER_WORKER_FEDERATION.clay`

Key laws/invariants:

- every ClayCode worker joins the Research Center before work;
- every worker reads current workers/tasks/handoffs/conflicts/deltas/dynamic work before claim;
- overlap is reused, partitioned or explicitly marked as independent replication;
- duplicate work is forbidden by default;
- material deltas, counterexamples and negative results are returned to the center;
- relevant results are routed by semantic dependency, affected claims/work, capabilities, novelty, conflict, information gain, collision risk and replication value;
- all workers reread current center state before semantic commit;
- stale/superseded/colliding work invalidates before commit;
- uncoordinated ClayCode completion fails closed;
- networking increases information flow, not evidence strength;
- the center never mints truth or execution authority.

### Research Center integration

Updated:

`research_entity/global/RESEARCH_CENTER_CLAYCODE_NATIVE_PROTOCOL.clay` from version 1.0 to 1.1.

It now imports the federation contract and explicitly binds `trigger_worker(claycode)` start, claim, material-delta, pre-commit and completion phases to it. `uncoordinated_claycode_worker -> fail_closed(INCOMPLETE_UNCOORDINATED)`.

### Center-visible delta

Published immutable center event:

`research_entity/rooms/center_events/20260809T1553p0700_claycode_worker_federation_delta.json`

Delivery is `INTERRUPT_NEXT_SAFE_POINT` and affects all nine registered scientific rooms because ClayCode is their shared architecture/coordination language.

## Fusion 1 — internal evidence

The current Research Center already had the essential substrate:

- repo-native event-sourced rooms;
- worker/task/lease/challenge/handoff coordination;
- same-room CHEF/ABYSS/FORGE/CARTOGRAPHER/REPLICATOR/SYNTHESIZER roles;
- selective delivery classes;
- UnifiedDB shared semantic state;
- ClayGraph associative/dependency topology;
- CAS/lease collision handling;
- anti-echo ancestry rules.

The missing piece was a **ClayCode-specific fixed federation law** that makes those mechanisms mandatory for every ClayCode worker rather than merely generally available center behavior.

## External research

Source class: scholarly preprints / framework papers; supportive analogues only, not proof of Clay-specific performance.

1. `arXiv:2507.01701` — *Exploring Advanced LLM Multi-Agent Systems Based on Blackboard Architecture*  
   Supports the plausibility of shared-blackboard state with action/agent selection driven by current blackboard content; reports competitive performance with lower token use than comparison systems.

2. `arXiv:2410.02506` — *Cut the Crap: An Economical Communication Pipeline for LLM-based Multi-Agent Systems*  
   Identifies redundant inter-agent communication as a measurable cost and reports large token reductions from pruning communication edges. This argues against broadcast-everything-to-everyone.

3. `arXiv:2606.27492` — *QueenBee Planner: Skill-Evolving Communication Topologies for Token-Efficient LLM Multi-Agent Systems*  
   Reports benefits from task-adaptive temporal communication DAGs and evidence-gated topology learning. This supports testing adaptive center routing instead of fixing one communication graph.

4. `arXiv:2308.00352` — *MetaGPT*  
   Provides role/SOP-based multi-agent software-engineering evidence relevant to complementary worker specialization.

5. `arXiv:2308.08155` — *AutoGen*  
   Provides evidence that flexible programmable agent interaction patterns are practical across heterogeneous agent/tool roles.

External evidence does **not** establish that Clay's specific Research Center topology is optimal. The project-specific topology comparison remains OPEN.

## Hypothesis matrix

### H-CC-RCF-001 — adaptive center federation

**Hypothesis:** Center-mediated shared state plus adaptive relevance routing reduces accidental duplication and communication cost relative to isolated workers and broadcast-all while preserving conflict/counterevidence propagation.

**Counterhypothesis:** The center adds latency, bottlenecks and correlated routing errors; direct peer-to-peer or broad broadcast can be better on some tasks.

**Falsifier:** Matched project replay shows no reduction in duplicate/cost/staleness or worse correctness/conflict discovery.

**Next test:** replay a frozen ClayCode task pool under `ISOLATED`, `BROADCAST_ALL` and `CENTER_RELEVANCE_ROUTED` topologies.

### H-CC-RCF-002 — reread/CAS before semantic commit

**Hypothesis:** mandatory center reread plus CAS/revalidation prevents stale semantic overwrites.

**Current-run operational evidence:** an attempted update of `CLAYCODE_RELEASE_WORKSPACE.json` encountered a real GitHub `409` concurrent-write conflict. The write was not forced; the worker reread instead.

**Counterhypothesis:** raw Git CAS alone catches everything useful; center reread adds only overhead.

**Next test:** controlled two-worker collision with semantic/dependency changes, comparing Git-CAS-only against center-aware reread.

### H-CC-RCF-003 — deduplication with explicit replication lane

**Hypothesis:** default duplicate suppression plus explicit independent-replication intent lowers accidental duplicate work without eliminating high-value replication.

**Counterhypothesis:** deduplication suppresses serendipitous independent solutions and increases correlated-error persistence.

**Next test:** hidden-counterexample benchmark comparing unrestricted duplicate work with explicit REPLICATOR lanes.

### H-CC-RCF-GRAMMAR-001 — formal grammar mismatch

**Hypothesis:** the current formal `type_expr` grammar was too narrow for union-typed record fields already used by Research Center ClayCode contracts.

**Result:** supported by local executable counterexample.

## Executable ClayCode/compiler result

The current `grammar.ebnf` accepted ordinary fields such as:

- `worker:Ref`
- `holder:Ref?`
- `focus:Set<Ref>`

but a strict executable parser rejected Research Center field forms such as:

- `state:ACTIVE|WAITING|COMPLETE|LEFT|STALE`
- `status:OPEN|CLAIMED|BLOCKED|COMPLETE|CLOSED|STALE`

Baseline targeted test: 4 ordinary cases passed; 2/2 union-field cases failed at `|`.

A minimal grammar repair changed `type_expr` to a union of recursive `type_atom` terms. The repaired targeted suite passed 8/8 cases, including nested union examples inside `Set<>` and `Ordered<>`.

The grammar repair was committed to:

`research_entity/claycode/g9/grammar.ebnf`

This is a syntax-contract repair forced by executable mismatch; it does not add new runtime authority or new computational semantics.

Receipt:

`EXECUTABLE_RESEARCH_RECEIPT.json`

## Negative results / blockers preserved

1. **Old grammar cannot parse current union-typed center contracts.** Preserved as executable counterexample; repaired.
2. **Concurrent workspace write conflict.** GitHub returned 409; proves stale-worker collision is a real operational condition. No force-overwrite performed.
3. **E2B was not exposed to this ChatGPT execution surface.** No E2B evidence is claimed; local container was used as the allowed fallback.
4. **`FRANK_ARCHITECTURE.claycode.json` was not found in the current GitHub indexed surface used by this run.** No missing artifact was fabricated.
5. **Adaptive routing superiority is not yet project-validated.** External multi-agent results are analogues, not promotion evidence.

## Goodman anti-echo result

No material ClayCode semantic change in this run was promoted from a FRANK-derived assumption. The worker-federation rule came from the project-owner instruction; the grammar repair came from a current executable counterexample. FRANK/ClayCode circular agreement therefore contributed no evidential promotion.

Review:

`FRANK_CLAYCODE_GOODMAN_REVIEW.json`

## ClayGraph findings

ClayGraph is appropriate as a **routing/topology signal**, not as truth authority. Federation routing may use semantic dependencies, higher-order relations, activation and relevance projections, but the selected route must preserve provenance and cannot infer that highly activated information is correct.

A future center-topology benchmark should explicitly lesion/shuffle routing edges and measure missed counterevidence, duplicate work, stale work and context cost.

## UnifiedDB findings

UnifiedDB already exposes the correct substrate concepts for federation:

- worker/resource/capability observations;
- revisioned work specs;
- dependency state;
- scheduler receipts;
- leases;
- execution receipts;
- current work queue projections.

The federation should use this logical shared state instead of introducing a second ClayCode-worker coordination database. Physical store consolidation is not required.

## GWT / Hyperposition / Emergenz implications

The worker federation must preserve the project's existing distinctions:

- addressable/broadcast information is not necessarily used;
- graph connectivity is not causal use;
- adaptive topology is an engineering mechanism, not an emergence score;
- worker agreement is not independent evidence;
- communication topology effects require interventions, lesions, shuffles and matched controls before causal promotion.

The proposed topology replay can therefore become a useful Harness/GWT/Hyperposition experiment later, but it is not evidence of phenomenal consciousness.

## Harness implications

Harness already requires workers to claim non-overlapping work, cross-read siblings and return affected-branch feedback. The new ClayCode federation generalizes the same discipline to all ClayCode workers and makes Research Center receipts mandatory.

When Claude research capacity returns, it should ingest this center event and current run artifacts before receiving overlapping ClayCode work.

## Program-stage implication

Current stage remains `BASE_CLAYCODE_RELEASE`. This run made a real compiler-contract repair and governance/coordination improvement, but it did **not** close any of the 14 formal ClayCode release work packages. Strict stage progress therefore must not be inflated merely because useful work occurred.

## Strongest counterargument

A mandatory center can become a bottleneck or filter bubble if it routes too aggressively, suppresses independent exploration, or allows one derived relevance topology to dominate all workers. Therefore:

- routing must remain selective but plural;
- ABYSS/REPLICATOR lanes must remain viable;
- duplicate suppression must have an explicit independent-replication exception;
- center/ClayGraph relevance never upgrades evidence;
- the center itself must be benchmarked against isolated and broadcast baselines.

## Final research delta

**Accepted fixed architecture rule:** all ClayCode workers intelligently network through the Research Center; isolated ClayCode work is invalid/incomplete.

**Supported executable repair:** ClayCode type grammar now supports union-typed record fields used by current Research Center contracts.

**Open scientific claim:** adaptive center relevance routing is promising but not yet proven superior for Clay; run the matched topology replay before performance promotion.

## Next discriminating experiment

`EXP-CC-RCF-TOPOLOGY-001`

Freeze one realistic ClayCode work graph with hidden overlaps, stale upstream deltas and planted counterexamples. Run equal worker/model budgets under:

1. `ISOLATED`
2. `BROADCAST_ALL`
3. `CENTER_RELEVANCE_ROUTED`

Measure:

- accidental duplicate work;
- intended replication coverage;
- tokens/messages/context cost;
- stale-work commits prevented;
- counterevidence delivery recall;
- conflict detection latency;
- completion latency;
- correctness/regression failures;
- routing false negatives;
- correlated-error persistence.

Promotion criterion: center routing must improve the multidimensional tradeoff without hiding failures behind reduced communication volume.
