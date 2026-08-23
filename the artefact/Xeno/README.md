# Xeno — current operational bootstrap

**Xeno** is the current-facing name of the executable system previously called Mini Entity.

This directory is the migration-safe current-facing root for new Xeno architecture artefacts. Existing `the artefact/MicroEntity/`, `mini_*`, `MINI_*`, database schema names and receipts remain compatibility/provenance surfaces until exact migration; they are not bulk-renamed because doing so can break hashes, imports, recovery or reproducibility.

Current authority:

- `research_entity/global/XENO_GO_OWNER_DIRECTIVE.md`
- `research_entity/global/XENO_COMPUTATIONAL_UNIT_RESEARCH_FUSION_2026-08-23.md`
- current `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- current `research_entity/rooms/PROGRAM_STATE.json`

## Xeno goal

Xeno incrementally becomes a multi-mode cognitive computational appliance and eventually the bootstrap of an EntityOS cognitive computer.

```text
new data
   |
   v
Xeno Entry Fabric
   |
   v
XRAM state fabric
   |
   +---- XPU deterministic control
   |
   +---- XCU shared-weight/vector inference
   |
   v
typed interconnect / workspace / Hyperposition
   |
   +---- GRID10
   +---- COGSIM10
   +---- WM_TEST
   +---- NESTED_SIM
   +---- SCALEOUT
   |
   v
candidate action -> EffectGate -> reality
```

Every `go` advances normal executable Xeno work **and** XCU/Entry co-development, or records `XCU_NO_CHANGE_WITH_REASON`.

## Current source candidate: Entry Fabric + GRID10/XPU baseline

The current `go` branch adds a first executable-shaped common substrate:

- `entry_fabric_v1.py` — deterministic typed admission binding `causal_id`, generation, provenance, modality, permissions, capability scope, timestamps, resource budget and an opaque/digest-backed `payload_ref` before cognition;
- `grid10_scheduler_v1.py` — deterministic XPU-style plan compiler for up to 10 logical cells over a smaller shared physical worker pool;
- `test_entry_grid_v1.py` — fail-closed generation/budget/effect-authority regressions plus the single `CAUSAL_ALIAS_POISON` discriminator;
- `receipts/2026-08-23_GO_XENO_ENTRY_GRID10_CAUSAL_BIND_GPT56SOL.json` — bounded source/evidence receipt.

Critical identity law: the plan digest commits to the admitted ingress/event identity. Two materially different events are therefore not allowed to collapse to the same route identity merely because they select the same mode/functions. Exact replay of the same event remains deterministic.

This candidate grants **zero runtime/model/HCU/EntityOS acceptance credit** until the exact bytes actually run in an authorized isolated executor.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.
