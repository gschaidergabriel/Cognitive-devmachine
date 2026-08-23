# MicroEntity package root

Canonical product-facing package workspace for the Mini Entity / EntityOS MicroEntity surface.

This directory owns the package-facing view of:
- bundled ~0.8B cognitive core integration;
- fixed Unified J-Space/GWT Cognitive Module;
- first-class Claude Code adapter;
- adaptive model/API engine profiles;
- self-hosted MicroEntity dashboard and activation/autostart contracts;
- the **Hyperposition Computational Unit (HCU)**: a VPS-oriented grid of many logical ~0.8B cognitive modules time-multiplexed over a small number of hot local inference lanes;
- package manifests, product implementation artifacts, tests and receipts.

`MICROENTITY_CURRENT.zip` is the current portable package snapshot. It must be rebuilt whenever this package or a linked product architecture contract changes.

## HCU package law

All HCU design files, configuration, generated plans, non-secret data, receipts and exportable runtime artifacts belong under `hcu/` and are included in the package snapshot. Secrets and provider tokens are never packaged.

The HCU is part of the same Mini Entity. It is not a second entity, second truth store or second effect path:
- MiniUnifiedDB remains canonical durable authority.
- HCU module outputs are candidates/measurements until admitted.
- EffectGate remains the only real-effect authority.
- Zero remains runtime identity/configuration, not a second durable entity.

The Zero research workspace lives at `research_entity/global/j-space/`.
Zero-trigger changes that affect the product must update both package roots and both ZIPs.

Secrets/API tokens are never packaged.
