# the artefact — EntityOS + HCU cognitive computer

`the artefact/` is the canonical product/research workspace for the current **EntityOS** system and its integrated **HCU** cognition/compute architecture.

Current authority is resolved from verified current `main`, especially:

- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_62.json`
- `research_entity/claycode/autonomous/SUPERVISOR_INBOX.json`
- `research_entity/claycode/CLAYCODE_ALL_WORKERS_EXECUTION_DIRECTIVE.md`

## Current naming law

- **EntityOS** = sole current product/system identity.
- **HCU** = sole current integrated cognition/compute architecture.
- `Xeno` = transitional implementation compatibility codename only.
- `XCU` = transitional/research alias for HCU only.
- `Mini Entity`, `MicroEntity`, `mini_*`, `MINI_*` = historical implementation/provenance surfaces where exact migration has not occurred.
- ClayVerse and Frank = historical donor/provenance only unless explicitly re-admitted.

Do not bulk-rename hashes, receipts, schemas, ABI/API names, persisted state or compatibility paths when that would break reproducibility. Useful mechanisms are fused into EntityOS/HCU rather than promoted as competing systems.

## Current architecture goal

EntityOS is incrementally built as a **multi-mode cognitive computational system** with one integrated HCU rather than a permanent swarm of agents.

```text
new data / event / prompt
          |
          v
   TYPED ENTRY FABRIC
          |
          v
 canonical state/evidence
          |
    +-----+------+
    |            |
    v            v
 deterministic   HCU accelerator plane
 control plane   shared-weight/vector/
                 inference/J-Space cells
    |            |
    +-----+------+
          |
 typed causal packet / workspace / Hyperposition fabric
          |
  +-------+---------+----------+----------+
  |                 |          |          |
GRID10           COGSIM10    WM_TEST   NESTED_SIM
  |                 |          |          |
  +-------+---------+----------+----------+
          |
      SCALEOUT
          |
 calibrated ActionCandidate
          |
 effect translation -> EffectGate/EffectJournal -> reality
```

Computer-like implementation roles may retain compatibility names while migration remains exact:

- **XRAM compatibility role** — canonical/hot/rebuildable/scratch/paged state tiers;
- **XPU compatibility role** — deterministic processor/control plane;
- **HCU accelerator plane** — shared-weight vector/inference/J-Space/function-cell compute; historical `XCU` names are aliases only;
- **Interconnect** — typed causal packets, workspace and Hyperposition;
- **Entry I/O** — typed ingress for all new data;
- **Effect translation** — candidate to typed effect request, then EffectGate/EffectJournal.

These are software architecture roles, not claims of custom silicon.

## Mandatory `go` law

Every explicit `go` has three coupled tracks:

1. **ENTITYOS_EXECUTABLE_CONVERGENCE** — improve the strongest real current implementation toward EntityOS.
2. **HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT** — advance/test/specify/wire/benchmark at least one HCU or typed Entry primitive, or record `HCU_NO_CHANGE_WITH_REASON`.
3. **GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS** — advance the functional J-Space/GWT prototype, causal traces, vector-control/data quality or zero-cost local ~0.8B readiness, or record `TRAINING_READINESS_NO_CHANGE_WITH_REASON`.

Material architecture work uses:

`OBSERVE -> HYPOTHESIS -> COUNTERHYPOTHESIS -> CHEAPEST DISCRIMINATOR -> SOURCE/TEST EVIDENCE -> FUSION -> BOUNDED DELTA -> RE-ENTER`

Prefer primitives reusable across multiple HCU modes. A component PASS is not a whole-HCU or whole-EntityOS PASS.

## HCU modes

### `GRID10`

Cheap 10 logical-cell shared-worker baseline for scheduler tests, lesions, small parallel reasoning and exact compute-matched baselines.

### `COGSIM10`

Request-scoped cognition simulation. A temporary 10-cell topology explores hypotheses/counterhypotheses/plans/critics and emits only candidates. No simulated action has direct real effects.

### `WM_TEST`

Bounded experimental world/transition-model mode. Predictions are noncanonical and must be calibrated against later observations.

### `NESTED_SIM`

Selective high-cost mode:

`observed state -> bounded world model -> virtual computer -> simulated AI cognition -> proposed action -> hypothesis/counterhypothesis comparison -> calibrated candidate -> EffectGate`

It is not the default and does not create a second reality authority.

### `SCALEOUT`

Scale logical contexts over shared physical workers. Benchmark ladder:

`10 -> 32 -> 64 -> 128 -> 256 -> ~600 logical contexts`

The ~600 H100-class target is a **research hypothesis only**. Logical module count is never reported as the same thing as resident model count or simultaneous decode streams.

## Authority law

- canonical durable state/evidence remains outside model-generated cognition and simulation;
- current compatibility MiniUnifiedDB/UnifiedDB surfaces may remain during exact migration;
- world-model state is projection/candidate state;
- HCU/J-Space/workspace outputs cannot mint canonical truth;
- Hyperposition preserves unresolved alternatives; majority vote is not truth;
- `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`;
- stale generation/provenance uncertainty fail closed;
- unknown external effect outcome remains UNKNOWN until verified;
- EffectGate + EffectJournal remain the only real/state-changing effect authority;
- no second persistent identity, truth store, effect path or recovery ledger is admitted.

## Typed Entry Fabric

All new data paths converge toward one typed ingress binding before cognition:

- immutable ingress/causal identity;
- generation;
- source/provenance;
- modality/type/schema;
- observed/received time;
- permissions/capability scope;
- parent/stream relation;
- compute/resource budget;
- payload reference/digest.

Capability claims in an untrusted Entry packet are **not authority**. Entry admission must compare them against the existing deterministic permission/capability authority and its exact binding/receipt identity; the packet may narrow an admitted capability set but may never self-grant or broaden it.

Replay-stable causal event identity and concrete transport/admission identity must remain distinguishable. Changing receive time, payload reference, permission snapshot or resource budget may change admission identity without redefining the immutable event identity. Changing immutable payload/provenance/event semantics must change event identity.

HCU route events and downstream inference receipts must ultimately re-enter through this fabric so event identity, generation, engine identity and causal provenance remain bound instead of becoming a side ledger.

## HCU reactive cognition

The current HCU direction is script-first and selective:

`canonical event -> deterministic maintenance -> selective HCU lane activation -> Hyperposition/J-Space candidate computation -> bounded projection -> EntityOS decision path`.

External providers are not admitted as required internal cognition. Exact local checkpoint/tokenizer/runtime identity is an acceptance gate, not an inferred fact. Until a positive local engine capability record exists, absence from an external-provider denylist is insufficient to prove internal engine admission.

**Pre-load hashing is not loader attestation.** A positive `EngineAdmission` constructed from checkpoint/tokenizer/runtime/build hashes receives zero HCU runtime credit unless the actual model loader is bound to the same consumed bytes. The admitted path must therefore use a generation-fenced physical engine lease or an enforced read-only/content-addressed artifact boundary and must echo the loader-consumed artifact identity into the downstream inference receipt. Wrong-path loads, post-admission mutation, stale lease reuse or unknown consumed bytes fail closed.

## Execution policy

Current autonomous supervisor `8.62` is **FREE_ONLY**. Build/test/experiment/runtime credit comes only from authorized isolated execution surfaces; VPS/self-hosted/production-host testing is forbidden. Together general inference, Together training/preflight/key lookup/job creation, paid fallback and unknown-cost provider execution are forbidden in this mode.

Vercel Hobby Sandbox is now admitted only as a **bounded included-tier FREE surface** for fixed, source-hash-bound, short capsules. Remaining monthly Sandbox quota is not assumed. If quota exhaustion, billing, an upgrade requirement, plan mismatch or any monetary charge path appears, execution must fail closed before proceeding. No generic caller-supplied shell/command surface receives evidence credit.

Observed bounded runtime evidence on 2026-08-24:

- exact-current J-Space dataset-family-split component: **6/6 PASS twice** in isolated execution; same-family rerun is reproducibility, not independent replication;
- RFC8785/JCS Entry canonicalization component: **7/7 PASS**, exit 0, secret fence PASS, cleanup PASS on Vercel Hobby Sandbox;
- the Entry capsule executed source/test Git blobs that were byte-identical at the then-current retained PR1263 head, but its route still emitted an older `source_commit` metadata label;
- therefore component runtime credit exists for those exact bytes only; whole EntityOS/HCU, local-model, model-specific J-Space, training and whole-product credit remain zero.

Source/component/historical PASS does not imply EntityOS/HCU runtime acceptance.

## Current frontier

1. repair the fixed HCU capsule manifest metadata so `source_commit`/source closure binds the exact immutable retained PR1263 identity used for the run; do not rely on byte equality plus a stale commit label for exact-head acceptance;
2. extend the same **single fixed hash-verified executor/capsule authority** toward the combined Typed Entry -> route -> verified engine load -> inference -> GRID10 -> Global J-Space/GWT -> admitted causal dataset closure;
3. wire `EngineAdmission` to the real deterministic EntityOS/HCU control-plane producer and bind it through a generation-fenced physical engine lease to the bytes actually consumed by the local checkpoint/tokenizer/runtime loader;
4. preserve replay-stable event identity vs concrete admission identity and wire Entry capability claims to the canonical deterministic capability authority;
5. bind the downstream inference receipt producer to serializer/event/Entry-admission/route/engine/class/artifact plus physical loader-lease/consumed-byte identity;
6. rebase/fuse the retained HCU/J-Space donor onto exact current FREE_ONLY main without restoring stale authority or creating a second Entry/router/inference/J-Space/data/effect path;
7. only after exact executable and real-trace gates, continue zero-cost local ~0.8B J-Space/GWT specialization; do not preflight or launch Together under supervisor 8.62.

## Latest `go` README re-entry — 2026-08-24

`README=UPDATED_SUPERVISOR_8_62_COMPONENT_RUNTIME_FRONTIER`.

This re-entry replaces the stale 8.61/two-track/callability-only description with current `main` authority and observed evidence. The earlier protected-preview bridge breakthrough remains valid infrastructure history, but the frontier has advanced: fixed hash-bound family-split and Entry/JCS components have now actually executed under bounded FREE conditions. Their success is deliberately scoped to exact component bytes, and the stale Entry capsule `source_commit` label is retained as a falsifier/repair obligation rather than silently treated as exact-head manifest identity.
