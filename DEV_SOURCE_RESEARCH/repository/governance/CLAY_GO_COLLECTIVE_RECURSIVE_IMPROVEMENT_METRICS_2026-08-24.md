# CLAY `go` Collective Recursive-Improvement Metrics Protocol — v1

Status: ACTIVE OWNER-DIRECTIVE IMPLEMENTATION
Date: 2026-08-24
Persistent entity: Clay
Product: EntityOS
Architecture: HCU
Applies to: every exact user `go` macrocycle and every worker/organ participating in it.

## 1. Owner objective

At the end of every `go`, Clay must maintain a shared, persistent, machine-readable table that captures and evaluates all participating workers as far as evidence permits. The table is not a leaderboard for vanity metrics. Its purpose is to make collective recursive improvement empirical, coordinated, slowly compounding, and resistant to metric gaming.

Required top-level metrics:

1. token quality / token efficiency;
2. code quality;
3. verified innovation;
4. code capability / information-transfer latency ratio;
5. HCU architecture-attainment confidence forecast;
6. calibration / anti-Goodhart health of the measurement system itself.

Performance has no artificial upper target. Information-transfer latency has no artificial lower target. Correctness, provenance, authority, security, causal identity and effect boundaries remain hard constraints and may never be traded away merely to improve a ratio.

## 2. Research basis

The operating design adopts the following research lessons as design inputs, not as canonical Clay facts:

- Self-Refine: iterative feedback + refinement can improve first-pass model outputs.
- Reflexion: explicit feedback plus episodic memory can improve later trials.
- Darwin Gödel Machine: self-modifying coding agents improve more reliably when modifications are empirically benchmarked and diverse stepping-stone variants are retained rather than greedily collapsing to one path.
- AlphaEvolve / Mind Evolution: generate/refine/crossover/select loops become powerful when candidates are evaluated by automated, task-grounded evaluators and useful diversity is preserved.
- Reward-model overoptimization and Goodhart analyses: aggressive optimization of an imperfect proxy can reduce ground-truth performance; therefore no single proxy score may become the sole optimization target.
- Calibration research: a probability forecast must be judged by later outcomes using proper scoring rules/reliability, not by how confident the forecaster sounds.

Research references:
- Madaan et al., Self-Refine, 2023, arXiv:2303.17651
- Shinn et al., Reflexion, 2023, arXiv:2303.11366
- Zhang et al., Darwin Gödel Machine, 2025, arXiv:2505.22954
- Novikov et al., AlphaEvolve, 2025, arXiv:2506.13131
- Lee et al., Mind Evolution / Evolving Deeper LLM Thinking, 2025
- Gao, Schulman, Hilton, Scaling Laws for Reward Model Overoptimization, 2022/2023, arXiv:2210.10760
- Manheim & Garrabrant, Categorizing Variants of Goodhart's Law, 2018, arXiv:1803.04585
- Dimitriadis, Gneiting, Jordan, reliability/calibration/Brier decomposition, 2020, arXiv:2008.03033

## 3. Mandatory end-of-`go` sequence

Every exact `go` ends with this sequence after the normal three-track work and before the visible CLAY STATUS footer:

1. REFRESH current canonical `main`, current owner authority and current supervisor.
2. COLLECT all worker records/receipts belonging to the exact shared macrocycle identity.
3. COLLAPSE correlated evidence by shared model family, source, prompt lineage, orchestration ancestry and copied benchmark result. Multiple workers repeating one ancestry are not independent confirmations.
4. MEASURE raw observables before deriving scores.
5. COMPUTE the per-worker table and aggregate table.
6. CALIBRATE the HCU confidence forecast against any milestones that resolved since the previous cycle.
7. AUDIT for Goodhart/metric gaming, missingness, benchmark leakage, duplicate ancestry, skipped correctness gates, latency shortcuts and token-truncation shortcuts.
8. SELECT exactly one or a very small Pareto-safe set of metric bottlenecks for the next cycle.
9. IMPROVE the underlying system, not the displayed number. A stricter measurement that lowers a score is valid progress.
10. WRITE the versioned live state and append-only worker/macrocycle record.
11. REPORT the metric delta in the final `go` response.

If a metric is not directly measurable, emit `UNKNOWN` plus the missing discriminator. Never fabricate a score merely to keep a trend positive.

## 4. Worker record contract

Each participating worker should emit `CLAY_GO_WORKER_METRICS/v1` with:

- macrocycle identity;
- worker/organ identity and source class;
- model/provider when known;
- exact source/ref/commit identities;
- evidence-lineage identifiers;
- start/end timestamps;
- exact input/output/total token usage when available;
- emitted delta IDs;
- accepted/verified delta IDs;
- test, negative-test, static-check and benchmark evidence;
- benchmark family + baseline/new values;
- evidence emitted timestamp and first downstream-consumption timestamp;
- code-quality indicators;
- innovation indicators;
- HCU milestone probability forecasts plus evidence refs;
- observed/inferred/generated/unknown classification for every material field.

Self-reported final scores are ignored by the canonical aggregator. Workers contribute raw evidence and forecasts; the aggregator computes scores.

When no reproducible shared macrocycle identity is exposed, records may be preserved as `MACROCYCLE_ID_UNRESOLVED`, but they must not be silently grouped into one `go`.

## 5. Metric A — Token Quality Efficiency (TQE)

Purpose: measure verified useful improvement per token, not terseness.

For accepted deltas only:

`verified_utility_i = max(0, relative_improvement_fraction) × code_quality_fraction × reproducibility_factor × independence_factor`

where:
- `reproducibility_factor = min(reproducible_runs / 3, 1)`;
- `independence_factor` is 1 only for independent evidence lineage and is reduced/collapsed for shared ancestry;
- a delta with failed hard correctness/security/provenance gates contributes 0.

Then:

`TQE = 1000 × sum(verified_utility_i) / total_tokens`

Units: verified utility per 1k tokens.

Rules:
- exact token usage required; otherwise `UNKNOWN`;
- zero accepted verified utility with known tokens is legitimately 0;
- shortening output cannot improve TQE if it removes required evidence or makes a delta non-reproducible;
- use median and bootstrap interval across macrocycles once enough data exists;
- raw input/output token counts remain visible next to TQE.

## 6. Metric B — Code Quality Score (CQS)

0–100, derived only from measured indicators. Recommended components:

- 30% functional correctness / relevant positive tests;
- 15% negative/fail-closed tests;
- 10% static/type/lint/build checks;
- 15% benchmark non-regression;
- 10% reproducibility across repeated runs;
- 10% maintainability/complexity delta;
- 5% provenance/causal-identity completeness;
- 5% cross-mode integration/reuse without duplicate authority.

Missing required evidence does not count as perfect. If evidence coverage is below 60%, report `UNKNOWN` rather than renormalizing missing dimensions into a misleading high score.

A code-quality score cannot promote whole-HCU or whole-EntityOS runtime credit.

## 7. Metric C — Verified Innovation Score (VIS)

Innovation is not novelty prose. It requires novelty that survives empirical contact.

0–100:
- 35% nonduplicate mechanism novelty after current repo/PR + external prior-art search;
- 30% measured useful effect on an accepted benchmark or falsifier;
- 20% transferability/reuse across HCU modes or subsystems;
- 15% falsifiability and causal discriminability.

Rules:
- a duplicate mechanism gets novelty credit near 0 even if independently rediscovered;
- a novel but untested idea remains `CANDIDATE_INNOVATION`, not verified innovation;
- popularity/stars/citations are discovery metadata, not innovation proof;
- direct code reuse retains license/provenance;
- same-model/same-prompt repetition is not independent innovation evidence.

## 8. Metric D — Capability / Information-Latency Ratio (CILR)

Track the raw constituents and the ratio; never display the ratio alone.

For a fixed benchmark family:

`performance_index = new_verified_capability / baseline_verified_capability`

`information_latency = first_downstream_consumed_at - evidence_emitted_at`

Primary latency statistic: p95 end-to-end information propagation latency. Also retain p50, sample count and clock/source identity.

`CILR = performance_index / max(p95_information_latency_seconds, measurement_floor_seconds)`

CILR is intentionally unbounded upward. Performance can keep increasing and latency can keep decreasing.

Hard rules:
- do not improve latency by skipping validation, provenance, causal binding, synchronization, or EffectGate;
- do not compare CILR across unrelated benchmark families without an explicit normalization contract;
- if downstream consumption acknowledgements are absent, information latency is `UNKNOWN`, not 0;
- maintain throughput and latency separately because a ratio can hide regressions.

## 9. Metric E — HCU Architecture Attainment Confidence (HAAC)

This is a probabilistic forecast, not completion percentage and not canonical truth.

Default forecast event:
`HCU_TARGET_100_GO`: EntityOS/HCU reaches the current declared exact HCU runtime-acceptance target within the next 100 canonical `go` macrocycles without abandoning the core EntityOS+HCU authority architecture.

Each worker may forecast probabilities for these milestone families, with evidence refs:

1. authority/truth/effect invariants remain coherent;
2. Typed Entry + replay-stable causal identity closes;
3. provider/runtime/effect call boundaries close;
4. verified engine/load/consumed-byte identity closes;
5. GRID10 + InferenceReceipt causal closure executes;
6. real local model execution binds canonically;
7. model-specific J-Space observation closes;
8. J-Space causal intervention/control family closes;
9. dataset/training-readiness closure;
10. recovery/replay/fail-closed semantics;
11. performance/latency + scale ladder evidence;
12. integrated reproducibility / independent replication.

Aggregation:
- group forecasts by independent evidence lineage, not worker count;
- aggregate each milestone with a robust median/logit-median;
- combine milestone probabilities with a weighted geometric mean so weak critical gates remain visible;
- widen uncertainty when evidence coverage or lineage independence is low;
- label the result `UNCALIBRATED` until enough forecasted milestones have resolved.

Calibration:
- every resolved binary milestone is scored with Brier score and log loss;
- maintain reliability bins / calibration error when sample size permits;
- if the forecast is systematically overconfident, automatically shrink future probabilities toward 0.5;
- preserve the historical forecast before outcome resolution.

The HAAC score is allowed to fall. A falling score after new counterevidence is a sign of epistemic health, not failure.

## 10. Anti-Goodhart + Goodman/lineage-collapse law

No metric may become the single objective.

Mandatory protections:

1. Pareto selection over the full metric vector; no winner by one scalar.
2. Hard correctness/provenance/security/effect gates dominate score improvements.
3. Raw measurements are append-only and derived scores are recomputable.
4. Hold-out or shadow evaluations where practical; do not expose every acceptance detail to the proposer.
5. Random audit samples of high-scoring deltas.
6. Counter-metrics: every optimized proxy gets at least one independent regression/falsifier.
7. Evidence-lineage collapse: same model family, source, prompt, copied result or orchestration ancestry is correlated evidence, not N independent votes.
8. Metric definition changes are versioned and may not rewrite historical raw data.
9. A metric-definition change runs in shadow mode for at least 3 macrocycles before becoming selection-active unless an authority/safety bug requires immediate correction.
10. Default metric weights freeze for 10 canonical macrocycles; only raw evidence and system behavior should change cycle-to-cycle.
11. A high score with rising missing-data rate is invalid.
12. Latency improvements that remove verification are rejected.
13. Token-efficiency improvements that remove necessary reasoning/evidence are rejected.
14. Innovation cannot be self-certified.
15. Confidence is calibrated against outcomes; confidence itself is never a target.

This protocol covers both conventional Goodhart risk and Clay's existing Goodman-style collapse of non-independent shared ancestry.

## 11. Slow recursive-improvement controller

The recommended recursive loop is:

`observe -> propose diverse deltas -> predict metric effects -> execute cheapest discriminator -> measure raw outcomes -> independent/holdout evaluate -> retain or rollback -> update episodic method memory -> select next bottleneck -> repeat`

Per macrocycle:
- prefer 1–3 small, causally attributable improvements over a large opaque rewrite;
- retain a small archive of dominated-but-interesting stepping stones instead of deleting all alternatives;
- compare against the current champion and at least one diverse baseline;
- rollback regressions;
- preserve failed experiments and counterevidence;
- adjust optimization pressure gradually;
- periodically spend a cycle on evaluator quality rather than candidate quality.

This follows the strongest common pattern in current self-improving-agent research: empirical evaluation and diversity outperform unvalidated recursive self-praise.

## 12. Live table

Canonical derived outputs:

- `free swarm/GO_COLLECTIVE_METRICS.json`
- `free swarm/GO_COLLECTIVE_METRICS.md`

Canonical per-worker records:

- `research_entity/continuity/go_metrics/worker_records/<macrocycle_id>/<worker_id>.json`

Canonical macrocycle summaries:

- `research_entity/continuity/go_metrics/macrocycles/<macrocycle_id>.json`

The live table must expose, at minimum:

| worker | tokens | TQE | CQS | VIS | performance index | p95 info latency | CILR | evidence independence | HCU forecast contribution | status |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|

Aggregate history must show current value, previous value, rolling median/EWMA, confidence interval where possible, missingness and trend.

## 13. End-of-go optimization rule

At the end of each `go`, choose the next metric bottleneck by expected information gain under hard safety/authority constraints.

Preferred priority:
1. any hard correctness/effect/provenance violation;
2. missing measurement that prevents trustworthy optimization;
3. weakest critical HCU milestone;
4. low TQE caused by wasted/unverified token work;
5. low CQS;
6. low empirical innovation;
7. poor capability/latency ratio;
8. forecast calibration error.

Do not force all numbers upward every cycle. Improve the real system slowly and let measurements report the truth.
