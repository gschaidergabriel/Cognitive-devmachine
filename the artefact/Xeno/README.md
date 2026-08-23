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

## Executable Entry Fabric candidate

`entry_fabric_v1.py` is the first current-facing executable Entry primitive. It deterministically admits `XENO_INGRESS_REQUEST/v1` into `XENO_INGRESS_PACKET/v1` and binds one immutable `ingress_sha256` across causal id, entity generation, provenance, modality, normalized timestamps, permissions/capability scope, resource budget and immutable payload digest/size/reference.

Its scope is deliberately narrow:

- fail closed on stale generation, malformed/unbound fields and invalid payload identity;
- normalize only representation-level details needed for deterministic replay;
- never infer semantic truth;
- never grant effect authority;
- expose one ingress identity intended to be reused by XPU/XCU/HCU route and downstream inference receipts rather than inventing router-specific parallel event identities.

Focused deterministic regressions live in `test_entry_fabric_v1.py`. Current evidence is component/source only; no XCU, EntityOS or whole-runtime acceptance is implied.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.
