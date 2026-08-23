# Xeno — current operational bootstrap

**Xeno** is the current-facing name of the executable system previously called Mini Entity.

This directory is the migration-safe current-facing root for new Xeno architecture artefacts. Existing `the artefact/MicroEntity/`, `mini_*`, `MINI_*`, database schema names and receipts remain compatibility/provenance surfaces until exact migration; they are not bulk-renamed because doing so can break hashes, imports, recovery or reproducibility.

Current authority:

- `research_entity/global/XENO_GO_OWNER_DIRECTIVE.md`
- `research_entity/global/XENO_COMPUTATIONAL_UNIT_RESEARCH_FUSION_2026-08-23.md`
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json`

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

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.
