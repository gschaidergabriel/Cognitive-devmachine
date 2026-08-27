# EMERGENZ FINAL REPORT — Abstraction Selection Guard for Causal Emergence

Run: `emergenz_20260809T1816p0700_abstraction_guard`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Status: **OPEN — synthetic mechanism support; no live FRANK emergence promotion**

## Main result

The strongest new constraint is an **abstraction-selection guard**:

> A macro/Assembly/higher-order representation must not be discovered and causally certified on the same finite traces without explicit nested selection-bias controls.

ClayGraph/Hyperposition/GWT may generate candidate macroscales. Their definitions must then be frozen by semantic hash (or generated on a separate discovery split) before causal emergence is evaluated on independent interventions/OOD traces.

This separates:

`candidate discovery != macro predictive stability != causal contribution != emergence promotion`.

## Why this is necessary

Current project contracts already reject novelty, graph density, recurrence, nonadditivity and workspace ignition as sufficient emergence evidence. Current negative results also show that stage presence is a weak causal validator and re-entry flags without an information path do not create gain.

External primary literature strengthens the need for causal/interventional evaluation:

- Hoel et al. (2013, PNAS, DOI 10.1073/pnas.1314922110) formalize macro-vs-micro causal comparison using interventions/effective information.
- Schreiber (2000, PRL, DOI 10.1103/PhysRevLett.85.461) shows why conditioning is needed to distinguish directed information transfer from common history/input.
- Rosas et al. (2019, PRE, DOI 10.1103/PhysRevE.100.032305) provide O-information for statistical higher-order synergy/redundancy, useful as a diagnostic but not by itself causal proof.
- Liu et al. (2024, arXiv:2405.09207) provide an exact causal-emergence treatment for linear stochastic iteration systems and connect optimal coarse-graining to dynamical eigenstructure.
- Hoel (2025, arXiv:2503.13395) proposes multiscale causal apportioning rather than a single privileged macro scale; this remains a preprint candidate framework.
- Sutter et al. (NeurIPS 2025) prove that unrestricted nonlinear alignment maps can trivialize causal abstraction, directly motivating complexity/frozen-map guards.
- Yang, Wang & Zhang (2026, arXiv:2605.03267) propose PEID, an interventionist decomposition of unique/synergistic causation under maximum-entropy interventions; this is a high-value candidate estimator, not yet project truth.

## Executed synthetic tests

### 1. Macro-search overfit null

500 null repetitions were generated with an 8-state microvariable X and independent binary Y. For each training set (N=64), all 254 nonconstant binary mappings X->M were searched and the mapping maximizing MI(M;Y) was selected. The frozen mapping was then evaluated on N=5000 fresh samples.

Results:

- mean best training MI: **0.06555 bit**
- median best training MI: **0.05973 bit**
- training p95: **0.12794 bit**
- mean held-out MI: **0.000147 bit**
- held-out p95: **0.000517 bit**

Thus an adaptively selected macro can look informative on causally null data simply from finite-sample search. Held-out evaluation collapses the effect.

### 2. Positive macro control

With a true fixed binary macro partition plus 10% outcome noise, the same search produced:

- mean best training MI: **0.54755 bit**
- mean held-out MI: **0.51361 bit**
- true mapping or complement recovered: **91.8%**

This authored control demonstrates that the split need not erase a stable macro relation.

### 3. Higher-order synergy control

Exact binary mechanisms produced:

- XOR: Omega=-2, joint MI=1.0 bit, individual A/B MI=0, joint-over-best-single=1.0 bit.
- AND: Omega=1, joint MI=0.81128 bit, individual MI=0.31128 each, joint-over-best-single=0.5 bit.
- A-only: Omega=0, joint MI=1.0 bit, best single MI=1.0 bit, excess=0.

This supports using joint-vs-simpler interventional controls, but the heuristic excess measure is not a replacement for PID/PEID.

### 4. Common-driver control

A latent common driver produced observational MI((A,B);Y)=**0.73993 bit** while randomized do(A,B) reduced MI to **0.0000249 bit**. Therefore observational information dependence can be large without causal influence from the measured sources.

### 5. Re-entry sanity check

In an authored system whose next outcome genuinely requires the re-entered signal:

- truthful re-entry success: **1.0000**
- shuffled re-entry: **0.50049**
- no re-entry: **0.50276**

This validates the discrimination logic only; it does not prove FRANK re-entry causal.

## Revised evidence ladder

A candidate emergent mechanism should preserve separate receipts for:

1. macro/Assembly definition and discovery lineage;
2. held-out predictive stability;
3. matched micro and best pairwise/state-machine baselines;
4. intervention-sensitive causal gain;
5. lesion loss;
6. rescue recovery;
7. truthful vs shuffled/no/provenance-broken re-entry;
8. common-driver/null/permutation controls;
9. OOD/context transfer;
10. H1->H2->H3 implementation transfer;
11. latency/compute/memory/instability/recovery shadows.

No scalar may hide a failed required dimension.

## ClayCode implication

Created `EMERGENCE_ABSTRACTION_GUARD.clay` with candidate types:

- `MacroDefinition`
- `EmergenceEvaluationSplit`
- `EmergenceClaimReceipt`

Current G9 generic record/rule/provenance machinery appears sufficient to represent this as a library/schema layer. **No ClayCode core semantic change is justified by this run.** BASE should first compile it; only an executable failure should reopen language semantics.

## H1 next experiment

Once H1 execution is available on the Ubuntu target:

1. generate candidate Assemblies/macroscales on discovery traces only;
2. freeze `macro_definition_hash`;
3. evaluate held-out matched interventions;
4. include Y-independent/null macro-search families and permutation calibration;
5. compare full n-ary macro against best pairwise/state-machine reduction;
6. run lesion/rescue and truthful/shuffled/no re-entry;
7. inject common drivers and frozen-model-output controls;
8. evaluate OOD/context transfer;
9. retain cost/recovery shadows;
10. repeat identically in H2 and H3 for implementation transfer.

## Infrastructure note

`tools/research_interconnect_preflight.py` is now aligned to `clayresearch`, but `ROOM_REGISTRY.json` still contains legacy `clay` room/trigger naming. This is governance drift and has zero scientific evidence weight.

## Decision

- Promote a FRANK emergent organ: **NO**.
- Promote a measurement constraint: **YES, as OPEN research constraint** — abstraction discovery and causal evaluation must be separated or explicitly selection-bias corrected.
- Change ClayCode core semantics: **NO**.
- Best next discriminator: **held-out H1 intervention experiment with frozen macro identities and null macro-search calibration**.
