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

## Current executable Entry Fabric candidate

`entry_fabric_v1.py` is the first current-facing Xeno ingress implementation candidate for the GRID10 baseline.

It deterministically binds:

- `causal_id` and exact live entity generation;
- positive-admission source and modality classes;
- provenance digest;
- normalized observed/received timestamps;
- payload content digest/reference;
- carried permission/capability claims without granting authority;
- exact v1 resource-budget keys with the current 10-logical-cell ceiling;
- a semantic `event_sha256` distinct from the admission-specific `ingress_id`.

The event/admission split is deliberate: two different observed events must not alias merely because later routing chooses the same XCU lanes, while the same observed event admitted under a different budget/permission envelope must retain the same event identity but receive a distinct admission identity.

`test_entry_fabric_v1.py` contains deterministic source regressions for replay identity, stale-generation rejection, unknown-field poisoning, positive source/modality admission, GRID10 over-budget rejection, payload-budget rejection, canonical claim ordering, event-vs-admission identity separation, and the bounded semantic-alias collision discriminator.

**Evidence boundary:** source candidate only. These new tests are not claimed executed until the exact branch bytes run in an authorized isolated executor. No runtime, HCU/XCU performance, J-Space, EntityOS or whole-product credit follows from the source delta alone.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.
