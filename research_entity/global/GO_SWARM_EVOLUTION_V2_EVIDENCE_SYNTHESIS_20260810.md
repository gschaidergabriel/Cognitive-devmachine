# GO Swarm Evolution v2 — Data-Driven Evidence Synthesis — 2026-08-10

**Status:** RESEARCH SYNTHESIS / INPUT TO OWNER-FIXED GO PROTOCOL EVOLUTION  
**Goal:** Frank v0.1 fully operational on Andreas Ubuntu developer system  
**Scope:** exact `go`, swarm coordination, live external research, OmniSource re-entry, adaptive routing, q23 bidirectional integration.

## 1. Why GO needs a stronger v2

The current GO protocol already contains the correct high-level loop: refresh, self-coordinate, live-web intake, hypothesis/counterhypothesis, build/test/measure, fuse, distribute and recurse. The latest repository evidence shows that the next bottleneck is not lack of activity. It is **coordination under very high state churn, information-flow selectivity, stale-work detection, and converting broad research activity into measurable cross-worker causal progress without flooding contexts or duplicating work.**

This synthesis treats the user's request for longer/deeper GO runs and broader live Internet research as a request for **maximum useful depth**, not repetition or hidden chain-of-thought persistence. The visible GO result should use as much of the available output budget as materially useful to report evidence, deltas, counterevidence, measurements, unresolved questions and next frontier. Worker-to-worker communication should remain compact, reference-based and selectively pullable.

## 2. Internal empirical signals from current swarm behavior

### I1 — High concurrent state churn is real

The 18:01 live-fusion manifest observed **48 new commits** between its durable-close base and initial input cut. This means a long worker can easily execute against a work specification that changes while it is running.

Implication:

- every material worker effect needs exact `work_id + spec_rev + repo_head + component/model/runtime hashes + execution_start` binding;
- technically successful but stale executions remain valuable diagnostics but cannot receive current-work completion credit;
- long GO recursion must repeatedly re-read current state, not merely refresh once per invocation.

### I2 — Revision guards cost throughput but prevent false credit

OmniSource V10's stronger current-work revision guard preserved stale diagnostics, rejected stale current-work credit and passed 11/11 sandbox checks, but the same general sandbox lane showed lower throughput after the stronger guard (~21.9k pairs/s vs ~29.3k pairs/s before the work-revision guard).

Implication:

- correctness-critical semantic/work-version guards should remain;
- use them selectively at promotion/effect boundaries rather than forcing maximal heavy validation on every low-materiality digest;
- measure coordination overhead instead of assuming more checking is free.

### I3 — Observation can perturb the system being observed

The GO observer-backaction shadow factorial found same-file observation roughly **3.42x / 3.80x / 3.81x p50/p95/p99** receipt-commit latency relative to no observer and roughly **50x primary WAL bytes**. Isolated observation was far cheaper (about 1.10x / 1.25x / 2.37x latency and ~1x primary WAL bytes), with integrity/restart checks passing in the shadow workload.

Implication:

- do not implement stronger live fusion as every worker continuously reading/writing the same hot persistence surface;
- favor isolated observation/control projections, compact digests, pull-on-demand payloads and asynchronous/rebuildable indexes;
- swarm observability itself requires a resource/backaction budget.

### I4 — Targeted duplicate suppression already works and should become explicit telemetry

One GO run verified that a material result had already been ingested and distributed by Hypofusion, and deliberately avoided duplicate feedback writes.

Implication:

- `duplicate_work_avoided`, `duplicate_distribution_avoided`, and `shared_ancestry_reuse` should be first-class positive swarm metrics;
- worker productivity should not be measured by number of writes or messages.

### I5 — Correlated control planes do not create independent evidence

The live-fusion research preserved the negative result that a second projection/control plane gives no recall advantage when missing-edge ancestry is fully correlated with the first.

Implication:

- greater worker count, denser communication or duplicate model prompts do not equal replication;
- swarm diversity must be measured by source/assumption/fixture/implementation ancestry, not agent labels.

### I6 — Current q23 work is high-value but remains unexecuted

The 18:01 fusion cut recognized the Q23 multimodal Retina/Qwen/MVC-to-UnifiedDB/EAP candidate while preserving the fact that its discriminating test obligations were still unexecuted.

Implication:

- GO must ingest q23 research deltas in both directions, but cannot let a well-connected research branch bypass executable H1/H2/H3 gates;
- GO should use q23 as a specialist frontier generator and q23 should use GO as a whole-mesh evidence/build/test feeder.

## 3. External current research fused into the redesign

The sources below are used as **mechanism candidates and counterevidence**, not as proof that they should be copied into Clay.

### E1 — CORAL: long-running autonomous multi-agent evolution

- Ao Qu et al., **CORAL: Towards Autonomous Multi-Agent Evolution for Open-Ended Discovery**, arXiv:2604.01658 (2026).
- Code: `Human-Agent-Society/CORAL` on GitHub.

Relevant mechanism: long-running agents, shared persistent memory, asynchronous execution, heartbeat interventions, evaluator separation, isolated workspaces and health/session management. Reported open-ended optimization gains motivate testing sustained multi-agent exploration rather than single-pass delegation.

GO implication: explicit worker heartbeat/lease freshness, persistent shared outcome memory, isolated workspaces/control surfaces, and evaluator/falsifier separation.

### E2 — GraphPlanner: historical interaction memory for routing

- Tao Feng et al., **GraphPlanner: Graph Memory-Augmented Agentic Routing for Multi-Agent LLMs**, arXiv:2604.23626 / ICLR 2026.
- Code: `ulab-uiuc/GraphPlanner`.

Relevant mechanism: routing decisions use historical query-agent-response interaction memory, not only static role descriptions.

GO implication: maintain evidence-based `WorkerCapabilityProfile` / `WorkOutcomeProfile` as a routing prior. Do not permanently assign topics; use historical success, stale-result rate, execution availability, falsifier yield and cost as decision support.

### E3 — DecentMem: centralized shared memory can collapse diversity

- Guangya Hao, Yunbo Long, Zhuokai Zhao, **Self-Evolving Multi-Agent Systems via Decentralized Memory**, arXiv:2605.22721 (2026).

Relevant mechanism: per-agent exploitation/exploration memory can preserve diversity and reduce communication/token overhead relative to a fully centralized shared-memory baseline in the reported experiments.

GO implication: do not force every worker's exploratory scratch material into global shared memory. Keep worker-local exploration hypotheses until material; publish provenance-bound deltas and reusable results to the institutional shared layer.

### E4 — Shared Selective Persistent Memory: full history can harm

- Sanjana Pedada, Aditya Dhavala, Neelraj Patil, **Shared Selective Persistent Memory for Agentic LLM Systems**, arXiv:2607.09493 (2026).

Relevant mechanism: selective reusable memory outperformed both no memory and naive full-history persistence in their scenarios; full history could bias agents with stale traces.

GO implication: maximize useful reasoning/output depth without equating depth to raw context accumulation. UnifiedDB/ClayGraph should retrieve task-conditioned assemblies; inter-worker messages should be compact references plus provenance, with full payload pulled only when needed.

### E5 — Dynamic communication topology should be task-adaptive

- Eric Hanchen Jiang et al., **Dynamic Generation of Multi-LLM Agents Communication Topologies with Graph Diffusion Models**, arXiv:2510.07799 (2025).

Relevant mechanism: static/hand-crafted topologies can waste communication on simple tasks and bottleneck complex tasks; adaptive sparse topology is treated as a multi-objective optimization problem.

GO implication: evolve the current Live Fusion Mesh from fixed targeting/broadcast toward telemetry-conditioned route selection among targeted delta, dense fanout, digest-only and pull subscriptions.

### E6 — Governed Shared Memory: stale propagation and provenance collapse are systems problems

- Yanki Margalit et al., **Governed Shared Memory for Multi-Agent LLM Systems**, arXiv:2606.24535 (2026).

Relevant mechanism: explicit scoped retrieval, temporal supersession, provenance tracking and policy-governed propagation; live evaluation exposed scope/order failures that design-only reasoning missed.

GO implication: preserve current Clay laws: ingestion/delivery never mint truth; stale work must not silently promote; provenance and supersession need explicit receipts and fault injection.

### E7 — AMA / adaptive memory granularity and iterative conflict repair

- Weiquan Huang et al., **AMA: Adaptive Memory via Multi-Agent Collaboration**, arXiv:2601.20352 / Findings of ACL 2026.

Relevant mechanism: constructor/retriever/judge/refresher roles, multi-granularity memory, conflict-triggered refresh and iterative retrieval.

GO implication: the shared mesh should support `KnowledgeNeed` requests from workers, retrieval refinement when evidence is insufficient, and explicit contradiction repair instead of one-shot broadcast.

### E8 — Peer-reviewed / publisher-source ecology matters

Relevant current examples include:

- Shuo Liu et al., **LLM Collaboration with Multi-Agent Reinforcement Learning**, AAAI 2026, DOI: 10.1609/aaai.v40i38.40487.
- A. Tiwari & V. Gupta, **A memory fabric for conversational AI agents enabling shared and persistent multiuser memory**, Discover Artificial Intelligence 6, 239 (2026), DOI: 10.1007/s44163-026-00992-z.

GO implication: live research should not be limited to arXiv/GitHub. For material questions, its source ecology should actively consider current journal/conference publisher records, standards, official implementations, datasets, issue trackers and independent replications.

## 4. GO v2 architecture decisions derived from evidence

### D1 — GO becomes a telemetry-driven recursive research controller

Every major GO cycle computes a `SwarmTelemetrySnapshot` and evaluates whether the current communication/routing/work assignment is producing measurable progress.

Key metrics:

- material progress deltas per cycle;
- executable evidence yield;
- hypothesis/falsifier creation and closure;
- duplicate work/distribution avoided;
- stale-work-result rate;
- work-revision drift rate;
- branch re-entry closure rate;
- contradiction survival/resolution;
- affected-branch recall and false interrupts;
- worker capability-fit accuracy;
- source lineage diversity;
- external evidence novelty per retrieval;
- cross-branch reuse;
- coordination and observer backaction cost;
- token/context/network/I/O cost per accepted delta;
- time/steps from new evidence to affected plan revalidation.

### D2 — Worker routing uses historical outcomes but never creates permanent castes

Maintain a `WorkerCapabilityProfile` keyed to capability/evidence history, including execution surfaces and topic-specific success/failure. Historical performance changes bid priors, but workers can still explore new domains and no profile creates truth authority.

### D3 — Two-layer memory: local exploration + shared institutional evidence

Worker-private/local exploration state may contain speculative branches and incomplete reasoning artifacts. Only material, provenance-bound outcomes/hypotheses/questions/negative results enter the shared institutional layer.

This preserves diversity and reduces echo while keeping durable team learning.

### D4 — Communication becomes request/response + delta/ack, not only push

Add explicit message classes:

- `KnowledgeNeed` — a worker asks the mesh for a specific missing fact/mechanism/test/result;
- `DiscoveryBeacon` — compact new evidence/hypothesis notice;
- `MaterialDelta` — provenance-bound semantic/work/architecture delta;
- `PullRequest` — receiver requests full payload or linked subgraph;
- `CounterChallenge` — adversarial worker requests evidence against a claim;
- `ReentryAck` — delivered/reconstructed/plan-revalidated/used/effect distinctions;
- `SaturationNotice` — branch reports locally exhausted route plus attempts already tried.

### D5 — Live topology is adaptive but isolated from the hot truth store

Route mode chosen from:

`TARGETED_FULL_REF | TARGETED_DIGEST | DENSE_FANOUT | SUBSCRIPTION_PULL | ANTI_ENTROPY_REPAIR | INDEX_ONLY`.

The route planner considers affected dependency span, urgency, branch load, stale risk, payload size, source lineage, current subscriptions and predicted repair cost.

Observation/control indexes should be rebuildable/isolated where possible so the swarm does not create the same-file observer backaction measured in I3.

### D6 — GO performs a broad source-ecology sweep plus recursive deep dives

Each exact GO invocation should conduct fresh external research. The first major research phase samples relevant current sources across multiple classes where available:

- official/current runtime, model, library, standard or provider source;
- primary paper/preprint;
- peer-reviewed journal/conference/publisher metadata where relevant;
- primary GitHub/open-source implementation or competing project;
- issue tracker/release notes/benchmark/dataset/failure evidence;
- independent replication/countermechanism when material.

Then GO follows the highest-information references/citations/code paths recursively. A long GO run must refresh externally again after material direction changes.

### D7 — Max useful output, not raw token burning

The final visible GO report should use the largest useful output depth available, including:

- what changed;
- measured data;
- fresh external evidence and source classes;
- hypotheses and strongest counterhypotheses;
- architecture/work/test deltas;
- negative results;
- swarm telemetry and coordination changes;
- q23 cross-feedback;
- unresolved blockers;
- next high-information frontier.

No filler, no duplicated source summaries, and no hidden chain-of-thought persistence. The system optimizes **material information per visible token**, while still preferring a long comprehensive report over an artificially short one for exact `go`.

### D8 — GO ↔ q23 is explicitly bidirectional

`go -> q23`:

- route all material multimodal, vision, GUI, Retina, MVC, <=4B model, visual-memory, perceptual-EAP, multimodal embedding and active-sensing deltas;
- route build/runtime failures that constrain q23 hypotheses;
- route new external projects/papers that open q23 frontier branches;
- answer q23 `KnowledgeNeed` requests using whole-mesh/runtime capability.

`q23 -> go`:

- feed material q23 packages, hypotheses, counterhypotheses, tests, architecture deltas and negative results into GO's whole-system frontier;
- GO decides whether each delta changes critical-path work, requires executable Harness evidence, affects another branch or stays research-only;
- q23 cannot grant its own build/release credit.

The bridge exchanges **questions as well as answers** and tracks closure.

## 5. Falsifiers for GO v2 itself

GO v2 must be treated as a measurable coordination architecture, not an owner-preference proof.

Strongest falsifiers:

1. `COORDINATION_OVERHEAD_DOMINATES`: telemetry/profile/ack layers reduce build/research throughput without reducing stale/collision/error rates.
2. `ROUTING_PROFILE_LOCKIN`: historical worker profiles suppress useful exploration and create permanent specialization/correlation.
3. `SELECTIVE_MEMORY_MISSES`: selective shared memory causes materially relevant findings to remain private or undiscovered.
4. `ADAPTIVE_TOPOLOGY_NO_GAIN`: fixed targeted routing performs equally well with lower complexity on real repo replay.
5. `LIVE_WEB_NOISE`: mandatory broad source sweeps increase context/noise without changing decisions or falsifiers.
6. `Q23_COUPLING_CAPTURE`: q23's high research activity pulls GO away from the actual staged critical path without executable benefit.
7. `MAX_OUTPUT_NO_GAIN`: longer reports consume user/context budget without increasing reproducibility, decision quality or handoff continuity.

These require matched replay and telemetry, not narrative adjudication.

## 6. Promotion/testing frontier

Required GO v2 evaluation should compare current GO protocol versus GO v2 on replayed real repository episodes with:

- high concurrent commit churn;
- work-revision change mid-execution;
- duplicate worker discovery;
- missing dependency edge;
- high-impact invalidation;
- correlated pseudo-replication;
- q23 material delta and q23 question request;
- stale external source replaced by newer primary source;
- broad research question requiring journal/arXiv/GitHub/issue/dataset traversal;
- worker crash/lease expiry/restart;
- observer backaction/resource accounting.

Report correctness, stale-current-credit errors, duplicate work, branch recall, false interrupts, time/steps to reentry closure, useful external novelty, executable progress, coordination cost and visible report information density.

**No GO v2 routing/mesh component is promoted merely because it sounds more interconnected.**
