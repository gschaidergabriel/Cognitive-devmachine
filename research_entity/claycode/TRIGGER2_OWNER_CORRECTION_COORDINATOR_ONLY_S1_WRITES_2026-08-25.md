# Trigger 2 Owner Correction — Coordinator-Only S1 Writes

Status: OWNER CORRECTION / HIGHER PRECEDENCE THAN V1 SHARED-STATE WRITE MODEL
Date: 2026-08-25
Applies to: exact trigger `2`, physical GRID10, Xeno/MicroEntity training/evaluation

## Hard law

Only dynamically leased coordinator nodes may write the shared cognitive state S1.

Ordinary modules:
- READ S1;
- receive assignments/state from S1;
- compute locally;
- return a typed ephemeral `NODE_RESULT/v1` to an active coordinator;
- MUST NOT append, mutate, CAS, publish, or otherwise write S1.

Coordinators:
- READ S1;
- receive ordinary-node results;
- arbitrate/filter/merge/reject them;
- WRITE S1 only while holding a valid scoped coordinator lease;
- preserve Hyperposition and evidence rules;
- do not mint canonical S0 truth/effects directly.

Required formula:

`ORDINARY_NODE = READ + COMPUTE + RETURN_TO_COORDINATOR`

`COORDINATOR = READ + RECEIVE + ARBITRATE + WRITE_S1`

`ORDINARY_NODE_WRITE_S1 = FORBIDDEN`

`NO_VALID_COORDINATOR_LEASE = NO_S1_WRITE`

## Communication semantics

Normal modules communicate indirectly through the shared state:

1. module reads shared state;
2. module performs assigned cognition;
3. module returns result privately/ephemerally to coordinator;
4. coordinator decides whether/how to commit it;
5. committed S1 delta becomes visible to every module;
6. all modules continue from the same new state epoch.

The ephemeral node->coordinator return channel is not shared state and grants no write authority.

## Training implications

Training must make the role boundary explicit.

Ordinary-node positive examples:
- read current epoch;
- compute scoped result;
- emit `NODE_RESULT/v1`;
- refuse direct shared-state mutation;
- request refresh on stale state;
- accept reassignment.

Coordinator positive examples:
- validate lease;
- consume many results;
- reject stale/duplicate/correlated outputs;
- preserve conflicting hypotheses;
- commit compact S1 delta;
- use CAS/rebase for conflicting coordinator commits;
- emit GWT broadcast through S1;
- perform failure/succession handling.

Mandatory hard negatives:
- ordinary node attempts S1 write;
- node self-promotes to coordinator;
- coordinator with expired lease writes;
- coordinator writes outside lease scope;
- ordinary node bypasses coordinator through a proposal log;
- majority results overwrite stronger evidence;
- silent last-writer-wins between coordinators.

## Acceptance implication

Physical GRID10 acceptance must prove technically, not just by model compliance, that ordinary-node S1 writes fail closed and that only valid coordinator leases can commit S1 deltas.

Canonical detailed architecture for this correction:
`research_entity/claycode/TRIGGER2_GRID10_SHARED_STATE_COORDINATION_ARCHITECTURE_V2.md`

This correction supersedes any v1 wording that allowed all nodes to append proposals to S1.
