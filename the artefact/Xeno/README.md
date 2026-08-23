# Xeno — transitional EntityOS/HCU compatibility surface

`Xeno` is **not** the current product identity. Current authority is:

- **EntityOS** — sole current product/system identity;
- **HCU** — sole current integrated cognition/compute architecture;
- **Xeno** — transitional implementation compatibility codename only;
- **XCU** — transitional/research alias for HCU only.

This directory remains a migration-safe compatibility surface while useful mechanisms are fused into the canonical EntityOS/HCU path. Do not bulk-rename hash-bound schemas, receipts, persisted identifiers or compatibility paths when doing so would break provenance or reproducibility.

Current authority must be resolved from verified `main`, especially:

- `research_entity/rooms/PROGRAM_STATE.json`;
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`;
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json`;
- `the artefact/README.md`.

## Current compatibility implementation candidate

The open Entry/GRID10 branch carries reusable mechanisms intended for **fusion into EntityOS/HCU**, not a second Xeno system:

- `entry_fabric_v1.py` — deterministic typed ingress admission before cognition, including causal/generation/provenance/isolation/security/resource binding and packet re-verification;
- `grid10_scheduler_v1.py` — deterministic compatibility control-plane planner for bounded logical GRID10 cells over shared physical workers;
- `test_entry_grid_v1.py` — fail-closed regressions plus the single already-declared `CAUSAL_ALIAS_POISON` source discriminator;
- `receipts/2026-08-23_GO_XENO_ENTRY_GRID10_CAUSAL_BIND_GPT56SOL.json` — bounded source/evidence receipt.

The branch has been converged to one Entry/GRID10 implementation path. A second monolithic Entry/GRID implementation was removed rather than retained as parallel authority.

## Authority law

These compatibility modules may produce candidate/control metadata only. They do not own canonical durable truth, identity, permissions, effects or recovery. UnifiedDB/current admitted compatibility state remains the durable state/evidence substrate, and EffectGate + EffectJournal remain the only real/state-changing effect authority.

GRID10, COGSIM10, WM_TEST, NESTED_SIM and future scale-out are **HCU modes / EntityOS mechanisms** under current authority. Logical module count is not physical model/decode concurrency.

## Evidence boundary

Current Entry/GRID10 changes remain source/regression candidates until exact then-current bytes execute in an authorized isolated sandbox. GitHub workflow admission failure before visible steps carries zero test/runtime credit. No VPS/self-hosted/production-host testing, no Together use, and no paid/model-training promotion are admitted under current policy.
