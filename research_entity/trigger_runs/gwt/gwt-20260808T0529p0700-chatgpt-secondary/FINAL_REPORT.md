# GWT RESEARCH RUN — Dual Workspace, Causal Closure, Capacity and Re-entry

**run_id:** `gwt-20260808T0529p0700-chatgpt-secondary`  
**trigger:** `gwt`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**protocols:** `MASTER_RESEARCH_TRIGGER_PROTOCOL.md`, `GWT_RESEARCH_PROTOCOL.md`  
**boundary:** results below concern functional/mechanistic global-workspace properties. No phenomenal-consciousness claim is made or promoted. Synthetic experiments are not live-FRANK evidence.

## Executive synthesis

The strongest model after this run is a **two-timescale, dual-workspace architecture** rather than a single undifferentiated GWT stage.

1. **Intra-model latent workspace:** current mechanistic evidence from Gurnee et al. (Anthropic, 2026) identifies a sparse intermediate-layer `J-space` in language models. It is limited in capacity, preferentially broadcast through model weights, causally involved in flexible internal reasoning, and selectively bypassed by more automatic processing. The authors explicitly do **not** claim a full brain-like GWT implementation: standard transformers lack cleanly separated specialist modules and within-pass recurrent loops, and sharp competitive ignition remains only partially characterized.
2. **Inter-episode system workspace:** FRANK's stronger engineering contract remains a temporally linked episode: `candidate → compete → ignite/select → broadcast → reconstruct → effect → outcome → reenter`. The existing RAE sandbox validator rejects causal defects that simple stage-presence checks miss, but live FRANK validation is still absent.
3. **Bridge hypothesis:** if FRANK uses an LLM whose internals contain a J-space-like substrate, external GWT receipts and latent workspace states should be treated as two independent evidence channels. A strong GWT claim should require cross-predictive alignment and, where feasible, cross-lesion agreement. Neither channel alone establishes the other.

This yields the run's central architecture delta: **logical global availability should be separated from physical broadcast fanout**. A system can expose workspace content globally while physically multicasting it only to causally relevant audiences, requiring reconstruction/effect receipts. This preserves GWT's availability function while reducing overcoupling and noise amplification.

## Internal evidence grounding

### Causal episode contract

`H-G3-005` is presently `supported_sandbox_replication`: functional GWT episodes require identity/order/receipt links rather than merely observing stage labels. `E-G3-GWT-001` reports 9,000 structured causal mutants: a stage-presence baseline rejected only `0.1333333333`, whereas the causal validator rejected `1.0`; it also accepted all 2,500 valid episodes in that sandbox. Scope remains CC-RC1.1 sandbox, not live FRANK.

### Re-entry

`H-G3-003` is `supported_synthetic_replication`: truthful outcome→re-entry improved a nonstationary adaptive-coupling proxy over shuffled re-entry. `E-G3-CHK-002` reports truthful-minus-shuffled `+0.05138`, bootstrap 95% interval `[0.047828125, 0.05540625]`. The critical boundary from `N-G3-004` is retained: a re-entry flag alone gives no benefit when no useful causal information path can affect future decisions.

### Fixed coupling is already refuted as a universal rule

`N-G3-003` preserves a cross-simulation contradiction: a prior proxy preferred coupling `kappa=0.9`, while the independent G3 toy preferred `0.5`. Therefore this run treats coupling and workspace capacity as controlled variables, not constants.

### Active decisive experiment

`EXP-LIVE-GWT-LESION` remains the highest-information target: whether truthful causal re-entry alters future live FRANK state/behavior. It still lacks a live read-only/twin trace. The current synthetic result is not live proof.

## External research

### 1. Anthropic 2026: mechanistic latent workspace evidence

Primary source: Gurnee et al., **"Verbalizable Representations Form a Global Workspace in Language Models"**, Transformer Circuits Thread, published 2026-07-06; companion preprint arXiv:2607.15495 and open-source `anthropics/jacobian-lens` reference implementation.

Important observations:

- The J-space emerges in intermediate depth rather than being uniformly present across the network.
- Sparse occupancy reaches roughly 25 J-lens directions in the median case, yet the J-space explains less than 10% excess activation variance. Small representational volume therefore does not imply low causal leverage.
- Functional capacity depends on semantic structure. Unrelated list items show a much tighter effective capacity than coherent semantic families, suggesting that "workspace capacity" should not be measured only in raw tokens/bytes/items.
- Ambiguous concept mixtures become sharply selected around workspace onset and later become bimodal. This is ignition-like evidence, but the authors explicitly leave open whether it matches classic competitive ignition.
- Specialized attention heads preferentially broadcast J-space content; ablating those heads degrades J-space content more than matched random-head controls while changing top-1 next-token predictions much less often.
- Flexible/internal reasoning is selectively impaired by J-space interventions while automatic or well-practiced computation can bypass it.
- The reference implementation fits and applies Jacobian lenses to open-weight decoder transformers, with examples using Qwen; the released repo provides code and synthetic replication/evaluation prompts.

Critical limitation: transformer depth is not the same as an indefinitely recurrent temporal workspace. The paper notes that finite feedforward depth can emulate a bounded number of recurrent computation steps, while longer serial processing requires token output and re-ingestion. For FRANK this is a direct reason to keep **within-pass latent workspace** and **cross-decision re-entry** separate in instrumentation.

### 2. Shared Global Workspace in modular deep learning

Goyal et al., ICLR 2022 / arXiv:2103.01197, implement a bandwidth-limited shared workspace in which specialist modules compete for access. Their results motivate capacity limits as a mechanism supporting specialization, compositionality, and synchronization. This is useful architectural evidence that capacity restriction can be functional rather than merely a hardware constraint.

### 3. Global Latent Workspace roadmap

VanRullen & Kanai, Trends in Neurosciences 44(9), 2021, propose a Global Latent Workspace using unsupervised translation between multiple specialist latent spaces. This supports treating representation translation/reconstruction as a first-class workspace interface rather than assuming all modules consume one native representation.

### 4. Temporal Selection-Broadcast Cycle

Nakanishi et al., Frontiers in Robotics and AI, 2025, explicitly elevate selection+broadcast into a repeated cycle and hypothesize benefits for dynamic thinking, experience-based adaptation, and real-time adaptation. Evidence class is **Hypothesis and Theory**, not a direct empirical FRANK validation. It nevertheless independently motivates the RAE focus on re-entry and temporal closure rather than one-shot broadcast.

### 5. Current LLM-agent GWT proposals

Shang, arXiv:2604.08206 (2026), proposes an event-driven "Global Workspace Agents" architecture with a central broadcast hub, heterogeneous agents, intrinsic diversity regulation and dual memory. This is current architecture evidence, but it does not displace causal lesion requirements; event-driven central broadcast can still be observational plumbing unless downstream effects and re-entry are demonstrated.

## Fusion 1 → falsifiable hypothesis set

### H-GWT-RUN-001 — dual-channel workspace bottleneck
**Mechanism:** external FRANK receipt episodes and a latent model workspace share causal responsibility for the same flexible reasoning events when an LLM is the active cognitive substrate.  
**Expected:** aligned episodes predict each other above shuffled controls; lesioning either channel selectively impairs the same flexible task family; combined lesions show non-additive mediation.  
**Counter:** the channels are independent correlates or one is an epiphenomenal readout.  
**Falsifier:** compute-matched cross-lesions show no shared mediation.

### H-GWT-RUN-002 — re-entry specificity and delay horizon
**Mechanism:** truthful outcome information improves future selection only while temporally relevant.  
**Expected:** truthful > shuffled/removed; sufficiently delayed re-entry loses benefit.  
**Counter:** extra state/update compute, not information identity, creates the gain.  
**Falsifier:** shuffled or compute-matched arbitrary updates rescue equally.

### H-GWT-RUN-003 — selection margin predicts causal fragility
**Mechanism:** the score margin between winner and runner-up measures how easily a different candidate can occupy the workspace.  
**Expected:** small-margin episodes are more sensitive to counterfactual score perturbations and winner swaps.  
**Counter:** downstream routing dominates; winner margin has little causal value.  
**Falsifier:** margin fails to predict outcome changes under targeted perturbation.

### H-GWT-RUN-004 — reconstruction is an independently necessary stage
**Mechanism:** transport/broadcast receipt is insufficient; each audience must reconstruct a usable local representation before producing an effect.  
**Expected:** reconstruction lesions break selected downstream effects despite successful transport receipt.  
**Counter:** all consumers share an identical representation and reconstruction is bookkeeping.  
**Falsifier:** deleting/replacing reconstruction has no audience-specific effect.

### H-GWT-RUN-005 — semantic capacity has an interior optimum
**Mechanism:** too little capacity omits causally relevant specialists; too much capacity admits noise/weak specialists and reduces selective advantage.  
**Expected:** task utility is non-monotonic in independent workspace slots and shifts with semantic coherence/task regime.  
**Counter:** averaging or larger context monotonically improves performance.  
**Falsifier:** representative tasks show monotonic benefit after compute matching.

### H-GWT-RUN-006 — broadcast overcoupling
**Mechanism:** stronger/broader broadcast accelerates useful integration but also amplifies workspace corruption.  
**Expected:** clean performance may improve with coupling while perturbed performance has a lower interior optimum; perturbation propagation rises with coupling.  
**Counter:** broad broadcast is robust because downstream modules filter errors independently.  
**Falsifier:** injected corruption shows no coupling-dependent propagation or utility penalty.

### H-GWT-RUN-007 — low variance can have high causal leverage
**Mechanism:** a sparse workspace can mediate flexible behavior despite explaining little total representational variance.  
**Expected:** targeted low-variance workspace lesion changes task outcomes more than larger variance-matched non-workspace lesions.  
**Counter:** J-space-like readout merely tracks small verbalizable residue.  
**Falsifier:** variance-matched controls equal or exceed causal mediation.

### H-GWT-RUN-008 — ignition requires a nonlinear intervention signature
**Mechanism:** true ignition is more than winner selection; it should show a sharp transition and preferably hysteresis/threshold behavior under controlled competition.  
**Expected:** interpolating candidate support produces an abrupt winner transition and stable post-threshold broadcast.  
**Counter:** ordinary soft selection produces a smooth response.  
**Falsifier:** all transitions are smooth after noise/measurement correction.

### H-GWT-RUN-009 — automatic bypass is a required negative control
**Mechanism:** a limited flexible workspace should not be required for every routine transformation.  
**Expected:** targeted workspace lesions disproportionately hurt flexible recombination, deliberate multi-step reasoning, or novel coordination while sparing matched automatic tasks.  
**Counter:** FRANK's workspace is simply the mandatory message bus for all cognition.  
**Falsifier:** specific lesions degrade every task uniformly after controlling for generic disruption.

### H-GWT-RUN-010 — finite depth is not cross-decision re-entry
**Mechanism:** bounded within-pass serial depth and persistent inter-episode recurrence solve different control problems.  
**Expected:** tasks requiring outcome-dependent adaptation across decisions fail when inter-episode re-entry is removed even if within-pass depth is unchanged.  
**Counter:** context/recomputation fully substitutes for explicit re-entry.  
**Falsifier:** removal of event re-entry causes no adaptation loss with matched context.

### H-GWT-RUN-011 — dual observability reduces false positives
**Mechanism:** requiring agreement between event receipts and independent latent probes reduces false GWT attribution.  
**Expected:** combined evidence discriminates causal workspace events better than either channel alone.  
**Counter:** channels are redundant.  
**Falsifier:** combined cross-validation adds no predictive/causal information.

### H-GWT-RUN-012 — relational binding is missing from flat workspace readouts
**Mechanism:** a bag of active concepts is insufficient to represent roles/n-ary relations needed for causal trace binding.  
**Expected:** role-aware relation encoding improves reconstruction and intervention specificity over flat concept inventories.  
**Counter:** downstream context recovers all binding without explicit role structure.  
**Falsifier:** role-aware encoding adds cost without measurable semantic/intervention benefit.

## Empirical work: EXP-GWT-RUN-ADAPTIVE-001

### Goal

Test three protocol requirements in one new synthetic proxy: capacity competition, truthful-vs-shuffled/removed/delayed re-entry, and a broadcast/coupling noise shadow.

### Generator

A 10-module adaptive estimator operates in a nonstationary environment. Every 70 steps, the hidden reliability assignment changes: 3 modules become high-quality specialists, 3 medium, and 4 noisy. Modules maintain trust estimates learned from outcome feedback. At each step the top-`k` modules compete into a workspace; their candidates are combined, then broadcast back into local beliefs with coupling `beta`. Re-entry modes are `truthful`, `shuffled`, `removed`, or `delayed`. This is intentionally a synthetic causal proxy, not a neural or FRANK simulation.

### Capacity result

With truthful re-entry and `beta=0.8`, 30-seed means:

| k | MSE |
|---:|---:|
| 1 | 0.07062 |
| 2 | 0.04981 |
| 3 | **0.04323** |
| 5 | 0.04379 |
| 8 | 0.04958 |
| 10 | 0.05061 |

This proxy therefore has an **interior selective-capacity optimum** around `k=3–5`; maximal capacity is not optimal.

### Re-entry result

At fixed `k=3`, `beta=0.8`, 40-seed estimates:

- truthful mean MSE `0.04088`
- shuffled mean MSE `0.18101`
- removed mean MSE `0.17167`
- delayed mean MSE `0.04290`

Paired bootstrap differences, truthful minus alternative:

- vs shuffled: `-0.13523`, 95% CI `[-0.14129, -0.12871]`
- vs removed: `-0.13305`, 95% CI `[-0.14554, -0.12101]`
- vs delayed: `-0.00179`, 95% CI `[-0.00242, -0.00118]`

Interpretation: in this constructed nonstationary specialist regime, identity-correct feedback matters strongly; one-step delayed feedback is only slightly worse because specialist regimes persist for many steps. This supports a **delay-horizon** formulation rather than an absolute "any delay kills re-entry" claim.

### Overcoupling/noise result

A second sweep injected workspace corruption on 5% of steps. Clean MSE continued to improve as `beta` increased, but corruption propagation increased roughly monotonically. In 60 paired seeds under corruption, `beta=0.4` achieved mean MSE `0.68975`, while `beta=1.0` achieved `0.71186`; difference `-0.02211`, bootstrap 95% CI `[-0.02554, -0.01865]`.

This is a new synthetic **negative result against maximizing coupling**: the coupling setting that optimizes the clean proxy is not the one that minimizes loss under corruption. It directly motivates keeping a perturbation-amplification shadow next to any broadcast utility metric.

### Experiment boundaries

The task generator was deliberately constructed so specialist reliability changes and feedback can identify it. The results validate the discrimination logic and produce a counterexample to universal maximal coupling; they do not establish numerical optima for FRANK, transformers, or biological GWT.

## Fusion 2 — transformed model

### 1. Split workspace into `LATENT_WS` and `EVENT_WS`

`LATENT_WS` is an optional model-internal substrate (e.g. J-space-like). `EVENT_WS` is FRANK's system-level causal episode. The bridge is explicit:

`EVENT_WS.broadcast_id ↔ model_call_id ↔ latent_probe_window ↔ EVENT_WS.effect/outcome/reentry`

A bridge may be absent for non-LLM modules. Latent evidence never becomes execution authority.

### 2. Replace "broadcast everywhere" with logical availability + selective causal multicast

Every authorized audience can request the workspace payload, but physical delivery is targeted using expected causal relevance. Each delivery emits:

`audience_receipt → reconstruction_receipt → effect_receipt | no_effect_reason`.

This preserves auditability while allowing fanout control.

### 3. Define a vector `Causal Workspace Closure Certificate` (CWCC)

Do not collapse GWT into one scalar. For an episode record at least:

- competition set and winner margin;
- selection/ignition intervention response;
- logical availability and actual audience fanout;
- audience receipt and reconstruction success;
- effect mediation;
- outcome receipt;
- truthful-vs-shuffled/removed/delayed re-entry sensitivity;
- next-state causal influence;
- capacity/load coordinate;
- perturbation amplification / `R_delta` shadow;
- optional latent/event cross-channel concordance;
- task utility, compute, latency and recovery cost.

### 4. Treat capacity in causal/semantic units

Anthropic's J-space results show that coherent semantic families can occupy the readout differently from unrelated concepts. FRANK therefore should measure capacity in independent causal payloads/relations, not only token count or message count.

### 5. Make automatic bypass a design test

A system where every routine operation requires workspace ignition risks becoming a centralized bus with a GWT label. FRANK should maintain matched automatic-task controls to verify selectivity.

## Architecture delta for FRANK/GWT

Candidate interface:

`candidate_id, producer, payload_ref, score_vector, uncertainty, dependencies`

`competition_id, candidate_ids, winner_id, runner_up_id, margin, policy_version`

`ignition_id, transition_curve_ref, threshold/hysteresis_metrics`

`broadcast_id, logical_scope, audience_plan, fanout_budget, payload_hash`

`audience_receipt, audience_id, reconstruction_hash, reconstruction_status`

`effect_receipt, effect_id, causal_parent, authority_ref, effect_hash`

`outcome_receipt, outcome_id, effect_id, utility_vector, environment_delta`

`reentry_receipt, source_outcome_id, target_decision_id, delay, truth_binding_hash`

`cwcc, episode_id, causal_metrics_vector, cost_shadows, latent_bridge_refs`

The external capability/effect gateway remains authoritative. Workspace selection can propose or prioritize effects but cannot self-authorize them.

## New negative results / non-promotions

- **N-GWT-RUN-001:** maximal broadcast/coupling is not a safe universal objective. In the synthetic corruption proxy, clean-optimal high coupling amplified injected workspace errors and was worse under corruption than moderate coupling.
- **N-GWT-RUN-002:** stage presence remains insufficient; existing 9,000-mutant evidence already demonstrates this in sandbox scope.
- **N-GWT-RUN-003:** a J-space-like latent workspace is not equivalent to a complete recurrent system GWT. The primary 2026 source explicitly identifies architectural differences and unresolved selection/ignition questions.
- **N-GWT-RUN-004:** workspace activation, verbal report, ignition-like sharpness, broadcast reach, or re-entry presence alone is not sufficient for a strong causal GWT claim.
- **N-GWT-RUN-005:** no phenomenal-consciousness inference is licensed by this run.

## Highest-information next experiments

1. **EXP-LIVE-GWT-LESION:** obtain a synchronized read-only/twin FRANK trace; run truthful vs shuffled vs delayed vs removed re-entry with compute-matched controls; compare downstream state hashes, candidate ranking, effects and outcomes.
2. **Open-model dual-workspace cross-lesion:** on a pinned Qwen-class model, fit/use a J-space-like probe, align latent windows to FRANK event episodes, independently lesion latent content and event re-entry, then test mediation and interaction.
3. **Selection/ignition interpolation:** continuously perturb top-two candidate scores/payload mixtures and measure winner, broadcast, downstream effect and hysteresis; distinguish smooth arbitration from ignition-like commitment.
4. **Reconstruction lesion:** preserve broadcast transport but corrupt/remove audience reconstruction in one module at a time; require audience-specific causal effects.
5. **Capacity × semantic coherence sweep:** vary number of independent causal payloads separately from correlated/coherent payloads, with fixed compute; fit task-specific capacity curves.
6. **Broadcast-noise sweep on FRANK twin:** inject bounded payload corruption at controlled points and estimate utility vs perturbation amplification as fanout/coupling changes.
7. **Automatic bypass control:** compare flexible novel tasks against matched routine transformations under workspace lesions.

## Provider/tool execution boundary

The repository's quota-aware provider plan classes were `scholarly`, `current_web`, `implementation`, `executable`, and `model_experiment`. In this ChatGPT product runtime, the registered OpenAlex/arXiv/Tavily/Exa/HuggingFace adapter scripts were not directly exposed as invokable tools; adapter-specific routing attempts are therefore recorded as `CONNECTOR_BLOCKED`/runtime failures in the tool manifest, with native web/direct primary sources as fallback. The GitHub connector and local sandbox were actually executed. The repository records OpenAlex/arXiv/Tavily/Exa/HuggingFace as verified in other RAE runtimes; that historical verification is not misrepresented as an execution in this session. E2B remains credential-blocked in the current registry.

## Promotion decision

`canonical_promotion = NOT_PERFORMED`.

Reason: the new numerical results are synthetic proxies, and the decisive live-FRANK trace plus open-model dual-workspace cross-lesion remain unavailable. The durable delta is packetized as OPEN/METHOD/MEASURED-SYNTHETIC knowledge, not promoted into canonical live truth.

## Source references

- Gurnee, W. et al. (2026), *Verbalizable Representations Form a Global Workspace in Language Models*, Transformer Circuits Thread; arXiv:2607.15495.
- `https://github.com/anthropics/jacobian-lens` — official companion reference implementation.
- Goyal, A. et al. (2022), *Coordination Among Neural Modules Through a Shared Global Workspace*, ICLR 2022; arXiv:2103.01197.
- VanRullen, R. & Kanai, R. (2021), *Deep learning and the Global Workspace Theory*, Trends in Neurosciences 44(9):692–704, DOI 10.1016/j.tins.2021.04.005.
- Nakanishi, J. et al. (2025), *Hypothesis on the functional advantages of the selection-broadcast cycle structure*, Frontiers in Robotics and AI 12:1607190, DOI 10.3389/frobt.2025.1607190.
- Shang, W. (2026), *"Theater of Mind" for LLMs: A Cognitive Architecture Based on Global Workspace Theory*, arXiv:2604.08206.

## Decision trace

**Evidence used:** verified RAE r2 canonical state; G3 hypothesis/evidence/negative-result ledgers; active GWT experiment; G5 dual-workspace packet; 2026 Anthropic primary paper and code; earlier modular/global-latent workspace literature; 2025 selection-broadcast cycle theory; new local synthetic intervention results.  
**Alternatives considered:** one monolithic workspace; stage-presence validation; maximizing broadcast reach; treating transformer depth as full recurrence; treating latent workspace readout as sufficient GWT evidence.  
**Inference/test:** separate latent and event workspace channels; test capacity/re-entry/coupling in a nonstationary modular proxy; preserve corruption cost shadow.  
**Result:** dual-workspace causal closure remains the strongest candidate; selective capacity and truthful re-entry can be useful; maximal coupling fails under corruption in the proxy.  
**Uncertainty:** high live-transfer uncertainty; moderate mechanistic external support; exact FRANK optima unknown.  
**Next falsifier:** live/twin FRANK re-entry factorial and pinned open-model cross-lesion.
