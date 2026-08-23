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

## Entry Fabric v1 source candidate

`entry_fabric_v1.py` is the first current-facing executable Entry Fabric binder. It validates and canonicalizes typed ingress metadata before cognition and emits an immutable `XENO_ENTRY_PACKET/v1` identity.

The packet binds event/source/type identity, causal identity, entity generation, modality, observed/received time, capability scope, resource budget, payload reference+digest, provenance digest, parent/stream relation and optional trace context. Stale generations, malformed digests, partial trace context and unknown budget keys fail closed.

This component does **not** mint semantic truth, select cognition engines, grant user rights or grant EffectGate authority. The next integration step is to bind its `entry_sha256` into the existing HCU reactive-route decision together with a positively resolved `LOCAL_INTERNAL` engine identity.

Current source candidate regression: 9/9 component tests PASS in an isolated container; this is not Xeno/EntityOS runtime acceptance.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.
