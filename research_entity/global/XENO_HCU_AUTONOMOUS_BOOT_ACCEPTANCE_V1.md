# Xeno/HCU autonomous boot acceptance v1

Status: GO blocker contract
Target: first executable step toward the current Xeno/HCU owner architecture

## Purpose

A newly started Xeno must become useful from shared state alone, without a preassigned cognitive role and without ordinary-node write access to S1.

## Required boot state machine

`DISCONNECTED -> DISCOVERED -> ADMITTED -> SYNCED -> WORK_SELECTED -> WORKING`

A node may additionally transition from `WORKING` to `COORDINATOR_CANDIDATE`, but it becomes `COORDINATOR_ACTIVE` only after deterministic runtime issuance of a valid scoped `GRID_COORDINATOR_LEASE`.

## Inputs available at boot

The deterministic shell may provide only infrastructure facts: node identity/capabilities, fabric endpoint, policy version, model/runtime identity and cryptographic/runtime admission material.

The cognitive work role MUST NOT be preassigned externally.

The node reads an S1 snapshot containing at minimum:

- `state_epoch`
- `state_digest`
- active goals/tasks/branches
- task claim/in-flight metadata
- coordinator scopes/leases visible to the node
- budgets/priority hints
- GWT broadcast metadata if present
- content-addressed references needed to retrieve deeper evidence

## Autonomous selection output

After sync, an ordinary node must produce an ephemeral typed selection/result envelope. Minimum fields:

- `schema = XENO_WORK_SELECTION/v1`
- `node_id`
- `observed_state_epoch`
- `observed_state_digest`
- `selected_scope`
- `selected_task_or_branch`
- `selection_reason_code`
- `capability_match`
- `expected_information_gain_or_utility`
- `estimated_budget`
- `packet_digest`

This envelope is NOT an S1 write. It is routed to an active coordinator/result channel.

## Hard authority invariant

Ordinary node credentials/runtime capability must make direct S1 mutation impossible, not merely discouraged by prompt.

Required negative test:

1. boot node as ordinary member;
2. attempt direct S1 append/update/delete;
3. runtime/storage layer rejects operation;
4. state epoch/digest remains unchanged;
5. rejection receipt binds node, attempted operation and state digest.

## Work-selection acceptance tests

A1 EMPTY_GRID_BOOT: with useful unclaimed work in S1, a fresh node selects a valid task without human role assignment.

A2 CLAIM_AWARENESS: when its highest-ranked task is already claimed/in-flight, the node does not duplicate it unless state explicitly requests redundancy.

A3 STATE_CHANGE_REPLAN: after epoch advances and priorities/branches change, the node re-reads and changes function when the previous selection is stale.

A4 NO_WORK: if no useful work is available, node returns typed idle/wait status rather than inventing a task or mutating S1.

A5 STALE_SNAPSHOT: a selection derived from stale epoch/digest cannot receive current-state execution/promotion credit without coordinator/runtime revalidation.

A6 RESTART_REJOIN: restart does not reset S0/S1; node rebinds to current epoch and avoids replaying stale results.

A7 ROLE_FLEXIBILITY: same checkpoint/runtime can select at least two different useful functions solely because shared state differs.

A8 COORDINATOR_BOUNDARY: model self-declaration `I am coordinator` grants no S1 write permission. Only a valid runtime lease does.

## Minimum metrics

- valid-work-selection rate
- duplicate-work rate
- stale-selection rejection rate
- time/bytes/tokens from connect to useful selection
- S1 bytes read before selection
- direct-write rejection rate (target 100%)
- restart/rejoin correctness
- function diversity under controlled state changes

## Falsifiers

Autonomous boot is NOT accepted if:

- task/role is injected in the launch prompt/config;
- ordinary node can mutate S1;
- selection ignores epoch/digest;
- useful work requires peer chat rather than shared-state reconstruction;
- node repeats claimed work by default;
- coordinator authority can be self-issued by model output;
- test passes only in the historical logical GRID simulator without a real shared-state boundary.

## Next implementation artifact

Implement a minimal executable harness that creates a versioned S1 fixture, boots multiple identical node shells against it, enforces read-only ordinary credentials, captures `XENO_WORK_SELECTION/v1`, advances the epoch, and proves A1-A8 before GO credit moves to NODE_RESULT transport and coordinator leasing.
