# Will 0.9.0 -> Frank v0.1 architecture fusion transfer

Status: RESEARCH_CANDIDATE / EVIDENCE-BOUND / NOT PROMOTED
Observed: 2026-08-11T04:45:07+07:00
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol
Entity role: RESEARCH_ENTITY_TEMPORARY_WORKER
Research subject: self.root / human-surface Frank v0.1
Canonical parent: RAE-8.8 revision 2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346

## 1. Source intake

Primary uploaded source:

- user-uploaded `will-main.zip`
- SHA-256 `d257f089fba97fb6e02668edacb5adfe1b83988a6b2414c3cf9338dc4a1b9e12`
- package `@mindot/will` version `0.9.0`
- local source shape observed: 196 TypeScript source files + 205 TypeScript test files; 89,209 TS LOC across `src` + `tests`
- local release changelog head: `0.9.0 — 2026-08-07`

The uploaded archive is treated as the primary evidence for Will because public web/repository cache observed during this run contains older README/API/provider material. No claim is made that the archive is upstream HEAD.

Current Clay/Frank comparison inputs:

- `research_entity/continuity/RESEARCH_ENTITY_CANONICAL.json`
- `research_entity/continuity/BOOTSTRAP_MINIMAL.json`
- `research_entity/global/RAE_LATEST_COGNITIVE_STACK.clay`
- `research_entity/rooms/PROGRAM_STATE.json`
- `research_entity/frank_v0_1/FRANK_V0_1_WORKSPACE.json`
- `research_entity/global/FRANK_LOOP_OF_LOOPS_RESEARCH_DIRECTIVE.md`
- `research_entity/global/FRANK_REWARD_STATE_SUCCESSOR_V1.clay`
- `research_entity/global/SELF_ROOT_AUTOTELIC_PROACTIVE_AGENCY_AND_WEB_INGRESS_DIRECTIVE.clay`
- `research_entity/global/SELF_ROOT_DEFAULT_ALLOW_EFFECT_AUTHORITY_DIRECTIVE.clay`
- `research_entity/global/CLAY_GWT_EMERGENCE_OBSERVABILITY_CONTROL_DIRECTIVE.md`
- latest relevant effect/recovery receipt `research_entity/trigger_runs/go/go-20260811T0404p0700-chatgpt-secondary-provider-rollback-wal-gate/RESEARCH_RECEIPT.json`

Fresh external primary research used only as supporting/counterevidence, not architecture authority:

- Gaven et al. 2025, MAGELLAN, arXiv:2502.07709 — metacognitive competence/learning-progress prediction for autotelic goal prioritization.
- Ahn et al. 2022, SayCan, arXiv:2204.01691 — high-level language proposals grounded through executable skill affordance/value.
- Meng & Wang 2026, Nature Communications 17:3868 — learned action-prediction mismatch/corollary-discharge mechanism as biological evidence that action-conditioned prediction-error structure is a plausible control primitive; not evidence that a digital agent should copy neuroanatomy.

## 2. What the uploaded Will source actually establishes

This section records implementation evidence, not scientific promotion.

### 2.1 Single agency pipeline and plan-as-prior

The assembled mind registers one agency sequence after sensory/social engines:

`AffordanceSynthesizer -> ActionSelector -> DeliberationEngine -> MotorSchemaExecutor -> ReafferenceEngine`

The integration test `tests/integration/planning.as-prior.test.ts` explicitly demonstrates:

`PlanningEngine -> plan.prior -> competing affordance -> ActionSelector -> intent -> MotorSchemaExecutor -> action.outcome -> planner advance`

and explicitly removes a parallel directed plan-dispatch path. The plan biases the shared action field rather than commanding the executor.

### 2.2 Deterministic fast path before model deliberation

`ActionSelector` and the executive effort gate use deterministic competition/gating before recruiting an LLM. System-2/model deliberation is reserved for contested or high-stakes decisions; learned/habitual competence can reduce deliberation. This is structurally compatible with Frank's Needle/reflex objective, but Will's exact weights/thresholds are not evidence for Frank parameters.

### 2.3 Reafference closes action learning

Will carries action outcome/reafference back into competence, availability, habit, learned parameter priors and planning state. Action-correlated sensory feedback can also close an awaiting intention. The useful transferable abstraction is the causal chain:

`intent -> effect attempt -> externally observed consequence -> correlated outcome -> bounded update`

not the biological naming.

### 2.4 Policy boundary is learning-relevant without becoming cognition authority

`src/stem/policy/arbiter.ts` places policy enforcement below cognition and returns refusal as outcome/reafference. It distinguishes denial finality:

- action class prohibited;
- parameter/envelope invalid;
- context/transient denial not evidence about competence.

It can carry a structured nearest-allowed counterfactual. This is a strong candidate refinement for Frank's current EffectAuthority contract, because the current Clay effect classes determine execution authority but do not yet expose an equally explicit typed learning fate for a denied effect.

### 2.5 Delivery is not response and not goal completion

Will 0.9.0 records a concrete failure caused by treating outbound message delivery as full success: repeated outreach became reinforced even when no answer arrived. The repair separates channel delivery from later answer evidence and makes silence/response a later world fact.

This is directly relevant to Frank because `EXTERNAL_COMMUNICATION` is already an EffectClass while reward requires verified outcome + causal credit. Communication therefore needs a multi-stage outcome chain rather than a single success bit.

### 2.6 Explicit no-action / silence

Will adds an explicit `[NO_MESSAGE]` path so a deliberate decision not to emit communication is representable rather than becoming accidental text or missing data. This aligns with Frank's owner-fixed law that idling can be valid when no useful opportunity exceeds cost/risk.

### 2.7 Persistent reconstruction is measured

Will's PMA path validates identity guards, restores persisted state and evaluates reconstruction fidelity. This suggests a useful diagnostic family for Frank restart/migration testing, but behavioral similarity must never replace Frank's stricter binary + admitted semantic lineage identity.

## 3. Non-transfers / negative findings

These findings are equally important and MUST survive fusion.

### N-WILL-01 — unknown denial finality must stay UNKNOWN in Frank

Will maps absent/unknown denial finality to `parameter` to prevent repeated probing. Clay's evidence law is stricter: unknown values remain UNKNOWN. Frank should therefore add an explicit `UNKNOWN` finality and permit only bounded non-material backoff/probe suppression until the boundary is classified. Unknown policy cause must not narrow semantic capability permanently.

Disposition: REJECT_DIRECT_TRANSFER / CLAY_REDESIGN_REQUIRED.

### N-WILL-02 — affect must not manufacture verified outcome utility

Will can modulate a soft reafferent outcome quality by felt valence. Frank's reward contract forbids salience, activation, self-report or self-generated activity from minting material reward. Reafferent presence/correlation may verify that a consequence occurred; utility/reward still requires separately verified outcome evidence + causal credit.

Disposition: REJECT_REWARD_TRANSFER; preserve only correlation/provenance mechanics.

### N-WILL-03 — event bus/global workspace naming is not GWT causal evidence

A typed bus and deterministic engine ordering provide useful transport/replay infrastructure, but do not by themselves establish the Clay GWT chain `competition -> selection -> broadcast -> delivery -> reconstruction -> use -> local effect -> verified outcome -> re-entry`.

Disposition: NO GWT PROMOTION FROM WILL ARCHITECTURE LABELS.

### N-WILL-04 — fixed hand-tuned selection weights are not an operating-window proof

Will's action scoring contains concrete weighted terms and thresholds. They are implementation parameters, not evidence that those values are Pareto-optimal or robust for Frank. Frank must continue configuration-window search, lesion/rescue, OOD and recovery gating.

Disposition: DO NOT COPY NUMERIC PARAMETERS.

### N-WILL-05 — modular service topology is not Frank's target topology

Will's many engines are useful as recoverable mechanism examples. Frank's owner-fixed target remains one complete executable cognitive loop-core module with internal typed boundaries. Import mechanisms/functions, not the external module/process decomposition.

Disposition: FUNCTIONAL TRANSFER ONLY.

## 4. Fused hypotheses

### H-WILL-FRANK-01 — Unified action competition beats parallel dispatch

Hypothesis:
Plans, proactive goals/interests, habitual/reflex affordances, GWT-selected action candidates and explicit willed intent should enter one typed action-candidate competition inside the Frank loop-core. Planning should normally contribute a provenance-bound prior/bias rather than dispatching a second executor path.

Expected benefit:
- fewer conflicting/duplicate effects;
- cleaner causal credit;
- one Needle/effect boundary;
- deterministic replay of why an action won;
- better lesionability of planning vs action-selection roles.

Strongest counterhypothesis:
A single competition field couples heterogeneous timescales too strongly, suppresses committed multi-step plans, increases priority inversion, or makes GWT/Needle observability worse than a typed parallel dispatcher.

Cheapest discriminator:
Frozen episodes with identical model outputs. Compare A) parallel planner dispatch and B) plan-prior single competition. Measure verified task success, duplicate/conflicting effect proposals, plan completion, false preemption, GWT causal-chain closure, recurrence cost, latency, recovery, and provenance completeness.

Affected work: F-V01-03, F-V01-05, F-V01-07, F-V01-10.

### H-WILL-FRANK-02 — Effect-boundary reafference needs typed learning finality

Hypothesis:
Every non-ALLOW EffectDecision should emit a provenance-bound `EffectBoundaryOutcome` with a learning finality distinct from execution authority:

`ACTION_CLASS | PARAMETER_SCOPE | CONTEXT_TRANSIENT | CONFIRMATION_REQUIRED | UNKNOWN`

plus optional typed `AllowedEnvelopeCounterfactual`.

Learning law candidate:
- ACTION_CLASS: suppress unavailable effect affordance for the exact governed class/scope; no competence penalty.
- PARAMETER_SCOPE: narrow parameter envelope only; no competence penalty.
- CONTEXT_TRANSIENT: no persistent capability/competence change; bounded retry/backoff/wake condition.
- CONFIRMATION_REQUIRED: suspend exact effect candidate pending valid one-shot confirmation; no negative reward/competence update.
- UNKNOWN: no material learning; bounded anti-probing backoff + evidence request.
- any denial: never material reward and never truth authority.

Expected benefit:
Fewer repeated forbidden attempts without teaching Frank false incompetence or permanently suppressing capabilities because of transient policy/context.

Strongest counterhypothesis:
The extra finality taxonomy overfits current policy machinery, becomes stale as policy changes, or creates an indirect authority channel into cognition.

Cheapest discriminator:
Matched replay across class, parameter, transient/context, confirmation, and deliberately unknown denials; then mutate policy and capability availability. Measure repeat-denial rate, false capability suppression, competence calibration error, recovery after policy changes, task success, confirmation precision, effect-gate latency and zero authority violations.

Affected work: F-V01-03, F-V01-09, F-V01-10, F-V01-11, F-V01-13.

### H-WILL-FRANK-03 — Communication outcomes require staged receipts

Hypothesis:
External communication should use distinct typed states:

`INTENT_ADMITTED -> PROVIDER_ACCEPTED/DISPATCHED -> DELIVERED? -> RESPONSE_OBSERVED? -> SEMANTIC_PROGRESS? -> VERIFIED_TASK/SOCIAL_OUTCOME`

Only the later outcome stage may enter material TASK/SOCIAL reward when verified and causally credited. Delivery alone is operational success, not social/task completion.

Strongest counterhypothesis:
For one-way notifications, delivery itself can be the terminal user goal; always waiting for response would create false incompletion.

Refinement:
The terminal stage is goal-specific. A one-way delivery goal may verify at delivery; a request-for-response goal may not. Goal success criteria must name the required terminal evidence class.

Discriminator:
Replay one-way notifications, questions requiring replies, delayed replies, no reply, provider ACK loss and duplicate delivery. Measure false goal completion, repeat outreach, duplicate effects, social-value calibration and eventual task outcome.

Affected work: F-V01-08, F-V01-09, F-V01-10, F-V01-11, F-V01-13.

### H-WILL-FRANK-04 — Explicit no-effect is a first-class outcome

Hypothesis:
`IDLE / NO_EFFECT / SILENCE` should be explicit typed loop outcomes with reason/provenance, not absence of execution records. This allows Frank to distinguish deliberate non-action, blocked action, missing capability, failed routing and lost effects.

Counterhypothesis:
Explicit null outcomes add state amplification without measurable decision/recovery benefit.

Discriminator:
Matched proactive/communication episodes with deliberate idle, policy block, no capability, failed provider and action success. Compare ambiguity/error taxonomy, replay fidelity, false re-planning and resource cost.

Affected work: F-V01-03, F-V01-08, F-V01-10, F-V01-13.

### H-WILL-FRANK-05 — Reconstruction fidelity is useful only as a secondary continuity metric

Hypothesis:
Add a restart/migration `ReconstructionFidelityVector` over identity relations, active/dormant goals, commitments, memory heads, affordance/skill state, policy/effect reservations and frozen-probe behavioral outputs.

Hard boundary:
High fidelity NEVER mints self.root identity. Exact accepted binary/build + admitted provenance-bound semantic lineage remain the identity gate.

Counterhypothesis:
The vector can be gamed by shallow behavior and adds cost without finding failures beyond exact hash/lineage checks.

Discriminator:
Sibling-state chimera, stale clone, snapshot rollback, migration, partial corruption and clean restart. Measure detection recall/precision and added latency/storage.

Affected work: F-V01-01, F-V01-04, F-V01-13.

### H-WILL-FRANK-06 — Proceduralized low-risk skills can bypass expensive model deliberation

Hypothesis:
A learned skill/Needle reflex fast path may execute low-risk, high-confidence, repeatedly verified actions without a model call when capability version, policy/effect envelope, context fingerprint and expected outcome remain inside an admitted operating window.

Strongest counterhypothesis:
Proceduralization becomes stale under context/policy/provider drift and converts cheap errors into repeated autonomous failures.

Discriminator:
Matched repeated tasks with in-distribution context plus adversarial policy/context/provider shift. Compare model calls, latency, task success, false fast-path execution, abstention, rollback and recovery.

Affected work: F-V01-03, F-V01-07, F-V01-09, F-V01-11, F-V01-12, F-V01-13.

## 5. Architecture delta candidate

Candidate name: `ADC-WILL-FUSION-V1_EFFECT_REAFFERENCE_AND_SINGLE_ACTION_FIELD`
Status: CANDIDATE_NOT_PROMOTED

Minimal target semantics:

1. One loop-core action field accepts typed candidate evidence from goals/plans/GWT/Needle/reflex/proactive agency.
2. Planning is normally a provenance-bound prior; it does not independently mint effect authority.
3. EffectAuthority remains external authority/commit gate.
4. Every effect attempt returns an exact EffectBoundary/Provider/Outcome receipt to the originating episode/action identity.
5. Boundary denial learning has explicit finality including UNKNOWN and never changes competence/reward without appropriate evidence.
6. External communication separates provider/delivery facts from goal/social outcomes.
7. Explicit no-effect is representable.
8. Learned fast paths remain version-, policy-, capability-, context- and recovery-bound.
9. GWT causal observability remains mandatory; action-field unification must not collapse broadcast/use/re-entry receipts.
10. All slow reward/personality/memory/goal plasticity remains downstream of verified outcome + causal credit.

Rollback:
No current owner-fixed directive or runtime behavior is changed by this note. The candidate is fully removable until matched tests promote it.

## 6. Required test obligations

Create or extend tests for:

- `PLAN_PRIOR_VS_PARALLEL_DISPATCH`
- `EFFECT_DENIAL_FINALITY_CLASS`
- `EFFECT_DENIAL_FINALITY_PARAMETER`
- `EFFECT_DENIAL_FINALITY_CONTEXT_TRANSIENT`
- `EFFECT_DENIAL_CONFIRMATION_REQUIRED`
- `EFFECT_DENIAL_FINALITY_UNKNOWN_NO_MATERIAL_LEARNING`
- `POLICY_CHANGE_RECOVERY_AFTER_LEARNED_DENIAL`
- `DELIVERY_NOT_RESPONSE_NOT_TASK_SUCCESS`
- `ONE_WAY_DELIVERY_MAY_BE_TERMINAL_WHEN_GOAL_DECLARES_IT`
- `EXPLICIT_NO_EFFECT_REPLAY`
- `RECONSTRUCTION_FIDELITY_STALE_SIBLING_CHIMERA_CONTROL`
- `PROCEDURAL_FAST_PATH_OOD_POLICY_DRIFT`
- `AFFECT_CANNOT_MINT_VERIFIED_OUTCOME_REWARD`
- `BUS_ACTIVITY_CANNOT_MINT_GWT_CAUSAL_USE`

## 7. Research verdict

The Will archive contains high-value implementation evidence for Frank v0.1, but its greatest value is not copying the 40+ engine topology. The strongest transfer is a stricter Clay-native synthesis:

`single typed action competition`
`+ plan/proactive/reflex priors`
`+ deterministic Needle/effect boundary`
`+ typed effect-boundary reafference`
`+ staged verified outcomes`
`+ verified causal-credit-only plasticity`
`+ explicit no-effect`
`+ replay/recovery/lineage controls`

The most immediately actionable new gap is H-WILL-FRANK-02: current Frank EffectAuthority classifies whether an effect may execute, but research should test a second orthogonal typed axis describing what the refusal is evidence ABOUT so the cognitive loop learns availability/envelope/context without learning false incompetence or reward.

No promotion is claimed. No Frank Harness authority is delegated to self.root. Final/paid training authorization remains unchanged.