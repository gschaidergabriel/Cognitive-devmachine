# Trigger 2 — GRID10 Shared-State Dynamic Coordination Architecture v2

Status: ACTIVE RESEARCH ARCHITECTURE CANDIDATE — SUPERSEDES V1 WRITE MODEL
Date: 2026-08-25
Program: EntityOS + HCU
Implementation codename: Xeno / MicroEntity compatibility
Target node: one fine-tuned Qwen3.5-0.8B + deterministic runtime shell
Target cluster: exactly 10 physical Xeno/MicroEntity nodes = GRID10

## 0. Hard owner law

**Only dynamically leased coordinator nodes may write the shared cognitive state S1.**

Ordinary GRID10 modules are strictly read-only with respect to S1. They read the same versioned shared state, perform their assigned cognition locally, and return a typed result directly to an active coordinator through an ephemeral result channel. The coordinator is the only model-facing role allowed to commit that result into S1.

Therefore:

`ORDINARY_NODE -> READ_S1 + COMPUTE + RETURN_TO_COORDINATOR`

`COORDINATOR -> READ_S1 + RECEIVE_RESULTS + ARBITRATE + WRITE_S1`

`ORDINARY_NODE_WRITE_S1 = FORBIDDEN`

`NO_VALID_COORDINATOR_LEASE -> NO_S1_WRITE`

This is a stronger rule than v1, which allowed ordinary nodes to append proposals. That path is superseded.

## 1. State hierarchy

### S0 — canonical EntityOS state

S0 remains the deterministic authority plane:
- UnifiedDB/current admitted successor;
- canonical facts/evidence;
- generation/provenance/capability state;
- EffectGate + EffectJournal outcomes.

Neither ordinary nodes nor coordinators may mint S0 truth directly from model output.

### S1 — GRID10 shared cognitive live state

S1 is the common cognitive workspace visible to all ten nodes:
- current task/episode state;
- RealityAnchor references;
- Hyperposition branch graph;
- evidence/counterevidence references;
- GWT competition/broadcast state;
- role assignments and work queues;
- coordinator leases;
- J-Space packet references;
- hypotheses/counterhypotheses/discriminators;
- pending ActionCandidates;
- resource/budget state;
- health/failure/rejoin metadata.

All nodes may read S1. Only valid coordinator lease holders may write S1.

### S2 — node-local scratch

Each node keeps temporary inference/KV/work state locally. S2 may diverge transiently. Any returned result must bind the S1 epoch/digest from which it was computed.

## 2. Ordinary-node execution contract

An ordinary node receives:
- `grid_id`
- `state_epoch`
- `state_digest`
- `task_id`
- `role`
- `branch_scope`
- `resource_budget`
- compact relevant state refs.

It may:
- read current S1 snapshot/deltas;
- dereference admitted payloads required by its assignment;
- reason/simulate/criticize/test within its scope;
- return one typed `NODE_RESULT/v1` to the assigned coordinator.

It may not:
- append proposals to S1;
- alter branch support/priorities;
- publish GWT broadcasts;
- assign roles;
- write evidence relations into S1;
- mutate work queues;
- write coordinator metadata;
- mint canonical facts/effects.

`NODE_RESULT/v1` is not a shared-state write. It is an ephemeral return message to a coordinator and includes:
- node_id
- task_id
- role
- source_state_epoch
- source_state_digest
- branch_scope
- result_class
- candidate payload/ref
- evidence/counterevidence refs
- confidence/calibration fields
- requested follow-up/discriminator
- output digest
- runtime/provenance binding.

If the coordinator rejects or ignores the result, it never enters S1.

## 3. Dynamic coordinator pool

Coordinator is a temporary role, never a permanent identity or special checkpoint.

All ten nodes use the same trained checkpoint; any eligible healthy node may become coordinator under a deterministic lease.

K is dynamic:
- K=1 default;
- K=2 for redundancy or clearly separable branch/task scopes;
- K>2 only when measured information gain justifies it;
- K=10 is exceptional and must be explicitly justified.

Coordinator selection should be deterministic from current state/health/load where possible. LLM self-election is not authority.

## 4. Coordinator lease and write authority

`GRID10_COORDINATOR_LEASE/v2` binds:
- grid_id
- coordinator_epoch
- node_id
- state_epoch_start
- scope
- branch_scope / GLOBAL
- allowed S1 write classes
- resource budget
- expiry/heartbeat
- predecessor lease digest
- deterministic selection proof.

Only a holder of a currently valid lease may submit an S1 commit.

Every commit must bind:
- current state_epoch + state_digest;
- coordinator_epoch + lease digest;
- read-set digest;
- write-set digest;
- source `NODE_RESULT` digests where applicable;
- deterministic reducer/version;
- CAS/rebase outcome.

Writes outside lease/scope fail closed.

## 5. Coordinator responsibilities

Coordinator nodes:
- assign/reassign roles;
- maintain work queues;
- receive ordinary-node results;
- reject stale/duplicate/correlated results;
- merge compatible results;
- preserve conflicting alternatives in Hyperposition;
- request discriminators;
- schedule GWT competition/broadcast;
- update branch activation/support metadata;
- allocate budgets;
- decide whether more nodes are worth activating;
- compress S1 into minimal sufficient state;
- surface ActionCandidates to deterministic EntityOS boundaries.

Coordinator does **not** become truth authority merely because it is the only S1 writer.

`COORDINATOR_WRITE != CANONICAL_TRUTH`

`GRID_CONSENSUS != FACT`

`MAJORITY != TRUTH`

## 6. Multi-coordinator conflict model

Multiple coordinators may exist, but write authority is scoped.

Preferred order:
1. partition by explicit task/branch/write class where possible;
2. each lease declares its write scope;
3. overlapping commits require short CAS against the same S1 epoch;
4. loser rebases/re-evaluates against the new state;
5. no silent last-writer-wins semantics.

This keeps ordinary nodes completely out of write arbitration and confines concurrency control to the much smaller coordinator set.

## 7. Near-zero-overhead colocated implementation

For one-host GRID10:
- durable S0/S1 checkpoints in UnifiedDB/SQLite-compatible authority store;
- memory-mapped/shared-memory HOT_STATE read view for all nodes;
- coordinator-only append/commit delta ring;
- ordinary nodes have read cursors, not write cursors;
- ephemeral node->coordinator result queues/ringbuffers;
- short atomic/CAS coordinator commits;
- batched persistence rather than DB write per token;
- content-addressed payloads; S1 stores compact refs/digests.

The ordinary-node hot path becomes:

`read snapshot -> compute -> return compact result -> continue/read next epoch`

No ordinary module needs a database/shared-state write transaction.

## 8. GWT under coordinator-only writes

GWT is a shared-state mechanism controlled by coordinators:
1. ordinary nodes return candidate/bid results to coordinator;
2. coordinator scores/schedules competition;
3. coordinator writes the selected GWT broadcast into S1;
4. all relevant nodes read the same broadcast sequence;
5. nodes return uptake/re-entry results to coordinator;
6. coordinator records accepted uptake/re-entry state in S1.

Thus ordinary nodes communicate indirectly through S1 without ever writing S1 themselves.

## 9. Hyperposition under coordinator-only writes

Ordinary nodes may discover/challenge branches, but only a coordinator may materialize those changes in S1.

A coordinator must preserve multiple unresolved branches when evidence does not justify collapse. It may prioritize work but cannot collapse by vote count.

Required hard negative:
- nine ordinary nodes return the same wrong candidate from correlated bias;
- one node returns stronger external evidence;
- coordinator must preserve/select according to evidence policy, not result count.

## 10. Training-data implications

The one 0.8B checkpoint must learn both role contracts.

### Ordinary-node training families
- reconstruct current S1 epoch;
- solve scoped assignment;
- return typed `NODE_RESULT/v1`;
- never emit a shared-state write instruction;
- recognize `NO_WRITE_AUTHORITY`;
- accept coordinator reassignment;
- detect stale source epoch and request refresh;
- communicate only through coordinator return channel + subsequent shared-state reads.

### Coordinator training families
- obtain/validate lease;
- consume many `NODE_RESULT`s;
- filter stale/duplicate/correlated results;
- merge evidence;
- preserve Hyperposition alternatives;
- write compact S1 delta;
- resolve overlapping coordinator commits using scope/CAS/rebase;
- issue GWT broadcast;
- rebalance roles;
- handle coordinator failure/succession;
- refuse canonical-truth/effect promotion without deterministic EntityOS gate.

### Mandatory hard negatives
- ordinary node attempts S1 write -> REJECT;
- expired/nonexistent coordinator lease attempts write -> REJECT;
- coordinator writes outside scope -> REJECT;
- stale result committed without revalidation -> REJECT;
- majority result overwrites stronger evidence -> REJECT;
- two coordinators use last-writer-wins -> REJECT.

## 11. Acceptance tests

Physical GRID10 must prove:
1. all ten nodes read the same committed epoch;
2. ordinary-node direct S1 writes are technically impossible/fail closed;
3. only valid coordinator leases can commit S1 deltas;
4. ordinary-node results become visible to other nodes only after coordinator commit;
5. K=1..N coordinator scaling preserves state correctness;
6. overlapping coordinator writes use scope/CAS/rebase, never silent overwrite;
7. coordinator crash -> deterministic successor without state loss;
8. GWT broadcast/uptake/re-entry works through coordinator writes;
9. Hyperposition branches survive correlated consensus pressure;
10. no S0 truth/effect bypass;
11. coordinator-only architecture beats or matches the old all-node-proposal architecture on quality while reducing write contention/overhead.

## 12. Core hypothesis

H1:

`many READ/COMPUTE nodes + few dynamic WRITE coordinators + one versioned shared cognitive state`

produces lower coordination overhead, simpler consistency semantics and better global cognitive control than allowing every node to mutate the shared workspace.

H0:

Coordinator serialization becomes a bottleneck or information filter and performs no better than direct all-node proposal writes or simpler single-model sampling under matched compute.

Promotion requires frozen matched-budget tests; this file defines the target, not runtime proof.
