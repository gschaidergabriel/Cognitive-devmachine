# GWT RESEARCH RUN 3 — Gate-vs-Ignition Identifiability and Reconstruction/Uptake

**run_id:** `gwt-20260808T0608p0700-chatgpt-secondary`  
**trigger:** `gwt`  
**actor:** `chatgpt-secondary`  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**boundary:** functional/mechanistic GWT only; no phenomenal-consciousness claim; new numeric results are synthetic diagnostic/proxy evidence.

## Executive synthesis

This run corrects two remaining ambiguities in the FRANK/GWT research model.

First, current source-grounded FRANK architecture already has a six-channel cognitive workspace in `services/workspace_broadcast.py`, with winner selection and a configured `ZUENDSCHWELLE=0.55`. Therefore `gezuendet=true` is an engineering controller state, not by itself scientific evidence for endogenous GWT ignition. Classical GNW ignition refers to nonlinear, self-amplifying recurrent dynamics. The 2026 Anthropic J-space study similarly distinguishes sharp/bimodal representational commitment from the still-unresolved question of classic competitive recurrent ignition. The current 2026 Ignition Index preprint operationalizes sharpness continuously and reports stronger ignition along the iteration axis of a depth-recurrent model than along depth alone.

Second, broadcast transport must be separated from receiver reconstruction and uptake. Current FRANK does not literally multicast one payload to six downstream cognitive modules: `workspace_broadcast` persists the selected semantic state, Core reads the newest row into `[INNER_STATE]`, and Qwen consumes that semantic projection. For current FRANK, the most important reconstruction boundary is therefore `persisted workspace semantic projection → Core context → model-internal uptake`. A transport/read receipt proves bytes/state arrived; it does not prove the receiver reconstructed or used their intended meaning.

The revised candidate becomes:

`candidate → compete → gate_event → logical workspace register → transport/read → projection/reconstruction → receiver uptake → effect → outcome → freshness-gated re-entry`

with a separate observer:

`ignition_evidence = {pre-gate transition width, threshold-shift anchoring, bimodality, hysteresis, recurrent-lesion effect, broadcast/effect consequences}`.

## Internal evidence update

FRANK Cycle 3 corrected the workspace identity using the newer 2026-08-05 runtime architecture source. The current cognitive path is `workspace_broadcast.py`, not the older process-local `global_workspace.py`. Six channels compete, the winner may cross `ZUENDSCHWELLE=0.55`, one focus receives full detail, the row is written to `consciousness.db.workspace_broadcast`, and Core reads it into `[INNER_STATE]`. This source-grounded claim remains OPEN pending independent live code/trace reproduction.

The same FRANK cycle independently converged on hybrid freshness: retain the 60 s heartbeat for spontaneous/idle cognition but refresh on semantic-dirty or high-salience conditions before consumption. Its synthetic timing model found fixed-60 s chronological query age near 30 s median/~57 s p95 while a constructed hybrid policy eliminated its defined semantic-stale reads with fewer refreshes than refresh-on-every-query. This reinforces GWT Run 2's causal-freshness direction but remains synthetic.

## External research

### Recurrent ignition
Peer-reviewed GNW reviews define ignition as a nonlinear network transition supported by recurrent processing: activity either enters a self-amplifying, sustained, globally accessible regime or decays. Thus a hardcoded threshold can implement a gate but cannot establish the recurrent mechanism it is meant to model.

### Anthropic J-space
Gurnee et al. show a sharp transition under concept interpolation: transition width narrows through middle layers and maximally ambiguous inputs become bimodal, especially in J-space. They explicitly state that transformers lack clean recurrent loops/specialist modules and that it remains unclear whether observed competition mirrors classic sharp competitive ignition. This makes J-space a useful comparator but not permission to relabel any thresholded controller as ignition.

### Ignition Index
`arXiv:2608.05160` fits sigmoid steepness to representation-vs-input-strength curves. Its reported recurrent-model result is especially relevant: Huginn-3.5B shows substantially stronger ignition along iteration than depth. Evidence class remains preprint. FRANK should borrow the measurement logic while adding controls for its explicit software threshold.

### Reconstruction/translation
VanRullen & Kanai's Global Latent Workspace roadmap treats translation among specialist latent spaces as a core mechanism. Broader latent-space translation work shows separately trained representational spaces can require explicit mappings even when they encode related semantics. For GWT engineering this supports a distinct receiver reconstruction stage instead of equating delivery with semantic availability.

## EXP-GWT-IGNITION-IDENT-004

A synthetic calibration varied the configured threshold over 0.45, 0.50, 0.55, 0.60 and 0.65 across 100 noisy replications.

For a smooth latent process followed by a hard configured gate, the estimated post-gate transition followed the configured threshold almost one-for-one: threshold-anchoring slope `0.99817 ± 0.01116`.

For a separately observable endogenous pre-gate nonlinear mediator, its transition location was invariant to the configured gate: anchoring slope approximately zero.

A recurrent fixed-point calibration added a second discriminator. Up/down-sweep hysteresis area was `0` with no feedback, ~`0.249` at feedback 1.0 and ~`0.643` at feedback 1.5. This does not prove hysteresis in FRANK; it shows why hysteresis plus feedback-lesion sensitivity is a stronger recurrent signature than one threshold crossing.

### Consequence
FRANK's planned ignition interpolation experiment is upgraded to a **threshold-shift identifiability experiment**. The configured threshold must be varied in replay/shadow mode while pre-gate candidate dynamics are observed. If the apparent transition simply moves with `ZUENDSCHWELLE`, it is controller-generated. Evidence for endogenous ignition requires an independently measured transition that survives threshold changes and weakens under recurrent/feedback lesions.

## EXP-GWT-RECONSTRUCTION-LESION-005

A synthetic six-audience latent-coordinate proxy preserved transport perfectly while removing only one receiver's reconstruction transform. Across 120 seeds × 5,000 samples, transport receipt success remained `1.0`. The lesioned target's semantic action accuracy fell to mean `0.433735 ± 0.090740`, while all five unlesioned audiences remained at `1.0` mean accuracy.

A transport-only validator therefore detected `0%` of these deliberately constructed semantic lesions; a reconstruction-aware validator detected `100%` by construction.

### Consequence
Receipts should be split:
- `transport_receipt`: payload/hash arrived;
- `projection_receipt`: deterministic/typed receiver projection succeeded;
- `uptake_receipt`: receiver representation or behavior shows the content was actually available/used;
- `effect_receipt`: downstream state/action changed causally.

For deterministic modules, uptake may be testable through parse/roundtrip/invariant checks. For Qwen, a future `LATENT_WS` probe (J-lens-like or another validated representation probe) can serve as one independent uptake channel; behavior/effect remains another. This gives the dual-workspace architecture a concrete role: `LATENT_WS` is not merely a second workspace claim, but potentially an observability channel for whether `EVENT_WS` semantic content was reconstructed inside the model.

## New hypotheses

1. **H-GWT-R3-001 — threshold-shift invariance.** Endogenous ignition should expose a pre-gate nonlinear transition that does not simply track the configured `ZUENDSCHWELLE`.
2. **H-GWT-R3-002 — recurrent dependence.** If ignition is genuinely recurrent, feedback/re-entry lesions should reduce transition sharpness, persistence or hysteresis beyond generic disruption controls.
3. **H-GWT-R3-003 — reconstruction necessity.** Transport success can coexist with receiver-specific semantic failure; reconstruction must therefore be independently lesionable/observable.
4. **H-GWT-R3-004 — latent uptake bridge.** When the receiver is Qwen, event-workspace payload uptake should align with an independent latent representation probe above shuffled/corrupted payload controls.
5. **H-GWT-R3-005 — current-FRANK audience mapping.** The primary current model audience is Core/Qwen via `[INNER_STATE]`; multi-audience selective multicast remains a future architecture hypothesis unless live runtime evidence shows additional consumers.
6. **H-GWT-R3-006 — gate/evidence separation reduces Goodharting.** Keeping `gate_event` and `ignition_evidence` separate prevents a configured threshold from automatically satisfying the metric used to evaluate ignition.

## New negative results / corrections

- A hardcoded threshold crossing is not evidence of endogenous ignition.
- A successful DB write/read or transport receipt is not evidence that the receiver reconstructed or used the intended semantics.
- Current FRANK source evidence does not justify describing the live system as physically multicasting the winning payload to all specialist channels; its measured path is workspace persistence followed by Core/Qwen consumption.
- A single scalar Ignition Index or threshold steepness should not be sufficient for FRANK because software thresholding can manufacture sharpness; threshold-shift and causal recurrent controls are mandatory.

## Architecture delta

Replace the overloaded stage `selection/ignition` with:

`competition → selection → gate_event(configured policy) → workspace publication`

and measure scientific ignition separately:

`pre_gate_transition + ambiguity/bimodality + threshold_shift_test + hysteresis + feedback_lesion + sustained/global causal effect`.

Replace `audience_receipt → reconstruction_receipt` with a four-stage receiver contract:

`transport_receipt → projection_receipt → uptake_receipt → effect_receipt`.

For current FRANK, instrumentation priority is:
1. log six candidate values, winner, runner-up, margin, `ZUENDSCHWELLE`, and pre-gate state;
2. shadow-replay multiple thresholds without changing production effects;
3. log exact workspace row/hash and Core `[INNER_STATE]` inclusion;
4. add deterministic projection/roundtrip checks where possible;
5. later add Qwen latent uptake probe and payload lesion/shuffle controls;
6. lesion feedback/re-entry and test whether sharpness/persistence/hysteresis changes.

## Provider execution

This run is the first GWT cycle to use the newly operational GitHub repo-runner bridge. OpenAlex, arXiv, Tavily and Exa returned successfully. Semantic Scholar returned HTTP 429 from the shared public pool and was replaced by the successful OpenAlex/arXiv evidence path. Hugging Face paid inference was not retried because the RAE quota cache records monthly included inference credit as depleted until 2026-09-01. Local sandbox supplied the diagnostic experiments; no model-target result is claimed.

## Highest-information next experiments

1. **EXP-LIVE-GWT-GATE-IDENTIFIABILITY** — current FRANK trace/replay; sweep shadow `ZUENDSCHWELLE`, log pre-gate curves, transition anchoring, bimodality and downstream consequences.
2. **EXP-LIVE-GWT-RECURRENT-LESION** — lesion outcome→re-entry/feedback while matching compute and measure transition width, persistence and hysteresis.
3. **EXP-LIVE-GWT-RECONSTRUCTION-UPTAKE** — hold row transport constant, perturb semantic projection, measure deterministic Core receipt + Qwen latent/behavior uptake + effects.
4. **EXP-LIVE-GWT-FRESHNESS-FACTORIAL** — fixed 60 s vs hybrid freshness on matched traces.
5. **EXP-GWT-DUALWS-CROSSLESION** — once a pinned Qwen-class probe is available, combine latent/event lesions and test mediation topology.

## Promotion decision

`canonical_promotion = NOT_PERFORMED`.

The newest FRANK architecture materially narrows the live target and the diagnostic experiments produce useful falsifiers, but this worker still has not executed the current FRANK host or pinned Qwen latent probe. Canonical scientific state remains r2.
