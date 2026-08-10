# HYPOFUSION Contradiction Map

Run: `hypofusion-20260810T2241p0700-chatgpt-secondary`

## C-01 — single global execution vs useful internal parallelism

Owner-fixed invariant: at most one global active Frank execution lease. This is not contradicted by internal parallel computation, read-only helpers or external clients existing concurrently; the contradiction appears only if those paths can independently write current state/effects or become a second SELF.

Open question: can bounded read-only subwork run in parallel under one execution identity without violating the single-spawn user semantics? Test as child operations fenced to the parent's execution epoch rather than a second lease.

## C-02 — one-module loop core vs observability/recovery

Owner direction favors one complete cognitive loop-core executable module. Historical modularity may make lesions, restart isolation and differential testing easier. One-module consolidation is therefore not itself evidence of better cognition.

Resolution candidate: one executable module with typed internal boundaries, explicit intervention handles, independent receipts and checkpoint/replay surfaces. Reject consolidation if fault containment or differential observability materially regresses.

## C-03 — recurrence helps vs recurrence wastes compute

External recurrent-depth and Sokoban evidence show recurrence can provide causal planning/reasoning benefit in some systems. Adaptive-TTC work and project counterhypotheses imply extra steps can overthink or waste compute.

Resolution: recurrence is a resource allocation policy. Compare adaptive vs fixed vs event-driven under matched maximum compute; no universal recurrence benefit claim.

## C-04 — proactive agency vs single-user continuity

Proactive AgencyState permits self-generated work; single-spawn directive forbids proactive acquisition while an interactive handoff remains unresolved. These are compatible only if proactive goals persist as dormant/ready state without executing until `IDLE + handoff CLEAR`.

Failure mode: treating lease `IDLE` or disconnect as evidence of user consent. Current V2 handoff lane correctly targets this.

## C-05 — structural prompt-injection defense vs contextual manipulation

CaMeL/Fides support structural control/data separation and information-flow policy. 2026 contextual-integrity critique argues contextual manipulation can preserve the appearance of legitimate flow while changing norms/roles/purpose.

Resolution: structural separation remains necessary but not claimed sufficient. Extend adversarial tests and typed effect inputs to contextual flow dimensions; preserve abstain/confirm pathways where legitimacy is genuinely ambiguous.

## C-06 — ClayCode-only semantic authority vs simpler typed implementation

Project architecture requires ClayCode-only cognition, but scientific evidence does not show every semantic feature must be novel language machinery. Current ClayCode work already follows `less change, more compile`.

Resolution: keep ClayCode as target semantic authority while requiring each new semantic primitive to beat reuse of existing ClayCode forms and, for high-cost features, compare with a simpler typed baseline to detect self-inflicted complexity.

## C-07 — selective proactive memory vs one-module identity

External proactive-memory work uses a separate memory agent. Frank's target should not infer that a second persistent identity is necessary.

Resolution: import the mechanism (structured state + intervention/null policy) as an internal typed subsystem or bounded helper under the same self.root execution epoch. Equalize compute in tests to isolate intervention timing from extra-model benefit.

## C-08 — dynamic dependency routing vs correctness

Live Fusion V2 synthetic evidence favors adaptive routing on cost/recall but still missed required deliveries before anti-entropy. Broadcast is expensive but simple.

Resolution: no promotion before real-repo replay with missing/stale-edge faults. Dense/broadcast mode remains valid for high-centrality contradictions or incomplete dependency confidence.

## C-09 — typed reward richness vs Goodhart/tuning surface

Typed reward preserves dimensions that a scalar could hide, but extra dimensions also create more parameters and routes for proxy optimization.

Resolution: reward updates remain downstream of verified outcome + causal credit; compare against simpler verified-outcome scalar+homeostasis; require lesion/rescue and OOD reversal tests before promotion.

## C-10 — Hyperposition higher-order structure vs generic diversity

No independent direct evidence in this run validates Frank's Hyperposition mechanism as uniquely useful. Dynamic causal-state literature is only an adjacent analogue.

Resolution: downgrade to comparative candidate; beam/top-k/reseed are mandatory baselines. No v0.1 critical-path dependence until a discriminating test shows unique benefit.

## C-11 — current workspace blocker text vs newer target PR activity

The current Clay workspace still states that target main contains stale pre-self.root identity semantics. Newer target PR #161 is a fresh repair candidate but is not equivalent to merged-main acceptance.

Resolution: do not clear F-V01-01 from PR metadata alone. Require green target-lane source-to-replay/boot/restart evidence and then refresh workspace from actual merged/current source.
