# Topic Packet — ClayCode CC-RC1.8 MCAAT

**status:** OPEN/HOLD  
**origin run:** `claycode-20260808T1934p0200-chatgpt-secondary-r4`  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Compact synthesis

CC-RC1.8 **Monotone Causal Authority & Admissibility Types (MCAAT)** extends CC-RC1.7 TCQS. The language/compiler candidate now treats collection semantics, information admissibility and causal stage as independent type dimensions, while external execution authority remains an opaque host capability that model output cannot mint.

The owner's strong destruction hypothesis was adversarially tested and refined. Direct destructive primitives such as physical delete/truncate/drop/format/wipe should remain outside model-authored ClayCode where feasible, but this does **not** make constructive actions harmless. A model can create a bad version and activate it while all old data remains recoverable. Therefore the security invariant becomes:

`destruction-free model IR + recoverability + no ambient authority + effect-time semantic validation + rollback/recovery + quotas`.

## Constituent micro-packets

- `research_entity/knowledge_micro_packets/claycode/KMP-CC13-001-MCAAT-BOUNDARY.md`
- `research_entity/knowledge_micro_packets/claycode/KMP-CC13-002-NONDESTRUCTIVE-NOT-HARMLESS.md`
- `research_entity/knowledge_micro_packets/claycode/KMP-CC13-003-TYPEFLOW-EXEC.md`

## Mesh links

FRANK C8 · Clay CACC-G12 · ClayGraph G2a · UnifiedDB U2 · GWT R5 · Hyperposition H5 · Emergenz E-CERT2 · ClayCode CC12.

## Highest-information next test

Run a real capability-sandbox red-team (preferably Wasm/WASI) with a frozen MCAAT corpus, including indirect destructive effects, bad repoints, resource exhaustion, network/tool effects, capability laundering, adapter label loss and rollback failure. Pair with an independent second compiler/lowerer and target-Qwen generation tests before any promotion.
