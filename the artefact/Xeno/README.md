# Xeno compatibility implementation root — EntityOS + HCU

`Xeno` is retained here only as a **transitional implementation/path codename** while exact migration is incomplete. The sole current product/system identity is **EntityOS** and the integrated cognition/compute architecture is **HCU**.

Existing `the artefact/MicroEntity/`, `mini_*`, `MINI_*`, Xeno path names, database schema names and receipts remain compatibility/provenance surfaces where exact migration is not yet safe; they are not bulk-renamed because doing so can break hashes, imports, recovery or reproducibility.

Current authority:

- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
- `research_entity/global/CLAY_STATUS_FOOTER_PROTOCOL.md`

## EntityOS + HCU computer path

```text
new data
   |
   v
Typed Entry Fabric
   |
   v
canonical state / XRAM compatibility layer
   |
   +---- deterministic control / XPU compatibility layer
   |
   +---- HCU shared-weight/vector/inference/J-Space plane
   |
   v
typed causal interconnect / workspace / Hyperposition
   |
   +---- GRID10
   +---- COGSIM10
   +---- WM_TEST
   +---- NESTED_SIM
   +---- SCALEOUT
   |
   v
candidate action -> typed effect request -> EffectGate/EffectJournal -> reality
```

Every `go` advances **ENTITYOS_EXECUTABLE_CONVERGENCE** and **HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT**, or records an exact HCU no-change reason.

## Executable bootstrap candidate

The current compatibility-path source candidate starts common machine primitives rather than adding another agent framework:

- `runtime/entry_fabric_v1.py` — strict typed ingress admission before cognition; binds generation, causal identity, source/provenance, modality, time, permission scope, parent ancestry, compute budget and payload identity into deterministic `XENO_ENTRY_PACKET/v1`;
- `runtime/grid10_v1.py` — deterministic `XENO_GRID10_SCHEDULE/v1` control/interconnect baseline with ten logical slots, bounded function allocation and ancestry-bound work packets;
- `tests/test_xeno_entry_grid10_v1.py` — generation, permission, budget, replay and causal-alias regressions;
- `receipts/2026-08-23_GO_XENO_ENTRY_GRID10_GPT56SOL.json` — exact-file bounded component evidence under current EntityOS + HCU authority.

The `XENO_*` schema names above are compatibility identifiers, not a second product identity.

Current evidence is **component/mechanism only**. These primitives do not yet receive integrated EntityOS or HCU model-runtime credit. Next they must enter the single canonical UnifiedDB/current MiniUnifiedDB compatibility state substrate and drive one positive-admitted HCU invocation with resolved engine identity under exact isolated execution.

Authority remains outside generated cognition: Entry/GRID10 do not write canonical truth, do not create a second identity or recovery ledger, and do not grant real-effect authority. EffectGate/EffectJournal remain the only real/state-changing boundary.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. The ladder `10 -> 32 -> 64 -> 128 -> 256 -> ~600` is a benchmark ladder. A future H100-class target around 600 logical modules is hypothesis-only until exact memory/throughput/concurrency benchmarks exist; logical module count never implies equal resident-model count or simultaneous decode streams.
