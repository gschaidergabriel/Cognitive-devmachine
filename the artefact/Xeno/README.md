# Xeno — current operational bootstrap

**Xeno** is the current-facing name of the executable system previously called Mini Entity.

This directory is the migration-safe current-facing root for new Xeno architecture artefacts. Existing `the artefact/MicroEntity/`, `mini_*`, `MINI_*`, database schema names and receipts remain compatibility/provenance surfaces until exact migration; they are not bulk-renamed because doing so can break hashes, imports, recovery or reproducibility.

Current authority:

- `research_entity/global/XENO_GO_OWNER_DIRECTIVE.md`
- `research_entity/global/XENO_COMPUTATIONAL_UNIT_RESEARCH_FUSION_2026-08-23.md`
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_52.json`

## Current-facing authority files

- `manifest.json` — current Xeno/EntityOS authority manifest.
- `ARCHITECTURE.md` — current Entry/XRAM/XPU/XCU architecture anchor.
- `entry_fabric_v1.py` — deterministic typed ingress admission before cognition.
- `test_entry_fabric_v1.py` — fail-closed source tests and causal-entry identity falsifier.

The historical root files `the artefact/manifest.json` and `the artefact/ARCHITECTURE.md` still contain ClayVerse-era product detail. They are donor/compatibility evidence under the newer Xeno owner directive and MUST NOT override this current-facing Xeno authority. They remain untouched until an exact migration can preserve downstream hashes, tests and reproducibility.

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

## Entry Fabric v1

Every new-data path should enter cognition only after a `XENO_ENTRY_PACKET/v1` binds causal identity, generation, source/modality, provenance, permissions, compute budget and payload identity/reference. Raw payload bytes and secrets do not belong in the control packet. The deterministic packet digest commits to the normalized causal input so later routers can bind decisions to an immutable event identity instead of hashing routing output alone.

The Entry Fabric is truth-neutral and effect-neutral. It can feed all Xeno modes without granting canonical truth, model authority or direct effects.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.

`logical_module_count != resident_model_count != physical_decode_concurrency`.

## Evidence boundary

The files in this directory are source candidates until exact authorized isolated execution binds the source tree and runs the relevant tests. Source coherence alone grants zero runtime or whole-EntityOS acceptance credit.
