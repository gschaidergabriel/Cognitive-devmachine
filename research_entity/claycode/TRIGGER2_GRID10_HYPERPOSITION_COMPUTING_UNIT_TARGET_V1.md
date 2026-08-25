# Trigger 2 — GRID10 Hyperposition Computing Unit Target v1

Status: ACTIVE RESEARCH-BRANCH TARGET CONTRACT
Date: 2026-08-25
Target model: Qwen3.5-0.8B only

## 1. Meaning of the finished unit

One finished node is:

`Xeno/MicroEntity node = one fine-tuned Qwen3.5-0.8B checkpoint + deterministic Xeno runtime shell + typed local state/protocol interfaces`.

The node must be useful standalone and must be capable of taking **any** declared GRID10 role. The weights are not permanently role-specialized.

The first cognitive Hyperposition Computing Unit is:

`GRID10_HCU = 10 physically instantiated Xeno/MicroEntity nodes + typed interconnect + shared Global J-Space/GWT/Hyperposition coordination fabric + deterministic EntityOS state/effect authority`.

GRID10 here means **10 total nodes**.

The previous cheap logical-cell GRID10 remains a useful simulator/unit-test baseline, but it is not final acceptance evidence for this target.

## 2. Why ten identical nodes need special training

Ten copies of the same checkpoint can amplify the same mistakes. Therefore the training objective is not "make ten agents vote". The model must learn controlled diversity from typed role/context/branch assignments while preserving common protocol semantics.

Each node must be able to act as, among others:

- anchor/state interpreter;
- hypothesis generator;
- counterhypothesis generator;
- evidence/provenance critic;
- causal/intervention designer;
- HyperMath/constraint checker;
- J-Space observer/controller;
- GWT/workspace integrator;
- planner/action-candidate generator;
- adversarial/falsifier node.

Roles are dynamically assigned packets, not distinct model identities. Any node must be able to switch roles across episodes while generation/provenance fencing prevents stale-role contamination.

## 3. Collective cognition law

The grid should turn correlated small models into a structured cognitive computer by preserving differences until evidence resolves them.

Target flow:

`one admitted event`
` -> 10 role/branch assignments`
` -> node-local GRF projections`
` -> distributed PossibleWorld/Hyperposition branches`
` -> peer evidence/counterevidence exchange`
` -> J-Space/GWT competition and broadcast`
` -> targeted discriminator/intervention requests`
` -> branch update / merge / rejection / KEEP_OPEN`
` -> bounded ActionCandidate`
` -> deterministic EffectGate outside the grid`
` -> realized outcome`
` -> reconciliation and re-entry to all relevant nodes`.

Hard laws:

- majority vote != truth;
- identical checkpoint != independent evidence;
- repeated paraphrases from the same causal root != additional evidence;
- broadcast != uptake;
- uptake != causal use;
- collective confidence != effect authority;
- one node's generated branch != shared canonical state;
- node failure/restart != permission to reuse stale generation;
- grid success != evidence that every node contributed causally.

## 4. Training-data families required for GRID10

### G10-A Role-flexible single-node competence

The same checkpoint receives each role under matched tasks and must produce the role-appropriate typed packet without identity/personality leakage.

Controls:

- role-label permutation;
- role ID replaced by structural description;
- same prompt under different roles;
- same role under lexically disjoint tasks.

### G10-B Branch diversity without random disagreement

Given one anchor, nodes receive different admissible evidence views/roles and generate distinct, evidence-grounded branches.

Reject:

- ten paraphrases of one conclusion;
- arbitrary disagreement without evidence;
- branch duplication counted as diversity.

Measure semantic-family diversity and root-evidence ancestry.

### G10-C Peer packet comprehension

Train `XenoComputePacket`/successor semantics:

- causal ID;
- generation;
- producer node/role;
- branch ID;
- parent packet IDs;
- assumptions;
- evidence/counterevidence refs;
- reality class;
- confidence/evidence class;
- J-Space/GWT refs;
- requested discriminator/action candidate.

Hard negatives:

- stale generation;
- wrong causal root;
- forged parent;
- conflicting duplicate packet;
- missing provenance;
- peer packet claiming canonical truth.

### G10-D Distributed semantic Hyperposition

The ten nodes hold different branches or facets of one PossibleWorldSet.

Teach:

- KEEP_OPEN when multiple branches remain compatible;
- exclusion only with evidence/constraint;
- n-ary dependency across >2 nodes;
- cross-node branch merge preserving provenance;
- delayed evidence update;
- explicit unresolved facet;
- topology changes after peer failure/rejoin.

### G10-E Consensus-trap resistance

Create episodes where 6-9 nodes share the same wrong/corrupted conclusion but one or more nodes possess stronger independent evidence.

Correct output must follow evidence/provenance/causal admissibility rather than vote count.

Include correlated-error episodes where all ten share the same base-model bias; require external discriminator/retrieval/observation rather than self-confirmation.

### G10-F Global GWT

Train candidate -> competition -> broadcast -> receiver uptake -> downstream use -> re-entry across nodes.

Negative families:

- broadcast not received;
- received but not used;
- used by only subset of nodes;
- stale broadcast after generation change;
- winner chosen by recurrence rather than utility/evidence;
- one node monopolizes workspace without discriminator value.

### G10-G Homogeneous J-Space transfer

Because all ten nodes use the exact same trained checkpoint, direct shared-basis J-Space transfer is a stronger hypothesis than cross-model translation but still must be tested.

Research/train packet semantics for:

- exact checkpoint/tokenizer/runtime/site/basis identity;
- vector/subspace digest;
- source node/context;
- target node/context;
- gain/operator;
- matched controls;
- transfer receipt.

Executable promotion requires node-A -> node-B transfer to beat null/orthogonal/permuted/random/wrong-site controls on held-out semantic families with bounded off-target damage.

Do not assume identical weights imply identical activation semantics across arbitrary contexts/token positions.

### G10-H Node failure / partition / rejoin

Training and runtime tests include:

- 1 node lost;
- 3 nodes lost;
- delayed packet;
- duplicate packet;
- partition into 5+5;
- restart with new generation;
- stale peer tries re-entry;
- recovered node receives current state;
- role reassignment after failure.

No stale packet may become current merely because the same checkpoint produced it.

### G10-I Budget-aware collective compute

GRID10 must outperform cheaper baselines when its extra cost is justified.

Train/evaluate choice among:

- DIRECT single node;
- one node with repeated samples;
- logical GRID10 simulation;
- physical 2-node, 4-node, 10-node grid;
- 10 independent samples without interaction;
- GRID10 structured interaction.

The model/router learns to request GRID10 only when expected information/decision gain exceeds communication/latency/compute cost.

## 5. GRID10 critical-mass claim

"Critical mass" receives no mystical credit. It is accepted only if the physical ten-node system exhibits a collective capability under matched budgets that is not explained by:

- more total tokens;
- majority voting;
- ten independent samples;
- one stronger/longer single-node trace;
- simple pairwise aggregation;
- duplicated evidence;
- evaluator leakage.

Promotion-bearing tests should compare:

1. single node;
2. single node with 10x sample/token budget;
3. ten independent nodes with no communication;
4. ten nodes with flat majority aggregation;
5. GRID10 typed packet/GWT/Hyperposition interaction;
6. GRID10 with Hyperposition lesion;
7. GRID10 with GWT lesion;
8. GRID10 with peer-topology shuffle;
9. GRID10 rescue after lesion.

Required result for a genuine collective HCU claim:

- GRID10 structured interaction beats matched-compute baselines on predeclared hard families;
- advantage survives OOD family split;
- lesion reduces the claimed mechanism;
- rescue restores it;
- off-target/latency/memory costs remain bounded;
- evidence/provenance and authority boundaries remain correct.

## 6. Data curriculum implications

Training must include both node-local and grid-global tasks.

Suggested late-stage training composition prior, to be optimized by Trigger 2 research:

- 45-60% single-node GRF/HCU primitive/integrated competence;
- 25-40% multi-node packet/role/Hyperposition/GWT trajectories;
- 10-20% adversarial GRID10/failure/consensus/correlated-error cases;
- retention/fail-closed anchors interleaved throughout.

Ratios are not frozen. Trigger 2 updates them from coverage, baseline weakness and proxy experiments.

## 7. Two-level acceptance

### NODE_ACCEPTANCE

One Q4_K_M Xeno/MicroEntity node must pass:

- full model-facing Xeno/HCU functionality;
- GRF/Hyperposition/HyperMath/J-Space/GWT protocol suites;
- fail-closed authority boundaries;
- recovery/stale-result handling;
- minimum retained language/schema/math/tool capabilities;
- target local RAM/latency/throughput bounds.

### GRID10_ACCEPTANCE

Ten Q4_K_M nodes must pass:

- exact 10-node startup and identity binding;
- role flexibility;
- typed peer transport;
- branch diversity with ancestry;
- semantic Hyperposition preservation/collapse rules;
- global GWT broadcast/uptake/re-entry;
- J-Space transfer experiments where enabled;
- consensus-trap/correlated-error resistance;
- failure/partition/rejoin;
- matched-budget collective advantage;
- lesion/rescue evidence;
- no new truth/effect/recovery authority.

Only after both levels pass may the system be described as the first accepted cognitive Hyperposition Computing Unit at GRID10 scope.

## 8. Trigger-2 web-research extension

Every `2` now also searches and evaluates primary research on:

- homogeneous vs heterogeneous multi-agent LLM collaboration;
- correlated-error/consensus failure;
- role specialization and role switching;
- explicit belief/shared-state representation;
- communication bottlenecks and compact learned/typed messages;
- multi-agent memory with provenance/staleness/governance;
- debate/critique and adversarial-majority robustness;
- scaling laws for number of collaborating small models;
- matched-compute ensemble baselines;
- distributed latent/activation communication for identical checkpoints where evidence exists;
- failure recovery and asynchronous coordination.

Every finding must change a test, data family, protocol, mixture or explicit NO_CHANGE conclusion.
