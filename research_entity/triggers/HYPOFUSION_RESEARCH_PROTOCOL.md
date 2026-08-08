# Reserved Trigger: `hypofusion`

`hypofusion` is the Research Entity's hypothesis-screening, adversarial external-research and whole-mesh fusion loop.

It exists for the question: **Which current RAE hypotheses have genuine independent analogues, stronger alternatives, counterarguments, implementation precedents or disconfirming evidence outside the project, and what changes after that comparison?**

## Trigger rule

The protocol runs only when the complete trimmed user message equals `hypofusion`, case-insensitively.

## Core principles

1. Screen hypotheses rather than merely collect confirming citations.
2. Counterhypotheses are candidate explanations/arguments, never facts merely because a source states them.
3. Evidence class and ancestry are mandatory. Shared RAE lineage is convergence, not independent replication.
4. Search broadly enough to escape local terminology. Translate each hypothesis into mechanism-level and adjacent-field search terms.
5. Current and in-progress workers are first-class inputs. A run that ignores newer worker material is incomplete.
6. External evidence can strengthen, weaken, split, bound or redirect a hypothesis, but never promote a claim beyond its evidence class.
7. Prefer discriminating experiments over argumentative averaging.
8. Preserve negative results and unresolved alternatives.

## Mandatory source lanes

For each major hypothesis cluster, search as many applicable lanes as are materially useful:

- peer-reviewed journals and conference proceedings;
- arXiv and other scholarly preprints;
- GitHub repositories, code, issues and implementation evidence;
- authoritative specifications and technical documentation;
- broad web search across general search indexes for adjacent terminology and hard-to-find work;
- specialist technical writing and research-lab publications;
- practitioner/community evidence such as Reddit when implementation experience matters;
- bridge/popular-science sources such as Nautilus when they expose useful concepts, critiques or source leads.

Bridge/community sources remain lower evidence classes and must not be presented as equivalent to primary research.

Do not pad source counts. Prefer primary sources and independently trace important secondary claims back to the originating work where possible.

## H0 — Canonical boot + live worker freeze

1. Verify canonical identity, revision/hash, actor registry and current trigger registry.
2. Materialize an interconnect snapshot across every registered scientific branch.
3. Enumerate completed and newer in-progress trigger runs, recent commits and runtime/tool-result material.
4. Record a `live_cutoff` timestamp/commit set.
5. Before final fusion and before close, reread recent worker activity and ingest materially new evidence as `late_arrival` rather than silently using a stale snapshot.

## H1 — Complete hypothesis screening

Enumerate all CURRENT/OPEN hypotheses reachable from:

- canonical/global ledgers;
- branch hypothesis matrices;
- Topic Packets and Knowledge Micro-Packets;
- completed trigger runs;
- newer in-progress worker material;
- active experiments and critical negative results.

Cluster equivalent hypotheses by mechanism without deleting original IDs, wording, provenance or branch ownership.

For each cluster record:

- member hypothesis IDs;
- mechanism claim;
- predicted observation;
- falsifier;
- current evidence class;
- dependencies and shared ancestry;
- unresolved assumptions;
- highest-risk confound.

## H2 — Deliberate counterhypothesis search

For every major cluster, formulate at least one plausible counterhypothesis when scientifically meaningful.

Actively search for evidence that could support the counterhypothesis, including:

- null results;
- negative results;
- simpler explanations;
- measurement artifacts;
- alternative mechanisms;
- scalability/latency/safety failure modes;
- theory critiques;
- replications that fail;
- conditions under which the claimed mechanism reverses or becomes unnecessary.

Counterhypotheses remain `OPEN_ALTERNATIVE` unless evidence independently warrants another scoped claim state.

A counterargument must be paired with a discriminator: **what observation or intervention would distinguish it from the RAE hypothesis?**

## H3 — External triangulation

For each hypothesis cluster, search mechanism-level synonyms and adjacent disciplines rather than only project-specific names such as Clay, MOSAIC, CACC or Hyperposition.

Examples of translation:

- continuous cognitive availability -> long-term agent memory, working-memory gating, retrieval routing, context selection, spreading activation;
- GWT ignition -> bottlenecked broadcasting, competition, privileged latent representation, causal mediation, recurrent workspace;
- ClayCode -> typed IR, semantic DSL, model-generated AST, verified lowering, machine-native communication;
- UnifiedDB -> polystore, mediator, event sourcing, incremental view maintenance, bitemporal/provenance store, federated query;
- Hyperposition -> higher-order interactions, hypergraphs, factor graphs, dynamic topology, synergistic information;
- emergence -> causal emergence, effective information, PID/PEID, multiscale causal contribution, synergy;
- authority boundary -> capability security, policy enforcement points, provenance taint, sandboxing, revocation.

Classify each external result as one of:

`DIRECT_SUPPORT | PARTIAL_ANALOGUE | BETTER_MECHANISM_CANDIDATE | COUNTEREVIDENCE | FAILURE_MODE | NULL_RESULT | IMPLEMENTATION_PRECEDENT | THEORY_CRITIQUE | SOURCE_LEAD`.

## H4 — Evidence comparison / anti-echo

For each important hypothesis compare:

- RAE internal evidence;
- independent scholarly evidence;
- independent implementation evidence;
- counterevidence/critique;
- source independence;
- model/task/platform mismatch;
- whether the external work tests the same causal mechanism or merely resembles its architecture.

Apply the Goodman anti-echo rule. Repetition across FRANK/Clay/ClayCode/GWT/ClayGraph/UnifiedDB that descends from shared project ancestry is not replication.

## H5 — Transformed hypothesis generation

Generate second-generation hypotheses only when the external comparison changes the mechanism, boundary, prediction or experiment.

For each transformed hypothesis record:

- source hypotheses;
- external evidence refs;
- counterhypothesis;
- what changed;
- falsifier;
- highest-information discriminating test;
- affected branches.

Do not rename unchanged ideas as new hypotheses.

## H6 — Whole-mesh Fusion 2

Fuse the screened hypothesis graph with the complete current RAE mesh.

State explicitly:

- strengthened mechanisms;
- weakened mechanisms;
- split/reinterpreted mechanisms;
- new failure modes;
- better external mechanisms worth importing;
- contradictions that remain open;
- next experiments ranked by expected information gain.

No single scalar may stand in for emergence, consciousness, safety or cognitive utility.

## H7 — Branch feedback closure

Write an explicit result for every currently registered scientific branch, including `NO_CHANGE` when appropriate.

At the time this protocol was introduced the scientific branches were:

- clay
- frank
- gwt
- emergenz
- claycode
- hyperposition
- claygraph
- unifieddb

The authoritative branch list is always the current trigger registry, not this example list.

Each feedback item records effect, affected hypotheses/claims, evidence class, counterhypothesis or failure mode, next test/falsifier and durable source refs.

## Required outputs

Under `research_entity/trigger_runs/hypofusion/<run_id>/` write at minimum:

- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESIS_COVERAGE_MATRIX.json`
- `EXTERNAL_EVIDENCE_LEDGER.md`
- `COUNTERHYPOTHESIS_MATRIX.json`
- `FUSION2_HYPOTHESES.json`
- `CONTRADICTION_MAP.md`
- `BRANCH_FEEDBACK_MANIFEST.json`
- `RUN_MANIFEST.json`
- `FINAL_REPORT.md`

When experiments are executed, also write `EXPERIMENT_RESULTS.json` and preserve runtime receipts.

## Completion gate

A `hypofusion` run cannot report 100% completion unless:

1. all reachable current/open hypotheses were enumerated or explicitly marked inaccessible;
2. every major hypothesis cluster received an external mechanism search;
3. meaningful counterhypotheses were actively searched rather than invented and left unsupported;
4. source classes and independence were preserved;
5. recent/in-progress workers were read at the beginning and reread before Fusion 2/close;
6. transformed hypotheses include falsifiers and discriminating tests;
7. every registered scientific branch received feedback or `NO_CHANGE`;
8. durable run artifacts were written and reread;
9. no evidence class was silently promoted;
10. the mandatory RAE status footer lists `hypofusion` among registered short commands.

## Scientific boundary

`hypofusion` is deliberately adversarial but not reflexively skeptical. A contrary paper is a possible argument until its method, scope and independence justify weight. Likewise, a matching external architecture is an analogue until the same causal mechanism has been tested. The goal is not consensus; the goal is higher-information hypotheses and experiments.