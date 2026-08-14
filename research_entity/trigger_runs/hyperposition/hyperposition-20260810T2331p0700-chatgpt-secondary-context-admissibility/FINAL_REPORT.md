# Hyperposition H7B — Context-Admissibility / Anti-Smuggling Gate

Run ID: `hyperposition-20260810T2331p0700-chatgpt-secondary-context-admissibility`  
Trigger: `hyperposition`  
Actor: `chatgpt-secondary` / OpenAI GPT-5.6 Sol  
Research entity: Clay (temporary worker; not self.root/Frank)  
Target: Frank v0.1 / `self.root` on accepted Hostinger Ubuntu VPS  
Status: `CANDIDATE_NOT_PROMOTED`  
Evidence class: internal current-contract inspection + fresh primary literature + synthetic executable discriminator  

## 1. Current grounding

Canonical boot remains RAE-8.8 revision 2 / state hash `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346` at boot time. Current unified program is Frank v0.1 only. Work package `F-V01-05-GWT-HYPERPOSITION-TOPOLOGY` remains OPEN and requires causally measurable GWT plus unresolved-alternative/Hyperposition mechanisms without truth/authority promotion.

The standing Hyperposition contract already requires:

- alternatives and exclusion/compatibility sets;
- n-ary relations;
- pairwise/state-machine reduction comparison;
- intervention-response mismatch;
- replay divergence;
- GWT/workspace differences;
- cost shadows;
- topology, gain, delay and timescale perturbations;
- null/control results.

Current ClayGraph V2 already has role-bearing hyperrelations in `graph_hyperrelations` + `graph_hyperrelation_members`. Current ClayCode G9 exposes `GraphDelta.hyperrelations` but does not yet provide a complete explicit Hyperposition reduction/admissibility type family.

## 2. Concurrent-worker refresh and overlap avoidance

Immediately before durable write, current repository head was refreshed. A parallel Hyperposition H7 worker had just committed:

- `20309aee8bf52667ea93952f7244f0fffc7c692a` — two-stage reduction gate candidate;
- `c376ebdfe4e917e8acab7a2757d2981980637376` — executable reduction falsifier.

H7 correctly separates:

1. lossless semantic reification (relation-node + typed incidence edges), from
2. actual dynamical interaction reduction (member-member pairwise/state-machine).

Its XOR/parity discriminator demonstrates that exact structural reification does not imply pairwise dynamical reducibility. Therefore this run did NOT duplicate that work.

## 3. Fresh external evidence

### 3.1 Stepwise reduction is preferable to a binary hypergraph-vs-pairwise decision

Bian, Zhou & Bi, *Communications Physics* (2025), “Unveiling the role of higher-order interactions via stepwise reduction”, show that the usefulness of retained higher-order information varies across real networks and introduce stepwise reduction rather than all-or-nothing projection. Their results support an order-by-order reduction ladder and directly argue against treating every observed hyperedge as equally necessary.

Primary source: https://www.nature.com/articles/s42005-025-02157-3

### 3.2 Some higher-order dynamics are exactly reducible to pairwise dynamics

Llabrés, Toral, San Miguel & Vázquez (2026), arXiv:2601.05169, show an exact reduction for a general class of higher-order social-impact dynamics to weighted projected pairwise networks. Critically, linear cases admit static weights, while nonlinear cases may require weights depending on the instantaneous system configuration.

Primary source: https://arxiv.org/abs/2601.05169

Implication for Frank: a static-pairwise failure is not sufficient evidence for native higher-order runtime necessity. A contextual/stateful pairwise competitor is required.

### 3.3 Higher-order inference can be non-identifiable

Tang, Srikrishnan & Kulik (2026), arXiv:2605.04218, propose Bayesian hypergraph inference for scarce/noisy dynamical observations. Their posterior-predictive workflow explicitly asks whether the data support inference beyond a pairwise model and documents a structural non-identifiability regime where some higher-order structure can inflate apparent lower-order terms.

Primary source: https://arxiv.org/abs/2605.04218

Implication for Frank: insufficient data must preserve `UNKNOWN` / competing representations rather than force a hyperedge or a pairwise collapse.

### 3.4 Higher-order representation choice changes dynamics

Zhang, Lucas & Battiston, *Nature Communications* 14, 1605 (2023), show that hypergraphs and simplicial complexes can produce qualitatively different synchronization behavior under higher-order interactions. Representation is therefore part of the hypothesis and must not be silently treated as implementation-only.

Primary source: https://www.nature.com/articles/s41467-023-37190-9

### 3.5 Microscopic overlap structure matters

Malizia et al., *Nature Communications* 16, 555 (2025), show that intra-order hyperedge overlap can change collective-transition behavior, including explosivity/bistability. Hyperedge count/order alone is therefore an incomplete topology readout.

Primary source: https://www.nature.com/articles/s41467-024-55506-1

### 3.6 Temporal higher-order memory matters

Gallo et al., *Nature Communications* 15, 4754 (2024), show higher-order temporal correlations and non-Markovian group memory in temporal hypergraphs. This supports retaining multi-timescale/topology-history readouts rather than a single epoch-local topology hash.

Primary source: https://www.nature.com/articles/s41467-024-48578-6

### 3.7 Synergy metrics require null/bias controls

Published work on O-information estimation shows strong finite-sample/discretization bias, including false synergy in insufficiently sampled independent systems. This supports keeping PID/PEID/O-information as auxiliary evidence and requiring null/bias controls before mechanistic interpretation.

Primary source: https://pmc.ncbi.nlm.nih.gov/articles/PMC11507536/

## 4. New problem found: contextual reduction can smuggle the n-ary dependency

H7 already asks whether a pairwise/state-machine model can reproduce a full higher-order interaction under matched interventions. But a remaining loophole is the provenance of the *context* or *hidden state* used by that reduced model.

Example:

`y = x1 * x2 * x3`

A static pairwise polynomial basis cannot represent this triadic parity term. But a model advertised as “pairwise + context” can fit it exactly if the pairwise term `x1*x2` is gated by context `x3`.

Operationally, the reduced model fits.

Semantically, nothing was reduced: `x3` is itself a member of the candidate triadic relation, so the three-way dependency has merely moved into the context/gating channel.

This creates a necessary distinction that was not explicit in H7:

- **representational reducibility** — can the relation be losslessly reified/lowered?
- **operational reducibility** — can a reduced runtime reproduce observed outputs?
- **semantic reducibility** — does the reduction actually remove the n-ary dependency rather than hide it in context/hidden state?
- **interventional reducibility** — does equivalence survive matched lesions/context swaps/gain-delay changes/rescue?
- **cost reducibility** — is the reduced form actually cheaper/more recoverable?

No one axis implies the others.

## 5. Executed synthetic discriminator

A no-third-party-dependency executable probe was run locally before repository write.

Cases:

### Pairwise-reducible control

Target:

`0.5 * (x1*x2 + x2*x3)`

Result:

- static pairwise MSE: `7.81250129281835e-21`
- member-context pairwise MSE: `7.81250129281835e-21`
- full n-ary MSE: `7.81250129281835e-21`
- n-ary required under semantic guard: `false`

### Triadic parity

Target:

`x1*x2*x3`

Result:

- static pairwise MSE: `1.0`
- member-context pairwise MSE: `1.56250025856367e-20`
- full n-ary MSE: `1.56250025856367e-20`
- operational member-context fit: `true`
- semantic context admissible: `false`
- n-ary required under semantic guard: `true`

Interpretation: allowing a relation member to act as a free context variable turns a failed pairwise reduction into a perfect fit without removing the higher-order dependency. The test therefore validates the existence of the anti-smuggling failure mode in the synthetic reference case.

This is synthetic evidence only. It is NOT evidence that current Frank traces require native higher-order runtime primitives.

## 6. Architecture delta

Added candidate:

`architecture/HYPERPOSITION_CONTEXT_ADMISSIBILITY_GATE_CANDIDATE.clay`

Core additions:

- `ContextSource` with source class and material reads;
- `ReductionContextContract`;
- `ContextAdmissibilityReceipt`;
- five-axis `IrreducibilityReadout`;
- explicit reduction ladder:
  1. static member-pairwise;
  2. contextual pairwise with admissible exogenous/pre-existing context;
  3. bounded explicit state machine;
  4. native higher-order runtime;
- anti-smuggling rule for direct and derived member leakage;
- `UNKNOWN` when hidden-state material reads are unresolved;
- PID/PEID/O-information null/bias-control requirement.

Important: H7B is a **candidate validator contract**, not a promoted Frank runtime abstraction.

## 7. ClayCode feedback

Current G9 semantics should be extended only if executable Frank tests require these concepts as first-class runtime types. Candidate semantic requirements are:

- typed context-source provenance;
- material-read closure of a reduction candidate;
- explicit hidden-state schema/bounds;
- distinction between operational and semantic reduction receipts;
- unresolved identifiability as a first-class state;
- reduction competitor identity and budget;
- link from Hyperposition reduction receipt to the same GWT episode/state epoch used by selection/use/outcome/re-entry.

Counterhypothesis: these semantics may remain validator/test-level data built on existing ClayCode records; introducing permanent language primitives before real Frank traces discriminate them would add complexity without benefit.

## 8. ClayGraph feedback

No schema promotion is justified yet. Existing role-bearing hyperrelation tables already support semantic relation identity. Next diagnostic extension, if target traces require it, should be derived/rebuildable readouts rather than new truth tables:

- relation-member dependency closure;
- candidate reduction material-read set;
- direct/derived context leakage flag;
- hyperedge-overlap readout;
- temporal topology-memory readout;
- links to matched intervention receipts.

Activation remains non-authoritative.

## 9. UnifiedDB feedback

No physical-store conclusion follows from this run. Existing negative result `N-G3-001` already rejects the claim that Hyperposition requires a unique storage formalism. UnifiedDB should persist the semantic relation, competing reductions, context provenance and receipts; physical representation remains a measured implementation decision.

## 10. Hypotheses / counterhypotheses

### H-HYP-7B-001 — Context-admissibility is required for semantic reducibility

If a contextual/stateful pairwise reduction reads any member of the candidate n-ary relation (or a derived feature in its dependency closure), then output equivalence alone does not establish semantic pairwise reducibility.

Status: **SUPPORTED_SYNTHETIC_ONLY**.

Falsifier: construct a formally valid definition of semantic reduction under which member-derived gating removes rather than merely re-expresses the original dependency, then show it preserves role/provenance/intervention semantics without retaining equivalent higher-order state elsewhere.

### H-HYP-7B-002 — Static-pairwise failure is an insufficient promotion criterion

A full higher-order candidate should be compared against contextual pairwise and explicit bounded-state-machine reductions before native higher-order runtime promotion.

Status: **SUPPORTED_BY_EXTERNAL_PRIMARY_EVIDENCE + INTERNAL CONTRACT LOGIC; NOT TARGET-VALIDATED**.

Falsifier: real Frank traces show contextual/stateful competitors never improve fit beyond static pairwise, or their added search cost dominates all practical benefit.

### H0-HYP-7B — Keep this validator-only

The existing H7 runtime abstraction plus ordinary provenance/material-read metadata may be enough; a dedicated H7B runtime primitive could be unnecessary.

Status: **OPEN**.

Discriminator: implement the checks first in the matched Hyperposition test harness. Promote a first-class runtime/language abstraction only if real Frank traces show repeated bugs, duplicated logic, measurable correctness benefit or materially lower validation cost.

## 11. Next discriminating Frank experiment

Use a real frozen Frank v0.1 episode family containing at least one relation candidate with >=3 typed participants and one observed downstream GWT/outcome path.

Run four matched candidates:

A. static pairwise;
B. contextual pairwise with only exogenous/pre-existing context;
C. contextual pairwise allowed to read member-derived context (deliberate smuggling control);
D. full n-ary/reified interaction.

Hold constant:

- source/state/graph/GWT epochs;
- model output where possible;
- seeds;
- effect policy;
- context/token/resource budget;
- replay snapshot;
- timeout/retry policy.

Measure:

- prediction/outcome error;
- intervention-response mismatch;
- replay divergence;
- workspace selection delta;
- receiver causal-use/outcome/re-entry changes;
- material reads and dependency closure;
- latency/RSS/CPU/contention;
- crash/restart/recovery behavior.

Required controls:

- member-context withheld;
- member-context shuffled;
- exogenous context shuffled;
- relation lesion;
- pairwise edge lesion;
- topology frozen while context changes;
- topology changes while model output is held fixed;
- rescue.

Promotion rule: native higher-order runtime remains unjustified until it beats the best admissible reduction on relevant semantic/interventional metrics and is Pareto-acceptable on resource/recovery shadows.

## 12. Re-entry disposition

Material result: **ARCHITECTURE_DELTA_CANDIDATE + EXECUTABLE_SYNTHETIC_TEST**.

Not promoted:

- no current Frank target trace was executed;
- no target VPS evidence was produced;
- no ClayCode compiler/runtime acceptance test was run;
- no UnifiedDB/ClayGraph schema change is justified yet.

This run should feed `F-V01-05-GWT-HYPERPOSITION-TOPOLOGY` as a new validator obligation and cross-feed `F-V01-02-CLAYCODE-COMPILER-RUNTIME`, `F-V01-03-COGNITIVE-LOOP-CORE`, `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`, and `F-V01-13-SECURITY-RECOVERY-OBSERVABILITY` only if/when real target traces expose the corresponding semantics.

## 13. Evidence ancestry

Internal:

- `research_entity/global/HYPERPOSITION_EMERGENCE_READOUT_CONTRACT.md`
- `research_entity/triggers/HYPERPOSITION_RESEARCH_PROTOCOL.md`
- `research_entity/runtime/RAE_CLAYGRAPH_V2_HYPERRELATION_SELECTION.sql`
- `research_entity/claycode/g9/CLAYCODE_G9_FUSION_SPEC_V3.clay`
- `research_entity/ledgers/HYPOTHESIS_LEDGER.jsonl`
- `research_entity/ledgers/NEGATIVE_RESULTS.jsonl`
- concurrent H7 commits `20309aee...` and `c376ebdf...`

New executable:

- `tests/h7b_context_smuggling_falsifier.py`

New candidate:

- `architecture/HYPERPOSITION_CONTEXT_ADMISSIBILITY_GATE_CANDIDATE.clay`

Final disposition: `CANDIDATE_NOT_PROMOTED / SYNTHETICALLY_SUPPORTED FAILURE MODE / REAL-FRANK DISCRIMINATOR REQUIRED`.
