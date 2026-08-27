# SPAWN FINAL REPORT — ClayCode Adaptive Visual Learner State

Run: `spawn-20260809T1746p0700-claycode-mvc-state`  
Trigger: `spawn`  
Origin branch: `claycode`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2` / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**

## 1. Spawn selection receipt

The canonical weighted distribution selected ClayCode through a real OS-CSPRNG draw:

- raw uint32: `3452589924`
- normalized draw: `25/100`
- ClayCode bucket: `1..50`

The first microdirection draw selected collection semantic identity, but recent ClayCode work already contained 50,000 randomized collection-identity cases and semantic-hash work, so the microdirection was rerolled under the spawn duplicate rule. The second draw selected capability/effect closure, but fresh control/effect work already covered that space heavily. The third draw selected the adaptive visual learner state contract and was accepted.

Random selection is provenance only; it does not increase evidence weight.

## 2. Research question

Can the existing ClayCode G9 semantic basis represent the complete **control-state semantics** required by FRANK v0.1 adaptive visual learning without adding a new dedicated language primitive?

The required state surface includes:

- classifier/prototype version identity;
- feature-backbone compatibility;
- GOLD/SILVER/BRONZE training-example provenance/tier;
- KNOWN_HIGH_CONFIDENCE / KNOWN_NEEDS_CONFIRMATION / AMBIGUOUS / UNKNOWN / CONFLICT outcomes;
- candidate/current/last-known-good lifecycle;
- evaluation-gated atomic promotion;
- rollback;
- bounded learner-resource state while perception remains available;
- deterministic replay hooks and exact version identity;
- separation of familiarity/confidence from sensor truth and effect authority.

This question is directly relevant to `CC-WP-02`, `CC-WP-03`, `CC-WP-04`, `CC-WP-05`, `CC-WP-11`, `CC-WP-13` and the later H1/H2 visual learner differential path.

## 3. Internal evidence and current frontier

The current project requires ClayCode BASE to express the adaptive visual learner state/update semantics but keeps the general-purpose compiler gate independent and forbids unnecessary language redesign.

Current G9 already contains generic typed records, Sets/Ordered collections, epochs/deltas, provenance, semantic hashes, explicit uncertainty/conflict concepts and a strict separation between model intent and execution authority. That makes a generic state-machine encoding plausible before inventing a dedicated learner primitive.

However the current ClayCode frontend is **not freeze-ready**. Recent branch evidence reports broad parser/identity/fuzz successes but also an unresolved strict-LALR construction blocker. Therefore this spawn run cannot convert semantic representability into normative compiler evidence and does not close `CC-WP-02` or BASE.

The Harness already treats the adaptive visual learner as mandatory in H1/H2/H3, including trust tiers, open-set behavior, shadow candidate evaluation, rollback, feature-version compatibility and bounded resources. This spawn run does not satisfy those gates; it produces a reusable semantic differential target for them.

## 4. External primary research

External literature was used only to test whether the **mechanism family** is credible, not to validate FRANK-specific performance.

1. Bär et al., CVPR 2024, *Frozen Feature Augmentation for Few-Shot Image Classification* reports strong few-shot use of lightweight classifiers on frozen pretrained visual features.  
   https://openaccess.thecvf.com/content/CVPR2024/html/Bar_Frozen_Feature_Augmentation_for_Few-Shot_Image_Classification_CVPR_2024_paper.html

2. Huang et al., CVPR 2024, *LP++: A Surprisingly Strong Linear Probe for Few-Shot CLIP* establishes a strong, efficient linear-probe adaptation family for CLIP.  
   https://openaccess.thecvf.com/content/CVPR2024/html/Huang_LP_A_Surprisingly_Strong_Linear_Probe_for_Few-Shot_CLIP_CVPR_2024_paper.html

3. Lee et al., CVPR 2026, *HyCal: A Training-Free Prototype Calibration Method for Cross-Discipline Few-Shot Class-Incremental Learning* reports prototype calibration over frozen CLIP embeddings with retention/adaptation emphasis under heterogeneous incremental learning.  
   https://openaccess.thecvf.com/content/CVPR2026/html/Lee_HyCal_A_Training-Free_Prototype_Calibration_Method_for_Cross-Discipline_Few-Shot_Class-Incremental_CVPR_2026_paper.html

4. Shao et al., CVPR 2024, *DeIL: Direct-and-Inverse CLIP for Open-World Few-Shot Learning* treats open-world few-shot recognition explicitly rather than assuming every sample belongs to a known class.  
   https://openaccess.thecvf.com/content/CVPR2024/html/Shao_DeIL_Direct-and-Inverse_CLIP_for_Open-World_Few-Shot_Learning_CVPR_2024_paper.html

These sources support trying frozen-feature/prototype/linear and explicit open-world gates. They do **not** establish FRANK's resource savings, accuracy, retention, calibration or personalization benefit; MVC-E1..E7 remain required.

## 5. Executable experiment

Artifact: `adaptive_visual_learner_semantic_proxy.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`  
Source SHA-256: `87e1d258fdc286813c88a0614033bd7c998ae453f063987fee789513e1bc1091`

The proxy models six event classes:

- observation/admission;
- resource-budget consumption;
- candidate creation;
- promotion;
- rollback;
- feature-backbone change.

It then executes:

- `1000` deterministic seeded streams;
- `100` transitions per stream;
- `100000` total replayed transitions;
- exact second-run state-sequence equality for every seed;
- targeted BRONZE, stale-backbone, UNKNOWN/AMBIGUOUS/CONFLICT, budget, promotion/LKG and rollback guards;
- four deliberate guard mutations.

Final result:

- deterministic replay: **PASS**
- BRONZE autonomous-training guard: **PASS**
- stale-backbone candidate guard: **PASS**
- UNKNOWN/AMBIGUOUS/CONFLICT preservation: **PASS**
- over-budget learning pauses while perception remains enabled: **PASS**
- promotion preserves previous current as last-known-good: **PASS**
- rollback: **PASS**
- mutation controls killed: **4/4**

Evidence class: **LOCAL_SEMANTIC_PROXY_EXECUTION**.

It is not normative ClayCode compiler evidence, not H1/H2 evidence, not live FRANK evidence and not Ubuntu target-host evidence.

## 6. Preserved negative result

`N-SPAWN-MVC-ORACLE-001` — **METHOD_NEGATIVE_RESULT**

The first reproducibility rerun encoded an over-strong stale-candidate assertion: it required candidate state to become `None` whenever a stale request was rejected. Random streams exposed the valid case where an earlier candidate already existed. The correct invariant is narrower and semantically stronger: **a rejected stale or over-budget candidate request must not change the prior candidate state**.

The oracle was repaired, the failure preserved, and the full deterministic/mutation test was rerun successfully. No scientific claim was promoted from the failed oracle.

## 7. Hypothesis result

### H-SPAWN-MVC-001 — existing G9 basis suffices

Status: `OPEN_SUPPORTED_BY_LOCAL_PROXY`.

The test did not expose a need for a new dedicated adaptive-learner primitive. The required control-state laws were representable using generic typed/versioned state transitions.

The conclusion is deliberately narrow:

> **No new ClayCode language primitive is currently justified for the MVC control-state contract.**

This is not equivalent to saying the normative G9 compiler already supports the corpus.

### Counterhypothesis still open

A real parser/typed-IR/type-effect/evaluator/lowering run may expose a semantic gap that the Python proxy cannot see, especially around atomic promotion, crash consistency, concurrent candidate updates, exact version migration or transaction/replay semantics.

That is the next discriminator.

## 8. Architecture / research delta

The most useful representation is a generic typed contract, not an MVC-specific language feature. The run therefore created:

`CLAYCODE_MVC_STATE_CANDIDATE.clay`

with records for:

- `VisualTrainingExample`;
- `VisualClassifierVersion`;
- `VisualFamiliarityResult`;
- `LearnerBudgetState`;
- `VisualLearnerState`.

The key invariants are:

- BRONZE never autonomously becomes training truth;
- learning budget failure never disables perception;
- stale feature-backbone candidates never promote;
- UNKNOWN/AMBIGUOUS/CONFLICT never get coerced into familiarity;
- promotion preserves last-known-good;
- classifier/model output never mints truth or effect authority.

## 9. Cross-branch feedback

The run wrote explicit feedback for all registered scientific branches.

Most important deltas:

- **ClayCode:** implement/compile existing typed semantics first; no language promotion.
- **FRANK:** the owner-fixed adaptive learner control state is representable at proxy level; no live claim.
- **Harness:** reuse the event corpus as H1/H2 differential oracle; add crash/restart/concurrency cases.
- **UnifiedDB:** persist exact current/candidate/LKG identity, feature-backbone compatibility, example lineage/tier, calibration/evaluation receipts and rollback history.
- **ClayGraph:** learned familiarity/prototype edges may drive relevance/activation but never upgrade sensor truth; backbone-version invalidation must propagate.
- **GWT:** learned familiarity is a routing input, not workspace truth; causal-use/outcome/re-entry receipts remain required for claimed system benefit.
- **Emergenz:** no change; deterministic learner execution is not emergence evidence.

See `BRANCH_FEEDBACK_MANIFEST.json` and `INTERCONNECT_MANIFEST.json`.

## 10. Durable work handoff

Because normative compiler and Ubuntu H1/H2 execution are outside this worker's current executable surface, the exact next action was written into the dynamic work fabric:

`research_entity/state/work/events/work_revise_cc_base_mvc_state_20260809T1746p0700.json`

It revises `WORK-CC-BASE-G9-PARSER-FREEZE-001` to add the MVC corpus to the normative parser -> canonical typed IR -> type/effect -> evaluator/lowering conformance path and later Ubuntu H1/H2 differential replay.

## 11. Claim-state changes

- No canonical scientific claim promoted.
- `H-SPAWN-MVC-001` opened with local-proxy support.
- `H-SPAWN-MVC-002..004` remain OPEN.
- `CH-SPAWN-MVC-001..003` remain OPEN.
- `N-SPAWN-MVC-ORACLE-001` preserved as NEGATIVE_RESULT.
- BASE / `CC-WP-02` remain not passed.

## 12. Final synthesis

This spawn run did not discover that ClayCode needs more semantics. It found the opposite, provisionally: **the adaptive visual learner requirement is a good stress test for the existing generic typed state machinery, and the highest-information next step is compilation, not language invention.**

The decisive next experiment is now concrete:

`MVC typed corpus -> normative parser -> canonical typed IR -> type/effect -> evaluator/lowering -> deterministic transition + mutation replay -> Ubuntu H1/H2 differential`

A failure there can justify a semantic change. Until then, the project law remains:

`less change -> more compile -> execute -> falsify`
