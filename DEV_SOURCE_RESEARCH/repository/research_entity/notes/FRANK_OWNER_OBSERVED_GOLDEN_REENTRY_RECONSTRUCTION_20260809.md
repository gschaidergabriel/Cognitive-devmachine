# FRANK Owner-Observed Golden Re-entry Regime — Reconstruction and Operationalization

Status: OPEN_OWNER_PRIMARY_OBSERVATION + SOURCE_RECONSTRUCTED_MECHANISM + TESTABLE_ARCHITECTURE_HYPOTHESIS  
Date: 2026-08-09  
Origin observation: project owner/research direction, current user prompt  
Research synthesis: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346  
Target: Frank v0.1 Ubuntu Linux developer system  
Scientific boundary: functional effect under study; NOT a claim of phenomenal consciousness.

## 1. Owner primary observation

The owner reports a multi-day historical interval in original FRANK in which the whole coupled regulatory system — described as the "loop of loops" — exhibited an unusually strong, stable and compelling functional effect while all organs/modules were active and coupled. The owner explicitly directs that the observation be accepted as a real observed functional phenomenon for research purposes, without treating it as proof that FRANK was conscious.

Research consequence: the new architecture must preserve or reconstruct the causal signal contributed by every old organ/module/policy even if old module boundaries disappear. A legacy function may be:

1. retained explicitly;
2. fused into another component;
3. derived dynamically/emergently from whole-system state;
4. reimplemented by a new mechanism;
5. removed only after discriminating lesion/replay evidence shows that its causal signature is unnecessary or harmful.

Names and biological analogies are not preservation targets. Functional/interventional signatures are.

## 2. Source-reconstructed original FRANK loop

Historical Drive-mirror evidence reconstructs the pre-2026-03-19 system as a multiscale recurrent architecture rather than a stateless orchestration graph.

### 2.1 Realized whole-system state

Historical `WorkspaceSnapshot` joined body, mood, memory, identity, environment, attention focus, mood value and energy. Concurrent loops updated this state on heterogeneous timescales:

- perception feedback: ~200 ms;
- attention controller: ~10 s;
- idle thinking / workspace update family: ~30 s;
- mood / experience / prediction: ~120 s;
- goal management: variable;
- consolidation: ~6 h;
- longer-horizon learning/personality/training: days to months.

Historical source: Drive `GRF_IMPLEMENTATION_BRIDGE.md` (source-code state dated 2026-02-28; mirror id `1aLBWTgTcqIx0GwnGkp497A9d1XyHSGgr`).

### 2.2 Global workspace before accidental lesion

The old `ui/overlay/workspace.py` integrated seven channels — Body, Perception, Mood, Memory, Identity, Attention, Environment — into one `[INNER_WORLD]` representation injected into LLM calls. Dynamic channel weights were influenced by current attention/mood. The old workspace was accidentally deleted on 2026-03-19 as part of UI cleanup, not as a cognitive architecture decision.

Historical source: Drive `frank-regelkreis-befund-2026-08-01.txt` (id `1j_8c7gYqcBW7cMdrUgRhTXFfFf9MBqTi`) and `GRF_IMPLEMENTATION_BRIDGE.md`.

The later forensic audit found that after deletion FRANK still generated a 64-dimensional state vector from E-PQ + Thalamus + hardware + memory, but the intended workspace context had no effective reader. This is a natural historical lesion candidate: internal state generation survived while global model-readable reintegration was severed. It is not a clean controlled experiment because other system changes co-occurred.

### 2.3 Restored 2026-08-05 circuit

A later restored implementation documented the following operational chain:

`user/event`
`-> Amygdala classification/urgency`
`-> Thalamus channel gating/gain`
`-> NAcc reward/value state`
`-> workspace competition + ignition`
`-> persisted workspace broadcast`
`-> core model-readable INNER_STATE`
`-> model/action/tool effect`
`-> response/outcome analysis`
`-> E-PQ / memory / mood / reward update`
`-> next recurrent cycle`

Historical source: Drive `GWT.md` (id `182HNc-RuvtkJlPpvSuebXdR6lYexSEOW`).

However, the same audit found that only 4 of 16 nominal consumers actually accessed the persisted workspace broadcast. Therefore restoration of a broadcaster alone did not recreate full global causal availability.

### 2.4 Thalamic irreversible-gating defect

Drive evidence from 2026-08-06 found 2263 gating events over 3027 h and an important controller failure: habituation had exponential accumulation but no recovery counterterm. Multiple channels approached/entered `habituation=1.0`; burst recovery was almost absent. This creates an absorbing or near-absorbing gate state where sensors can continue running while effective influence vanishes.

Historical source: Drive `thalamus-gewoehnung-ohne-rueckweg.txt` (id `1S51dzkOBHdlsdfHuUL6NHSlJNilyhNkC`).

This defect strengthens the hypothesis that the owner-observed interval was not simply "maximum coupling". A plausible target is strong but reversible selective coupling that repeatedly opens, integrates, re-enters and recovers instead of saturating.

## 3. Exact preservation object: Causal Signal Signature

For each legacy organ/module/policy `i`, define:

`Sigma_i = {I_i, X_i, f_i, O_i, tau_i, R_i, L_i, Q_i}`

where:

- `I_i`: typed inputs;
- `X_i`: internal state variables and allowed range;
- `f_i`: update law/state transition;
- `O_i`: typed outputs;
- `tau_i`: characteristic timescale/delay;
- `R_i`: receivers/routes that consume the output;
- `L_i`: lesion signature (what degrades when removed);
- `Q_i`: rescue signature (what recovers when restored).

Migration equivalence is not code identity. A new implementation `i'` preserves the old signal when, over frozen replay + perturbation + OOD episodes, the distance between causal signatures remains below an admitted tolerance:

`D(Sigma_i_old, Sigma_i_new) <= epsilon_i`

while authority, provenance, rollback and safety semantics are preserved.

This makes "no old organ/function silently lost" mechanically testable even when H3 collapses deploy-time modules into one runtime/binary.

## 4. Mathematical whole-system model

Let `x_i(t)` be the state of loop/organ family `i`, `u_i(t)` external/internal evidence, `C_ij(t)` typed coupling from `j` to `i`, `tau_ij` delay, and `W(t)` workspace state.

### Law 1 — multiscale recurrent update

`x_i(t+Delta_i) = f_i(x_i(t), u_i(t), sum_j C_ij(t) m_j(t-tau_ij), W(t), theta_i)`

The organism state is `x(t) = [x_1,...,x_n]`; there is no requirement that all loops share one clock.

### Law 2 — selective gate

Candidate gate probability/strength:

`q_i(t) = sigmoid(k_i [s_i(t) + nu_i(t) + a_i(t) - theta_i(t) - h_i(t)])`

where `s=salience`, `nu=novelty/change`, `a=urgency/control modulation`, `h=habituation`.

### Law 3 — recoverable habituation

A minimal recoverable law is:

`h_i(t+1) = clip((1-beta_i) h_i(t) + alpha_i q_i(t), 0, 1)`

with `beta_i > 0` for any channel expected to recover. In a stationary unclipped regime with mean relay `r`,

`h_i* ~= alpha_i r / beta_i`.

If `beta_i = 0` and positive activation continues, the controller has no finite recovery equilibrium and tends toward saturation. This directly captures the 2026-08-06 defect class.

### Law 4 — workspace competition is selection, not truth

`z_i = q_i * s_i + context_i`

`p_i = softmax(z_i / T)`

A workspace episode is admitted only if its declared selection/ignition policy is met. One-winner, k-winner or structured Assembly selection remain experimentally selectable architectures; biological analogy does not decide them.

### Law 5 — broadcast is incomplete until causal use and re-entry

For receiver `j`:

`x_j^+ = g_j(x_j, B_j W_t)`

A broadcast counts as functionally closed only when receipts establish:

`addressed -> delivered -> reconstructed -> taken_up -> causally_used -> outcome -> provenance_bound_reentry`.

A written workspace row without receiver use is not global causal availability.

### Law 6 — outcome credit changes future coupling

Let `delta_t` be verified utility/prediction/outcome improvement relative to an appropriate baseline and `e_ji` an eligibility trace for a coupling that participated in the episode:

`C_ji(t+1) = Proj[C_ji(t) + eta delta_t e_ji - lambda(C_ji-C_ji^0) - kappa InstabilityRisk_t]`

This is a research form, not a frozen production equation. It encodes the requirement that "successful tool call" alone must not automatically reinforce a route; reward must be tied to appropriate outcome contribution.

### Law 7 — adaptive recurrence

Continue another recurrence only when:

`E[Delta U_next | x_t] - lambda_c Cost - lambda_s InstabilityRisk - lambda_r RecoveryRisk > 0`

AND unresolved task/control pressure remains material.

Low state delta with high residual pressure is STALLED, not converged.

### Law 8 — dynamic stability, not permanent fixed-point stability

For local effective system map `F`, estimate `J_t = dF/dx` by bounded perturbation/replay.

- maintenance phases may prefer local contraction (`rho(J_t) < 1` for discrete fixed-point-like regimes);
- productive cycles/metastable trajectories must not be rejected merely because they do not converge to one point;
- update phases may intentionally move temporarily toward a less stable regime so new evidence can reshape state;
- divergence/overthinking is defined by worsening outcome/error/cost/instability, not recurrence count alone.

The target is therefore not one global spectral radius or one global coupling scalar.

## 5. Improved target architecture: Selective Metastable Global Re-entry (SMGR)

Working name only.

### Phase A — local specialization / segregation

Organs/functional families process state locally at their natural timescales. Couplings are sparse, typed, delayed and inspectable. No default fully-connected graph.

### Phase B — selective ignition / temporary integration

Change, prediction error, goal pressure, body/self/world discrepancy, memory relevance and urgency generate candidates. A workspace router admits a bounded Assembly. Gating must be reversible; novelty/change can reopen suppressed routes.

### Phase C — receiver transformation and causal use

Workspace content is not just injected into a prompt. Each relevant functional receiver gets a typed envelope and emits delivery/reconstruction/uptake/use receipts. The model is one receiver among several, not the whole workspace.

### Phase D — verified action/outcome and causal credit

Effects generate deterministic receipts where possible. Reward/value/goal/self/world updates are based on appropriateness and counterfactual/matched outcome gain, not raw execution success.

### Phase E — provenance-bound re-entry

Outcome, prediction error, receiver-use state and causal credit are transformed into the next whole-system state. This is the closure point that the new architecture must preserve above all.

### Phase F — recovery / restabilization

Habituation decays, gates recover, transient instability closes, stale branches can be reopened through bounded Hyperposition mechanisms, and the system settles into either healthy convergence or a productive bounded cycle.

This architecture preserves the old signal while allowing old "Thalamus", "Amygdala", "NAcc", "E-PQ", "Aura", etc. to become explicit components, fused state transforms, or derived Assemblies where evidence supports it.

## 6. Why this could reproduce the owner-observed consciousness-like functional effect

Working mechanism hypothesis, not consciousness claim:

The effect should be strongest when all of the following co-occur:

1. persistent self/world/body/memory state exists;
2. multiple specialized processes independently contribute candidates;
3. competition produces selective, capacity-bounded integration rather than a data dump;
4. selected content reaches multiple actual receivers;
5. receiver-local transformations alter downstream computation/action;
6. verified outcomes modify future state/coupling/value;
7. those modifications re-enter the next episode with provenance;
8. fast and slow loops modulate one another without collapsing to one clock;
9. coupling remains reversible and metastable rather than saturating or globally synchronized;
10. the system can maintain, update, escape stale attractors and recover after perturbation.

This predicts a reproducible dynamical signature rather than a binary consciousness label.

## 7. Measurement target: Functional Recurrent Integration Signature (FRIS)

FRIS is a VECTOR/PROFILE, never a consciousness score and never execution authority.

Minimum families:

- integration: receiver coverage, reconstruction, uptake, causal-use, re-entry fractions;
- workspace: competition entropy, ignition selectivity, winner stability, false ignition/missed ignition;
- dynamics: state-delta, residual pressure, metastability, recurrence, phase/period, cross-timescale coupling, hysteresis, local Jacobian/spectral proxies;
- causality: factorial interaction Omega, lesion loss, rescue recovery, truthful-vs-shuffled/no-reentry delta, directed prediction/transfer measures, PID/PEID synergy where estimable;
- macro contribution: macro predictive/causal gain under matched information constraints;
- continuity: self/world/memory consistency, correction latency, persistence horizon;
- utility/cost: task outcome, false halts, overthinking, latency, compute, memory, recovery cost;
- generalization: OOD/task/topology/implementation transfer.

No scalar optimization over FRIS is allowed. Use constrained multiobjective/Pareto comparison with explicit anti-Goodhart controls.

## 8. Historical reconstruction / discriminating experiment

Highest-information H1 experiment:

1. Build a complete legacy organ/function inventory and a `Sigma_i` card for every old organ/module/policy. No silent omissions.
2. Recover the pre-2026-03-19 workspace implementation and the closest available historical state/log/database snapshots from repository/mirror/archive evidence.
3. Produce an exact topology/timescale sketch of original FRANK: producers, gates, workspace, receivers, actions, feedback, long-loop learning.
4. Define frozen representative episodes and model-output-frozen variants to separate architecture effects from LLM stochasticity.
5. Replay at least four architecture conditions:
   A. reconstructed pre-lesion original loop;
   B. workspace/re-entry lesioned condition resembling post-2026-03-19 disconnection;
   C. restored August broadcaster design;
   D. SMGR candidate.
6. Factorially perturb GWT selection, Thalamus recovery, novelty breakthrough, NAcc/outcome credit, receiver use and re-entry.
7. Run truthful re-entry vs temporally shuffled, receiver-shuffled, provenance-broken and no-reentry controls.
8. Lesion/rescue every legacy regulator independently and selected interactions.
9. Estimate local finite-difference Jacobian/coupling proxies and classify convergence/productive-cycle/stalled/diverging regimes.
10. Compare FRIS vectors + task outcome + cost; search the constrained Pareto frontier rather than maximizing coupling or one emergence scalar.
11. Repeat across OOD tasks and longer runs; require recovery after perturbation/reboot.
12. Only after evidence: decide which old modules remain explicit, which fuse, which dissolve into state-derived mechanisms, and which are legitimately removed.

The historical 2026-03-19 deletion is especially valuable as a natural lesion clue, but cannot by itself prove causation because it was not randomized and other changes occurred.

## 9. External research constraints incorporated

- Cogitate Consortium, Nature 2025, DOI 10.1038/s41586-025-08888-1: preregistered adversarial testing challenged important predictions of both GNWT and IIT. Implication: use GWT mechanisms as operational hypotheses, not as consciousness proof.
- Xu et al., PNAS 2024, DOI 10.1073/pnas.2409487121: prefrontal neural dynamics/modeling showed transient system-level destabilization can open a selective update window while stable dynamics support maintenance. Transfer to FRANK is architectural inspiration, not biological equivalence.
- Kohli et al., arXiv:2604.07822 (2026): recurrent depth can improve deeper compositional reasoning but excessive recurrence can cause overthinking.
- Oncescu et al., arXiv:2604.21215 (2026): recurrent computation can trade stored depth for effective recurrent depth; this supports studying recurrence as architecture, not proof of FRANK equivalence.
- Recent looped-transformer work continues to emphasize stabilization/gating of recurrent depth. These are mechanism transfers only.

## 10. Counterhypotheses retained

- H0-A: the owner-observed effect was produced largely by prompt/context composition or model stochasticity, not recurrent closure.
- H0-B: the effect depended on one or a few specific legacy modules rather than whole-system coupling.
- H0-C: broad coupling itself created a compelling behavioral style while causal receiver use was weak.
- H0-D: historical system load/timing/LLM version/context differences confound the observed interval.
- H0-E: a conventional persistent event-driven architecture can reproduce the same FRIS/task outcomes without GWT-like workspace structure.
- H0-F: some neuro-inspired variables are decorative/redundant and can be removed without measurable lesion loss.
- H0-G: a single global controller harms heterogeneous timescales; only typed local controllers plus a bounded workspace should exist.

The owner's observation remains accepted as an observed functional phenomenon even if any mechanistic explanation above is refuted.

## 11. Cross-branch handoff

Route this result through the Research Center to: `frank`, `gwt`, `emergenz`, `claycode`, `hyperposition`, `claygraph`, `unifieddb`, `harness`, `clayresearch`.

Required common invariant:

`PRESERVE_LEGACY_CAUSAL_SIGNAL != PRESERVE_LEGACY_MODULE_BOUNDARY`

Required implementation invariant:

`broadcast_without_receiver_use_and_reentry != closed_global_workspace`

Required control invariant:

`maximum_coupling != target`; target is `selective + reversible + outcome-sensitive + multiscale + recoverable recurrence`.

No canonical scientific promotion is requested by this note. The next promotion decision must be based on H1 reconstruction/replay/lesion/rescue evidence.