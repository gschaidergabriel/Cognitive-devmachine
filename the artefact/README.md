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
2. **HCU_AND_TYPED_ENTRY_FABRIC_CO_DEVELOPMENT** — advance/test/specify/wire/benchmark at least one HCU or typed Entry primitive.
3. **GLOBAL_JSPACE_GWT_PROTOTYPE_AND_FREE_ONLY_LOCAL_08B_READINESS** — advance instrumented J-Space/GWT causal traces and zero-cost local ~0.8B readiness without entering a paid lane.

If track 2 cannot safely advance, record `HCU_NO_CHANGE_WITH_REASON`; if track 3 cannot safely advance, record `TRAINING_READINESS_NO_CHANGE_WITH_REASON` and the next discriminator.

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

Current autonomous supervisor `8.62` is **FREE_ONLY**. Build/test/experiment/runtime credit comes only from authorized isolated execution surfaces that remain inside the admitted no-spend boundary. VPS/self-hosted/production-host testing is forbidden. Together general inference and the paid Together training lane are forbidden in this supervisor mode; the owner paid one-shot directive remains provenance only and may not trigger credential lookup, preflight, network I/O, job creation or spend.

Vercel Hobby Sandbox is now admitted only as a **bounded included-tier FREE isolated execution surface** under explicit fail-closed conditions. Credit-bearing runs must use fixed source-hash-bound capsules, remain short and isolated, and clean up promptly. If remaining quota is uncertain, or billing, plan mismatch, upgrade, paid fallback or any monetary charge path appears, execution fails closed before the run. Remaining quota is not assumed merely from the Hobby plan name.

An exact-current J-Space dataset family-split component has executed `6/6 PASS` twice in isolated execution. This is component runtime evidence/reproducibility only; it grants no whole HCU, J-Space model, training, EntityOS or canonical-semantics credit. Earlier Vercel capsule executions that raced stale cost authority remain quarantined with zero acceptance credit.

Source/component/historical PASS does not imply EntityOS/HCU runtime acceptance.

## Current frontier

1. keep **PR #1401** as the current-main HCU fusion candidate and **PR #1263** as retained donor provenance; do not create a second HCU/Entry/J-Space authority;
2. refresh/rebase the fusion to exact current `main` before promotion;
3. run one fixed exact-source **repaired HCU capsule** on the bounded admitted Hobby Sandbox surface;
4. bind Research main SHA/tree, HCU fusion/donor SHA/tree, capsule/source digests, executor identity/result digest, secret fence and cleanup in one immutable receipt;
5. on pass, extend the same path toward Typed Entry -> route -> real deterministic engine admission -> generation-fenced loader-consumption evidence -> inference receipt -> GRID10 -> J-Space/GWT -> admitted causal dataset closure;
6. preserve replay-stable event identity vs concrete admission identity and wire Entry capability claims to the existing deterministic capability authority rather than event self-claims;
7. bind the actual downstream inference producer to event/route/engine/class/artifact/loader-lease identity;
8. only after exact executable and real-trace gates, continue zero-cost local ~0.8B checkpoint/tokenizer/runtime work; do not preflight or launch Together under the current FREE_ONLY supervisor;
9. rebuild/digest-bind compatibility snapshots only after route/Entry/loader semantics settle.

## Latest `go` README re-entry — 2026-08-24

`README=UPDATED_SUPERVISOR_8_62_AUTHORITY_REENTRY`: verified current `main` exposed a concrete successor split immediately before the next HCU runtime gate: `SUPERVISOR_INBOX` selected `SUPERVISOR_STEERING_8_62`, while Bootstrap/Program/manifest/root routing/README/footer surfaces still named older 8.61/8.52 authority. This branch re-enters those current-facing surfaces toward one 8.62 FREE_ONLY contract before any credit-bearing HCU run.

Supervisor 8.62 also changes the executable frontier materially: Vercel Hobby Sandbox is admitted only within the observed included-tier boundary under fixed-hash capsule, quota/billing/upgrade fail-closed, secret-fence and cleanup conditions. The first bounded component evidence is the exact-current J-Space family split `6/6 PASS` twice; same-family rerun is reproducibility, not independent replication, and grants no whole-HCU/EntityOS/model/training credit.

Next executable discriminator remains one exact-current repaired HCU capsule over the single retained fusion path, with complete source/result/secret/cleanup identity binding. If the callable connector surface cannot issue that fixed capsule invocation, the blocker is execution ingress capability—not semantic test failure—and source coherence must remain explicitly unpromoted.
