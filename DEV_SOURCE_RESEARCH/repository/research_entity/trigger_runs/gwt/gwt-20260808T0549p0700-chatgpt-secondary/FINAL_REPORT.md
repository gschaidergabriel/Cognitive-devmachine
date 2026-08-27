# GWT RESEARCH RUN — Causal Freshness, Selective Broadcast and Cross-Lesion Identifiability

**run_id:** `gwt-20260808T0549p0700-chatgpt-secondary`  
**trigger:** `gwt`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**boundary:** functional/mechanistic GWT research only. No phenomenal-consciousness claim. New numeric results are synthetic proxies, not live-FRANK evidence.

## Executive synthesis

This run extends the previous dual-workspace result (`LATENT_WS ↔ EVENT_WS`) with two control mechanisms that make the architecture more falsifiable and more implementable.

1. **Logical global availability should be separated from physical push fanout.** The workspace payload can remain globally addressable while a causal router pushes only to predicted relevant audiences. Unpushed modules can recover access through a query/pull path. This creates an empirical tradeoff among causal audience recall, false delivery, communication cost, latency and perturbation amplification instead of treating full all-to-all broadcast as definitionally required.
2. **Re-entry requires causal freshness rather than a fixed age rule.** A re-entry payload should be accepted according to whether it still predicts the current regime/state when consumed. The cross-domain Age-of-Information-at-Query literature independently supports measuring freshness at use time in pull-based systems. Synthetic AR(1) tests show that the useful re-entry delay horizon scales strongly with environmental persistence.

The architecture candidate is therefore now:

`candidate → competition → selection/ignition → logical workspace register → causal push router ↔ query/pull rescue → audience reconstruction → effect → outcome → freshness-gated re-entry`

with an optional `LATENT_WS` probe/intervention plane linked to `EVENT_WS` only by measured alignment and cross-lesion evidence.

## Canonical/internal grounding

The canonical state remained RAE-8.8 r2 during this run. Existing high-value GWT evidence retained:

- `E-G3-GWT-001`: in CC-RC1.1 sandbox, the causal episode validator rejected 100% of 9,000 structured causal mutants while stage-presence validation rejected only 13.33%; 2,500 valid episodes were accepted. Boundary: sandbox only.
- `E-G3-CHK-002`: truthful re-entry beat shuffled re-entry in a nonstationary synthetic proxy; live transfer remains open.
- `EXP-GWT-RUN-ADAPTIVE-001`: selective capacity had an interior optimum and maximal coupling amplified injected corruption in the previous GWT run.
- `EXP-LIVE-GWT-LESION`: still blocked on synchronized live/read-only or twin FRANK traces. The active experiment ledger continues to state `live FRANK trace unavailable`.

## External evidence

### Gurnee et al. 2026 — model-internal workspace
Primary mechanistic source: *Verbalizable Representations Form a Global Workspace in Language Models*, arXiv:2607.15495 / Transformer Circuits. J-space is an intermediate-layer, limited-capacity, broadly readable/writable representational subspace with causal involvement in flexible reasoning. The authors explicitly do not claim the full recurrent GWT architecture of specialized processors competing for and receiving recurrent broadcast. This continues to justify separating `LATENT_WS` from FRANK's temporally recurrent `EVENT_WS`.

### Goyal et al. — bandwidth-limited shared workspace
*Coordination Among Neural Modules Through a Shared Global Workspace*, ICLR 2022 / arXiv:2103.01197, shows that specialist competition for a bandwidth-limited shared workspace can support specialization, compositionality and synchronization. Capacity limits can therefore be functional rather than only resource constraints.

### VanRullen & Kanai — translation/reconstruction
*Deep learning and the Global Workspace Theory*, Trends in Neurosciences 2021, proposes an amodal Global Latent Workspace built through translation among specialized latent spaces. For FRANK this strengthens the decision to make audience reconstruction independently observable instead of assuming transport implies semantic receipt.

### Nakanishi et al. 2025 — temporal cycle
The Selection-Broadcast Cycle paper explicitly introduces temporal recurrence to GWT-inspired AI architectures and motivates dynamic, experience-based and real-time adaptation. Evidence class is Hypothesis and Theory, not target validation.

### Age of Information at Query — cross-domain transfer
Holm et al. (arXiv:2011.00917) and Chiariotti et al. (arXiv:2105.06845) formalize freshness in pull-based communication where information age matters at query/use time. This does not prove a GWT mechanism, but it provides an independent control-theory/communications analogue for a workspace in which logical availability is persistent while physical delivery is demand-sensitive.

### Sparse routing implementation analogues
Current sparse attention/MoE work supplies implementation evidence that content-dependent routing can reduce physical computation/communication without necessarily making information semantically inaccessible. These are engineering analogues, not GWT evidence.

### Practitioner evidence boundary
Reddit discussion around the 2026 J-space paper frequently jumps from functional workspace evidence to claims of consciousness/access consciousness. This is preserved only as community-reaction evidence and as a Goodhart/interpretation warning. It is not scientific support for consciousness.

## Experiment 1 — EXP-GWT-MULTICAST-002

### Question
Can logical global availability plus selective push and pull rescue approximate full broadcast while materially reducing physical fanout and irrelevant activation?

### Synthetic design
- 20 audiences per episode.
- 5 are causally relevant.
- Causal router scores all audiences and pushes to top 5.
- Router quality is varied by Gaussian score separation; reported as pairwise relevance AUC.
- Relevant audiences omitted by push can query/pull with configurable sensitivity.
- Unselected irrelevant audiences have 2% false-positive pull probability.
- Full broadcast baseline physically delivers to all 20 and therefore covers all 5 relevant and all 15 irrelevant audiences.
- Main evaluation uses 30 independent seeds × 5,000 episodes per seed.

### Key result
At router `AUC = 0.92135` and pull sensitivity `0.95`:
- relevant-audience coverage: **0.98734 ± 0.00089 SD**;
- physical delivery reduction vs full broadcast: **0.67641 ± 0.00067**;
- irrelevant-delivery reduction vs full broadcast: **0.89766 ± 0.00091**.

At the same router quality, raising pull sensitivity from 0.90 to 0.98 moved relevant coverage from approximately 0.9746 to 0.9949 while communication reduction remained approximately 0.68 to 0.67.

### Interpretation
The constructed system demonstrates that `global availability` and `all-to-all physical push` are separable engineering properties. It does **not** establish functional equivalence to full broadcast: imperfect pull still misses causal audiences. The target experiment must therefore treat missed-causal-audience rate as a first-class safety/utility metric and allow full-broadcast fallback when router/rescue confidence is insufficient.

## Experiment 2 — EXP-GWT-FRESHNESS-003

### Question
Does truthful re-entry have a task-dependent delay horizon governed by environmental persistence?

### Synthetic design
- latent scalar environment follows stationary AR(1): `theta_t = rho*theta_(t-1) + innovation`;
- current observation is noisy (`sigma=0.45`);
- truthful re-entry is a lower-noise past observation (`sigma=0.20`) combined with fixed weight 0.35;
- compare truthful delayed re-entry to removed re-entry and shuffled controls;
- sweep `rho ∈ {0.6,0.8,0.9,0.95,0.98}` and delays; representative boundary comparisons use 120 paired seeds with bootstrap confidence intervals.

### Result
Last tested delay at which truthful re-entry still improved MSE over removed re-entry:

| rho | process correlation half-life | last useful delay |
|---:|---:|---:|
| 0.60 | 1.36 | 1 |
| 0.80 | 3.11 | 2 |
| 0.90 | 6.58 | 5 |
| 0.95 | 13.51 | 11 |
| 0.98 | 34.31 | 29 |

Across these constructed regimes, crossover delay was approximately linear in correlation half-life (`R² ≈ 0.9997`; fit is descriptive only).

Representative paired bootstrap effects, positive meaning truthful re-entry beats removed:
- `rho=.60, delay=1`: +0.01410, 95% CI [0.01330, 0.01483]; delay=2 becomes harmful: −0.04467 [−0.04566, −0.04370].
- `rho=.90, delay=4`: +0.02786 [0.02707, 0.02864]; delay=8: −0.02729 [−0.02873, −0.02590].
- `rho=.95, delay=8`: +0.02962 [0.02866, 0.03056]; delay=16: −0.02493 [−0.02670, −0.02315].
- `rho=.98, delay=16`: +0.04441 [0.04342, 0.04540]; delay=32: −0.00488 [−0.00676, −0.00286].

### Interpretation
A fixed global re-entry TTL is not supported even in this simple proxy. Useful age depends on the dynamics of the information source. The FRANK analogue should measure **causal freshness at use time**, combining age with regime/state compatibility and predictive value.

## Fusion 2 — transformed architecture hypotheses

### H-GWT-R2-001 — logical availability without all-to-all push
A shared addressable workspace plus selective causal push and query/pull rescue can preserve task-relevant global availability at lower physical fanout than full push. Falsifier: target replay shows materially worse causal audience coverage/outcomes after equal latency/retry budgets.

### H-GWT-R2-002 — router/rescue confidence controls broadcast mode
Selective broadcast is safe/useful only above task-specific causal-recall and rescue thresholds; below them the controller should widen fanout or fall back to full broadcast. Falsifier: fixed full broadcast or fixed sparse routing dominates across regimes.

### H-GWT-R2-003 — re-entry has predictive TTL
The usefulness of re-entry decays with loss of predictive relevance rather than wall-clock age alone. Falsifier: after matching compute and payload quality, delay remains unrelated to environmental/state persistence.

### H-GWT-R2-004 — causal freshness at query
Workspace/re-entry freshness should be evaluated when an audience actually consumes the payload, using age plus source-state compatibility and causal value. Falsifier: ordinary global age alone predicts utility equally well across pull/query regimes.

### H-GWT-R2-005 — cross-lesion signatures identify dual-workspace topology
A 2×2 `LATENT_WS lesion × EVENT_WS lesion` factorial can distinguish candidate relationships: serial mediation predicts occlusion/subadditivity; redundant parallel channels predict a large double-lesion interaction; an epiphenomenal channel predicts little/no unique lesion effect. Falsifier: signatures are non-identifiable under target noise even with paired replay.

### H-GWT-R2-006 — state-bound re-entry prevents stale causal injection
Binding re-entry to `source_state_hash`, `validity_epoch`, episode identity and measured age should reduce stale feedback errors during regime changes. Falsifier: guard ablation has no effect on stale-apply rate or outcomes.

### H-GWT-R2-007 — capacity and fanout should be co-controlled
Workspace payload capacity and broadcast fanout are coupled resource/noise controls. Falsifier: independently optimizing them matches joint control across target regimes.

## Cross-lesion identifiability matrix

Expected qualitative signatures for paired, compute-matched interventions:

| Candidate relation | LATENT lesion | EVENT lesion | Double lesion |
|---|---|---|---|
| serial LATENT→EVENT | large | large | ≈ stronger single lesion |
| redundant parallel | small/moderate | small/moderate | much larger |
| additive parallel | measurable | measurable | approximately additive |
| latent epiphenomenal | ~null | large | ≈ EVENT lesion |
| event epiphenomenal | large | ~null | ≈ LATENT lesion |

This matrix is a preregistration aid, not evidence about which topology FRANK currently has.

## Architecture delta

Add to `EVENT_WS`:

1. **Workspace Register** — immutable payload/hash + logical addressability.
2. **Causal Router** — predicts audiences needing immediate push and records routing confidence.
3. **Pull Rescue** — unpushed audience may request current workspace payload when local causal need emerges.
4. **Reconstruction Receipt** — proves semantic reconstruction separately from transport.
5. **Causal Freshness Gate** for re-entry — fields: episode id, source state hash, outcome hash, generated-at/age, validity epoch/regime tag, predictive-relevance estimate, stale/reject reason.
6. **Adaptive broadcast fallback** — widen fanout or full-push when causal recall/rescue confidence is below threshold or effect class is safety-critical.

Extend CWCC with:
- causal audience recall;
- false/irrelevant delivery rate;
- pull-rescue count and rescue latency;
- missed-causal-audience rate;
- re-entry age at query;
- stale-apply/reject rate;
- predictive freshness / value-at-use;
- physical fanout and perturbation amplification.

## Negative results / non-promotions

- Full all-to-all physical broadcast is **not proven necessary** by the function of global availability; a synthetic counterexample preserves near-complete causal coverage with much lower fanout. This is not proof that sparse routing is sufficient for FRANK.
- Imperfect selective routing is not equivalent to global broadcast: at AUC≈0.92 and 95% pull sensitivity, coverage is ~98.7%, not 100%.
- Fixed re-entry age/TTL is not a universal rule in the synthetic freshness proxy.
- Age alone is not causal value. Very recent information can be irrelevant after a regime change; older information can remain useful in a stable regime.
- No live FRANK trace became available in this run.
- No pinned Qwen/J-space model experiment was executed in this ChatGPT worker surface.
- J-space/GWT evidence does not establish phenomenal consciousness.

## Highest-information next experiments

1. **EXP-LIVE-GWT-LESION-FRESHNESS:** truthful/shuffled/removed plus delay/validity factorial on synchronized FRANK replay; record state hashes, candidate ranks, effects, outcomes and stale-apply decisions.
2. **EXP-LIVE-GWT-MULTICAST-SHADOW:** run the causal router in shadow mode beside current broadcast; never suppress live delivery initially; measure counterfactual causal audience recall, pull-rescue demand, latency and fanout reduction.
3. **EXP-GWT-DUALWS-CROSSLESION:** pinned Qwen-class model; latent probe/intervention + event receipt alignment; preregister the 2×2 topology signatures above.
4. Reconstruction lesion preserving transport.
5. Ignition interpolation/hysteresis test.

## Promotion decision

`canonical_promotion = NOT_PERFORMED`.

Reason: all new numeric evidence is synthetic; live FRANK and open-model cross-lesion dependencies remain unresolved. The research delta is persisted as an OPEN Topic Packet update and micro-packets, not promoted to canonical live truth.
