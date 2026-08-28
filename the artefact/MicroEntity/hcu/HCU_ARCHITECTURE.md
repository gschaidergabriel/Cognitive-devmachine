# EntityOS Hyperposition Computational Unit (HCU)

Status: **CURRENT ENTITYOS/HCU ARCHITECTURE CONTRACT — SOURCE CANDIDATE**
Date: 2026-08-23
Product: **EntityOS**
Compute architecture: **HCU**
Compatibility root: `the artefact/MicroEntity/hcu/`

The `MicroEntity` path is retained for exact implementation/provenance compatibility only. It does not define a current Mini Entity product or a second runtime identity. Historical versions of this file remain available in Git history and receipts.

## 1. Objective

HCU is the single integrated cognition/compute architecture inside EntityOS. It coordinates deterministic control, typed ingress, bounded logical cognition cells, Hyperposition/workspace coordination and measured execution capacity while preserving canonical truth and effect authority outside model-generated cognition.

The active computer path is:

```text
new data / event / prompt
        |
        v
  TYPED ENTRY FABRIC
        |
        +--> immutable event identity
        +--> concrete admission identity
        +--> generation / provenance / capability / resource bindings
        |
        v
canonical durable state/evidence
        |
  +-----+-----------------+
  |                       |
  v                       v
deterministic          HCU accelerator
control plane          shared-weight/vector/
                       inference/J-Space cells
  |                       |
  +-----------+-----------+
              v
 typed causal packet / Hyperposition / workspace
              |
      +-------+---------+----------+----------+
      |                 |          |          |
   GRID10            COGSIM10    WM_TEST   NESTED_SIM
      |                 |          |          |
      +-------+---------+----------+----------+
              |
           SCALEOUT
              |
      calibrated candidate
              |
 effect translation -> EffectGate + EffectJournal
```

## 2. Authority boundary

```text
EntityOS       = sole current product/system identity
HCU            = sole integrated cognition/compute architecture
UnifiedDB      = canonical durable state/evidence authority
MiniUnifiedDB  = compatibility implementation surface where exact migration is incomplete
EffectGate + EffectJournal = only real/state-changing effect authority
HCU/J-Space/world-model/workspace/model output = candidate/projection/measurement only
Hyperposition  = unresolved alternative holder, never truth by vote
```

Required laws:

- `HCU != SECOND_ENTITY`
- `HCU != SECOND_WORLD_TRUTH`
- `HCU != EFFECT_AUTHORITY`
- `MODEL_OUTPUT != CANONICAL_TRUTH`
- `MAJORITY_VOTE != TRUTH`
- `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`
- unknown external effect outcomes remain unknown and are never blindly replayed.

## 3. Typed Entry and causal identity

All new data converges toward one Typed Entry Fabric before HCU cognition.

A causal event has a replay-stable identity over immutable event semantics. A concrete admission has a separate identity because receive time, resource budget, capability snapshot or transport metadata can differ without redefining the underlying event.

Untrusted Entry content may request a capability or resource envelope, but it may only narrow independently admitted deterministic authority. It may never self-grant or broaden it.

HCU routing consumes event identity only through an admitted Entry binding. Concrete admission identity stays available downstream so a valid inference receipt cannot be replayed across a distinct admission.

## 4. Engine admission

Local/internal cognition is positive-admission only. Absence from an external-provider denylist is not engine authority.

Engine/provider/class/checkpoint/tokenizer/runtime identities come from deterministic control-plane evidence, not the causal event. Exact artifact bytes and measured runtime capacity are separate admission dimensions.

The current retained donor lane is PR #1263. It contains candidate mechanisms for `EngineAdmission`, Typed Entry, routing, inference receipts and GRID10. Those mechanisms must be rebased/fused into current EntityOS/HCU authority; a competing router or admission path is forbidden.

## 5. HCU modes

### GRID10

Deterministic 10 logical-cell baseline. Ten logical cells do not imply ten resident models or ten simultaneous decoders. MODEL cells are bounded by separately admitted resource/capacity evidence.

### COGSIM10

Request-scoped cognition simulation using temporary logical function slots for hypotheses, counterhypotheses, plans and critics. Outputs are candidates only.

### WM_TEST

Bounded noncanonical world/transition-model experiment. Predictions must be calibrated against later observations before stronger claims.

### NESTED_SIM

Selective higher-cost nested simulation. It is not permanent reality, a second entity or a truth authority.

### SCALEOUT

Logical-context scaling over shared physical workers. The benchmark ladder is `10 -> 32 -> 64 -> 128 -> 256 -> ~600`; physical decode concurrency is measured separately. The ~600 H100-class target remains a hypothesis until exact benchmark evidence exists.

## 6. Hyperposition and workspace

Disagreement is preserved as typed alternatives with evidence, counterevidence, unresolved facets and discriminators. Collapse requires evidence or deterministic policy; recurrence, sampling count or provider consensus cannot mint truth.

Workspace/J-Space coupling is an empirical causal-interface hypothesis. Injected context, traces or self-report are not proof of model-internal causal use. Promotion requires discriminating intervention or model-specific evidence.

## 7. Scheduling and capacity

The efficient HCU design multiplexes many logical roles/contexts over a bounded physical worker pool rather than duplicating one full model per logical cell.

Historical `topology.kvm4.json` values remain planning data only. Current runtime capacity can be admitted only through exact, authorized isolated measurement bound to source/model/tokenizer/runtime identities. VPS, self-hosted and production-host testing are forbidden for current acceptance credit.

## 8. Effects and recovery

HCU emits candidates or typed effect requests. Real effects remain journaled and generation/provenance fenced through EffectGate + EffectJournal. A crash does not convert an uncertain effect into success and does not authorize blind replay.

No HCU component may create a second recovery ledger, second state authority or generic host execution bypass.

## 9. Canonicalization convergence

Current HCU/Entry work contains historical or experimental encoder identities. Before heterogeneous/cross-language identity is promoted, EntityOS must select exactly one versioned current Entry+HCU canonical identity path and explicitly preserve older hashes as provenance rather than silently rewriting them.

## 10. Acceptance frontier

Source architecture alone grants zero EntityOS/HCU runtime credit. The next executable frontier is:

1. positive local engine/checkpoint/tokenizer/runtime admission from the real deterministic control plane;
2. bind immutable causal event identity + concrete Entry admission identity + resolved engine identity into the current HCU route/inference receipt path;
3. preserve capability/resource narrowing and generation fences;
4. run exact combined Entry + route + inference-receipt + GRID10 regressions in an actually-started authorized isolated executor;
5. then measure physical model fit, throughput, latency and scale separately from logical module count.

Together API and paid fallback remain forbidden. Final paid/model training requires explicit owner authorization.
