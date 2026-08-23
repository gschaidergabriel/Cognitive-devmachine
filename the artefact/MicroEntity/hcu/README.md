# Hyperposition Computational Unit (HCU)

Status: **OWNER-DIRECTED MINI ENTITY WORKSTREAM — SOURCE CONTRACT v1**

This directory is the package-facing home of the Mini Entity **Hyperposition Computational Unit**.

The HCU is a CPU-first modular cognition fabric for a separate resource-bounded VPS. It coordinates many logical ~0.8B cognition modules as one scheduled compute fabric while preserving the existing Mini Entity authority boundary.

Reference host supplied by the owner on 2026-08-23: KVM 4; 4 CPU cores; 16 GB RAM; 200 GB disk; 16 TB bandwidth.

The HCU is developed in parallel on exact `go` cycles. It does **not** create a second entity, second durable world truth, second effect path, or hidden autonomous authority.

## Directory law

All HCU source contracts, topology profiles, package data indices, deterministic receipts and non-secret generated release artefacts belong under `the artefact/MicroEntity/hcu/` and are included in `the artefact/MicroEntity/MICROENTITY_CURRENT.zip`.

Operational truth/state remains canonical in MiniUnifiedDB. Release archives may include privacy-filtered exports and receipts, but never API tokens, secret values or opaque credential material.

## Files

- `HCU_ARCHITECTURE.md` — architecture and authority contract.
- `topology.kvm4.json` — resource-adaptive KVM4 **planning** topology; numeric targets are not runtime evidence.
- `FREE_LLM_FEED_CONTRACT.json` — FREE_ONLY external candidate-feed contract.
- `HCU_DATA_INDEX.json` — release/package data policy and generated-artifact index.
- `capacity_guard_v1.py` — fail-closed bridge from source topology to exact measured capacity; without an admitted measurement it returns capacity as unresolved.
- `test_capacity_guard_v1.py` — deterministic authority/capacity poison regressions.
- `receipts/` — non-secret bounded evidence receipts.

## Core idea

The efficient implementation is **not** to keep dozens of independent full model copies in RAM. Instead keep a small resident ~0.8B worker pool, share/checkpoint-map immutable weights where supported, multiplex many logical roles/contexts over those workers, keep canonical state in MiniUnifiedDB, preserve alternatives in Hyperposition, and let deterministic gates admit durable state/effects.

This makes the grid GPU-like only in the scheduling sense: many logical lanes feeding a bounded execution fabric. It is not represented as literal GPU hardware.

## Capacity evidence law

`target_slots=16`, `adaptive_ceiling=24`, `target_resident_inference_workers=2` and similar topology values are source planning targets only.

Numeric runtime capacity may be admitted only through `HCU_CAPACITY_MEASUREMENT/v1` bound to exact source/model/tokenizer/runtime/measurement identities from `AUTHORIZED_ISOLATED_SANDBOX`. Target-VPS execution does not satisfy current test admission law.

## Evidence boundary

The HCU architecture is a **SOURCE/ARCHITECTURE CONTRACT**. The capacity guard has exact deterministic component-mechanism evidence. Neither establishes measured throughput, model fit, resident-module count, J-Space/GWT causality, target-VPS behavior, or whole Mini Entity runtime acceptance.
