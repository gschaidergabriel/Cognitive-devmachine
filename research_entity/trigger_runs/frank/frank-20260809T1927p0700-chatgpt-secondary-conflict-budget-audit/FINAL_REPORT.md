# FRANK Trigger Run — ActiveAssembly Conflict-Budget Audit + Whole-Mesh Re-Fusion

**run_id:** `frank-20260809T1927p0700-chatgpt-secondary-conflict-budget-audit`  
**trigger:** `frank`  
**actor:** `chatgpt-secondary` · OpenAI · GPT-5.6 Sol  
**identity:** Research Entity temporary worker; NOT Frank  
**canonical parent:** RAE-8.8 r2 · `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**program stage:** `BASE_CLAYCODE_RELEASE`  
**target host:** Andreas Ubuntu Linux developer system only  
**fixed final target:** `ONE_CLAY_BINARY + ONE_LOCAL_UNIFIEDDB + ONE_CLAY_NATIVE_4B`  
**scientific promotion:** `NONE`

## 1. Why this run is materially new

The immediately preceding FRANK cascade made `ActiveAssembly` executable as an H1 ordinary-code reference and demonstrated that ancestry/conflict-aware selection can preserve explicit counterevidence better than naive score-only selection in one constructed fixture. The current run did not repeat that positive result. It searched for a failure created by the same mechanism.

The new discriminator asks:

> Under a hard local-4B context budget, can unconditional "conflicting alternatives first" reservation itself starve higher-value non-conflict evidence as conflict cardinality grows?

This is important because the current H1 reference is explicitly bounded. A rule that preserves contradiction by consuming all available slots can satisfy conflict visibility while degrading the rest of the cognitive slice.

## 2. Current joined state

Canonical identity remains RAE-8.8 revision 2. The Research Entity remains separate from Frank. Frank v0.1 remains scoped to the Andreas Ubuntu developer system; Android/mobile/edge portability remains out of v0.1 scope.

ClayCode BASE remains `NOT_PASS` in the authoritative release workspace: WP-01 is formally PASS and WP-02..WP-14 remain OPEN there. Concurrent implementation is moving rapidly, including held-out corpus, runtime/effect and release-audit work, but package credit remains receipt-gated rather than inferred from commit names.

A new strict target receipt contract landed during this run. It explicitly requires the real `ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM`, all required BASE work-package receipts, all ten production application proofs, the real FRANK handoff, empty unresolved language counterexamples and preserved authority boundaries. Hosted CI/proxy receipts cannot satisfy that contract.

H-WP-02 remains claimed and unresolved at the target-host level. The current research decision is still to use the merged oracle ledger only as a differential/adjudication candidate until the three implementation lineages are run against one frozen corpus on Andreas' Ubuntu host. This run does not fake that unavailable target evidence.

## 3. Current FRANK causal spine

The strongest current H1 realization remains:

`instance ingress + percept + local state + peer/capability evidence`

`-> coherent Unified semantic state / event identity`

`-> dependency and epoch closure`

`-> transient topology + Hyperposition alternatives`

`-> bounded ActiveAssembly`

`-> GWT competition / broadcast / recurrence proposal`

`-> local Clay-native 4B + Needle/peer proposal surfaces`

`-> EffectIntent`

`-> fresh dependency/capability revalidation`

`-> opaque deterministic authority gateway`

`-> external effect`

`-> OutcomeReceipt`

`-> re-entry + causal credit + semantic delta`

The current research direction is still one organism with multiple semantic timescales, not a permanent service zoo. H1/H2 boundaries exist for measurement and differential testing; H3 may collapse them physically only if their semantics remain non-bypassable.

## 4. ActiveAssembly source re-read after concurrent changes

The current `research_entity/harness/reference/active_assembly.py` advanced during this run to `frank.active-assembly.v1.1` with source blob SHA `cc8e5c442dd25c467dc58d8870451c1e1661a9f6`.

The implementation now additionally:

- binds packet identity to the complete semantic/provenance payload;
- treats exact duplicate deliveries idempotently;
- fails closed on packet-ID/content collision;
- marks conflict-selected packets explicitly as `CONFLICT_VISIBILITY`;
- grants those packets zero independent replication credit;
- allows same-ancestry opposite propositions to bypass the ancestry-family cap when the total hard context budget permits.

This concurrent improvement is epistemically useful: `conflict visibility != independent replication` is now explicit. It does not remove the new failure. Conflict representatives are still selected before ordinary evidence and still consume the same hard total-item budget. If anything, permitting same-ancestry opposites to bypass the ancestry cap makes it even more important to test total conflict allocation pressure.

## 5. New executed counterexample

Artifact:

`EXPERIMENT_ACTIVE_ASSEMBLY_CONFLICT_BUDGET.py`

Receipt:

`EXPERIMENT_RECEIPT.json`

Evidence class: `SYNTHETIC`.

Environment: hosted Linux 6.18.35 x86_64, Python 3.13.5. This is not the Andreas target-host acceptance environment.

### Direct 8-slot starvation case

Constructed input:

- hard budget: 8 items;
- four explicit two-way conflicts = eight conflict representatives;
- three independent non-conflict packets with deliberately much higher packet scores.

Current conflict-first result:

`c0a, c1a, c2a, c3a, c0b, c1b, c2b, c3b`

Critical high-score packets retained: `0/3`.

Therefore the current scheduler has a deterministic counterexample in which conflict visibility consumes the complete active budget and ordinary high-value evidence receives no slot.

This counterexample is structural. It does not depend on model quality, stochastic decoding or a particular Qwen checkpoint.

## 6. 10,000-trial synthetic tradeoff sweep

A deterministic seed `20260809` generated 10,000 authored trials with 0..7 conflict groups, three deliberately high-score packets labeled `critical`, and unrelated distractors.

Two arms were compared:

1. current unconditional conflict-first selection;
2. a deliberately simple discriminator arm limiting the initial conflict reservation to four of eight slots.

Observed aggregate results:

### Current conflict-first

- critical-packet recall: `0.4666`;
- all-three-critical retention rate: `0.3840`;
- complete conflict-pair retention per generated conflict claim: `0.690273`.

### Fixed four-slot conflict discriminator

- critical-packet recall: `1.0000`;
- all-three-critical retention rate: `1.0000`;
- complete conflict-pair retention per generated conflict claim: `0.358031`.

### Correct interpretation

This is **not evidence that 50% conflict reservation is optimal**. The generator explicitly labels and scores three packets as task-critical, so the fixed-cap arm has an authored objective advantage. The experiment is deliberately adversarial toward the current policy.

What it does establish is narrower and useful:

`conflict visibility` and `general high-value evidence retention` compete for the same bounded resource.

The current H1 policy contains an implicit absolute scheduling decision that had not yet been stress-tested against conflict-cardinality saturation. A production policy cannot be selected from the current positive conflict-retention fixture alone.

## 7. Cross-domain pattern fusion

### ClayGraph / stability-plasticity

The recent Reversal-Aware Binding run found a genuine stability/plasticity frontier: provenance-diverse slow-promotion gates sharply reduced false reversal under correlated source echo but increasingly slowed true reversal as the diversity threshold tightened. It also found that simple context identity, not richer machinery, explained most of the context-bifurcation benefit.

Transfer to ActiveAssembly:

- strong preservation constraints can remove one failure mode while creating another;
- conflict/ancestry semantics should be measured as a Pareto tradeoff, not treated as free safety;
- richer state/policy must beat simpler baselines at matched cost.

### GWT / adaptive resource allocation

The current GWT recurrence research similarly rejects one-signal control: low state delta alone is not convergence, and even residual pressure can fail if noisy/stale. The candidate controller therefore combines pressure, trend/marginal utility, cost, instability and budget rather than letting one variable act as the halt oracle.

Transfer to ActiveAssembly:

`conflict exists` should not automatically mean `conflict consumes every remaining active slot`.

Conflict identity can be an input to a bounded scheduling decision without becoming the decision itself.

### Hyperposition

Hyperposition's set-valued/alternative semantics suggest a second mechanism family: contradiction awareness might be preserved in a grouped or latent alternative representation, with selective re-expansion, instead of always materializing every alternative as a separate local-4B packet. This remains OPEN and must preserve provenance and explicit uncertainty.

### UnifiedDB

UnifiedDB should preserve conflict-group identity, ancestry/provenance, version/epoch and re-expansion identity independently of which alternatives enter the current Assembly. Selection is not truth-state mutation. That separation is necessary for replaying different policies against the same underlying semantic state.

### Emergenz

Selection policy changes which evidence becomes causally exposed downstream. Therefore it is itself an intervention/confound in GWT/emergence experiments. No emergence claim can treat one ActiveAssembly policy as neutral without control arms.

### ClayCode

No new core ClayCode syntax is justified. Existing semantics should first represent policy identity, budgets, conflict groups, selection roles and receipts. The project rule remains `less change, more compile`.

## 8. External research fusion

External evidence is used as mechanism context, not FRANK validation.

- `DeepLoop: Depth Scaling for Looped Transformers` (arXiv:2607.13491) reports that repeated parameter visits change the stability/scaling problem. This supports the project's broader rule that recurrence depth is not a monotonic free benefit and must be measured under repeated-visit dynamics.
- `Adaptive Depth in Looped Transformers: Diagnosing Learned Halting Gates and Trajectory Readouts` (arXiv:2607.20519) separates trajectory formation from exit readout and finds that simple post-hoc readouts on fixed-prior trajectories can be competitive. Transfer: FRANK must keep fixed/event-driven/frozen-trajectory baselines when evaluating adaptive loop control.
- `DF-RAG` (arXiv:2601.17212) and `Vendi-RAG` (arXiv:2502.11228) provide external evidence that bounded retrieval can benefit from explicitly trading relevance against diversity rather than maximizing one criterion. Transfer: ActiveAssembly should test a relevance/conflict/diversity frontier, not assume either pure score or pure conflict reservation is globally optimal.
- The official Qwen repository currently exposes `Qwen3.5-4B` as a 4B-class multimodal candidate. It remains a benchmark candidate only; Frank's local 4B must be selected by measured Andreas-Ubuntu quality/latency/memory/backend behavior rather than model recency.

None of these sources proves ActiveAssembly, GWT, recurrence, Hyperposition or Qwen3.5-4B is the correct FRANK mechanism.

## 9. Hypothesis generation after second fusion

Full matrix: `HYPOTHESES.json`.

### H-FRANK-AA-CB-01 — Conflict-first starvation

Unconditional conflict-first reservation can degrade useful evidence retention when contradiction cardinality approaches the hard active-context budget.

Counterhypothesis: explicit contradiction visibility is sufficiently valuable that current policy still wins on downstream verified outcomes.

Required falsifier: frozen/live H1 matched-policy traces.

### H-FRANK-AA-CB-02 — Policy identity should be explicit

Conflict allocation should be a typed/replayable policy rather than an invisible absolute pre-pass.

Counterhypothesis: parameterizing the policy only adds complexity/Goodhart surface; deterministic fixed conflict-first is sufficient.

### H-FRANK-AA-CB-03 — Claim-group compression

Grouped/latent alternatives plus selective re-expansion may preserve contradiction awareness with fewer active slots.

Counterhypothesis: grouping hides provenance/detail and harms local-4B correction.

### H-FRANK-AA-CB-04 — Adaptive allocation

The best allocation may vary by episode based on conflict severity, uncertainty, expected utility, re-expansion cost and remaining budget.

Counterhypothesis: adaptive scheduling overhead/calibration failure erases benefit; a simple fixed quota or ordinary diversified retrieval wins.

No hypothesis is promoted.

## 10. Architecture-to-Harness gap matrix after this run

### P0 — H-WP-02 target-host ledger convergence

Unchanged highest-risk semantic dependency. Run all three state-ledger lineages on the actual Andreas Ubuntu host before downstream consumers crystallize around incompatible root/epoch/idempotency semantics.

### P1 — ClayCode BASE target receipts

The strict Andreas-Ubuntu receipt contract now makes the acceptance boundary more explicit. Hosted proxy progress remains useful but cannot close BASE. WP-02..WP-14 remain OPEN in the authoritative workspace read.

### P2 — ActiveAssembly matched H1 policy benchmark

Expanded by this run. Compare:

- current conflict-first;
- broad retrieval/cache;
- relevance-only top-k;
- diversity-aware/MMR-like retrieval;
- fixed conflict reservation;
- claim-group compression + re-expansion;
- adaptive utility-aware conflict allocation.

Sweep conflict density, ancestry duplication and total context budget.

Primary outcomes:

- verified task outcome;
- explicit contradiction recall;
- false certainty;
- critical-evidence recall;
- provenance/ancestry fidelity;
- correction time;
- re-expansion success;
- downstream GWT/4B causal use;
- token/KV cost;
- selection latency;
- state/update amplification.

Durable work item created: `WORK-FRANK-AA-CONFLICT-BUDGET-001`, blocked until frozen H1 traces and stable ledger identities are available.

### P3 — executable end-to-end Golden Trace spine

Integrate already-created H1 slices into one trace:

`state/snapshot -> ActiveAssembly -> GWT/model proposal -> EffectIntent -> fresh commit revalidation -> opaque authority -> outcome -> re-entry`.

Include stale/relevant/unrelated changes, ABA, dependency laundering, conflict-saturated Assembly, capability epoch changes and crash/restart.

### P4 — recurrence controller discrimination

Keep fixed-budget, event-driven and fixed-trajectory/post-hoc readout arms. GWT focus or residual pressure alone must not become the controller oracle.

### P5 — Needle / capability / model / Retina target measurements

Continue only with exact receipt parity, fail-closed authority, target runtime/model/tokenizer evidence and explicit proxy-vs-target separation.

## 11. Negative results and non-claims

Preserved explicitly:

- no Andreas target-host execution occurred in this run;
- no H1 release PASS;
- no BASE package promotion;
- no local 4B winner selected;
- no 50% conflict quota selected;
- no proof that adaptive conflict scheduling is superior;
- no proof that ActiveAssembly beats ordinary retrieval/cache;
- no proof that recurrence or GWT improves live Frank;
- no emergence/consciousness inference;
- no model/peer/Assembly/Needle/visual state receives execution authority;
- a concurrent GitHub 409 write conflict was observed and handled by refreshing repository state before retry; no failed write was counted as durable work.

## 12. Durable delta written by this run

Created:

- `EXPERIMENT_ACTIVE_ASSEMBLY_CONFLICT_BUDGET.py`
- `EXPERIMENT_RECEIPT.json`
- `HYPOTHESES.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- work event `WORK-FRANK-AA-CONFLICT-BUDGET-001`
- this `FINAL_REPORT.md`

Research fidelity: `IMPROVED` because an untested failure mode of an executable H1 mechanism is now explicit, reproducible and routed back to the mesh.

Architecture semantics: `NO POLICY PROMOTION`.

Canonical scientific generation: unchanged at r2.

## 13. Final synthesis

The strongest new result is not a replacement scheduler. It is a new required invariant for FRANK's bounded cognition:

> **Preserving contradiction must not silently consume the entire active cognitive budget without a measured downstream justification.**

The current ActiveAssembly correctly separates conflict visibility from independent replication credit and preserves hard total boundedness. The new counterexample shows that this is still insufficient to establish a good scheduler. The next policy must be selected on real/frozen H1 episodes where contradiction recall, task utility, correction behavior, provenance and compute cost can all be measured together.

This leaves the broader FRANK architecture direction intact while making one of its newest executable components more falsifiable.
