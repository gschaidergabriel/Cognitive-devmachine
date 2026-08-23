# MicroEntity package root

Canonical product-facing package workspace for the Mini Entity / EntityOS MicroEntity surface.

This directory owns the package-facing view of:
- bundled ~0.8B cognitive core integration;
- fixed Unified J-Space/GWT Cognitive Module;
- first-class Claude Code adapter;
- adaptive model/API engine profiles;
- the Hyperposition Computational Unit (HCU) sparse ~0.8B logical-module grid and permanent strategic world-model/simulation lane;
- self-hosted MicroEntity dashboard and activation/autostart contracts;
- package manifests, product implementation artifacts, tests, data and receipts.

## HCU package lane

Canonical HCU package root:
`the artefact/MicroEntity/hcu/`

All package-safe HCU-generated source, configuration, schemas, tests, receipts, calibration data, simulation-derived data and deployment profiles belong under that root. Provider credentials, tokens and other secrets never belong there.

The current owner-nominated HCU deployment resource profile is KVM4 / 4 vCPU / 16 GB RAM / 200 GB disk / 16 TB bandwidth. Current acceptance testing remains authorized-isolated-sandbox-only; the VPS profile does not create a testing exception.

The HCU is a compute/simulation organ inside the same Mini Entity. MiniUnifiedDB remains the canonical durable authority; HCU/LLM/J-Space/GWT outputs remain candidate/measurement layers and HCU has no direct effect authority.

## Snapshot law

`MICROENTITY_CURRENT.zip` is the current portable package snapshot only when it matches the package source.

It must be rebuilt whenever this package or a linked product architecture contract changes. In particular, the ZIP must recursively include `hcu/` and is stale after any HCU package change until rebuilt. The ZIP must not include itself, secrets or transient caches.

The Zero research workspace lives at `research_entity/global/j-space/`.
Zero-trigger changes that affect the product must update both package roots and both ZIPs where the current product contract requires that mirroring.

Secrets/API tokens are never packaged.
