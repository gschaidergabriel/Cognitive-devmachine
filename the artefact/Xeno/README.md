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

## Executable Xeno v1 — typed Entry -> GRID10

The first current-facing executable Xeno runtime primitive now lives under `runtime/`:

- `entry_fabric_v1.py` — typed admission, canonical payload digest, immutable causal `event_sha256`, replay-distinct `ingress_id`, provenance/generation/permission/budget binding;
- `grid10_runtime_v1.py` — deterministic XPU-like routing over exactly 10 logical function cells with physical worker budget tracked separately;
- `xeno_cli_v1.py` — stdin JSON entry point for new data -> typed admission -> route decision;
- `tests/test_xeno_entry_grid10_v1.py` — replay, stale-generation, provenance-collision, capability and logical-vs-physical regressions.

Example:

```bash
printf '%s\n' '{"payload":{"prompt":"smoke"},"causal_id":"smoke-1","generation":7,"source":"human:gabriel","provenance":{"channel":"smoke"},"modality":"text","observed_at":"2026-08-23T15:00:00Z","received_at":"2026-08-23T15:00:01Z","permissions":["read","candidate"],"capability_scope":["mode:grid10"]}' \
  | python "the artefact/Xeno/runtime/xeno_cli_v1.py" --generation 7 --physical-workers 2
```

The v1 route identity commits to the immutable event digest. Transport replay can therefore keep the same causal event/route identity while receiving a distinct ingress receipt; two materially different events selecting the same cells cannot silently alias.

This runtime is candidate/control-plane evidence only. It does not yet execute the ~0.8B XCU worker, write UnifiedDB/MiniUnifiedDB, or call EffectGate.

## Scale semantics

The baseline is 10 logical cells. Larger targets are logical contexts over shared physical workers. A future H100-class target around 600 logical modules is research planning only until exact memory/throughput/concurrency benchmarks exist.
