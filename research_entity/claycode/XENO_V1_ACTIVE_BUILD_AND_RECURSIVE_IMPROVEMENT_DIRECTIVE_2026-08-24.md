# Xeno v1 active-build and recursive-improvement directive

Status: **OWNER EXECUTION PRIORITY FOR `go`**  
Date: 2026-08-24  
Product identity: **EntityOS**  
Integrated cognition/compute architecture: **HCU**  
Implementation codename: **Xeno**

This directive changes the optimization target of `go`: architecture synthesis is no longer the primary output. The architecture/concept phase is mature enough that `go` must converge on the first finished, runnable Xeno implementation with an integrated specialized ~0.8B cognitive core, then keep improving it recursively until a newer explicit owner instruction supersedes this directive.

Xeno remains an implementation codename inside EntityOS/HCU. It does not create a second canonical truth authority, effect authority, product identity or persistent entity.

## Phase A — build Xeno v1

Every `go` should preferentially consume unresolved work from this gate chain:

1. `V1_RUNTIME` — one runnable end-to-end slice exists: Typed Entry -> canonical state/route -> admitted engine -> ~0.8B inference -> structured result -> receipt/effect boundary.
2. `V1_08B_ENGINE` — exact base checkpoint/revision/tokenizer/runtime/loader identity is bound; current preferred candidate is `Qwen/Qwen3.5-0.8B` unless exact evidence forces another ~0.8B-class choice.
3. `V1_JSPACE_GWT` — the concrete Global J-Space/GWT control path, `JSPACE_VECTOR_CONTROL_ABI/v1`, trace instrumentation and matched lesion/sham/off-target controls are executable.
4. `V1_DATASET` — deterministic trace -> family-split train/validation/holdout compiler exists with hard negatives, sidecar provenance and leakage checks.
5. `V1_TRAINING` — pre-train baseline is frozen; one specialized fine-tuned ~0.8B candidate exists and is hash-bound. Training execution must obey the newest current monetary/provider authority; no paid job is implied merely by this build directive.
6. `V1_INTEGRATION` — the fine-tuned candidate is integrated behind the same engine/state/effect/recovery boundaries as the base model and can be swapped without canonical-state reset.
7. `V1_ACCEPTANCE` — the exact candidate passes the frozen capability, quality, latency, throughput, RSS, recovery, authority-boundary, token-efficiency, J-Space causal and packaging/startup acceptance suite.

A prose-only architecture answer does not advance a gate unless it removes a precise executable blocker. The preferred worker artifact is a minimal source patch plus tests and a benchmark/falsifier. `ready_for_forge=true` requires a non-empty unified diff, target files and executable test commands.

## Phase B — recursive improvement after Xeno v1

When a bound `XENO_V1_ACCEPTANCE/v1` PASS exists, `go` automatically changes from `XENO_V1_ACTIVE_BUILD` to `RECURSIVE_IMPROVEMENT`. It must not stop merely because v1 exists.

The recursive objective is multi-dimensional and adversarial to Goodhart collapse:

- improve capability coverage and task quality;
- reduce end-to-end p50 latency and protect/reduce p95 latency;
- increase useful throughput;
- reduce/protect resident memory;
- improve/protect crash/recovery and exactly-once behavior;
- improve/protect authority-boundary correctness;
- improve token efficiency / useful-result-per-token;
- increase the fraction of the Xeno module represented in ClayCode;
- preserve exact state/effect/provenance/generation fences.

Token count, logical-worker count, consensus, architecture elegance, benchmark cherry-picking or a single improved metric never constitutes recursive progress.

## Promotion law

The deterministic comparison gate is `tools/xeno_build_gate.py`.

For a normal recursive candidate:

- every protected metric must be present and finite;
- **no protected metric may regress**;
- `capability_pass_rate`, `task_quality_score`, `p50_latency_ms`, `throughput_tokens_s` and `claycode_fraction` must all improve in their intended directions;
- otherwise reject/rework/revert the candidate.

For any **ClayCode migration** candidate, the rule is deliberately stricter:

- compare the same frozen before/after metric vector;
- every tracked metric must improve in its intended direction;
- equality on even one tracked metric is insufficient for promotion of that migration step;
- if the ClayCode conversion is semantically prettier but not globally better by the measurements, do not promote it.

This makes ClayCode conversion an empirical optimization process rather than a rewrite campaign.

## Frozen metric vector

The initial mandatory vector is:

- `capability_pass_rate` — higher;
- `task_quality_score` — higher;
- `p50_latency_ms` — lower;
- `p95_latency_ms` — lower;
- `throughput_tokens_s` — higher;
- `rss_mb` — lower;
- `recovery_pass_rate` — higher;
- `authority_boundary_pass_rate` — higher;
- `token_efficiency_score` — higher;
- `claycode_fraction` — higher.

A future owner/supervisor may add metrics, but a candidate cannot silently remove a difficult metric from the comparison set.

## Worker allocation law

The active Xeno fabric should bias work toward implementation rather than open-ended architecture search. Roles include end-to-end integration, ~0.8B engine/runtime, J-Space/GWT, dataset compiler, train/eval, Typed Entry, state/effect/recovery, ClayCode migration, performance/latency, capability, falsification and recursive improvement.

Workers must prefer the currently closest-to-shipping path and avoid parallel substitute frameworks unless a falsifier proves the current path untenable.

Research remains useful only when it feeds a concrete implementation decision, test, benchmark, dataset transformation or counterexample back into the build loop.

## Fine-tuning authority boundary

The target remains a **fine-tuned specialized ~0.8B core**. This directive authorizes building toward that target; it does not itself authorize an unbounded paid service, recurring retraining or paid fallback.

At any moment, actual training-job creation must resolve the newest owner/supervisor authority. If the current mode forbids a paid/provider training lane, `go` must still complete every zero-cost prerequisite it can: exact base binding, prototype traces, vector ABI, dataset compiler, hard negatives, splits, baseline, training launcher interface, evaluation harness and integration seam. It then fails closed exactly at the monetary execution boundary rather than reverting to architecture-only work.

If/when the exact fine-tuning lane is explicitly admitted, create only the authorized run(s), bind the resulting model identity and immediately continue integration/evaluation.

## Recursive stop condition

There is no terminal `done` state after Xeno v1. The default state becomes:

`measure -> hypothesize -> patch -> test -> benchmark -> compare full metric vector -> promote/reject -> ClayCode migrate where strictly dominant -> remeasure -> repeat`

This continues until a newer explicit owner instruction changes the objective.
