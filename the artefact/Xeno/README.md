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

## Executable bootstrap candidate

The current Xeno source candidate now starts the common machine substrate instead of adding another agent framework:

- `runtime/entry_fabric_v1.py` — strict typed ingress admission before cognition; binds generation, causal identity, source/provenance, modality, time, permission scope, parent ancestry, compute budget and payload identity into deterministic `XENO_ENTRY_PACKET/v1`;
- `runtime/grid10_v1.py` — deterministic `XENO_GRID10_SCHEDULE/v1` control/interconnect baseline with ten logical slots, bounded function allocation and ancestry-bound work packets;
- `tests/test_xeno_entry_grid10_v1.py` — generation, permission, budget, replay and causal-alias regressions;
- `receipts/2026-08-23_GO_XENO_ENTRY_GRID10_GPT56SOL.json` — exact-file bounded component evidence.

Current evidence is **component/mechanism only**. These primitives do not yet receive integrated Xeno, HCU/XCU model-runtime or EntityOS runtime credit. Next they must enter the single canonical XRAM/MiniUnifiedDB-to-UnifiedDB path and drive one real current HCU/XCU invocation under exact isolated execution.

Authority remains outside generated cognition: Entry/GRID10 do not write canonical truth, do not create a second identity or recovery ledger, and do not grant real-effect authority. EffectGate remains the only real/state-changing boundary.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.
