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

## Current executable core candidate — 2026-08-23

Branch candidate `go/xeno-entry-grid10-core-20260823-2324-sol` adds the first current-facing stdlib-only Xeno machine primitive under this root:

- `xeno_core_v1.py` — fail-closed `XENO_INGRESS_PACKET/v1`, producer `source_event_key`, deterministic GRID10 planning and candidate-only `XENO_COMPUTE_PACKET/v1` interconnect;
- `test_xeno_core_v1.py` — exact component regressions for generation, schema, capability, payload identity, budget and logical-vs-physical scheduling fences;
- `receipts/2026-08-23_GO_XENO_ENTRY_GRID10_CORE_GPT56SOL.json` — exact source/evidence boundary and the single unusual discriminator for the `go` macrocycle.

The candidate deliberately separates:

`producer event identity -> admitted causal ingress identity -> logical 10-cell plan -> physical active-decode limit -> candidate packet`

This makes the same primitive reusable by `XENO_GRID10`, `XENO_COGSIM10`, `XENO_WM_TEST` and `XENO_NESTED_SIM`. It does **not** yet wire UnifiedDB persistence, HCU model workers, recovery leases or SCALEOUT, and it has zero product-runtime credit until exact authorized isolated runtime execution exists.
