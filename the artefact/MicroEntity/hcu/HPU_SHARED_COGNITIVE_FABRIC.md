# HPU Shared Cognitive Fabric — candidate architecture

Status: **OWNER-REQUESTED DESIGN CANDIDATE / NO RUNTIME CREDIT**  
Date: 2026-08-23  
Program: Mini Entity / EntityOS  
Package lane: `the artefact/MicroEntity/hcu/`

## 1. Core idea

The HPU/HCU must not behave like a chatty multi-agent swarm.

Its modules share one generation-fenced world state and one dynamically routed cognitive field. They do not need pairwise negotiation or consensus to stay coherent.

```text
MiniUnifiedDB generation G
        |
        v
immutable GLOBAL_STATE_FRAME/G
        |
        +----------------------------+
        |                            |
        v                            v
GLOBAL J-FIELD / workspace       Hyperposition plane
(dynamic sparse projection)      (unresolved alternatives)
        |
   many independent logical modules
        |
   typed candidate deltas only
        |
        v
single deterministic reducer / gates
        |
        v
MiniUnifiedDB generation G+1
```

The desired property is:

**same base state + independent computation + field-mediated coupling + deterministic convergence**.

`SHARED_INFERENCE` is not required and must not become an architectural dependency. A small resident ~0.8B worker pool may time-slice many logical modules; the persistent continuity is in the shared state/workspace fabric, not duplicated model processes or private KV state.

## 2. Authority law

This fabric does not change the existing authority boundary.

```text
MiniUnifiedDB = only canonical durable state/evidence/configuration authority
EffectGate    = only admitted real-effect authority
Global J-Space / J-Field = ephemeral projection/routing/measurement fabric
HCU/HPU modules = independent candidate compute contexts
Hyperposition = unresolved alternatives, never truth by vote
ClayCode = orchestration + invariant enforcement
LLM/model output = candidate only
```

The J-Field may change **who sees what and when**. It may never change what is canonically true merely because an activation, score, edge weight, majority or recurrent pattern is high.

## 3. Do not use SQLite itself as the hot communication bus

MiniUnifiedDB/SQLite remains the canonical source, but every logical module must not hold a long-lived read transaction or repeatedly query the DB for each microstep.

That would create avoidable latency and WAL/checkpoint pressure. Historical Zero measurement already found the dangerous pattern: persistent readers allowed a WAL to grow very large and contributed to lock/latency failures.

Instead use two levels:

### 3.1 Canonical plane

SQLite/WAL holds durable state, bindings, receipts and accepted transitions.

Reads that establish a new generation frame are short-lived and generation-fenced. Canonical writes remain serialized through one reducer/gate path.

### 3.2 Hot shared frame

At each admitted generation, a `StateFrameCompiler` materializes the exact relevant canonical state into an immutable memory-mapped/read-only frame.

Candidate schema:

```text
HPU_GLOBAL_STATE_FRAME/v1 {
    entity_generation
    canonical_state_hash
    frame_epoch
    source_binding_digest
    world_model_digest
    workspace_digest
    hyperposition_digest
    channel_index_digest
    payload_digest
}
```

All modules scheduled against generation `G` read the **same immutable frame bytes** or deterministic slices derived from them.

No module can mutate the frame. A new canonical state creates a new frame `G+1`.

This makes the low-latency path shared-memory/mmap reads while SQLite remains the Base of Truth.

## 4. Global J-Field: the dynamic information matrix

The Global J-Space should be extended into a system-level **J-Field**: a sparse, dynamic routing matrix between information channels and logical modules.

This is not a claim about hidden model-internal activations. It is an explicit external cognitive fabric.

Let:

- `C = {c1 ... cn}` be typed information channels;
- `M = {m1 ... mk}` be logical modules;
- `W[g][m,c]` be the routing weight at generation/epoch `g`.

Example channels:

```text
WORLD.STATE
WORLD.DELTA
WORLD.CAUSAL_EDGE
GOAL.ACTIVE
GOAL.PRESSURE
SIMULATION.BRANCH
HYPOTHESIS.OPEN
CONTRADICTION
UNCERTAINTY
PROVENANCE
RESOURCE.PRESSURE
ZERO.BEHAVIOR
WORKSPACE.BROADCAST
HYPERPOSITION.SET
OUTCOME.VERIFIED
```

`W` determines the bounded workspace slice exposed to each module. It does **not** confer truth or effect authority.

## 5. Dynamic routing rule

The topology should change continuously from measured utility rather than fixed agent links.

A candidate route score is:

```text
route_score(m,c) =
    + a1 * salience
    + a2 * novelty
    + a3 * contradiction_pressure
    + a4 * expected_uncertainty_reduction
    + a5 * verified_causal_coupling
    + a6 * downstream_usefulness
    + a7 * temporal_relevance
    - b1 * redundancy
    - b2 * compute_cost
    - b3 * stale_generation_risk
```

Then update with bounded adaptation and hysteresis:

```text
W_next = hysteretic_topk((1-eta) * W_prev + eta * normalized(route_score))
```

Hard constraints:

- deterministic tie-breaking;
- per-module channel budget;
- minimum hold time / hysteresis to prevent route flapping;
- stale-generation edges rejected;
- provenance and privacy filters before routing;
- explicit `UNKNOWN` rather than implicit zero;
- route scores are routing evidence, never fact confidence.

For recurrent module -> field -> module paths, normalize the effective recurrent operator to an accepted stability envelope. A spectral-radius/Jacobian guard can detect runaway positive feedback before the dynamic topology becomes a self-amplifying echo chamber.

## 6. Cross-quadrant emergent coupling without module chat

The requested cross-quadrant behavior falls naturally out of a common field.

Example:

```text
Quadrant A: weather
Quadrant B: transport
Quadrant C: resources
Quadrant D: population
```

A weather module never sends `message(B, ...)`.

Instead:

1. A computes a candidate delta against frame `G`.
2. The delta enters the shared candidate/workspace plane.
3. Deterministic world rules expose affected variables/channels.
4. The J-Field raises or lowers routes based on measured coupling.
5. B/C/D receive the relevant changed channels on a later micro-epoch or generation.
6. All remain anchored to the same `state_frame_digest` and generation.

Thus coupling is mediated by the shared world/workspace, not pairwise agent negotiation.

This allows globally coherent emergent patterns while preserving local specialization.

## 7. Three coupling classes

To avoid confusing correlation with causal structure, J-Field edges should carry a class.

### STRUCTURAL

Derived from explicit world-model/ClayGraph relations and deterministic rules.

### ADAPTIVE

Short-lived routing learned from co-activation, salience, novelty, contradiction and downstream utility.

### CAUSAL_EVIDENCE

Earned only by admitted perturbation, replay, counterfactual comparison, transfer-entropy/lag analysis or other discriminating evidence.

A high adaptive edge does not automatically become a causal edge. A causal edge still remains routing/model evidence unless separately admitted as canonical world knowledge.

## 8. Workspace protocol per module

Reuse the existing Zero/J-Space ancestry rather than inventing a second workspace identity.

Candidate envelope:

```text
HPU_MODULE_WORKSPACE_CAPSULE/v1 {
    entity_generation
    state_frame_digest
    global_workspace_digest
    jfield_digest
    module_id
    logical_role
    selected_channels[]
    selected_workspace_slots[]
    hyperposition_digest
    contradiction_state
    resource_budget
    route_digest
    provenance_refs[]
    capsule_digest
}
```

Rules:

- references one exact immutable global frame;
- bounded projection only;
- no private durable memory authority;
- no hidden transcript authority;
- deterministic digest over exact exposed content/refs;
- explicit abstention when required state is unavailable;
- module output cannot escape its capsule ancestry.

Where a module invokes an LLM, the existing `ZERO_WORKSPACE_CAPSULE` / `ZERO_INFERENCE_PACKET` / capability-binding semantics should be reused or versioned into one shared packet family. Do not create a parallel inference authority for HPU.

## 9. Candidate plane

Modules publish typed candidate deltas into a non-canonical append/ring plane.

```text
HPU_CANDIDATE_DELTA/v1 {
    module_id
    generation
    state_frame_digest
    workspace_capsule_digest
    causal_scope
    touched_channels[]
    observations[]
    proposed_state_deltas[]
    hypotheses[]
    counterevidence[]
    uncertainty
    resource_cost
    candidate_digest
}
```

The candidate plane can use an in-memory queue/ring buffer because it has no durable truth authority. Important candidates are later persisted with provenance through the normal MiniUnifiedDB path.

No module writes canonical SQLite rows directly.

## 10. Deterministic reducer

One reducer owns transition construction for generation `G -> G+1`.

```text
same StateFrame/G
+ ordered candidate set
+ fixed ruleset/version
+ Hyperposition preservation
+ deterministic tie-breakers
+ authority gates
= proposed next state
```

A canonical transition should bind at minimum:

```text
previous_generation
previous_state_hash
state_frame_digest
jfield_digest
ordered_candidate_set_digest
ruleset_digest
result_state_hash
commit/no_commit result
```

This preserves the owner's requirement that all modules can operate on the exact same Base of Truth while still producing different specialized contributions.

## 11. Global workspace broadcast

Do not broadcast every candidate to every module.

Use a bounded competition similar to the measured Zero workspace principle:

```text
many candidate signals
-> scoring/eligibility
-> small winning coalition
-> J-Field projection
-> only relevant modules receive full payload
```

Metadata can remain broadly visible while full content is materialized only for selected routes.

This saves context, CPU and memory while retaining global coordination.

The Zero workspace evidence showed that selection must be a real bottleneck: if a module can bypass the workspace and independently read the same hidden full payload, workspace ablations become meaningless.

## 12. Information planes

The HPU cognitive fabric should distinguish five planes:

1. **Canonical State Plane** — MiniUnifiedDB, durable truth/evidence/configuration.
2. **Immutable Frame Plane** — generation-fenced read-only materialization for low latency.
3. **Workspace/J-Field Plane** — dynamic sparse routing and active coalition.
4. **Hyperposition/Candidate Plane** — unresolved alternatives and module proposals.
5. **Effect Plane** — only EffectGate may admit real external effects.

These planes are coupled but must never collapse into one undifferentiated shared database table.

## 13. ClayCode fusion

The high-level scheduling and invariant path should be expressible in ClayCode so the HPU fabric is not a separate Python personality/runtime authority.

Candidate orchestration shape:

```text
pipeline_state_frame_open
-> hpu_jfield_project
-> hpu_workspace_capsule_compile
-> hpu_schedule_module
-> optional inference_generate
-> hpu_candidate_admit
-> hpu_reduce
-> hpu_gate
-> hpu_commit_generation
-> hpu_finalize_receipt
```

ClayCode owns ordering/invariants. Native/Python helpers may implement mmap, hashing, numeric routing or inference backends, but their outputs remain typed effects/results under the ClayCode contract.

The existing main pipeline already follows the important pattern:

```text
compile
-> build prompt
-> pre-inference cognitive fabric admission
-> inference
-> deterministic gate
-> canonical commit
-> post-turn UCF finalization
```

HPU should extend that ancestry rather than bypass it.

## 14. Relationship to model-local J-Space

Two layers must remain distinct:

```text
MODEL-LOCAL J-SPACE
    optional measured/transient model-local representation

SYSTEM GLOBAL J-FIELD
    explicit HPU/Mini Entity workspace and routing fabric
```

For a bundled local ~0.8B model, admitted local activation measurements may become **candidate routing signals**.

For Claude/external models, use `COMPILED_EXTERNAL`: only explicit prompt/output/context evidence is available unless a provider exposes a separately admitted observable. Never pretend external hidden states are visible.

A mapping between local and global J-Space is a measured projection, not identity.

## 15. Dynamic specialization

A logical module should not have a permanently hard-coded neighborhood.

Its active specialization can be represented as a small profile vector:

```text
role_prior
channel_affinity[]
recent_utility[]
causal_gain[]
uncertainty_reduction[]
compute_cost
refractory_state
```

This allows the HPU to reorganize itself:

- world modules temporarily bind to a resource crisis;
- critics attach where contradiction rises;
- simulation lanes fan out around uncertain futures;
- provenance attaches to evidence-heavy routes;
- unused routes decay;
- successful cross-quadrant paths remain warm but not canonical.

The result is a changing communication topology without pairwise negotiation.

## 16. Failure controls

Mandatory controls before any runtime claim:

- no long-lived SQLite readers used as the hot bus;
- WAL size/checkpoint health monitored;
- every hot frame bound to one canonical generation/hash;
- stale-frame candidate rejection;
- deterministic reducer replay equality;
- candidate-order permutation test;
- route-flapping/hysteresis test;
- echo/redundancy poison test;
- false cross-quadrant correlation test;
- recurrent runaway/spectral stability test;
- no-workspace bypass test;
- missing-channel/UNKNOWN test;
- crash/restart with no state fork;
- candidate ring loss must not fabricate canonical absence/presence;
- external model cannot gain local latent/J-Space privileges by provider/model name.

## 17. Experiments needed

The design remains a hypothesis until measured.

Highest-value experiments:

1. **Replay identity** — same frame + same candidate inputs + same rules produce identical next-state hash.
2. **Cross-quadrant intervention** — perturb one controlled state variable and test whether only causally connected quadrants respond more strongly than shuffled controls.
3. **Dynamic-route ablation** — fixed topology vs adaptive J-Field at equal compute budget.
4. **Workspace bottleneck** — selected workspace vs bypass/empty/shuffled controls.
5. **Latency** — SQLite-per-module baseline vs immutable shared frame + candidate ring.
6. **WAL safety** — sustained readers/writers with bounded WAL/checkpoint behavior.
7. **Stability** — increase recurrent gain until oscillation; verify guard detects/blocks unsafe regime.
8. **Capacity** — useful logical module count on the KVM4 profile without promoting unmeasured numbers.

## 18. Acceptance claim boundary

This document specifies a candidate architecture only.

It establishes **no** runtime performance, HCU capacity, J-Space causality, model capability, consciousness, emergent-world correctness or product acceptance claim.

The target is to turn the owner's concept into falsifiable mechanisms:

**one canonical state; many independent modules; one low-latency shared cognitive field; dynamic measured routing; deterministic state convergence.**
