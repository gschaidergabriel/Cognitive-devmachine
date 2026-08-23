# the artefact — EntityOS + HCU cognitive computer

`the artefact/` is the canonical product/research workspace for the current **EntityOS** system and its integrated **HCU** cognition/compute architecture.

Current authority is resolved from verified current `main`, especially:

- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/claycode/autonomous/SUPERVISOR_STEERING_8_61.json`
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

Every explicit `go` has two coupled tracks:

1. **ENTITYOS_EXECUTABLE_CONVERGENCE** — improve the strongest real current implementation toward EntityOS.
2. **HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT** — advance/test/specify/wire/benchmark at least one HCU or typed Entry primitive.

If track 2 cannot safely advance, record `HCU_NO_CHANGE_WITH_REASON` and the next discriminator.

Material architecture work uses:

`OBSERVE -> HYPOTHESIS -> COUNTERHYPOTHESIS -> CHEAPEST DISCRIMINATOR -> SOURCE/TEST EVIDENCE -> FUSION -> BOUNDED DELTA -> RE-ENTER`

Prefer primitives reusable across multiple HCU modes.

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

Inputs may originate from humans, tools, external events, sensor/stream data, canonical database changes or intrinsic system events.

Capability claims in an untrusted Entry packet are **not authority**. Entry admission must compare them against the existing deterministic permission/capability authority and its exact binding/receipt identity; the packet may narrow an admitted capability set but may never self-grant or broaden it. No second HCU permission authority is introduced.

Replay-stable causal event identity and concrete transport/admission identity must remain distinguishable: changes such as receive time, payload reference, permission snapshot or resource budget may change the admission identity without silently redefining the underlying immutable event identity. Changing immutable payload/provenance/event semantics must change event identity.

HCU route events and downstream inference receipts must ultimately re-enter through this fabric so event identity, generation, engine identity and causal provenance remain bound instead of becoming a side ledger.

## HCU reactive cognition

The current HCU direction is script-first and selective:

`canonical event -> deterministic maintenance -> selective HCU lane activation -> Hyperposition/J-Space candidate computation -> bounded projection -> EntityOS decision path`.

External providers are not admitted as required internal cognition. Exact local checkpoint/tokenizer/runtime identity is an acceptance gate, not an inferred fact. Until a positive local engine capability record exists, absence from an external-provider denylist is insufficient to prove internal engine admission.

**Pre-load hashing is not loader attestation.** A positive `EngineAdmission` constructed from checkpoint/tokenizer/runtime/build hashes receives zero HCU runtime credit unless the actual model loader is bound to the same consumed bytes. The admitted path must therefore use a generation-fenced physical engine lease or an enforced read-only/content-addressed artifact boundary and must echo the loader-consumed artifact identity into the downstream inference receipt. Wrong-path loads, post-admission mutation, stale lease reuse or unknown consumed bytes fail closed.

## Execution policy

Current autonomous supervisor `8.61` is **FREE_ONLY**. Build/test/experiment/runtime credit comes only from authorized isolated execution surfaces that do not introduce a new paid provider/resource fallback. VPS/self-hosted/production-host testing is forbidden under current control. Together inference/training is forbidden in this supervisor mode. Secrets do not enter source/receipts.

A protected Vercel Preview route on retained PR810 has now empirically demonstrated worker-callable `Sandbox.create` + `runCommand` without a GitHub token or separate Sandbox probe secret. This grants **Vercel Sandbox infrastructure callability credit only**. It does not grant EntityOS/HCU runtime, local-model, J-Space-model, training, target-hardware, effect, or whole-product acceptance. Vercel team plan observed through the authorized connector is `hobby`; explicit zero-monetary-cost Sandbox pricing was not established by the available documentation, so FREE_ONLY accounting must not infer cost from plan name alone.

Source/component/historical PASS does not imply EntityOS/HCU runtime acceptance.

## Current frontier

1. replace the old credential-bearing arbitrary POST dependency with the verified protected-preview Sandbox bridge plus fixed SHA-bound source capsules/regression commands, so exact private Research bytes can be executed without persisting or requesting a GitHub runtime token;
2. wire the retained HCU route's separate `EngineAdmission` to the **real deterministic EntityOS/HCU control-plane producer** and bind it through a generation-fenced physical engine lease to the bytes actually consumed by the local checkpoint/tokenizer/runtime loader; a pre-load hash alone receives zero runtime credit, and an untrusted causal Entry event may request but may never mint engine authority;
3. keep the replay-stable **event identity vs concrete admission identity** split and wire Typed Entry capability claims to the existing canonical deterministic capability authority rather than a test fixture or event self-claim;
4. bind the downstream inference receipt **producer** to the already-defined serializer/event/Entry-admission/route/engine/class/artifact echo contract plus the exact physical loader lease/consumed-byte identity;
5. converge the versioned Typed Entry canonicalization path to one accepted authority before making heterogeneous/cross-language hash-identity claims;
6. run exact combined Entry + HCU route + engine-load-lease + inference-echo + GRID10 + J-Space regressions through the now-callable protected-preview Vercel Sandbox bridge, with exact Research main/PR1263 identities and result digests bound in one receipt;
7. rebuild and digest-bind the stale `MICROENTITY_CURRENT.zip` compatibility snapshot only after route/Entry/loader semantics settle.

Completed authority migration note: current `the artefact/manifest.json` and the compatibility-named authority validator now select **EntityOS + HCU** while preserving historical ClayVerse controls only as immutable donor/safety ancestry. This source-level convergence does not create runtime acceptance.

## Latest `go` README re-entry — 2026-08-24

`README=UPDATED_VERCEL_SANDBOX_CALLABILITY`: the previous blocker was not a lack of Vercel Sandbox capability but an uncallable execution-admission shape: retained PR810 required an arbitrary credential-bearing POST before `Sandbox.create`. A bounded PR810 delta changed only the diagnostic probe to a protected-preview, exact-branch GET surface with no extra probe secret. Deployment `dpl_9vST7MFPJzdcHjw8s47MSHs4DbSM` from bridge commit `33cdfd2aecf820c9b48e7d47376f126d0e831bfd` returned `VERCEL_SANDBOX_EXECUTION_VERIFIED`: Linux x86_64, Python 3.13.1, filesystem hash `77707d7ae00b238db00d1d983a78f73b357afd36fdf5268c6f89a49509308436`, secret fence PASS, exit 0, cleanup PASS. Receipt: `the artefact/MicroEntity/hcu/receipts/2026-08-24_GO_SANDBOX_CALLABILITY_GPT56SOL.json`. This is an execution-infrastructure breakthrough only; EntityOS/HCU/model/J-Space/training/whole-product runtime credit remains zero. The next discriminator is to use this callable bridge with fixed SHA-bound source capsules rather than runtime GitHub credentials.
