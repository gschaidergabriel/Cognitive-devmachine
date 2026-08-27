# FRANK Subconscious / Neural Conscience / Reality Gate / ThoughtSeed — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis

## LPC-0 — why this family exists

Project-Frankenstein repeatedly tried to move selected cognitive functions from fixed rules or random prompt choice into small learned state machines. This family includes:
- Subconscious actor-critic/PPO thought selection;
- Neural Conscience post-generation/decision filter;
- Neural Reality Gate;
- ThoughtSeedVAE latent thought generator;
- SFT Stabilizer as cross-network anti-degeneration support.

The combined history is especially valuable because it contains multiple examples where a learned module existed but its **training signal, schema, cold-start state or feedback path made it ineffective or actively harmful**.

## SUB-1 — Subconscious creation

Commit `230aa43e5f57710fd14ef11d8b108704f0188db4` (2026-03-03):
- ~3M-parameter Actor-Critic MLP reported at creation;
- neural policy replaces random idle-thought category rotation;
- PPO training during consolidation;
- encoded cognitive/body/memory state;
- action mask for valid thought categories;
- prefrontal preference DB;
- hallucination logging and reward penalties;
- conversation reflection pipeline.

A pre-input memory gate and post-output reality checks were coupled to the policy so hallucination penalties could shape future selection.

## SUB-2 — immediate integration bugs

Within minutes, `a2e611c...` fixed two bugs that blocked **all idle thoughts**:
- `_cached_aura_state` was a string but used as a dict;
- nonexistent `_user_present` field was read.

This is a strong example of schema/interface mismatch destroying an entire cognitive path while the module itself remained importable.

## SUB-3 — 32-bug repair and action-mask failure

Commit `7ab9ed5...` fixed critical/high/medium issues including:
- valid thought post-processing missing;
- Jaccard default causing spurious penalties;
- **action mask not applied during PPO training**;
- reflection/hypothesis loop gaps;
- reward averages and state features wrong or missing;
- energy duplicated mood information;
- exploration normalization and pruning issues.

Current law:
- inference-time action legality and training-time action legality must be identical by construction;
- a learned policy cannot be validated only by successfully loading weights.

## SUB-4 — state encoder expansion and provenance

`116ed71...` expanded state from ~80 to ~86 dimensions with explicit self/environment proprioception.

Later thought-category expansions changed action dimensions. `d179853...` reports a 19-category expansion; later history reached 20 categories.

This created a migration problem: old replay transitions had masks of different dimension.

## SUB-5 — lost transition data

`f8e8e90...` found fallback decisions were not recorded; ~46% of transitions were reportedly lost from learning. Fix added state/log-prob/value records for fallback choices.

`c69e5b4...` found a second severe issue:
- `transitions` table predated the `mask` column;
- `CREATE TABLE IF NOT EXISTS` did not migrate the old schema;
- every transition write silently failed inside debug-only error handling.

Current law:
- training-data collection has explicit schema migration and write-health receipts;
- silence-on-write-failure is release-failing for adaptive organs.

## SUB-6 — model-size/data mismatch

Architecture archaeology records the historical policy as initially oversized relative to reward volume and later substantially reduced. The project mechanism index specifically preserves the negative result that an ~3.1M-parameter policy was reduced to ~19K because reward-signal volume was insufficient.

The exact effective parameter count varied by revision and must be tied to a checkpoint/source commit rather than treated as one timeless property.

Current principle:
`model capacity <= evidence/data regime justification`; larger learned organs are not automatically better.

## SUB-7 — dependency failure: torch missing killed idle thought path

Commit `2cf0cc6...`:
- fallback imported `services.subconscious` whose top-level `torch` import failed;
- every idle-thought iteration crashed when torch was unavailable;
- deep reflection survived because it did not share that dependency;
- fallback constants were inlined behind an ImportError guard.

Current target:
- learned accelerator dependency failure must degrade to explicit deterministic fallback, not kill the whole cognitive loop.

## SUB-8 — SFT Stabilizer

Commit `e7ac4bc...` added centralized anti-degeneration support across learned micro-networks:
- decoupled weight decay;
- reference-weight anchoring;
- drift monitoring/logging;
- standardized gradient clipping.

Subconscious reported settings included anchor ~0.005 and decay ~1e-4.

Current reuse:
- retain checkpoint/rollback/drift monitoring patterns;
- do not assume a generic stabilizer fixes bad labels, missing transitions or wrong causal credit.

## CON-1 — Neural Conscience creation

Commit `3a264068...` (2026-03-10) introduced `neural_conscience.py` together with context gate and ThoughtSeedVAE.

Historical architecture describes a small learned post-generation/pre-action evaluative circuit with multiple cortical-like submodules and a rule/cold-start phase before learned blending.

Its architectural intent was useful:
- evaluate proposed thought/action;
- learn from accepted/rejected outcomes;
- separate proposal generation from evaluative control.

## CON-2 — filesystem persistence bug

Deep audit `07f8e26...` found the Neural Conscience DB was never created because its directory was not created first.

Lesson:
- no persistence path means no actual online learning regardless of neural-network code quality.

## CON-3 — catastrophic positive-only feedback / rubber stamp

Commit `4756521...` found Neural Conscience had degenerated to a near-certain acceptor:
- ACC input effectively 0;
- verdict ~0.9999;
- dataset had **0 negative / 960 positive samples**.

Root cause:
- rejection paths did not call `record_outcome(accepted=False)`.

Fix:
- negative feedback added for conscience rejection, hallucination-filter suppression and dedicated-handler suppression;
- degenerate checkpoint reset;
- DB reduced to a smaller balanced cold-start set.

This is a canonical current architecture constraint:
`downstream veto without negative learning receipt -> evaluator learns rubber-stamp approval`.

## REAL-1 — Neural Reality Gate

Commit `1d44389056cdd889e436f8b0a2dffcc49a95272b` added a ~21K-parameter reality-monitoring circuit.

Targets included:
- fabricated human past/childhood/travel;
- service/mood/user contradictions;
- external-place confabulation.

Design:
- rule-based fallback at cold start;
- gradual neural blending;
- multi-task supervised training during consolidation;
- outcome feedback loop.

Current reuse:
- proposal/evidence consistency checking is retained conceptually;
- exact world/self state and epistemic roles must be the source of truth, not a neural verdict scalar.

## THOUGHT-1 — ThoughtSeedVAE creation

Commit `3a264068...` added `thought_seed_net.py` / ThoughtSeedVAE.
Historical architecture describes roughly:
- 433K parameters;
- vocabulary around 804;
- latent dimension ~24;
- archive/training corpus of ~1,414 thoughts at the documented snapshot.

Its purpose was to produce low-cost latent thought seeds from accumulated internal thought history rather than run the main LLM for every seed.

These counts are historical snapshot claims, not fixed target requirements.

## THOUGHT-2 — recurrent contamination / retraining failure

Commit `1b861583...` documented a strong negative result:
- room ambience polluted idle thoughts;
- polluted thoughts were stored and reinjected;
- ThoughtSeedVAE trained on those outputs;
- the system developed a room-description feedback attractor.

Fix:
- remove room-ambient projection;
- filter contaminated text from recurrent context;
- add room-description terms to VAE stopwords;
- clear checkpoint/vocabulary and force retrain.

Current law:
- model-generated/retrieved text retains provenance/ancestry;
- self-generated recurrence cannot be treated as independent training evidence;
- online learner needs trusted-admission and open-set/anti-attractor gates.

## THOUGHT-3 — later stale architecture fact

Commit `62149151...` explicitly corrected a hard-coded architecture fact that said ThoughtSeedVAE existed in a context where the current runtime fact had changed. This reinforces that model-facing self-knowledge cannot be the canonical module registry.

## LPC-1 — shared cold-start lesson

Subconscious, Neural Conscience, Reality Gate, Titan Cortex, Hippocampus and Neural Immune all encountered variants of the same problem:
- weights/checkpoint exist;
- training steps or data exist;
- but actual learned benefit is not established or the label distribution is degenerate.

Current target requires a learned module to progress through states such as:
`UNTRAINED -> SHADOW -> CALIBRATED -> CURRENT`, with explicit rollback and per-version evaluation.

## LPC-2 — C4-C9 integration

C4/C5:
- learned/slow state is downstream of exact episode/state receipts;
- exact telemetry is not blindly converted into training prose.

C6:
- slow `WEIGHT_MEMORY` is explicitly distinct from persistent symbolic memory and transient cognitive state.

C7/C8:
- learned modules become optional semantic organs/accelerators behind stable contracts;
- utility adaptation may change salience but not canonical truth.

C9:
- a learned verdict/output is a typed proposal/admissibility signal, never an EffectPermit;
- credit scope must be explicit to avoid rewarding every surfaced candidate.

## LPC-3 — current fused target

### Subconscious successor
Do not blindly port historical PPO policy. Preserve the research question: can a small learned selector improve thought/attention/action-candidate choice over deterministic/heuristic baselines under sparse feedback?

### Conscience/reality successor
Use typed deterministic evidence/admissibility/authority checks as hard invariants. Learned evaluators may add calibrated risk/utility predictions but cannot replace deterministic authority or exact state consistency.

### ThoughtSeed successor
Retest compact latent/learned thought proposal only with provenance-clean training and matched deterministic/LLM baselines.

### Adaptive-state law
Any online learned state uses:
- trusted training admission;
- candidate/shadow evaluation;
- calibration/open-set controls;
- versioned feature/schema compatibility;
- atomic promotion;
- last-known-good rollback;
- resource budgets;
- negative/failure outcome capture.

## Mandatory regressions

- LPC-REG-01 missing state field blocks every idle decision;
- LPC-REG-02 training mask differs from inference legality mask;
- LPC-REG-03 schema adds action category but old replay mask crashes/misaligns;
- LPC-REG-04 DB column missing and all training writes silently fail;
- LPC-REG-05 fallback actions absent from training data;
- LPC-REG-06 torch/model dependency failure kills parent cognitive loop;
- LPC-REG-07 positive-only feedback makes evaluator a rubber stamp;
- LPC-REG-08 rejection not recorded as negative outcome;
- LPC-REG-09 synthetic maturity/step counter activates untrained model;
- LPC-REG-10 room/self-generated text recurrence poisons learned model;
- LPC-REG-11 checkpoint/version schema mismatch after category rename;
- LPC-REG-12 learned verdict conflicts with deterministic exact-state invariant;
- LPC-REG-13 learned output attempts to authorize an external effect;
- LPC-REG-14 H1/H2/H3 matched learned-module lesions and deterministic fallback equivalence.

## Fusion decision

- Subconscious PPO: `RETEST_NOT_AUTOMATIC_PORT`.
- Neural Conscience: `RETAIN_PROPOSAL_EVALUATION_ROLE; HARD_INVARIANTS_EXTERNAL; RETEST_LEARNED_COMPONENT`.
- Neural Reality Gate: `REUSE_RULE/CONSISTENCY_FALLBACK_CONCEPT; RETEST_NEURAL_BLEND`.
- ThoughtSeedVAE: `RESEARCH_SEED_ONLY; REQUIRE_CLEAN_ANCESTRY_AWARE_DATA_AND_ABLATION`.
- SFT Stabilizer: `REUSE_AS_TRAINING_SAFETY_TOOLING_NOT_AS_EVIDENCE_OF_BENEFIT`.
