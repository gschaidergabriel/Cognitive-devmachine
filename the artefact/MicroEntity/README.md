# MicroEntity package root

Canonical product-facing package workspace for the Mini Entity / EntityOS MicroEntity surface.

This directory owns the package-facing view of:
- bundled ~0.8B cognitive core integration;
- fixed Unified J-Space/GWT Cognitive Module;
- first-class Claude Code adapter;
- adaptive model/API engine profiles;
- the owner-directed Hyperposition Computational Unit (`hcu/`) built as a grid of approximately-0.8B tiles for the persistent strategic/world-model lane;
- self-hosted MicroEntity dashboard and activation/autostart contracts;
- package manifests, product implementation artifacts, tests, generated data and receipts.

`MICROENTITY_CURRENT.zip` is the current portable package snapshot. It must be rebuilt whenever this package or a linked product architecture contract changes.

## HCU package invariant

All HCU-specific source, architecture, host profiles, topology, tests, generated calibration/capacity data and HCU receipts live under `hcu/`. HCU work must not create a second package root or second Mini Entity authority.

Every `go` considers HCU work in parallel with the Mini Entity frontier. When HCU package files change, those files must be included in `MICROENTITY_CURRENT.zip` and enumerated by `PACKAGE_MANIFEST.json`.

The owner-supplied HCU deployment target is KVM 4: 4 CPU cores, 16 GB RAM, 200 GB disk, 16 TB bandwidth. It remains a deployment target rather than a current acceptance-test surface under the active execution control.

The Zero research workspace lives at `research_entity/global/j-space/`.
Zero-trigger changes that affect the product must update both package roots and both ZIPs.

Secrets/API tokens are never packaged.
