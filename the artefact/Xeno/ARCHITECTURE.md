# Xeno current architecture — Entry/XRAM/XPU/XCU toward EntityOS

Status: **SOURCE CANDIDATE / CURRENT-FACING ARCHITECTURE ANCHOR**  
Owner authority: `research_entity/global/XENO_GO_OWNER_DIRECTIVE.md`  
Persistent research entity: **Clay**  
Operational bootstrap: **Xeno**  
Destination: **EntityOS** with integrated **HCU/XCU**

## Authority boundary

Xeno is the current executable bootstrap. Historical ClayVerse, Mini Entity, MicroEntity and `mini_*`/`MINI_*` files remain donor or compatibility evidence where exact migration has not occurred; they are not competing current product authority.

Canonical durable state/evidence remains in UnifiedDB or the currently admitted Xeno MiniUnifiedDB compatibility substrate. Model output, J-Space activity, workspace selection, HCU/XCU computation, world-model rollout and simulation state are candidates/measurements only. They cannot mint canonical truth.

Real or state-changing actions leave cognition only through typed candidate translation into **EffectGate + EffectJournal**. Unknown external outcomes remain UNKNOWN. No second persistent identity, truth store, effect path or recovery ledger is admitted.

## Computer decomposition

```text
human/tool/event/sensor/db/intrinsic input
                |
                v
        XENO ENTRY FABRIC
   typed packet + causal identity
                |
                v
          XRAM STATE FABRIC
 canonical / hot / rebuildable / scratch
                |
       +--------+--------+
       |                 |
       v                 v
 XPU CONTROL          XCU ACCELERATOR
 deterministic        shared-weight/vector/
 scheduling, leases,  inference/J-Space cells
 budgets, recovery
       |                 |
       +--------+--------+
                |
 typed packet interconnect / workspace / Hyperposition
                |
  +-------------+-------------+-------------+-------------+
  |             |             |             |             |
GRID10       COGSIM10       WM_TEST      NESTED_SIM     SCALEOUT
  |             |             |             |             |
  +-------------+-------------+-------------+-------------+
                |
       calibrated ActionCandidate
                |
       typed effect translation
                |
        EffectGate/EffectJournal
                |
              reality
```

The hardware analogy is architectural. XRAM/XPU/XCU are software responsibility boundaries, not claims of custom silicon or DGX-equivalent performance.

## Entry Fabric v1

`entry_fabric_v1.py` is the first current-facing executable primitive. Before cognition it requires a typed `XENO_ENTRY_PACKET/v1` control packet binding:

- `ingress_id` and `causal_id`;
- live `entity_generation`;
- source kind and modality;
- observed and received timestamps;
- provenance reference;
- permission scope;
- bounded compute budget;
- payload reference, SHA-256 and byte size;
- optional parent/stream relation and mode hint.

The packet carries **references and identity**, not raw payload bytes or secrets. Unknown keys, stale generation, malformed digests, invalid budgets or unsupported modes fail closed. The packet hash commits to the normalized causal input identity so materially different admitted inputs cannot alias merely because later routing decisions happen to choose the same lanes.

The Entry Fabric grants neither truth nor effect authority. It is usable by `GRID10`, `COGSIM10`, `WM_TEST`, `NESTED_SIM` and future scale-out because the same packet identity survives topology changes.

## Mode law

- `XENO_GRID10`: 10 logical cells for exact scheduler/interconnect/lesion baselines.
- `XENO_COGSIM10`: request-scoped cognition simulation; output is candidate reasoning only.
- `XENO_WM_TEST`: bounded noncanonical transition/world-model experiments calibrated against later observations.
- `XENO_NESTED_SIM`: selective expensive world-model -> virtual computer -> simulated AI -> action-candidate composition; never the default authority path.
- `XENO_SCALEOUT`: logical contexts over shared physical workers.

`logical_module_count != resident_model_count != physical_decode_concurrency`.

The ~600 logical-module H100-class target remains a planning hypothesis until exact checkpoint, quantization, KV/HBM, throughput, p50/p95 latency, scheduler-overhead and recovery measurements exist.

## GO dual-track gate

Every explicit `go` must advance both:

1. `XENO_EXECUTABLE_CONVERGENCE`;
2. `XCU_AND_ENTRY_FABRIC_CO_DEVELOPMENT`.

If track 2 cannot safely change, record `XCU_NO_CHANGE_WITH_REASON` and the discriminator. Prefer cross-mode primitives over one-off glue.

## Current source-level acceptance boundary

This architecture and Entry Fabric are **source candidates only** until exact authorized isolated execution runs the tests against the exact bound source tree. No runtime, throughput, HCU-emergence, J-Space-causality, model-capacity or EntityOS whole-product credit is granted by these files alone.
