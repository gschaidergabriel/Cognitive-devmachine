# EPOCH-G9 — Epoched Projection, Orchestration & Causal-Handoff Kernel

**Status:** OPEN/HOLD architecture candidate over CASK-G8. **Not canonical.** Canonical parent remains RAE-8.8 r2 / Clay generation 3.

## Core architecture delta

G8 made selective/fast behavior conditional on coverage and stability. G9 adds two boundaries discovered by fresh branch/runtime evidence:

1. **Selection Integrity Boundary:** authentic records can still be maliciously or accidentally *selected* by a compromised/noisy structural selector. Selection/provenance is therefore distinct from record provenance when decisions can reach effects.
2. **Projection Compilation Boundary:** deterministic facts/operators should be resolved by a trusted runtime/compiler before an LLM sees the problem. Model-visible representation is a compiled active view, not canonical authority.

```text
EXACT AUTHORITY PLANE
append-only events + exact state + provenance + capabilities
        │
        ├── Hyperposition semantic topology S
        ├── invariant/coordination topology C
        ├── physical topology P
        └── selector/accessibility view Q (non-authoritative)
        │
        ▼
IMMUTABLE SEMANTIC EPOCH
base index/graph + delta overlay + exact basis/root witness
        │
        ├── read-aware compaction/rebuild governor
        └── crash/replay epoch manifest
        │
        ▼
SPARSE LATENT FIELD (ephemeral)
lazy timestamped decay + typed local propagation + active-set GC
activation != truth != GWT ignition != authority
        │
        ▼
QUERY / ASSEMBLY PLANNER
exact-address / FTS fast path
      ↘ uncertainty / relational intent / evidence-chain gap
        graph/vector/role traversal escalation
        │
        ▼
SELECTION INTEGRITY BOUNDARY
selection provenance + structural trust + effect criticality
ordinary exploratory cognition may use broad associative cues;
effect-bound evidence selection must satisfy stronger policy
        │
        ▼
TRUSTED PROJECTION COMPILER
1. deterministic filter/join/min/max/version/capability operations
2. remove solved dimensions
3. retain unresolved semantic candidates
4. bind projection identity
        │
        │ projection_receipt = {
        │   basis_state_epoch, cognitive_frame_id,
        │   graph_epoch, activation_epoch?,
        │   query_plan_hash, semantic_hash,
        │   projection_hash, reader_version,
        │   selection_provenance_ref
        │ }
        ▼
MODEL SEMANTIC RESOLVER
small/local/cloud model receives only unresolved semantics + required witnesses
model output = proposal, never authority
        │
        ▼
GWT WORKSPACE EPISODE
competition/gate kept separate from projection/reconstruction/uptake
graph prior × workspace selection × projection × re-entry remain orthogonal factors
        │
        ▼
CC-RC1.3 / OTCC CLOSURE
trusted static envelope + observed trace
observed_trace ⊆ trusted_static_envelope
query/projection plan bound into closure identity
        │
        ▼
EFFECT GATEWAY / OUTBOX
validate capability + causal freshness + closure + effect class
+ selection integrity for selected-memory-dependent irreversible effects
atomic state+intent → recheck → idempotent release → receipt
        │
        ▼
OUTCOME / RE-ENTRY
re-entry requires compatible frame/state/graph/projection basis
```

## 1. Exact authority plane
Truth remains exact and replayable. Graph nodes, summaries, latent activation, workspace winner labels and model outputs cannot self-authorize. Hyperposition preserves simultaneously valid alternatives without destructive merge. The physical storage backend remains implementation-neutral.

## 2. Epoched semantic memory
G9 accepts ClayGraph G1d only as a **HOLD-compatible substrate**: immutable base semantic epochs plus add/remove delta overlays. Fresh C4 evidence and G9 economics both reject one fixed compaction threshold. Candidate decision variables:

`maintenance_decision = f(delta_fraction, overlay_postings, expected_reads, p95_tax, space_debt, recovery_debt, effect_criticality)`

Epoch readers pin one manifest; publication is atomic; reclamation is delayed until no pinned reader requires the old epoch.

## 3. Sparse latent field
The field is a between-query accessibility prior, not a database of truth. Required properties:
- lazy timestamped decay;
- typed/relation-specific propagation candidate;
- bounded neighborhood updates;
- active-set threshold and GC;
- exact epoch/event provenance for reconstruction;
- no direct capability/effect authority.

G9's reproducible proxy reduced global-decay operation count ~445× while matching sampled touched values to floating-point precision; this is computational evidence only.

## 4. Retrieval arbitration
The default path is **cheap deterministic retrieval**, not universal graph activation. Escalation signals may include:
- explicit relational/multi-hop intent;
- low lexical/exact-address confidence;
- missing evidence-chain links;
- contradiction/conflict detection;
- expected downstream decision value.

This aligns current PRISM/MemArbiter/GAM-style external work with ClayGraph's own negative hot-path evidence without assuming those systems validate FRANK.

## 5. Selection integrity
Record provenance answers: *Where did this fact come from?*  
Selection provenance answers: *Why did this fact enter the active decision set and which structure could change that membership?*

For effect-bound decisions, candidate receipt fields:
- selector/query-plan hash;
- graph epoch;
- structural edge provenance/trust classes traversed;
- selected ids and rank margins where relevant;
- authenticated-subgraph / policy-check result;
- fallback used (FTS/exact/full authorized set) when selector integrity is uncertain.

This boundary is especially important because an attacker/noisy writer can potentially redirect authentic evidence without falsifying the records themselves.

## 6. Deterministic-before-generative ClayCode
The G9 Groq arm moved from 6/10 raw-state reading to 8/10 after trusted candidate compilation while cutting prompt tokens 487→324. But it still chose the wrong min candidate once and omitted a unique answer. G9 therefore makes a stronger inference than 'compiled prompts are better':

> **If the runtime can soundly compute a relation/operator, it should compute it. Do not pay a stochastic model to rediscover deterministic state semantics.**

ClayCode becomes three things at once:
1. canonical semantic IR;
2. trusted transformation/query-plan source;
3. compiler for reader-specific unresolved semantic projections.

## 7. GWT orthogonalization
Future causal runs must independently manipulate:
- `GRAPH_PRIOR` — latent/associative accessibility;
- `WORKSPACE_SELECTION` — competition/winner/gate;
- `PROJECTION` — what semantic content reaches reader;
- `REENTRY` — what returns to future state.

Pin CognitiveFrame/state epoch, graph epoch, final facts, option/order/token budget wherever the experimental factor does not require changing them. A configured threshold or graph activation is not endogenous ignition evidence.

## 8. Exact-addressable semantic zoom
Canonical exact items remain addressable; active context may show summary/pointer/ambient form. Query uncertainty or effect value triggers exact recall. This avoids treating summaries as truth and allows bounded context without irrevocable information deletion.

## 9. Maintenance/resource governor
One policy surface coordinates:
- delta compaction/rebuild;
- latent active-set pruning;
- exact zoom;
- graph escalation;
- GWT fanout;
- KV/context allocation;
- speculation/model path;
- thermal/memory protection.

But G9 rejects one scalar 'maintenance debt' as universally optimal: its own seeded proxy lowered p95 with debt-aware rebuilding while worsening mean cost. Objectives and hard constraints must stay explicit.

## 10. Emergence anti-Goodhart
A persistent latent field or self-evolving graph is **not** emergence evidence. Candidate Assembly-level evidence still requires preregistered function, lesion, specific rescue, compute-matched/shuffled controls, OOD recurrence, higher-order intervention metrics and robustness/cost shadows. No phenomenal-consciousness claim follows.

## Promotion gate
EPOCH-G9 remains HOLD until at minimum:
1. real/twin FRANK atomic epoch/frame tests;
2. target Qwen3-4B raw vs compiled-projection reader test;
3. no-field vs truthful-field vs shuffled-field causal memory test;
4. adversarial selector-integrity test on effect-bound decisions;
5. actual-corpus retrieval Pareto comparison against SQLite/FTS/packet envelopes;
6. crash/replay of epoch publication + compaction + latent reconstruction + effect outbox;
7. Android sustained resource-governor trace.
