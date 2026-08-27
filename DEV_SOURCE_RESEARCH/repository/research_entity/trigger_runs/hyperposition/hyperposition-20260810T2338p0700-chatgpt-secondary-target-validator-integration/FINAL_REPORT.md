# Hyperposition H7C — Target-Validator Integration / Promotion Rollback

Run ID: `hyperposition-20260810T2338p0700-chatgpt-secondary-target-validator-integration`  
Trigger: `hyperposition`  
Actor: `chatgpt-secondary` / OpenAI GPT-5.6 Sol  
Research entity: Clay temporary worker; not self.root/Frank  
Target: Frank v0.1 / `self.root` on accepted Hostinger Ubuntu VPS  
Status: `VALIDATOR_INTEGRATED_TARGET_VPS_RUN_REQUESTED_NO_RUNTIME_PROMOTION`  
Canonical scientific promotion: `NONE`

## 1. Current-state refresh

Current program remains the unified `FRANK_V0_1` program. `F-V01-05-GWT-HYPERPOSITION-TOPOLOGY` is the relevant work package.

At the start of this run, target `claycode/frank_hyperposition.clay` could represent unresolved alternatives and declarative higher-order reduction/lesion hooks, while `harness/frank_harness_runtime.py` exposed only `open-hyperposition` as an executable Hyperposition operation. There was no direct executable current-target collapse/lesion/reduction path.

Prior H6 evidence already separated causal-credit topology from exposure/selection/authority. Its synthetic credit experiment strongly favored receipt-gated credit over broadcast reward, but remained non-target evidence.

## 2. Fresh external evidence

Primary literature pushes in both directions and therefore supports an admission gate rather than a default hypergraph runtime:

1. Chiang et al., CLeaR 2026, establish information-theoretic correspondences between PID components and causal structure in Bayesian networks/hypergraphs. This supports higher-order informational signatures as a plausible diagnostic family, not as an automatic runtime primitive.
   - https://proceedings.mlr.press/v323/chiang26a.html

2. Bresler et al., COLT 2025, show that recovering a random hypergraph from its graph projection has exact/partial recovery thresholds. Pairwise projection can therefore lose higher-order identity.
   - https://proceedings.mlr.press/v291/bresler25a.html

3. Duta & Lio, ICML 2025 SPHINX, show that learned latent hypergraphs can improve downstream performance in evaluated tasks. This supports testing task-conditioned higher-order structure.
   - https://proceedings.mlr.press/v267/duta25a.html

4. Llabrés et al., 2026 preprint, show a general class of higher-order social-impact dynamics that can be exactly reduced to weighted pairwise dynamics, including state-dependent weights in nonlinear cases. This is direct counterevidence to native n-ary-by-default.
   - https://arxiv.org/abs/2601.05169

5. Lyu, Clark & Raviv, 2025 preprint, report fundamental inconsistencies for lattice-based multivariate PID beyond simple cases. PID/PEID-style synergy should therefore remain auxiliary evidence with null/bias controls, never the sole Hyperposition promotion criterion.
   - https://arxiv.org/abs/2508.05530

Combined conclusion: `observed higher-order relation != native higher-order runtime necessity` and `pairwise fit != semantic pairwise reducibility`.

## 3. Concurrent-worker fusion

A live refresh during this run discovered three highly relevant parallel results.

### H7 — two-stage reduction gate

`20309aee8bf52667ea93952f7244f0fffc7c692a`

H7 separates:

- lossless semantic reification, such as relation-node + role-labelled incidence edges;
- actual interaction/dynamical reduction to member-pairwise or bounded state-machine mechanisms.

It requires matched intervention/replay/workspace/outcome/resource/recovery evidence before claiming interaction reducibility.

### H7B — context-admissibility / anti-smuggling

`7828b70f989ff3e675ff90d684fe02eecc24ce2b`

H7B identifies a loophole: a nominal pairwise model can reproduce `x1*x2*x3` by using `x3` as context/gating state. Operational fit is perfect, but the n-ary dependency has merely moved into context. Therefore contextual/stateful reduction needs material-read provenance and must reject direct or derived reads from relation members when claiming lower-order semantic equivalence.

### HyperMath thin-net + H7B fusion

`da1fac98794464b07b6b8d3dce93d80ed18e3677` and `cdfe6067aaa40468de4e9500971e9e5628f7c235`

HyperMath proposes a multi-sorted, law-carrying algebraic fabric with content-addressed semantic handles and carrier-specific rewrite certificates. Its local synthetic POC measured 75.68% lower repeated annotation wire volume and a ~48,562x median speedup on a deliberately factorable synthetic enumeration problem. The result explicitly attributes these gains to conventional interning/factorization mechanisms until target traces show otherwise.

H7B then adds the missing law precondition: a `CONTEXT_GATE`, marginalization or factorization rewrite cannot claim lower-order semantic equivalence if member-derived dependency is merely renamed into context/hidden state.

## 4. Self-correction / negative result

Before the concurrent H7/H7B refresh became visible, this worker briefly changed target `claycode/frank_hyperposition.clay` to add candidate/admitted n-ary representation states and causal-credit fields (`ce4f4e5844f8440d036d8f1161dad2e2312a68ae`).

The concurrent evidence made that promotion premature because:

- H7/H7B are explicitly candidate validators, not promoted target semantics;
- static pairwise failure is not enough;
- real Frank matched traces have not yet discriminated contextual pairwise, state-machine and native n-ary runtime;
- adding first-class production types before that discriminator could create semantic/compiler complexity without benefit.

The target semantic change was therefore rolled back immediately in `25b4a296143a627a6417e426f0748640ab97ca8b` to the pre-run blob `db6dca7a5d72b95c57f5da7db4c559713d9d8cdc`.

This rollback is a material negative result:

> Synthetic irreducibility + literature support is sufficient to add a validator obligation, but insufficient to promote a new production Hyperposition runtime/language primitive.

## 5. Target-repository validator integration

The evidence-backed change retained in the target is test/validation only.

### Executable probe

Target commit `fb8baa2dc47705e3ce59d9ceb26943c2280a43ff` updates:

`harness/hyperposition_irreducibility_probe.py`

Synthetic controls:

1. pairwise-reducible control `y=x1*x2`;
2. triadic parity `y=x1*x2*x3` against static pairwise Walsh basis;
3. deliberate member-context smuggling: pairwise `x1*x2` gated by context `x3`;
4. direct and derived member-context provenance gates;
5. exogenous-context admissibility control;
6. causal-credit guards: exposure alone, unverified outcome and authority-minting all reject positive credit.

Local execution on this worker environment produced:

- pairwise control MSE: `0.0`;
- triadic static-pairwise MSE: `1.0`;
- triadic member-context operational MSE: `0.0`;
- member context admissible: `false`;
- derived member context admissible: `false`;
- exogenous context admissible: `true`.

Environment for this local check:

- Linux `6.18.35-x86_64-with-glibc2.41`;
- Python `3.13.5`;
- evidence class: local synthetic equivalence check only.

Interpretation: the test reproduces the exact H7B anti-smuggling failure class. It does NOT establish that any real Frank relation is irreducibly higher-order.

### CI integration

Commit `5aa8be94b5e6110001aa477b20b8b9353804a898` adds the probe to the ordinary central-state CI path.

### Accepted target-VPS lane

Commit `df7f9da4d9ba6e7b9e88552b93dd47a5b38235f7` adds a dedicated self-hosted `[self-hosted, Linux, X64]` workflow. Its execute job is repository-read-only with credential-free checkout and records source/blob identities, `/usr/bin/time -v` resource shadow and executor metadata. A separate writer persists a receipt only after verifying the transported hashes/result.

The workflow classifies any successful run as:

`REAL_SELF_HOSTED_ACCEPTED_TARGET_VPS_HYPERPOSITION_SYNTHETIC_VALIDATOR`

and explicitly records:

- canonical state not mutated;
- external effect not performed;
- real Frank trace not executed;
- promotion `VALIDATOR_ONLY`.

At report-write time, the persisted target receipt had not yet been observed in repository history; therefore target-VPS execution is `REQUESTED/PENDING_EVIDENCE`, not claimed PASS.

## 6. Fused architecture hypothesis

### H-HYP-7C — Adaptive irreducibility ladder

Use one semantic n-ary identity when the hypothesis itself is n-ary, but choose active/runtime representation only after the strongest admissible reduction competition:

1. exact semantic reification;
2. static member-pairwise reduction;
3. contextual pairwise reduction using only admissible exogenous/pre-existing context;
4. bounded explicit state-machine reduction with declared hidden state and material-read closure;
5. native higher-order interaction only if the prior candidates materially fail on matched semantic/interventional metrics and native form remains Pareto-acceptable on resource/recovery metrics.

Status: `SUPPORTED_AS_VALIDATOR_DESIGN; NOT_TARGET_VALIDATED`.

### H-HYP-7C-CREDIT — credit topology is orthogonal

Which representation is selected cannot determine which state receives learning credit. Positive credit requires verified outcome plus causal-use evidence; credit never mints effect authority.

Status: `SUPPORTED_BY_PRIOR_H6_SYNTHETIC_EVIDENCE + CURRENT_VALIDATOR_GUARD; NOT_TARGET_VALIDATED`.

## 7. Strongest counterhypotheses

### H0-A — ordinary structures are enough

Current ClayGraph role-bearing hyperrelation tables, ordinary relation-node lowering, material-read provenance and existing intervention receipts may already express all useful behavior. A named Hyperposition runtime abstraction may add no target value.

### H0-B — HyperMath is only a compiler/planner facade

HyperMath's gains may be fully explained by ordinary content-addressing, factorization, variable elimination, provenance circuits and query planning. If so, keep the algebra only as a compiler facade or reject it entirely.

### H0-C — real Frank does not need higher-order runtime

Real target episodes may be matched by admissible pairwise/state-machine competitors within tolerance at lower latency/memory/recovery cost. Native n-ary active runtime would then be unjustified even though semantic n-ary identity remains useful.

### H0-D — validator complexity costs more than it saves

Material-read closure, context-provenance checks and multi-arm reduction search may cost more than occasional false higher-order promotion on v0.1 workloads. Measure validation overhead explicitly.

## 8. Highest-information next target experiment

Use frozen real Frank v0.1 episodes with at least one >=3-member typed relation candidate and an observed GWT -> causal-use -> outcome -> re-entry chain.

Arms:

A. plain current ClayCode/UnifiedDB;
B. exact relation-node reification + static pairwise interaction;
C. contextual pairwise with admissible exogenous context;
D. member-context smuggling control;
E. bounded explicit state-machine competitor;
F. native higher-order candidate;
G. HyperMath law-carrying planner with H7B guard.

Matched:

- state/graph/GWT epochs;
- model/model output where possible;
- seeds/input/candidate order;
- effect policy;
- token/context/CPU/RAM budget;
- timeout/retry policy;
- replay snapshot.

Measure:

- semantic roundtrip error;
- material-read/dependency closure;
- prediction/outcome error;
- intervention-response mismatch;
- replay divergence;
- GWT selection/receiver-use/outcome/re-entry deltas;
- false semantic reduction;
- alternative retention/collapse accuracy;
- latency p50/p95/p99;
- CPU/RSS/context tokens/wire bytes;
- crash/restart/recovery;
- stale epoch rejection;
- effect-authority integrity.

Controls:

- member context withheld/shuffled;
- exogenous context shuffled;
- relation lesion/rescue;
- pairwise edge lesion;
- topology frozen while context changes;
- context frozen while topology changes;
- model output frozen while topology changes;
- no-reentry/shuffled-reentry where applicable.

Promotion rule:

> Native higher-order runtime or first-class HyperMath/Hyperposition language primitives remain unpromoted unless they beat the strongest admissible conventional reduction on target-relevant correctness/causal metrics and are Pareto-acceptable on cost/recovery.

## 9. Re-entry disposition

Material result: `TARGET_VALIDATOR_INTEGRATION + NEGATIVE_PROMOTION_RESULT + TARGET_VPS_EXECUTION_REQUEST`.

Durable target commits:

- `3a8f880f5a4ee59e813745b81ea38bf1dc35315b` — initial pairwise irreducibility probe;
- `5aa8be94b5e6110001aa477b20b8b9353804a898` — ordinary CI execution;
- `25b4a296143a627a6417e426f0748640ab97ca8b` — rollback premature production semantic promotion;
- `fb8baa2dc47705e3ce59d9ceb26943c2280a43ff` — H7B context-smuggling validator;
- `df7f9da4d9ba6e7b9e88552b93dd47a5b38235f7` — accepted target-VPS workflow.

No current canonical scientific revision change is justified. F-V01-05 should remain active/open until a real Frank target trace discriminator closes at least the relation-reduction/GWT causal-use path.
