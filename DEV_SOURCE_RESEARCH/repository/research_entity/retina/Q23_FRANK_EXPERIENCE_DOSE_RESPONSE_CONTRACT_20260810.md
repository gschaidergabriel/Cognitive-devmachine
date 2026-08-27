# Q23 Frank Experience Dose-Response Contract — 2026-08-10

**Status:** MANDATORY TEST CONTRACT FOR MEMORY-BENEFIT CLAIMS / NOT AN ARCHITECTURE PROMOTION  
**Scope:** QNDRF, PAR-1, Retina/Qwen/MVC, UnifiedDB/EAP, Frank 4B.

## 1. Core requirement

Any q23 experiment claiming that Frank benefits from prior experience MUST distinguish:

- `E0_NO_FRANK_EXPERIENCE`: Frank has no admissible target-relevant episodic experience for the held-out task/entity/state;
- `E>0_FRANK_EXPERIENCE`: Frank has provenance-bound prior experience available through its memory substrate;
- increasing experience dose `N` so the experiment measures when benefit first appears, how it grows, when it saturates and whether excess/conflicting experience becomes harmful.

Qwen pretrained knowledge is NOT counted as Frank experience. It remains constant across conditions.

## 2. What counts as one experience data point

One experience data point is one independent provenance-bound Frank episode containing, at minimum:

- episode id and time;
- observed visual evidence / frame or ROI identity;
- relevant entity/state refs when known;
- task/context;
- action or interpretation where applicable;
- observed outcome / verification;
- source/model/mmproj/feature-version identity where relevant;
- UnifiedDB epoch/hash and memory provenance.

Multiple near-identical frames from one uninterrupted episode do NOT count as multiple independent experience points. Repeated samples with shared ancestry must be grouped so the dose axis is not inflated by correlated duplicates.

## 3. Mandatory dose ladder

Default nested experience doses:

`N = {0, 1, 2, 4, 8, 16, 32, 64}`

If the effect is still rising at 64 and more independent data exist, continue geometrically (`128, 256, ...`) while useful. If the effect saturates early, keep later points as confirmation/saturation controls when affordable.

Each larger dose must contain the smaller-dose evidence plus additional independently sourced episodes, or use a matched stratified resampling design that preserves comparability.

## 4. Experience classes

Run the dose ladder separately for at least these regimes where fixtures permit:

1. `EXACT_RECURRENCE`: same entity/state/task family seen before;
2. `STATE_VARIANT`: same entity but changed state/layout/context;
3. `RELATIONAL_TRANSFER`: different current percept whose relevant memory is connected through UnifiedDB/EAP relations;
4. `NOVEL_ENTITY`: no target-specific prior experience; memory should not fabricate familiarity;
5. `CONFLICTING_EXPERIENCE`: prior episodes contain stale/contradictory outcomes;
6. `IRRELEVANT_SHAM_EXPERIENCE`: matched memory volume with unrelated episodes, controlling for cache/database size and generic priming.

## 5. Mandatory system variants at every dose

At each `N`, compare at minimum:

- `QWEN_ONLY`: no Frank episodic memory supplied;
- `DIRECT_MEMORY_N`: admissible experience available through the simplest exact/FTS/direct path;
- `PAR_EAP_N`: same experience corpus available through visual-seed -> UnifiedDB/EAP ActiveAssembly;
- `PAR_ACTIVE_N`: EAP may guide active sensing but cannot override sensor evidence;
- `SHAM_N`: same number/size of irrelevant experience records;
- fault lanes where applicable: wrong high-confidence seed, stale epoch/hash, shuffled graph, contradictory memory.

The no-experience lane must still use the same Qwen model/runtime and general Frank machinery; only target-relevant Frank episodic experience is removed.

## 6. Required learning/effect curves

For every primary metric report the curve over N, not only endpoint means.

Primary outcome vector:

- task/action correctness;
- wrong-action rate;
- sensor->correct-decision p50/p95/p99;
- visual + text token cost per correct decision;
- relevant-memory precision/recall;
- false familiarity / unknown rejection;
- memory-induced sensor override / confirmation error;
- GWT false ignition where measured;
- CPU/RAM/VRAM/cache cost.

Also report:

- `Delta(N) = metric_with_experience(N) - matched_E0_or_QWEN_ONLY` in the appropriate benefit direction;
- dose-response monotonicity/non-monotonicity;
- between-seed / between-episode variance;
- cold/warm cache separation.

## 7. Effect onset and saturation

Do not hard-code a presumed useful sample count.

Estimate:

- `N_onset`: smallest tested N at which the memory-enabled path shows a reproducible net benefit over the matched no-experience lane on the preregistered primary outcome, without violating safety/error tolerances;
- `N_robust`: smallest N where that benefit remains present across independent seeds/episode orderings and relevant fixture classes;
- `N_90`: smallest N reaching at least 90% of the best observed asymptotic/plateau benefit when a stable plateau can be estimated;
- `N_harm`: smallest N where additional experience increases stale/conflicting-memory failures or total cost enough to reverse net benefit.

Use confidence intervals/resampling across independent episodes/seeds. A single favorable run is not an onset. If intervals remain inconclusive, report `N_onset > max_tested_N` rather than inventing a threshold.

## 8. Net-effect requirement

A memory effect does not count merely because retrieval accuracy improves.

Promotion-relevant benefit requires a positive end-to-end tradeoff including:

`perception + seed resolution + retrieval/EAP + prompt/context attention + reasoning/decode + action/outcome`

and must preserve or improve correctness/safety.

The experiment must therefore distinguish:

- retrieval benefit;
- decoder/reasoning benefit;
- latency/token/resource cost;
- confirmation-bias harm.

## 9. Strongest counterhypotheses

1. `NO_DOSE_EFFECT`: Qwen already solves the task; Frank experience adds no measurable benefit at any practical N.
2. `THRESHOLD_TOO_HIGH`: benefit exists only after more independent experience than Frank can realistically accumulate for that class.
3. `EARLY_OVERFIT`: small N improves exact recurrence but harms state variants/novel cases through false familiarity.
4. `MEMORY_VOLUME_CONFOUND`: apparent gain comes from generic extra context/cache warming rather than relevant experience; SHAM_N should expose this.
5. `EAP_NOT_CAUSAL`: direct memory at the same N performs equally or better; EAP adds no causal value.
6. `NONMONOTONIC_CONFLICT`: benefit rises then degrades as stale/conflicting episodes accumulate.

## 10. Promotion boundary

No claim that PAR/QNDRF "uses Frank's experience" may be promoted without the E0-vs-E>0 separation and a measured dose-response curve.

A valid conclusion may be:

- `NO_EFFECT_WITHIN_TESTED_RANGE`;
- `EFFECT_ONSET_AT_N≈...`;
- `BENEFIT_ONLY_FOR_EXACT_RECURRENCE`;
- `BENEFIT_REQUIRES_EAP`;
- `DIRECT_MEMORY_DOMINATES_EAP`;
- `NONMONOTONIC / HARM_AFTER_N`;
- `INSUFFICIENT_INDEPENDENT_DATA`.

The architecture must follow the measured curve rather than assuming that more memory is always better.
