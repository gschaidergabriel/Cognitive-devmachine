# CLAY EXTERNAL SOLUTION HARVEST LOOP

Status: ACTIVE
Authority source: `governance/CLAY_DUAL_MACHINE_EXECUTION_AUTHORITY_2026-08-24.md`

This file is an operational expansion of the external-solution harvest requirement used during `go` cycles.

## Trigger

Run this loop continuously when it has plausible information value, and obligatorily for any non-trivial blocker, unexplained result, performance gap, missing capability, or architecture question before investing heavily in a from-scratch solution.

## Discovery sources

Search current primary/high-signal sources, especially:

- GitHub repositories, issues, discussions, commits, releases and benchmark harnesses;
- arXiv papers and linked code/data/model artifacts;
- project documentation, technical blogs, standards, benchmark leaderboards and upstream issue trackers;
- other primary repositories/papers that materially sharpen the hypothesis.

## High-recall acquisition

Favor recall over premature filtering. Plausibly relevant candidates should be inspected. Clone/download candidates into disposable VPS sandbox research space when doing so materially improves understanding or reproducibility.

Use shallow clones, sparse checkouts, selective artifact downloads and deletion after triage to control storage. Never let candidate harvesting consume the working reserve needed for EntityOS/HCU research.

## Required candidate record

For each serious candidate, capture at least:

- source URL/repository/paper identifier;
- exact version/commit/release when available;
- license;
- claimed mechanism and performance;
- dependencies and resource cost;
- reproducibility status;
- observed strengths, weaknesses and failure modes;
- relevance to the active EntityOS/HCU problem;
- decision: reject, retain as reference, test further, or adapt.

## Reproduction and dissection

Do not accept README/paper claims as proof. Reproduce the reference behavior whenever practical. Dissect the smallest causal core: algorithm, data structures, scheduling, memory semantics, state transitions, interfaces, invariants, optimizations and measurement assumptions.

When a large repository is relevant only for one principle, isolate and test that principle rather than importing the entire architecture.

## Clay adaptation loop

1. define baseline and metric;
2. reproduce/reference-test candidate;
3. identify causal principle;
4. construct minimal ClayCode/EntityOS/HCU-native implementation;
5. A/B test against the reference under matched conditions;
6. run ablations and regression/resource tests;
7. iterate until the Clay version is measurably better on the intended objective or gives a clearly valuable system-level tradeoff;
8. integrate only when the gain is reproducible and regressions are acceptable;
9. preserve receipts, benchmark data and provenance.

A marginal improvement is sufficient when it is real, repeatable and does not worsen the broader system enough to erase the benefit.

## Reuse and licensing

Direct code reuse must respect license/attribution requirements. When only the underlying idea is valuable, prefer independent ClayCode-native reimplementation and verify behavior experimentally against the reference.

## Continuous revisiting

The candidate set is not final. Re-search as upstream repos/papers evolve, as new blockers appear, and as EntityOS/HCU constraints change. A previously rejected approach may become useful under a different architecture or metric.
