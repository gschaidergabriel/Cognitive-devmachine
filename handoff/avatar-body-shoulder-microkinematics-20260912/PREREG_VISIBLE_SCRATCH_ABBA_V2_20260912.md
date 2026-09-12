# Visible shoulder residual matched ABBA v2 — preregistration

Status: SCRATCH ONLY / NO LIVE MUTATION.

The first visible A/B gate remains a formal FAIL because its BASE control contained a 48 FPS sample while the candidate passed. This v2 does not lower thresholds and is not an unchanged rerun. It removes the timing asymmetry by introducing an excluded warm-up followed by equal A/B/A/B measurement windows in the same isolated browser/runtime.

Exact parent: `e21a579d655ae6608d20f4813919e4845f029fa3`.

Schedule after WebGL readiness: warmup 4 s (excluded), A/base 6 s, B/candidate 6 s, A/base 6 s, B/candidate 6 s. Telemetry is aggregated only for phases `base` and `candidate`. One screenshot is captured inside the first A and first B window. Production Chrome PID/window and live HTML hash must remain invariant.

Pass criteria are unchanged from v1: AMD/Radeon renderer, gl_error=0, >=12 textures, >100 candidate draws, same screenshot dimensions/nonempty, scratch entirely left of x=1680, production subject invariant, and both BASE and CANDIDATE valid FPS mean >=58 with minimum >=55.

A PASS closes only the visible non-headless scratch shoulder residual runtime-health scope. It grants no production activation or whole-avatar credit.
