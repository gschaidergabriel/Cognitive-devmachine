# FRANK Genesis / Hypothesis Engine / Experiment Lab — deep evolution lineage

Run: `fusion-20260809T1538p0700-frank-architecture-lineage`
Status: archaeology + current target synthesis

## GHE-0 — separate two ideas that history later disentangled

Early FRANK grouped several forms of self-improvement/research under one broad autonomy narrative. History eventually separated:
1. **Genesis** — evolutionary self-improvement/proposal organism;
2. **Hypothesis Engine** — explicit observe -> hypothesize -> predict -> test cycle;
3. **Experiment Lab** — constrained simulation/execution stations;
4. autonomous research/tool use.

Genesis became a major negative result and was disabled. Hypothesis Engine and Experiment Lab survived. The current architecture must preserve that distinction.

## GEN-1 — Genesis existed at first public baseline

Initial public commit `e1a8812767668091d146ee958bbc2ebb2743031c` already described self-improvement via a Genesis daemon, with ASRS/invariants as safety systems.

Historical documented Genesis concepts later included:
- primordial soup of `IdeaGenome` organisms;
- motivational/emotional field;
- mutation/reproduction/fusion;
- crystallization;
- manifestation gate;
- F.A.S. approval;
- code/config/prompt/personality proposal types.

The architecture is project-specific composition, not proof that evolutionary dynamics improve software.

## GEN-2 — personality/prompt modification bridge

Commit `f2cb391...` allowed Genesis crystals to propose:
- E-PQ vector adjustment;
- non-core prompt evolution.

F.A.S. approval and backups/rollback were added; core identity was intended to remain protected.

This is an early precursor of proposal-vs-authority separation, but the current architecture strengthens it: FRANK may formulate an improvement proposal, but may not mutate its own Harness/authority boundary.

## GEN-3 — generic proposal failure

`adfa1bb...` found Genesis suggestions were generic because random exploration seeds had no concrete code evidence. Fix propagated file/check/detail metadata from CodeAnalyzer and tightened dedup/specificity.

Lesson:
- generative novelty without grounded evidence yields low-value proposals;
- current proposal objects must cite exact evidence/source/basis.

## GEN-4 — no selection pressure / evolutionary paradise

Commit `6d9130b...` reports a major mechanism failure:
- all emotions saturated around 1.0;
- average energy ~142k;
- 8.9M births with 0 deaths;
- 100 mature organisms but 0 useful proposals;
- no selection pressure -> no meaningful evolution/crystallization.

Fixes introduced:
- energy caps;
- senescence;
- metabolism/reproduction costs;
- starvation/death;
- periodic culling;
- lower crystallization threshold;
- saturation dampening.

A 2k-tick simulation reportedly then produced 470 deaths and 9 crystals.

Current lesson:
- open-ended self-improvement metrics require negative pressure/cost and quality outcomes;
- internal population dynamics are not themselves software-quality evidence.

## GEN-5 — noisy sensors create fake evolution

`d3f1030...` added noise filters because GTK warnings, systemctl spam, removed-code errors and deprecations became fix organisms/proposals.

`2dc02b0...` further fixed Genesis scanning old log history from file start on every restart; sensor now seeks EOF for new events, persistent dedup added, and specificity/quality gates were strengthened.

Current law:
`observed log line != current defect != actionable proposal`.
Sensor freshness, source and dedup identity are part of the causal contract.

## GEN-6 — crash-loop / watchdog coupling

`2dc02b0...` reports Genesis crashed 18x/hour because sensors could block >30s while systemd watchdog expected heartbeats within 120s. Fix pets watchdog around long sensors/ticks.

Current principle:
- long model/tool work must not share liveness assumptions with fast health loops;
- process watchdog success is still not cognitive usefulness.

## GEN-7 — metadata inheritance and monoculture

`1bb9854...` propagated metric/evidence metadata.
`6925e57...` then found mutated/reproduced organisms lost metadata, leaving 0% evidence coverage and blocking crystallization.

Same commit added:
- monoculture penalty when one approach dominates >40%;
- fusion preference for same target/different approach;
- looser but evidence-aware gate.

Current analogue:
- proposal ancestry/provenance must survive mutation/composition;
- diversity controls prevent frequent-attractor monoculture but do not prove quality.

## GEN-8 — self-authored proposals and rewards

`fcc7319...` added full self-authored proposal flow and room proposals. It also fixed NAc reward channels that had been firing into no reachable targets.

Current correction:
- self-authored proposal can be cognitively useful;
- self-approval/self-reward is not independent validation;
- external owner/harness/evidence gate remains authoritative.

## GEN-9 — proposal quality collapse

Commit `e267121...` is decisive:
- disabled CodeAnalyzer->Frank review pipeline;
- moved remaining proposal generation to stronger RLM;
- fixed placeholder/preamble leakage;
- **purged 119 old proposals, described as all garbage**;
- added explicit experimental warning.

This is a strong failed-negative for automatic software self-improvement under the then-current model/coupling.

## GEN-10 — Genesis disabled

Commit `113bc080a317d39e32836e707d002f8b7161ddd2` (2026-03-20):
- all 31 Genesis files preserved but execution disabled;
- six consciousness Genesis functions stubbed;
- services/watchdog stopped and disabled;
- UI/proposal routes removed;
- Swarm topology removed Genesis nodes/edges;
- reason: reduce cognitive load; capable-enough base model was not available.

Experiment Lab and Hypothesis Engine explicitly remained active.

Current reuse decision:
`GENESIS_EXECUTION = REJECT/ARCHIVE_AS_NEGATIVE_RESULT`.
Mechanism ideas such as proposal ancestry, evidence metadata, diversity and external approval are reusable independently.

## HYP-1 — Hypothesis Engine creation

Commit `9c1e034...` (2026-03-02):
- empirical loop: `observe -> hypothesize -> predict -> test`;
- regex/rule-based synthesis;
- passive and active evaluation;
- Genesis sensor integration;
- Experiment Lab connection.

Later relational domain (`230aa43...`) added quality filtering over conversation-derived hypotheses.

The engine is architecturally important because it separates a hypothesis from an observation/result instead of letting model text directly become belief.

## HYP-2 — parse/evaluation failure

Deep audit `07f8e26...` reports **158 hypothesis experiment parse failures**. Fix added station templates and fallback parsing.

Current lesson:
- natural-language experiment request -> executable test is a compiler/lowering boundary;
- parse success and scientific validity are separate;
- structured experiment IR and translation-validation receipts are required.

## HYP-3 — resolved results become later cognition

`3277107...` added `get_recent_resolved()` and injected specific confirmed/refuted hypotheses into later thought, with experiment discoveries similarly exposed.

Current correction:
- resolved status, evidence and summary remain distinct objects;
- re-entry can affect later cognition but must carry exact experiment/result identity.

## HYP-4 — stale hypotheses need decay

`279eb175...` added passive confidence decay for stale hypotheses.

Current target generalizes this to temporal validity and contradiction-preserving hypothesis state rather than a single confidence scalar.

## HYP-5 — contamination from recurrent room text

`083ba1a...` archived room-contaminated active hypotheses after room-aesthetic text had entered topic interests and recurring cognition.

Current anti-echo law applies:
- model-derived thematic recurrence does not become independent evidence for a hypothesis.

## EXP-1 — Experiment Lab creation

`9c1e034...` introduced six stations:
- physics;
- chemistry;
- astronomy;
- Game of Life;
- mathematics;
- electronics;
with daily budgets.

This was intended as a constrained test substrate for hypotheses rather than unrestricted shell execution.

## EXP-2 — experiment results into memory

`809f0d6...` added Experiment Lab API and extracted one-sentence findings into Titan for later retrieval.

Current architecture preserves the loop but separates:
`raw fixture/config -> execution receipt -> measured result -> interpretation -> memory projection`.

## EXP-3 — station/template expansion

`60f97a2...` expanded station types and synthesis/visualization. The earlier 158 parse failures show that station coverage and parser robustness must be explicit conformance tests.

## GHE-1 — relation to current RAE research center

The current RAE research center inherits the useful part of the old hypothesis/experiment architecture but changes evidence governance:
- branch-specific specialists;
- machine-readable hypotheses/counterhypotheses/falsifiers;
- anti-echo ancestry correction;
- actual execution receipts;
- no consensus-based truth promotion;
- Harness interventions/Golden Traces.

This is a direct evolutionary successor rather than a literal port of the old Hypothesis Engine.

## GHE-2 — current fused target

### Hypothesis object
Must carry:
- claim;
- counterhypothesis;
- source evidence refs;
- ancestry;
- predicted observations;
- falsifier;
- experiment requirements;
- status/temporal validity.

### Experiment object
Must carry:
- fixture/input identities;
- executable semantics;
- seed/environment/version;
- intervention/lesion/control arm;
- measurements;
- result/evidence class;
- failure/parse/timeout state.

### Proposal object
Architecture/harness improvement may be proposed by FRANK, but execution belongs to separate research/harness authority. No model-generated proposal mints permission.

## Mandatory regressions

- GHE-REG-01 old log lines repeatedly become new defects/proposals;
- GHE-REG-02 generic proposal without concrete evidence passes quality gate;
- GHE-REG-03 organism/proposal mutation loses evidence metadata;
- GHE-REG-04 all internal population survives/saturates and produces no selection;
- GHE-REG-05 one approach becomes monoculture;
- GHE-REG-06 watchdog/liveness killed by long sensor/model work;
- GHE-REG-07 LLM placeholder/preamble parsed as actual proposal fields;
- GHE-REG-08 natural-language experiment parse silently changes requested test;
- GHE-REG-09 experiment result summary overwrites raw evidence;
- GHE-REG-10 contaminated self-generated topic creates hypotheses;
- GHE-REG-11 self-authored proposal self-rewards/self-approves;
- GHE-REG-12 disabled Genesis code accidentally re-enters current runtime;
- GHE-REG-13 H1/H2/H3 hypothesis/experiment trace equivalence.

## Fusion decision

- Genesis: `ARCHIVE_EXECUTION / REUSE_SELECTED_META-PRINCIPLES / DO_NOT_REACTIVATE_AS_CURRENT_SELF-MODIFIER`.
- Hypothesis Engine: `REUSE_CORE_EPISTEMIC_CYCLE; REBUILD_AS_TYPED_EVIDENCE_OBJECTS`.
- Experiment Lab: `REUSE_CONSTRAINED_TEST_SUBSTRATE_IDEA; EXPAND_IN_HARNESS_WITH_DETERMINISTIC_FIXTURES`.
