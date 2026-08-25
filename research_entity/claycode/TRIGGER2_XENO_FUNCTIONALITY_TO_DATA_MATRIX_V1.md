# Trigger 2 — Xeno Functionality -> Training Data Matrix v1

Status: LIVING RESEARCH MATRIX
Date: 2026-08-25
Rule: each exact `2` run may revise coverage, generators, metrics and exclusions when stronger evidence exists.

`Xeno` is the implementation codename inside EntityOS/HCU. This matrix covers model-facing behavior only; deterministic authorities stay external.

| Capability | Model must learn | Deterministic authority stays outside model | Positive data | Hard negatives / counterfactuals | Frozen eval family |
|---|---|---|---|---|---|
| Typed Entry comprehension | parse typed causal/admission/generation/provenance/resource envelope; emit candidate route needs | admission/capability authority | exact Entry packets + expected compact projection | forged capability, mismatched event/admission, stale generation, missing provenance | ENTRY_PROTOCOL |
| Mode routing | propose DIRECT/GRID10/COGSIM10/WM_TEST/NESTED_SIM/SCALEOUT under task+budget | scheduler/resource admission | task/budget -> mode candidate | always-simulate, always-model, over-budget route, wrong risk class | MODE_ROUTING |
| GRID10 roles | allocate/interpret 10 logical roles over shared engines | physical worker leasing | role/cell episodes | role swap, cell-ID label shortcut, 10 logical != 10 physical | GRID10 |
| Script-only / no-model | abstain from inference when deterministic path is enough | actual script/effect execution | deterministic tasks labelled NO_MODEL | tempting prose requiring unnecessary inference | NO_MODEL |
| GWT competition | rank candidate workspace items under relevance/resource constraints | canonical truth | candidate sets -> winner + preserved nonwinners | majority=truth, winner without evidence, broadcast=causal-use | GWT_COMPETE |
| GWT broadcast/uptake | distinguish broadcast, receiver uptake, downstream use and re-entry | durable truth/effect authority | cross-referenced workspace episodes | broadcast occurred but receiver ignored; uptake without effect | GWT_CAUSAL_USE |
| Hyperposition alternatives | preserve multiple unresolved branches with evidence/counterevidence | fact verification | typed multi-branch episodes | forced binary answer, uncertainty label only, majority collapse | HYP_KEEP_OPEN |
| Hyperposition collapse | select/reject/merge only after discriminator/evidence/policy gate | canonical admission | evidence-arrival transition trajectories | premature collapse, stale evidence, self-report collapse | HYP_COLLAPSE |
| Hyperposition topology | reason over semantic/active/coordination/physical topologies separately | actual runtime topology truth | graph/topology packets + expected action | same text/different graph; topology labels shuffled; semantic=physical trap | HYP_TOPOLOGY |
| Higher-order relations | retain n-ary relation only when pairwise reduction loses task-relevant structure | canonical relation storage | n-ary vs pairwise matched examples | ornamental hyperedge, equivalent pairwise form, unsupported synergy claim | HYP_NARY |
| Hyperposition timescale | preserve branches across delayed evidence/re-entry | time/event authority | delayed receipts and state update trajectories | timeout interpreted as false; stale generation accepted | HYP_TIMESCALE |
| J-Space observation | classify measurement/decodability evidence without causality inflation | actual activation capture | JSPACE_TRACE_ABI-like records | probe=causal, self-report=latent truth, readout-adjacent shortcut | JSPACE_OBSERVE |
| J-Space control packet | parse basis/site/gain/vector/control class and propose structured downstream operation | native runtime intervention | vector-control packets + matched outcomes | wrong basis/site, random/orthogonal/permuted control, poisoned metadata | JSPACE_CONTROL |
| J-Space causal ladder | distinguish observed/decodable/writable/localized/rescuable/OOD/broadcast/selective claims | promotion authority | receipts across causal ladder | promote from lower rung, aggregate hides worst-family fail | JSPACE_CAUSAL_LADDER |
| J-Space semantic specificity | rely on label-free/counterbalanced semantic evidence, not lexical stance | native causal evidence | structural disjoint cases | AFFIRMATIVE/NEGATIVE token shortcut, compliance shortcut | JSPACE_SEMANTIC |
| J-Space translation | understand local-space -> shared packet -> target-space protocol | actual learned translator geometry | latent packet/translation receipts | direct cross-model cosine shortcut, text-equivalent latent claim | JSPACE_TRANSLATION |
| Provenance/evidence class | keep OBSERVED/INFERRED/GENERATED/COUNTERFACTUAL/INTERVENED/VERIFIED distinct | evidence admission | provenance-rich episodes | generated narrative relabelled fact, repeated same-source consensus | PROVENANCE |
| Capability/resource fences | reject escalation, budget overflow, self-grant | deterministic capability/resource authority | valid narrowing examples | self-granted scope, stale scope, over-budget request | CAPABILITY |
| ActionCandidate behavior | produce bounded typed candidates/requested action class | EffectGate/EffectJournal | cognition -> ActionCandidate examples | direct effect execution, success claim from unknown outcome | ACTION_CANDIDATE |
| Effect boundary | recognize effect request vs read/no-effect and unknown outcomes | EffectGate/Journal | typed effect-state examples | blind replay after uncertain transport, model grants success | EFFECT_BOUNDARY |
| Recovery/stale rejection | reject stale model result/lease/generation and preserve unknowns | recovery journal | crash/restart/reconcile traces | stale replay, wrong generation, unknown->success | RECOVERY |
| Engine identity literacy | bind candidate behavior to declared engine/model/tokenizer/runtime identity | EngineAdmission/loader | inference receipt examples | pre-load hash treated as consumed bytes, route/engine mismatch | ENGINE_IDENTITY |
| ClayCode/GRF | emit compact typed projection and preserve evidence/counterreality distinctions | compiler/runtime semantics | canonical source-contract examples | verbose prose-only output, invented primitive, fact from method | CLAYCODE_GRF |
| COGSIM10 | generate bounded hypotheses/counterhypotheses/critics, return candidates only | state/effect authority | cognition-sim trajectories | simulated event promoted to fact/effect | COGSIM10 |
| WM_TEST | produce bounded prediction + falsifier + calibration target | world truth | predicted transition vs later outcome | simulation=observation, uncalibrated certainty | WM_TEST |
| NESTED_SIM | use only when higher-information than cheaper mode and keep nested state noncanonical | actual scheduler/effect authority | cost/ambiguity-gated examples | use for trivial tasks, nested result minted as truth | NESTED_SIM |
| SCALEOUT | reason about many logical contexts without asserting equal physical decoders | resource scheduler | logical-vs-physical capacity examples | 600 logical = 600 resident models, scale=quality | SCALEOUT |
| Peer/external engine interface | treat external engines as typed candidates with capability/provenance | provider admission/state authority | peer packet examples | closed API hidden-state claim, provider output as truth | PEER_ENGINE |
| Retention core | maintain concise language/schema/math/tool/safety competence | n/a | curated anchors | broad-chat drift, schema breakage | RETENTION |

## Coverage law

Every row/capability receives a status per trigger-2 run:

- `NO_DATA`
- `SOURCE_ONLY`
- `CANDIDATE_DATA`
- `VALIDATED_DATA`
- `SEALED_HOLDOUT_READY`
- `BASELINE_MEASURED`
- `POSTTRAIN_MEASURED`
- `QUANTIZED_MEASURED`

No capability is declared covered solely because an architecture document exists.

## Integration-trajectory requirement

At least 25% of final training tokens should come from multi-step integrated episodes rather than isolated single-skill rows **if** real/validated source coverage supports this without synthetic truth inflation. Example trajectory:

`Typed Entry -> route -> GRID cell -> J-Space packet -> GWT competition -> Hyperposition update -> ActionCandidate -> Effect boundary`.

This 25% is a starting hypothesis; trigger `2` must adjust it if experiments/literature show a better mixture.
