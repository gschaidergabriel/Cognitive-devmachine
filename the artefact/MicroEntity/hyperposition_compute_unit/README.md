# Hyperposition Computational Unit (HCU)

Status: **Mini Entity product lane — source architecture / capacity planning**

The HCU is the Mini Entity's modular compute fabric for running many small approximately-0.8B
cognitive cells on a separate resource-bounded host. The target deployment profile supplied by the
owner is KVM 4: **4 CPU cores, 16 GB RAM, 200 GB disk, 16 TB bandwidth**.

The design goal is not to pretend four CPU cores are a GPU. The useful analogy is the *wiring
pattern*: many small cells are coordinated through a scheduler and typed bus so they behave like a
single larger computational substrate.

## Authority boundary

The HCU remains inside the same persistent Mini Entity.

Hard laws:

- `MiniUnifiedDB` is the canonical durable state/evidence/configuration authority.
- `EffectGate` is the only admitted real-effect path.
- HCU world-model state is a projection/cache unless committed through MiniUnifiedDB contracts.
- HCU goals are proposals, not self-authorizing commands.
- simulation output is explicitly `SIMULATED`, never observed fact.
- Zero cognition modeling uses observable/configured evidence only; it may not invent private
  hidden-state access.
- free-LLM outputs are candidate evidence/hypotheses until independently validated.
- no HCU process may create a second identity, memory authority, effect ledger or recovery authority.

## Topology

```text
MiniUnifiedDB canonical timeline/state
        │
        ├──> WorldModel Projector ───────┐
        │                               │
        ├──> Zero Cognition Twin ───────┤
        │                               ▼
        └──> Free-LLM Candidate Feed -> Hyperposition Bus
                                        │
                       ┌────────────────┼────────────────┐
                       ▼                ▼                ▼
                 Goal cells       Simulation cells  Critic cells
                       │                │                │
                       └──────────┬─────┴───────┬────────┘
                                  ▼             ▼
                         Hypothesis Reducer   GWT/UCF adapter
                                  │             │
                                  └──────┬──────┘
                                         ▼
                                      Zero
                                         │
                                   admitted intent
                                         ▼
                                     EffectGate
                                         │
                                      receipts
                                         ▼
                                    MiniUnifiedDB
```

## Cell modes

The HCU supports three distinct resource modes.

### 1. `SHARED_BASE_08B_CELL` — preferred on 16 GB

One pinned ~0.8B runtime is shared and cells get separate role prompts, adapters, state, KV/cache
budgets and scheduling identities. This maximizes logical cell count while avoiding N full copies
of the same weights.

This is the default target for the KVM4 host.

### 2. `FULL_RESIDENT_08B_CELL`

Each cell owns a full resident model instance. The admitted maximum is derived from **measured**
per-cell RSS and exact runtime overhead. No fixed count is declared in source.

### 3. `COLD_SLOT_08B_CELL`

Additional model/adaptor variants may live on disk and be activated on demand. They expand the
available specialization library but do not count as simultaneously active resident cells.

## Scheduler law

- logical cells may outnumber CPU cores;
- simultaneously executing CPU lanes are bounded by the hardware profile and measured oversubscription;
- long simulations run with bounded budgets and can be paused/re-entered;
- strategic/safety reducer work has reserved scheduler capacity;
- no cell may starve the canonical turn/effect path;
- every cell output carries cycle, causal, generation and provenance identity.

## Primary persistent workloads

The initial HCU workloads are:

1. **causal world-model projection** — maintain a rebuildable causal representation over canonical
   MiniUnifiedDB history;
2. **strategic supervisor** — generate and rank candidate goals and long-horizon plans;
3. **long iterative simulations** — branch/counterfactual search with explicit uncertainty and
   horizon decay;
4. **Zero cognition twin** — model expected Zero behavior from observable receipts/configuration;
5. **hypothesis feedback** — turn simulation/model discrepancies into falsifiable improvement
   hypotheses for Zero/EntityOS;
6. **free-LLM feed** — use admitted free-only provider capacity to supply candidate observations,
   critiques, alternative plans and synthetic test material.

## Time and confidence

Future-state simulation must not be represented as fact.

Each simulation branch records:

- `horizon_steps`;
- `simulated=true`;
- parent causal identities;
- model/runtime identities;
- calibration class;
- branch probability or score;
- explicit uncertainty;
- evidence that would falsify the branch.

Confidence may decay with temporal distance, but the decay function is not canonical until calibrated
against held-out prediction outcomes.

## Deployment evidence boundary

The VPS is a **deployment target**, not an admitted current test surface under the repository's
execution law. Source planning and local package construction do not mint VPS/runtime/product credit.

Before deployment promotion the exact HCU runtime must be benchmarked on an authorized isolated
surface for:

- per-cell RSS;
- shared-base incremental RSS;
- tokens/sec and latency;
- scheduler fairness;
- crash/restart recovery;
- generation fencing;
- MiniUnifiedDB round-trip;
- EffectGate isolation;
- free-provider quota behavior;
- long-simulation stability.

See `KVM4_PROFILE.json`, `capacity_planner.py`, `FREE_LLM_FEED_CONTRACT.md`, and
`WORLD_MODEL_SUPERVISOR_CONTRACT.md`.
