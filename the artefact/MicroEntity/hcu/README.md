# Hyperposition Computational Unit (HCU)

Status: **OWNER-DIRECTED MINI ENTITY WORKSTREAM — SOURCE CONTRACT v1**

This directory is the package-facing home of the Mini Entity **Hyperposition Computational Unit**.

The HCU is a CPU-first modular cognition fabric for a separate resource-bounded VPS. It is designed to coordinate many logical ~0.8B cognition modules as one scheduled compute fabric while preserving the existing Mini Entity authority boundary.

Reference host supplied by the owner on 2026-08-23:

- plan: KVM 4;
- CPU: 4 cores;
- RAM: 16 GB;
- disk: 200 GB;
- bandwidth: 16 TB.

The HCU is developed in parallel on exact `go` cycles. It does **not** create a second entity, second durable world truth, second effect path, or hidden autonomous authority.

## Directory law

All HCU source contracts, topology profiles, package data indices, deterministic receipts and non-secret generated release artefacts belong under:

`the artefact/MicroEntity/hcu/`

and are included in `the artefact/MicroEntity/MICROENTITY_CURRENT.zip`.

Operational truth/state remains canonical in MiniUnifiedDB. Release archives may include privacy-filtered exports and receipts, but never API tokens, secret values or opaque credential material.

## Files

- `HCU_ARCHITECTURE.md` — architecture and authority contract.
- `topology.kvm4.json` — resource-adaptive KVM4 reference topology.
- `FREE_LLM_FEED_CONTRACT.json` — FREE_ONLY external candidate-feed contract.
- `HCU_DATA_INDEX.json` — release/package data policy and generated-artifact index.

## Core idea

The efficient implementation is **not** to keep dozens of independent full model copies in RAM.

Instead:

1. keep a small number of resident ~0.8B inference workers;
2. share/checkpoint-map weights where the runtime permits;
3. multiplex many logical module identities, contexts, adapters and tasks over those workers;
4. persist causal state, hypotheses, simulations, goals and receipts in MiniUnifiedDB;
5. use Hyperposition to retain alternatives instead of majority-vote truth collapse;
6. let deterministic Mini Entity gates admit any durable state or real effect.

This makes the grid GPU-like only in the scheduling sense: many logical lanes feeding a bounded execution fabric. It is not represented as literal GPU hardware.

## Evidence boundary

This package defines a **SOURCE/ARCHITECTURE CONTRACT**. It does not claim measured throughput, resident-module count, memory fit, model quality or whole Mini Entity runtime acceptance on the KVM4 host.
