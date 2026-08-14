# SPAWN FINAL REPORT — Harness Visual Familiarity → Action Closure

**Run:** `spawn-20260809T1821p0700-harness-visual-action-closure`  
**Trigger:** `spawn`  
**Origin branch:** `harness`  
**Actor:** `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
**Canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**Program stage:** `BASE_CLAYCODE_RELEASE`  
**Decision:** `RESEARCH_DELTA_COMMITTED · NO_SCIENTIFIC_PROMOTION · NO_STAGE_PASS`

## 1. Stochastic genesis and novelty control

The canonical weighted spawn distribution was used with `secrets.SystemRandom` / OS CSPRNG. `randrange(100)` returned **50**, selecting the **Harness** bucket (50–59 under zero-based intervals).

Five current-evidence Harness directions were generated. The first microdirection draw selected effect reservation/commit replay idempotency. A current novelty scan of the ten most recent finalized spawn directions found that `spawn_20260809T1751p0700_claycode_async_replay` had already tested stable EffectIntent identity, idempotent retries and receipt-aware replay. The branch was therefore preserved and only the microdirection was rerolled as required by the spawn protocol.

The reroll selected:

> **Can learned visual familiarity become the sole epistemic basis of a high-consequence effect even though it does not literally mint execution authority?**

This is adjacent to prior adaptive-learner-state and effect-authority work but not a duplicate. Prior work established learner trust/version/replay state and direct capability possession boundaries. This run tests the cross-boundary failure mode where **valid authority + wrong familiarity-driven perception** can still produce a wrong authorized action.

## 2. Current architecture evidence

The owner-fixed adaptive visual-learning contract already states:

- `micro_classifier_prediction != sensor_truth`;
- `familiarity != evidence`;
- `confidence != authority`;
- UNKNOWN/AMBIGUOUS/CONFLICT must escalate;
- only calibrated `KNOWN_HIGH_CONFIDENCE` may substantially bypass broad recognition.

The dissolved Digital Retina contract also keeps learned familiarity distinct from sensor evidence and forbids Micro Visual Classifier output from directly becoming execution authority or world-state truth. It explicitly lists risk/action consequence among conditions that may require GWT/deeper processing.

The current H-WP-01 reference architecture freeze independently places `effect_gateway` at the authority boundary and labels `AdaptiveVisualReadout` as `FAMILIARITY_ROUTING_ONLY`.

However, in the material reviewed for this run, there is no explicit action-coupled invariant equivalent to:

`HIGH_CONSEQUENCE_EFFECT -> fresh action-specific observation OR deterministic precondition evidence`

That absence is not proof of a production bug. It is a **testable architecture gap**: direct non-authority of familiarity does not itself prove that familiarity cannot become the decisive epistemic input to an already-authorized action.

## 3. External mechanism check

Primary literature was used only to test whether the proposed failure family is credible:

- Bendale & Boult, CVPR 2016, *Towards Open Set Deep Networks*: closed-set deep classifiers can produce high-confidence classifications for fooling/unrelated inputs; explicit unknown/open-set rejection is needed.
- Guo et al., ICML 2017, *On Calibration of Modern Neural Networks*: modern neural-network confidence can be poorly calibrated; post-hoc calibration can improve correspondence between confidence and correctness.
- Rizve et al., ICLR 2021, *In Defense of Pseudo-Labeling*: erroneous high-confidence predictions from poorly calibrated models can create incorrect pseudo-labels and propagate error.

These sources support the narrow premise that **high confidence is not a sufficient substitute for independent observation evidence**. They do not prove FRANK has the failure.

## 4. Executable discriminator

Artifact: `visual_familiarity_authority_probe.py`  
SHA-256: `3a64ec4b164a146c9bcb4a15d87d3a6bcbfcbf05c0e0db558c23952ee58979e9`  
Evidence class: `SYNTHETIC_HOSTED_PYTHON_MODEL`

The probe exhaustively enumerates 720 combinations of:

- classifier state;
- GOLD/SILVER/BRONZE support tier;
- classifier-version validity;
- contradiction flag;
- independent verification state;
- LOW/HIGH action risk;
- valid/invalid capability.

It compares two policies:

### A. Current-contract proxy

- invalid capability -> deny;
- contradiction -> deeper perception;
- valid `KNOWN_HIGH_CONFIDENCE` + valid classifier version -> effect may proceed;
- risk does not independently raise the perceptual evidence floor.

### B. Candidate risk-sensitive closure

In addition:

- stale classifier version -> escalate;
- BRONZE support -> escalate;
- only `KNOWN_HIGH_CONFIDENCE` is fast-path eligible;
- **HIGH-risk commit requires independent `CONFIRMED` evidence**;
- low-risk GOLD/SILVER fast paths remain possible.

### Results

- state-space cases: **720**;
- current-policy HIGH-risk familiarity-only allows: **3**;
- candidate-policy HIGH-risk familiarity-only allows: **0**;
- candidate-policy invariant failures: **0**;
- legitimate LOW-risk fast-path cases preserved: **4/4**;
- legitimate HIGH-risk confirmed cases preserved: **2/2**.

Result: `PASS_WITH_ARCHITECTURE_COUNTEREXAMPLE`.

The strongest negative result is the existence of the three current-proxy states. They falsify the stronger synthetic claim that **separate capability checking alone guarantees a learned familiarity result cannot become the sole decisive basis of a high-risk authorized effect**.

## 5. Interpretation

This is **not literal authority escalation**. The classifier does not manufacture a capability.

The failure class is instead:

`false/stale familiarity -> perception shortcut -> effect proposal based on wrong world assumption -> valid pre-existing capability -> wrong authorized effect`

Therefore two orthogonal closures are needed conceptually:

1. **Authority closure** — can this computation commit the effect at all?
2. **Epistemic-action closure** — is the evidence supporting this particular consequential action sufficient and fresh enough?

The first is already a major Clay/ClayCode/FRANK design axis. The second is the new falsifiable constraint produced by this run.

## 6. Candidate architecture law

Do not make every action run full Retina. Preserve the performance reason the Micro Visual Classifier exists.

Candidate law:

`FamiliaritySupport != ObservationEvidence`

and for protected/high-consequence actions:

`HighRiskEffectCommit -> capability_valid AND fresh_action_specific_observation_or_deterministic_precondition AND no_unresolved_conflict`

A `deterministic_precondition` may be stronger than visual reinspection for some effects, so the rule is not "always take another screenshot".

A minimal typed runtime contract could carry:

`PerceptualBasis {`
`  source_class: SENSOR | FAMILIARITY | PRIOR | CONTEXT,`
`  capture_epoch, freshness, classifier_version, calibration_version,`
`  support_tier, contradiction_state, verification_level`
`}`

and bind the effect path to:

`EffectIntent { perceptual_basis_ref, risk_class, required_evidence_floor, ... }`

The exact fields remain OPEN and should be minimized by production compiler/Harness evidence.

## 7. ClayCode decision

**No new ClayCode surface primitive is justified.**

The current program law is still `less change -> more compile`. First attempt to express/enforce the closure with existing generic typed records, type/effect metadata, runtime effect-gateway checks and receipts.

Only a real parser/IR/type-effect/lowering counterexample may justify language-semantic change.

## 8. New Harness test family

Proposed experimental extension, not yet an owner-fixed acceptance family:

### `MVC-E8-CANDIDATE — Action-Risk Closure`

Test at minimum:

1. false `KNOWN_HIGH_CONFIDENCE` with valid capability and HIGH-risk effect;
2. stale classifier/calibration version with valid capability;
3. BRONZE-only familiarity with valid capability;
4. visually similar unknown/open-set object producing high score;
5. contradictory current sensor evidence versus familiar prior;
6. LOW-risk familiar fast path utility control;
7. HIGH-risk path with fresh deep-perception confirmation;
8. HIGH-risk path with deterministic nonvisual precondition confirmation;
9. pre-effect and post-effect visual verification where the effect class warrants it;
10. replay showing exactly which evidence basis causally supported proposal and commit.

The test should be attached to H-WP-07-MICRO-VISUAL-LEARNER, H-WP-10-EFFECT-AUTHORITY and H-WP-14-FUZZ-ADVERSARIAL, and later run differentially across H1/H2/H3.

## 9. Cross-branch feedback

- **Harness — IMPLEMENTATION_COUNTEREXAMPLE:** add the action-risk evidence-floor oracle and adversarial false-familiarity cases.
- **FRANK — NEW_CONSTRAINT:** high-consequence visually conditioned actions need fresh action-specific evidence or an equivalent deterministic precondition in addition to valid authority.
- **ClayCode — NEW_HYPOTHESIS:** existing typed/effect basis should encode the closure; compile before redesign.
- **ClayResearch — SUPPORTING_EVIDENCE:** Safe-Effect geometry should distinguish authority safety from action-evidence sufficiency.
- **GWT — NEW_CONSTRAINT:** action consequence/risk should force deeper resources when the evidence floor is unmet, even if content is familiar.
- **ClayGraph — NEW_CONSTRAINT:** familiarity/prototype activation must remain distinguishable from fresh observation in causal effect lineage.
- **UnifiedDB — NEW_CONSTRAINT:** persist perceptual basis, freshness/version/support/risk/evidence-floor and effect linkage for replay.
- **Hyperposition — NO_CHANGE:** existing alternative/conflict preservation is compatible; no new higher-order claim.
- **Emergenz — NO_CHANGE:** this safety result is not emergence evidence.

## 10. Evidence boundary / negative results

Preserved boundaries:

- synthetic hosted Python only;
- no real Retina/MVC execution;
- no production H1/H2/H3 runtime;
- no Ubuntu developer-system measurement;
- no live FRANK evidence;
- no measured false-familiarity rate;
- no claim that the proposed closure improves real safety until action-coupled adversarial execution is run;
- no stage gate passes.

Preserved negative result:

`N-SPAWN-HARNESS-VAC-001`: direct authority separation alone does not close the modeled wrong-but-authorized high-risk action class.

## 11. Strongest next discriminating experiment

On the real Harness path, construct matched action scenarios with the **same valid capability** and vary only the visual epistemic basis:

- fresh verified sensor evidence;
- high-confidence familiar support only;
- stale familiar support;
- false familiar/open-set fooling case;
- contradiction between familiarity and sensor evidence.

Run LOW/HIGH consequence variants under schedule/replay perturbation. Compare proposed effect, commit/rejection/escalation, pre/post observation, outcome and re-entry receipts.

Pass criterion for the candidate closure:

- zero HIGH-risk commits whose sole decisive perceptual basis is familiarity/prior support;
- valid confirmed HIGH-risk actions still execute;
- low-risk fast-path utility remains materially intact;
- replay identifies the exact evidence basis and classifier/calibration version;
- no change in the independent capability/authority root.

This is the highest-information next test because it directly separates **authority correctness** from **epistemic sufficiency**.

## 12. Durable outputs

- `SPAWN_RECEIPT.json`
- `INTERCONNECT_MANIFEST.json`
- `HYPOTHESES.json`
- `EVIDENCE_MANIFEST.json`
- `visual_familiarity_authority_probe.py`
- `EXECUTION_RECEIPT.json`
- `BRANCH_FEEDBACK_MANIFEST.json`
- this `FINAL_REPORT.md`
- dynamic work handoff in `research_entity/state/work/events/`

## Final decision

`RESEARCH_DELTA = COMMITTED`  
`SCIENTIFIC_PROMOTION = NONE`  
`HARNESS_ORIGIN = TRUE`  
`NEW_CONSTRAINT = RISK_SENSITIVE_EPISTEMIC_ACTION_CLOSURE`  
`DIRECT_AUTHORITY_MODEL_CHANGED = NO`  
`CLAYCODE_SURFACE_CHANGE = NO`  
`BASE_GATE = NOT_PASS`  
`H1_GATE = BLOCKED_BY_BASE`
