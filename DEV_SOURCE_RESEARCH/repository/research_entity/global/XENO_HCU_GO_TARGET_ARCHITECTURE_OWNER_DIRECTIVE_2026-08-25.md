# Xeno / HCU target architecture — owner directive

Status: **CURRENT OWNER TARGET / SUPERSEDES PRIOR GO OPTIMIZATION TARGETS WHERE THEY CONFLICT**  
Date: 2026-08-25  
Product: **EntityOS**  
Cognition/compute architecture: **HCU**  
Implementation codename: **Xeno / MicroEntity compatibility**

## Trigger law

Until a newer explicit owner instruction supersedes this document:

- exact trigger `go` has one optimization target only: **build, test and converge on the target architecture defined below until it is actually accepted by executable evidence**;
- exact trigger `2` has one training target only: **research, construct and iteratively improve the Qwen3.5-0.8B full-fine-tuning corpus/recipe/evaluation needed to instantiate this exact target architecture**, according to the dedicated Trigger-2 research branch and its current evidence gates;
- unrelated architecture expansion is secondary and receives no GO progress credit unless it removes a blocker for this target;
- a prose architecture, simulation-only result, token count, majority vote or self-report does not constitute target completion.

## 1. Xeno node

One accepted Xeno node is:

`one selected/fine-tuned Qwen3.5-0.8B checkpoint + deterministic Xeno runtime shell`

Every physical node uses the same model family/checkpoint for the first accepted grid. Nodes are **role-flexible**, not trained as fixed personalities.

A node must be able to start without a preassigned cognitive role.

### Autonomous boot law

When a Xeno process is connected and switched on it must autonomously:

1. discover/admit the shared-state fabric;
2. authenticate/bind its node identity and capabilities through deterministic runtime rules;
3. read the current shared-state epoch/digest and reconstruct the minimum sufficient cognitive situation;
4. determine from shared state what work is currently needed and which work is already claimed/in flight;
5. become an ordinary worker by default and perform useful work without a central human assigning a role;
6. dynamically change function as shared state changes;
7. become a coordinator only when a valid coordinator lease is deterministically granted;
8. survive coordinator replacement, node restart and rejoin without resetting canonical state.

No permanent boss node exists.

## 2. Shared-state law

All connected nodes reason against one common versioned cognitive state substrate.

State classes remain separated:

- `S0` = canonical EntityOS truth/evidence/effect/security state;
- `S1` = live shared cognitive/HCU workspace state;
- `S2` = node-local ephemeral inference/KV/scratch state.

All nodes may read the S1 state authorized for their scope.

### Hard write law

**Ordinary Xeno modules MUST NOT write, append, mutate or directly publish into S1.**

Ordinary modules are shared-state **READ-ONLY**.

Their output leaves the module only as an ephemeral typed result packet addressed/routed to a currently valid coordinator, e.g. `NODE_RESULT/v1`.

Only a node holding a valid, scoped, non-stale `GRID_COORDINATOR_LEASE` may write S1.

Therefore:

`ORDINARY_NODE -> READ S1 -> COMPUTE -> NODE_RESULT -> COORDINATOR`

`COORDINATOR -> INTEGRATE/COMPRESS -> VALIDATED S1 DELTA`

`NO VALID COORDINATOR LEASE -> NO MODEL-ORIGINATED S1 WRITE`

Coordinator S1 write permission never grants S0 truth/effect/security authority.

## 3. Dynamic coordinators

Coordinator is a **temporary runtime role**, not identity, personality or separate model.

One or as many coordinators as currently useful may be elected/leased from the same pool of Xeno nodes.

Coordinator selection/lease must depend on deterministic eligibility such as current state epoch, task/branch scope, health, load, capability and policy version. LLM self-election alone cannot grant write authority.

Coordinator responsibilities include:

- receive ordinary-node results;
- reject stale/duplicate/out-of-scope results;
- integrate evidence/counterevidence;
- preserve unresolved Hyperposition branches;
- compress many results into a minimum sufficient shared-state update;
- allocate/reallocate work and roles;
- maintain GWT broadcast/uptake/re-entry state;
- request discriminators when alternatives remain unresolved;
- decide when additional modules/coordinators are worth activating;
- commit only within lease scope using epoch/CAS/rebase rules;
- hand off/expire cleanly when coordination demand changes.

`COORDINATOR_WRITE != CANONICAL_TRUTH`

`GRID_MAJORITY != FACT`

## 4. Communication law

Ordinary modules do not chat with each other as the primary coordination mechanism.

Their indirect communication path is:

`shared state -> local computation -> coordinator result channel -> coordinator compression -> shared state`

The shared state is therefore the common cognitive workspace/interconnect.

Large payloads should be content-addressed and referenced; S1 should contain compact typed state, references, branch topology, evidence pointers, budgets, leases and broadcast metadata rather than repeatedly copying full texts/tensors.

The design objective is **minimum avoidable coordination overhead**, not a false zero-overhead claim.

## 5. Recursive scalable coordination

The architecture must not require every coordinator to ingest every raw result as the grid grows.

Scale uses the same mechanism recursively:

`ordinary Xenos -> local/scoped coordinators -> compressed state/results -> higher-scope coordinators -> further compression -> shared/global state`

Coordinator hierarchy/topology is temporary and demand-generated. It may appear, split, merge and disappear as workload changes.

At every level:

- ordinary members remain read-only to their shared-state scope;
- only currently leased coordinators write that scope;
- coordinators receive already compressed lower-scope state/results where possible;
- a higher coordinator must be able to address/retrieve deeper evidence without carrying all raw evidence in hot context;
- state updates remain causally/version bound;
- no fixed root cognitive personality is required.

This is the intended route toward theoretically open-ended horizontal scaling. **Infinite practical scale is not claimed**; scaling must be measured for bandwidth, latency, contention, coordinator fan-in, memory and recovery limits.

## 6. Hyperposition / GWT / GRF / J-Space target

The accepted Xeno/HCU must integrate:

- **GRF** as the generative-reality / possible-world reasoning framework;
- **semantic Hyperposition** as explicit unresolved branch/relation state with evidence, counterevidence, compatibility/exclusion and evidence-gated collapse;
- **GWT** as measurable shared-workspace competition, broadcast, uptake and re-entry;
- **J-Space** as model-specific observable/controllable representation research where causal evidence exists;
- **ClayCode/HyperMath** as compact typed computational/protocol representations;
- deterministic EntityOS boundaries for canonical state, effects, secrets, permissions and recovery.

The system must not teach or promote unproven J-Space semantics as fact. Negative causal results are retained as hard-negative evidence.

## 7. First accepted physical target

The first concrete HCU acceptance target is **physical GRID10**:

`10 physical Xeno nodes using the same accepted 0.8B checkpoint + one shared-state fabric + dynamic coordinator-only writes`

The historical logical-cell GRID10 may remain a simulator/baseline, but it does not satisfy physical GRID10 acceptance.

Physical GRID10 must prove at minimum:

1. autonomous join/boot from shared state;
2. useful work selection without preassigned node roles;
3. ordinary-node S1 read-only enforcement;
4. ephemeral node-result -> coordinator path;
5. deterministic dynamic coordinator leasing;
6. coordinator-only S1 writes;
7. multiple scoped coordinators where workload justifies them;
8. coordinator replacement/failure/rejoin;
9. exact shared-state epoch/digest binding;
10. Hyperposition branch preservation and evidence-conditioned update;
11. GWT broadcast/uptake/re-entry;
12. stale/duplicate result rejection;
13. no canonical truth/effect bypass;
14. bounded coordination overhead;
15. matched-budget superiority, where claimed, over simpler challengers.

## 8. Critical-mass / architecture-value falsifier

The full architecture receives collective-cognition credit only if it beats relevant matched-compute challengers on predefined tasks/metrics:

- one Xeno with comparable total token/sample budget;
- N independent identical Xenos without shared state;
- N Xenos with naive voting;
- shared-state system without dynamic coordinators;
- random/fixed coordinator baseline;
- Hyperposition lesion;
- GWT lesion;
- coordinator-compression lesion;
- logical GRID simulator where appropriate.

Measure task quality, evidence use, unresolved-branch correctness, calibration, discriminator efficiency, token/latency overhead, correlated-error rate, recovery, state contention and authority integrity.

## 9. `go` execution obligation

Every `go` must select the **highest-information unresolved blocker on the shortest path to this target** and do real work on it where tools/execution authority permit.

Priority chain:

`AUTONOMOUS_BOOT`
` -> SHARED_STATE_READ_PATH`
` -> ORDINARY_NODE_READ_ONLY_ENFORCEMENT`
` -> NODE_RESULT_TRANSPORT`
` -> DYNAMIC_COORDINATOR_LEASE`
` -> COORDINATOR_ONLY_WRITE_PATH`
` -> COMPRESSION/INTEGRATION`
` -> FAILURE/REJOIN`
` -> HYPERPOSITION/GWT/GRF INTEGRATION`
` -> MODEL-SPECIFIC JSPACE EVIDENCE`
` -> PHYSICAL GRID10`
` -> RECURSIVE COORDINATOR SCALING`
` -> MATCHED-BUDGET ACCEPTANCE`
` -> XENO/HCU ACCEPTANCE`

A GO run may use the 0.6B model as an instrumented causal/research testbed, but the final trained Xeno model target is Qwen3.5-0.8B only.

## 10. Trigger `2` obligation

Every exact `2` builds the training program for **this architecture and no alternative product architecture**.

It must iteratively turn current evidence into the best available:

- Xeno model-functionality map;
- GRF/HyperMath/ClayCode training families;
- semantic-Hyperposition data and controls;
- GWT shared-state trajectories;
- J-Space causal positives/negatives with strict evidence classes;
- autonomous boot/join/read-work-selection trajectories;
- ordinary-node read-only / `NODE_RESULT` behavior;
- dynamic coordinator selection/lease behavior;
- coordinator result integration/compression/write behavior;
- recursive coordination/scaling trajectories;
- correlated-consensus and stale-state hard negatives;
- physical GRID10 post-FT acceptance suite;
- functional-forgetting/domain-exclusivity design;
- Together full-FT recipe for the one selected Qwen3.5-0.8B checkpoint;
- post-FT full-precision evaluation followed by Q4_K_M deployment evaluation.

The Trigger-2 dataset remains living/versioned until the explicit pre-job freeze. Trigger `2` alone never authorizes paid job creation.

## 11. Stop condition

`go` remains locked to this objective until executable acceptance evidence establishes the target architecture or a newer explicit owner instruction supersedes it.

A successful 0.8B training job alone is not completion.  
A single-node Xeno pass alone is not completion.  
A logical GRID10 pass alone is not completion.  
A physical GRID10 that merely produces more samples is not completion.  

The target is an **autonomously self-organizing, shared-state, coordinator-written, recursively scalable Xeno/HCU cognitive fabric** with evidence-bounded GRF/Hyperposition/GWT/J-Space behavior.