# Hyperposition Computational Unit (HCU)

Status: source architecture candidate; runtime capacity unverified.

## 1. Purpose

The HCU is the Mini Entity's persistent strategic compute organ. It uses a grid of approximately-0.8B cognition modules to maintain causal hypotheses, simulate futures, propose goals/plans, model Zero, and return falsifiable improvement candidates.

It is deliberately **not** a second entity, second memory authority or second effect path.

## 2. Target host profile

Owner-nominated deployment target:

| Resource | Target |
|---|---:|
| vCPU | 4 |
| RAM | 16 GB |
| Disk | 200 GB |
| Bandwidth | 16 TB |
| Plan | KVM 4 |

This host profile is a deployment target. Acceptance evidence still follows the repository's current isolated-sandbox-only execution law.

## 3. Why a logical grid instead of N duplicated model processes

A literal grid of many independent 0.8B processes is memory-feasible only at a crude weight-count level and becomes CPU/cache/KV-bound quickly on four cores. The HCU therefore separates:

- **physical workers**: resident model runtimes holding ~0.8B weights;
- **logical cells**: role-specific cognition lanes with independent context, state references, adapter/profile and scheduling identity.

The default design is shared-weight, sparse and time-sliced. Physical worker count is promoted only from measured RSS/latency/throughput evidence.

Initial unverified deployment defaults:

- `physical_workers_target = 1`;
- `physical_workers_hard_cap = 2` until benchmarked;
- `logical_cells = 16`;
- `active_cells_per_round <= 4`;
- contexts are bounded and recycled;
- weight files should be memory-mapped/shared where the chosen runtime supports safe sharing.

These are starting constraints, not acceptance claims.

## 4. Cell roles

The grid can instantiate multiple copies of each role as logical cells:

1. **Observer cells** — compress/admit incoming world evidence into typed candidate observations.
2. **Causal cells** — propose causal edges, dependencies and counterfactual mechanisms.
3. **Goal cells** — generate goal candidates from unresolved state, commitments and opportunity signals.
4. **Planner cells** — simulate multi-step paths toward admitted goals.
5. **Counterfactual cells** — search alternative futures and failure branches.
6. **Critic cells** — attack assumptions, detect contradiction, overconfidence and self-reinforcement.
7. **Zero-model cells** — predict Zero's likely interpretation/action as an explicit model, never as ground truth about hidden cognition.
8. **Verifier cells** — compare predictions against later observed outcomes and produce calibration feedback.
9. **Compression cells** — distill old simulation branches without becoming a hidden lossless transcript authority.
10. **Method cells** — extract reusable validated methods while preserving `FACT_UNKNOWN + METHOD_PRESENT != FACT_PRESENT`.

Roles are configuration, not permanent model identities. A shared 0.8B core can service many role lanes.

## 5. GPU-like interconnect analogy

The GPU analogy is architectural, not hardware-equivalence.

The HCU consists of:

- a **scheduler** analogous to a command processor;
- a **shared weight pool** analogous to resident compute kernels;
- many **logical cells** analogous to lanes/warps;
- a typed **Hyperposition Bus** analogous to an interconnect;
- a **workspace arbiter/GWT** selecting bounded active coalitions;
- MiniUnifiedDB references acting as canonical backing state;
- deterministic admission/effect gates outside model control.

Cells do not directly share arbitrary mutable Python objects or private hidden transcripts. They exchange typed packets.

## 6. HCU packet contract

Minimum conceptual packet fields:

```text
HCU_PACKET/v1
  packet_id
  parent_packet_ids[]
  entity_generation
  causal_id
  episode_id
  source_refs[]
  world_state_refs[]
  role
  operation
  hypothesis_id
  alternative_set_id
  content_digest
  confidence
  uncertainty_type
  valid_from
  valid_until
  provenance
  budget
```

A packet is cognition transport, not truth. Canonical state changes require deterministic admission into MiniUnifiedDB.

## 7. Hyperposition Bus

The bus preserves unresolved alternatives as a set rather than forcing early agreement.

Each alternative can carry:

- supporting evidence refs;
- counterevidence refs;
- causal assumptions;
- predicted observations;
- falsifiers;
- calibrated probability/confidence;
- horizon;
- cost/value-of-information.

Majority vote does not collapse Hyperposition. Collapse requires admitted evidence or a decision rule that explicitly permits action under uncertainty without rewriting epistemic state.

## 8. Permanent world-model loop

```text
free/provider candidate input
        |
        v
provenance + quarantine + normalization
        |
        v
MiniUnifiedDB canonical observations/state refs
        |
        v
HCU scheduler -> sparse cell coalition
        |
        +--> causal hypotheses
        +--> goal candidates
        +--> long simulations
        +--> Zero-model predictions
        +--> counterfactual/failure worlds
        |
        v
GWT/arbiter bounded selection
        |
        v
validated goal / hypothesis / plan candidates
        |
        v
Zero / EntityOS operative runtime
        |
        v
EffectGate / deterministic execution authority
        |
        v
verified outcome / UNKNOWN
        |
        v
causal re-entry -> MiniUnifiedDB -> calibration -> HCU
```

The HCU may run continuously while Zero is idle, but its outputs remain proposals until admitted.

## 9. Dynamic goals

Goal generation is allowed, autonomous goal authority is not.

Every HCU-generated goal is a typed candidate with:

- origin and causal trigger;
- expected utility;
- owner/system constraints;
- required capabilities/effects;
- falsifiable completion criteria;
- expiry/horizon;
- confidence and uncertainty;
- conflict relation to existing commitments.

Goal admission remains deterministic and policy-bounded. A model cannot grant itself capability by inventing a goal.

## 10. Modeling Zero

The HCU can maintain explicit models of Zero's likely behavior, such as:

- likely next interpretation;
- likely tool/operation choice;
- common failure pattern;
- confidence calibration profile;
- expected response to a hypothesis or prompt;
- expected resource cost.

These are predictive hypotheses about the operative layer. They are never claimed as direct observation of hidden internal cognition unless an admitted measurement mechanism supports that scope.

## 11. Long simulation and temporal confidence

Simulation branches are versioned and horizon-bound. Future confidence should decay according to empirical calibration, not a fixed narrative rule.

Target calibration signals include:

- historical Brier/log-loss by horizon;
- branch survival rate;
- prediction error conditioned on domain and evidence density;
- model/provider disagreement;
- causal intervention accuracy;
- Zero-behavior prediction error.

A future branch can be useful for planning while remaining explicitly uncertain.

## 12. Free-LLM token-fundus ingestion

Free inference providers are external cognition suppliers, not authorities.

Ingestion path:

```text
FREE_ONLY provider scheduler
-> provider capability profile
-> request budget/quota guard
-> candidate response
-> provenance envelope
-> contradiction/duplication checks
-> HCU candidate pool
-> optional cell critique/synthesis
-> deterministic state admission
```

Requirements:

- provider/model/version/request/time provenance;
- no secrets in MiniUnifiedDB package snapshots or ZIPs;
- no paid fallback;
- 402 hard stop;
- 429 provider-wide backoff;
- no quota-evasion key rotation;
- consensus across providers is evidence of agreement, not factual truth.

## 13. State authority and separate-VPS rule

The HCU VPS may persist:

- runtime caches;
- model mmap files;
- rebuildable indexes;
- bounded simulation working sets;
- signed/digested checkpoints whose canonical status is recorded in MiniUnifiedDB.

It may **not** own a competing canonical world database.

If disconnected from MiniUnifiedDB, the HCU either:

1. continues in explicit `DEGRADED_NONCANONICAL_SIMULATION` using the last admitted snapshot, or
2. pauses canonical-write attempts.

Reconnection requires generation/provenance reconciliation before any proposed update is admitted.

## 14. Resource strategy for 4 vCPU / 16 GB

Initial budget envelope, to be replaced by measurements:

- reserve ~3-4 GB for OS, DB, scheduler, buffers and safety margin;
- make the remaining memory budget explicit to the model runtime;
- prefer one shared/mmap 0.8B runtime over many copied processes;
- use short bounded contexts for specialist cells;
- activate only the top-k relevant cells per round;
- use idle-time simulation queues rather than CPU-saturating all cells continuously;
- cap disk growth with retention classes and semantic compaction;
- preserve the causal timeline and high-value evidence, not unlimited raw provider chatter.

The correct module count is an empirical capacity result, not a design-time integer.

## 15. First acceptance experiments

When an authorized isolated execution surface can reproduce the host envelope, measure:

1. one physical worker vs two physical workers;
2. 4 / 8 / 16 / 32 logical cells under identical work;
3. mmap/shared-weight vs duplicated-process RSS;
4. sparse top-k activation vs all-cell activation;
5. throughput, p50/p95 latency, RSS, swap, CPU saturation and queue age;
6. plan quality and calibration vs a single-cell baseline;
7. whether multi-cell synthesis improves verified outcomes rather than only verbosity;
8. restart/recovery and stale-generation rejection;
9. provider-feed contamination/duplication and offline degradation;
10. Zero-model prediction calibration.

Promotion criterion: the grid must beat a simpler single-0.8B baseline on verified task utility per unit resource, not merely produce more internal text.

## 16. Package boundary

All package-safe HCU files live under:

`the artefact/MicroEntity/hcu/`

The current MicroEntity ZIP must recursively include this directory whenever rebuilt. Secrets never enter the package.
