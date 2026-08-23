# MicroEntity package root

Canonical product-facing package workspace for the Mini Entity / EntityOS MicroEntity surface.

This directory owns the package-facing view of:
- bundled ~0.8B cognitive core integration;
- fixed Unified J-Space/GWT Cognitive Module;
- first-class Claude Code adapter;
- adaptive model/API engine profiles;
- self-hosted MicroEntity dashboard and activation/autostart contracts;
- package manifests, product implementation artifacts, tests and receipts.

`MICROENTITY_CURRENT.zip` is the current portable package snapshot. It must be rebuilt whenever this package or a linked product architecture contract changes.

The Zero research workspace lives at `research_entity/global/j-space/`.
Zero-trigger changes that affect the product must update both package roots and both ZIPs.

Secrets/API tokens are never packaged.
