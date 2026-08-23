# Hyperposition Computational Unit (HCU)

This directory is the canonical Mini Entity package surface for the **Hyperposition Computational Unit**: a CPU-first grid of approximately-0.8B cognition tiles intended to run on a dedicated deployment host while remaining inside the same Mini Entity / EntityOS authority boundary.

Current owner addendum:
`research_entity/global/MINI_ENTITY_HYPERPOSITION_COMPUTATIONAL_UNIT_OWNER_ADDENDUM.md`

## What belongs here

- HCU architecture and world-model contracts;
- host/capacity profiles;
- grid/topology definitions;
- scheduler/capacity source;
- tests;
- generated capacity/calibration data;
- receipts;
- later deployment templates;
- model/tile manifests or content-addressed references.

Secrets and API tokens never belong here or in the package ZIP.

## Authority boundary

HCU is a compute organ only.

- MiniUnifiedDB remains canonical durable state/evidence/configuration authority.
- HCU world-model and future branches are derived/simulated state until admitted through canonical gates.
- Zero remains runtime identity/configuration.
- Unified J-Space/GWT remains the cognitive selection fabric where admitted.
- external effects remain behind deterministic EntityOS/Mini Entity effect gates.
- a tile may propose, simulate, critique and synthesize; it may not directly mint canonical truth or perform external effects.

## Initial host profile

The owner-supplied target is `KVM 4`: 4 CPU cores, 16 GB RAM, 200 GB disk and 16 TB bandwidth. See `KVM4_PROFILE.json`.

The included planner deliberately separates:

- **resident tiles**: model instances/pages kept ready in RAM;
- **active tiles**: tiles decoding concurrently within CPU/context limits;
- **cold artifacts**: additional model/checkpoint variants stored on disk;
- **logical tiles**: role/state instances that may share exact read-only base weights when the admitted runtime really supports page sharing.

No fixed resident count is treated as fact before exact measurements. Current values are planning estimates only.

## ZIP invariant

Every file created for this HCU lane must remain under this directory and be included in `../MICROENTITY_CURRENT.zip` whenever the package snapshot is rebuilt.
