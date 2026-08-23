# MicroEntity package root

Canonical product-facing package workspace for the Mini Entity / EntityOS MicroEntity surface.

This directory owns the package-facing view of:
- bundled ~0.8B cognitive core integration;
- Hyperposition Computational Unit (HCU): a GPU-like grid of logical ~0.8B cognition lanes inside the same Mini Entity;
- fixed Unified J-Space/GWT Cognitive Module;
- first-class Claude Code adapter;
- adaptive model/API engine profiles;
- self-hosted MicroEntity dashboard and activation/autostart contracts;
- package manifests, product implementation artifacts, tests and receipts.

HCU lanes are ephemeral cognitive compute slots, not additional persistent agents. MiniUnifiedDB remains the sole durable state/evidence authority and EntityOS/Mini Entity deterministic gates remain the only admitted effect authority. Numeric lane/resident/parallel capacity is fail-closed until exact model/runtime RSS and CPU scaling are measured.

`MICROENTITY_CURRENT.zip` is the current portable package snapshot. It must be rebuilt whenever this package or a linked product architecture contract changes. Every file created for the HCU lane is included in that snapshot; secrets/API tokens are never packaged.

The Zero research workspace lives at `research_entity/global/j-space/`.
Zero-trigger changes that affect the product must update both package roots and both ZIPs.
