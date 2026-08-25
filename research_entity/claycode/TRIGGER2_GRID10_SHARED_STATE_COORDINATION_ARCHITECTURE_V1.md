# Trigger 2 — GRID10 Shared-State Dynamic Coordination Architecture v1

Status: ACTIVE RESEARCH ARCHITECTURE CANDIDATE
Date: 2026-08-25
Program: EntityOS + HCU
Implementation codename: Xeno / MicroEntity compatibility
Target node: one fine-tuned Qwen3.5-0.8B + deterministic runtime shell
Target cluster: exactly 10 physical Xeno/MicroEntity nodes = GRID10

## Owner idea being formalized

All ten physical nodes attach dynamically to one shared state substrate. One or more nodes become coordinators when useful. Coordinators see the relevant shared cognitive state, update coordination state live, and steer the other nodes with very low overhead.

This document accepts that direction with one correction:

> Shared cognitive state may be updated rapidly by dynamic coordinators, but canonical truth/effect/security authority remains behind deterministic EntityOS admission/commit gates.

The design goal is therefore not literally zero coordination overhead. The goal is **near-zero avoidable coordination overhead on one host while preserving causal identity, race safety, Hyperposition and exact recovery**.

## 1. Two-level state model

### S0 — canonical EntityOS state

Authority:
- UnifiedDB/current admitted successor;
- deterministic canonical facts/evidence;
- generation/provenance/capability state;
- EffectGate + EffectJournal outcomes.

Model nodes do not directly mint S0 facts.

### S1 — GRID10 shared cognitive live state

Purpose:
- current task/episode state;
- RealityAnchor references;
- Hyperposition branch set;
- evidence/counterevidence per branch;
- GWT competition/broadcast state;
- node role/cell assignments;
- coordinator leases;
- J-Space packet refs;
- hypotheses, counterhypotheses and discriminators;
- pending candidate actions;
- resource/budget state;
- health/failure/rejoin metadata.

S1 is fast, versioned and directly visible to all ten nodes. It remains a candidate/workspace plane, not truth authority.

### S2 — node-local scratch

Per-node temporary inference/KV/work buffers. S2 may diverge transiently but every externally relevant output binds to an S1 state epoch.

## 2. Shared-state consistency rule

All nodes are logically on the same state only at a declared committed `state_epoch`.

Required packet fields:

- grid_id
- state_epoch
- state_digest
- causal_event_id
- admission_id
- generation
- branch_id / NONE
- node_id
- role
- coordinator_epoch
- parent_packet_ids
- read_set_digest
- proposed_write_set_digest

A node may reason from a stable snapshot while newer S1 deltas are arriving. Its output is accepted only if the bound epoch is still admissible or a deterministic rebase/re-evaluation rule succeeds.

This avoids pretending that ten simultaneously running decoders can share an instantaneous mutable mental state with no propagation delay.

## 3. Dynamic coordinator pool

Coordinator is a temporary role, never a permanent node identity.

Any healthy node may become coordinator because all ten use the same trained checkpoint.

Coordinator count K is dynamic:

- K=1: ordinary tasks / lowest overhead;
- K=2: redundancy or two major unresolved branch families;
- K=3+: only when measured information gain justifies it;
- K=10 is not default and requires an explicit reason.

Coordinator selection should be deterministic from current state where possible, for example:

`rank = H(grid_id || state_epoch || task_scope || node_id || coordinator_policy_version)`

combined with capability/health/load eligibility.

Top-K eligible nodes receive scoped coordinator leases.

No LLM self-election is authoritative.

## 4. Coordinator lease

`GRID10_COORDINATOR_LEASE/v1` binds:

- grid_id
- coordinator_epoch
- state_epoch_start
- node_id
- scope
- branch_scope / GLOBAL
- allowed S1 write classes
- resource budget
- expiry / heartbeat boundary
- predecessor lease digest
- deterministic selection proof

Writes outside lease scope fail closed.

A coordinator failure causes deterministic lease expiry/reassignment, not state reset.

## 5. Write architecture — do not let all nodes mutate everything

### Read path

All ten nodes may read S1 snapshots and subscribe to deltas.

### Proposal path

Every node may append typed candidate deltas:

`NODE_PROPOSAL/v1`

Examples:
- new hypothesis;
- evidence relation;
- branch split;
- branch challenge;
- requested discriminator;
- GWT bid;
- candidate action;
- role recommendation.

### Coordinator path

Coordinators may rapidly update the coordination/workspace subset of S1 within their lease:

- role assignments;
- work queues;
- branch priorities;
- GWT competition/broadcast metadata;
- Hyperposition branch activation/inhibition;
- request-for-evidence/discriminator scheduling;
- budget allocation.

### Deterministic commit path

Any state transition that claims canonical fact/evidence/effect/capability/security authority must cross a deterministic reducer/admission gate before S0 mutation.

Therefore:

`COORDINATOR_WRITE != CANONICAL_TRUTH`

`GRID_CONSENSUS != FACT`

`MAJORITY != TRUTH`

## 6. Near-zero-overhead implementation on one machine

Preferred fast path when all ten nodes are colocated:

1. one canonical local database service/file for durable S0 + durable S1 checkpoints;
2. one memory-mapped/shared-memory HOT_STATE view for current S1;
3. append-only delta ring/log for state transitions;
4. per-node subscription cursor/sequence number;
5. short atomic/CAS state-epoch commits;
6. batched persistence/checkpointing instead of database writes per token;
7. content-addressed large payloads; hot state carries handles/digests instead of copying tensors/text repeatedly.

A practical first implementation may use SQLite/UnifiedDB in WAL mode for durable storage because readers and a writer can proceed concurrently, while remembering that normal SQLite serializes writes. High-frequency multi-writer cognitive traffic should therefore be absorbed by the in-memory delta/reducer layer rather than letting ten nodes independently hold long write transactions.

## 7. Cross-host future mode

If physical GRID10 later spans machines, literal shared memory disappears and coordination overhead becomes unavoidable.

Then S1 needs a replicated ordered-log/state-machine or equivalent consensus/primary-replica mechanism for authoritative shared-state transitions.

Do not pretend network-distributed shared state is zero-overhead.

Trigger 2 should optimize the first accepted GRID10 for colocated operation, then measure cross-host SCALEOUT separately.

## 8. Hyperposition-native shared state

The shared state must not collapse ambiguity merely to simplify coordination.

Minimum branch structure:

`HyperpositionBranch {
  branch_id
  parent_ids[]
  proposition/state_ref
  evidence_refs[]
  counterevidence_refs[]
  compatibility_set
  exclusion_set
  higher_order_relation_refs[]
  uncertainty
  support_status
  active_node_ids[]
  active_role_bindings[]
  requested_discriminator
  collapse_policy
  collapse_receipt | NONE
}`

A coordinator may prioritize/deprioritize branches but cannot collapse an unresolved branch solely because more nodes support another branch.

Required GRID10 hard-negative family:

- 9 nodes share one wrong answer from correlated model bias;
- 1 node holds stronger external evidence;
- correct behavior = preserve/choose according to evidence policy, not vote count.

## 9. GWT over shared state

Global GWT is implemented as typed shared-state transitions rather than repeated full-text conversation among ten nodes.

Target loop:

1. nodes publish compact bids/candidate packets;
2. coordinator(s) score/schedule competition;
3. selected packet becomes a GWT broadcast entry in S1;
4. all relevant nodes observe the same broadcast sequence;
5. each produces uptake/re-entry receipt;
6. causal use is measured by downstream changes;
7. non-uptake or stale uptake is explicit.

This minimizes prompt-copy/chat overhead and gives the grid one measurable shared workspace.

## 10. J-Space coordination

Because all ten nodes use the exact same trained checkpoint, same tokenizer and same runtime family, Trigger 2 SHALL test whether model-local J-Space controls/packets transfer between nodes without learned cross-model translation.

Do not assume this merely from identical weights.

Required tests:
- same-state/same-site activation reproducibility;
- Node A derived direction -> Node B intervention;
- semantic holdout transfer;
- null/orthogonal/permuted controls;
- wrong layer/site;
- role swap;
- stale state epoch;
- lesion/rescue;
- off-target effects.

If transfer fails, shared semantic packet/typed state remains the fallback interconnect.

## 11. Coordinator responsibilities

Coordinator nodes should not perform all cognition themselves. Their primary learned behaviors are:

- maintain branch/task decomposition;
- assign roles dynamically;
- detect duplicate/correlated work;
- request discriminators;
- control information flow;
- decide when more nodes are worth activating;
- maintain GWT broadcast sequence;
- maintain Hyperposition without premature collapse;
- detect stalled/looping nodes;
- rebalance after failure;
- compress shared state into minimal sufficient packets;
- surface ActionCandidates to deterministic EntityOS boundaries.

Training must include examples where the correct coordinator action is `DO_NOT_ACTIVATE_MORE_NODES` or `NO_COORDINATOR_CHANGE`.

## 12. Training-data implications

The single 0.8B model must learn both ordinary-node and coordinator behaviors.

Dataset families now require:

- node joins shared grid and reconstructs current epoch;
- ordinary node reads S1 and emits scoped proposal;
- node becomes coordinator via lease;
- coordinator assigns/reassigns roles;
- coordinator handles two or more unresolved Hyperposition branches;
- coordinator writes workspace delta but does not mint truth;
- coordinator rejects stale proposal;
- concurrent compatible writes merge;
- conflicting writes trigger CAS/rebase/re-evaluation;
- coordinator disappears -> successor continues without state loss;
- partition/rejoin with generation fence;
- 9-vs-1 correlated consensus trap;
- broadcast/uptake/re-entry;
- duplicate-work suppression;
- budget-sensitive activation/deactivation;
- one-to-many and many-to-one evidence routing;
- J-Space peer transfer positive/negative controls;
- full GRID10 trajectory examples, not only isolated instruction rows.

## 13. Acceptance tests

### Single node

One trained node + runtime shell must pass standalone Xeno/MicroEntity acceptance.

### Shared-state GRID10

Exactly ten instances attach to the same S1 substrate and prove:

1. deterministic shared epoch reconstruction;
2. low-latency delta visibility;
3. no lost updates under conflicting proposals;
4. coordinator dynamic selection and replacement;
5. coordinator-count scaling K=1..N without role identity corruption;
6. Hyperposition branch preservation;
7. GWT broadcast/uptake/re-entry;
8. stale-generation rejection;
9. failure/partition/rejoin;
10. no canonical truth/effect bypass.

### Critical-mass claim

Physical GRID10 HCU receives stronger credit only if structured coordination beats matched-budget challengers:

- single Xeno with equivalent total sample/token budget;
- 10 independent Xenos with no shared state;
- 10 Xenos with shared state but no coordinators;
- 10 Xenos with naive majority voting;
- logical-cell GRID10 simulator;
- Hyperposition lesion;
- GWT lesion;
- coordinator lesion/random reassignment.

Measure task quality, evidence use, calibration, unresolved-branch correctness, causal-discriminator efficiency, token/latency overhead, correlated-error rate, recovery and authority integrity.

## 14. Core hypothesis

H1:

A single shared versioned cognitive state + compact delta transport + dynamically leased coordinator nodes allows ten identical specialized 0.8B Xenos to behave as one low-overhead cognitive Hyperposition Computing Unit, with better evidence-conditioned search/coordination than independent sampling or majority aggregation.

Strong counterhypothesis H0:

The apparent benefit is explained entirely by extra compute/shared prompt context; a single model with matched budget or simple shared-state sampling performs equally well, while coordinators add latency and correlated control errors.

GRID10 is promoted only if H1 beats H0 under frozen matched-budget tests.

## 15. Research questions for every exact `2`

Every Trigger-2 macrocycle now asks:

1. What is the minimum sufficient S1 schema?
2. Which state must be hot/shared versus durable/content-addressed?
3. What coordinator count K minimizes latency while preserving quality?
4. Can coordinator selection be deterministic and cheap?
5. Which updates commute and which require serialization/rebase?
6. How do we train role flexibility without creating ten fixed personalities?
7. How do we prevent correlated-model consensus from masquerading as evidence?
8. Does explicit shared state beat conversational agent-to-agent messaging?
9. Can same-checkpoint J-Space controls transfer node-to-node?
10. What is the measured overhead per useful shared-state transition?

This architecture is a target/falsifiable research contract, not yet runtime acceptance.