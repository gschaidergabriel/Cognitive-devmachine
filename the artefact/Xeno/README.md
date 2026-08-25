# Xeno — EntityOS/HCU implementation codename

**Status:** current-facing implementation root.  
**Product:** EntityOS.  
**Integrated cognition/compute architecture:** HCU.  
**Implementation compatibility codename:** Xeno / MicroEntity where migration-safe compatibility is still required.

Xeno is **not** a competing product, persistent entity, canonical truth store, or real-effect authority. It is the current implementation codename for the shippable EntityOS/HCU computational node described by the newest owner authority.

## Current authority

Newest explicit owner target:

- `research_entity/global/XENO_HCU_GO_TARGET_ARCHITECTURE_OWNER_DIRECTIVE_2026-08-25.md`

That directive supersedes conflicting older Xeno/GRID10 optimization targets. Older files in this directory remain useful as donor/provenance material only where they disagree with the 2026-08-25 owner target.

## Current GO target

The shortest-path implementation order is:

```text
AUTONOMOUS_BOOT
  -> SHARED_STATE_READ_PATH
  -> ORDINARY_NODE_READ_ONLY_ENFORCEMENT
  -> NODE_RESULT_TRANSPORT
  -> DYNAMIC_COORDINATOR_LEASE
  -> COORDINATOR_ONLY_WRITE_PATH
  -> COORDINATOR_COMPRESSION_AND_INTEGRATION
  -> FAILURE_REJOIN
  -> HYPERPOSITION_GWT_GRF_INTEGRATION
  -> MODEL_SPECIFIC_JSPACE
  -> PHYSICAL_GRID10
  -> RECURSIVE_COORDINATION_SCALING
  -> MATCHED_BUDGET_ACCEPTANCE
  -> XENO_HCU_ACCEPTANCE
```

## State / authority split

```text
S0  canonical EntityOS truth/evidence/effect/security authority
S1  live shared cognitive/HCU workspace
S2  node-local ephemeral cognition/scratch
```

Ordinary Xeno nodes are strictly **READ-ONLY** on S1 and return typed ephemeral `NODE_RESULT/v1` packets. Only the current valid scoped `GRID_COORDINATOR_LEASE` holder may mutate S1. Coordinator status never grants S0 truth/effect authority; real effects remain behind the canonical deterministic EntityOS effect boundary.

## Physical GRID10

The current first concrete GRID acceptance target is **10 physical Xeno nodes** using the same accepted ~0.8B checkpoint plus deterministic shell, one shared-state fabric, ordinary-node read-only S1 access, and dynamic coordinator-only S1 writes.

Historical "10 logical cells over shared workers" remains a useful component simulator/baseline, but it is **not** the current physical GRID10 acceptance target.

## Current implementation primitive

`tools/xeno_shared_state_v1.py` is the current source primitive for the first owner-priority path. Its regression is `tests/test_xeno_shared_state_v1.py`.

The primitive currently covers:

- autonomous boot against exact S1 epoch/digest;
- SQLite-enforced ordinary-node read-only S1 access;
- node-admission-bound signed `NODE_RESULT/v1` packets;
- deterministic dynamic coordinator leases;
- atomic lease validation + S1 CAS writes;
- atomic lease validation + result admission;
- coordinator replacement/stale/duplicate/forged-result rejection.

Until admitted exact-source runtime evidence exists, this remains component source/regression evidence only. It does not establish full HCU, physical GRID10, model-specific J-Space, training, or whole-product acceptance.
