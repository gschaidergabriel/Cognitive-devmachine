#!/usr/bin/env python3
"""FRANK loop-readout quality discriminator.

Evidence class: SYNTHETIC_MECHANISM_TEST_NOT_TARGET_ACCEPTANCE.
Tests the project law that low state delta + high unresolved pressure must not be
classified as convergence, and tests the counterhypothesis that a pressure-aware
controller itself becomes unsafe when the residual-pressure readout is stale or noisy.
"""
from __future__ import annotations
import json, math
import numpy as np

SEED = 20260809
N = 50000
MAX_STEPS = 12


def generate(regime, rng, max_steps=16):
    residual = [float(rng.uniform(0.65, 1.0))]
    state = [float(rng.normal())]
    for t in range(max_steps):
        r = residual[-1]
        if regime == "FAST":
            reduction = max(0, 0.38*r + rng.normal(0, 0.012))
            r2 = max(0, r-reduction); d = abs(reduction) + abs(rng.normal(0, 0.008))
        elif regime == "SLOW":
            reduction = max(0, 0.11*r + rng.normal(0, 0.010))
            r2 = max(0, r-reduction); d = abs(reduction) + abs(rng.normal(0, 0.008))
        elif regime == "STALLED":
            reduction = max(0, (0.09*r if t < 2 else 0.002*r) + rng.normal(0, 0.003))
            r2 = max(0, r-reduction); d = abs(rng.normal(0.006 if t >= 2 else 0.07, 0.004))
        else:
            phase = t % 4
            reduction = max(0, (0.16*r if phase in (0, 3) else 0.015*r) + rng.normal(0, 0.007))
            r2 = max(0, r-reduction)
            d = 0.07 + 0.04*math.sin((t+1)*math.pi/2) + abs(rng.normal(0, 0.006))
        residual.append(float(r2))
        state.append(state[-1] + (d if t % 2 == 0 else -d))
    return np.array(residual), np.array(state)


def delta(ep, t):
    return abs(ep[1][t]-ep[1][t-1]) if t >= 1 else float("inf")


def delta_only(ep, eps=.02):
    for t in range(1, MAX_STEPS+1):
        if delta(ep, t) < eps:
            return t, "CONVERGED"
    return MAX_STEPS, "MAX"


def global_dual(ep, eps=.02, res_thr=.08):
    for t in range(1, MAX_STEPS+1):
        if delta(ep, t) < eps and ep[0][t] < res_thr:
            return t, "CONVERGED"
    return MAX_STEPS, "MAX"


def typed(ep, eps=.02, res_thr=.08, cost=.012):
    lowdelta_highres = 0
    improvements = []
    for t in range(1, MAX_STEPS+1):
        d = delta(ep, t)
        improvements.append(ep[0][t-1]-ep[0][t])
        lowdelta_highres = lowdelta_highres+1 if d < eps and ep[0][t] > .25 else 0
        if lowdelta_highres >= 2:
            return t, "ESCALATE_STALLED"
        if ep[0][t] < res_thr:
            return t, "CONVERGED"
        if t >= 4 and float(np.mean(improvements[-3:])) < cost and ep[0][t] < .25:
            return t, "HALT_MARGINAL"
    return MAX_STEPS, "MAX"


def typed_observed(ep, rng, noise_sd, stale_p, eps=.02, res_thr=.08, cost=.012):
    lowdelta_highres = 0
    improvements = []
    obs_prev = max(0, float(ep[0][0] + rng.normal(0, noise_sd)))
    for t in range(1, MAX_STEPS+1):
        obs = obs_prev if rng.random() < stale_p else max(0, float(ep[0][t] + rng.normal(0, noise_sd)))
        d = delta(ep, t)
        improvements.append(obs_prev-obs)
        lowdelta_highres = lowdelta_highres+1 if d < eps and obs > .25 else 0
        if lowdelta_highres >= 2:
            return t, "ESCALATE_STALLED"
        if obs < res_thr:
            return t, "CONVERGED"
        if t >= 4 and float(np.mean(improvements[-3:])) < cost and obs < .25:
            return t, "HALT_MARGINAL"
        obs_prev = obs
    return MAX_STEPS, "MAX"


def aggregate(regimes, episodes, controller):
    rows = []
    for regime, ep in zip(regimes, episodes):
        t, out = controller(ep); r = float(ep[0][t])
        rows.append((regime, t, out, r, bool(out == "CONVERGED" and r > .25)))
    mean = lambda xs: float(sum(xs)/len(xs))
    stalled = [x for x in rows if x[0] == "STALLED"]
    fast = [x for x in rows if x[0] == "FAST"]
    cyc = [x for x in rows if x[0] == "PRODUCTIVE_CYCLE"]
    return {
        "mean_steps": mean([x[1] for x in rows]),
        "mean_final_residual": mean([x[3] for x in rows]),
        "false_convergence_rate": mean([x[4] for x in rows]),
        "stalled_false_convergence_rate": mean([x[4] for x in stalled]),
        "stalled_escalation_rate": mean([x[2] == "ESCALATE_STALLED" for x in stalled]),
        "stalled_mean_steps": mean([x[1] for x in stalled]),
        "fast_mean_steps": mean([x[1] for x in fast]),
        "productive_cycle_mean_steps": mean([x[1] for x in cyc]),
    }


def main():
    rng = np.random.default_rng(SEED)
    regimes = rng.choice(["FAST", "SLOW", "STALLED", "PRODUCTIVE_CYCLE"], size=N, p=[.35, .30, .20, .15])
    episodes = [generate(r, rng) for r in regimes]
    metrics = {k: aggregate(regimes, episodes, v) for k, v in {
        "delta_only": delta_only,
        "global_dual": global_dual,
        "typed": typed,
    }.items()}
    sensitivity = []
    for noise in [0.0, .03, .08, .15]:
        for stale in [0.0, .2, .5]:
            rr = np.random.default_rng(SEED + int(noise*1000) + int(stale*100))
            rows = []
            for regime, ep in zip(regimes, episodes):
                t, out = typed_observed(ep, rr, noise, stale); r = float(ep[0][t])
                rows.append((regime, t, out, r, bool(out == "CONVERGED" and r > .25)))
            stalled = [x for x in rows if x[0] == "STALLED"]
            sensitivity.append({
                "noise_sd": noise,
                "stale_probability": stale,
                "false_convergence_rate": float(sum(x[4] for x in rows)/len(rows)),
                "stalled_escalation_rate": float(sum(x[2] == "ESCALATE_STALLED" for x in stalled)/len(stalled)),
                "mean_steps": float(sum(x[1] for x in rows)/len(rows)),
                "mean_final_residual": float(sum(x[3] for x in rows)/len(rows)),
            })
    print(json.dumps({
        "schema_version": "1.0",
        "experiment": "FRANK_LOOP_REGIME_CONTROLLER_DISCRIMINATOR",
        "evidence_class": "SYNTHETIC_MECHANISM_TEST_NOT_TARGET_ACCEPTANCE",
        "seed": SEED,
        "episodes": N,
        "regime_mix": {"FAST": .35, "SLOW": .30, "STALLED": .20, "PRODUCTIVE_CYCLE": .15},
        "metrics": metrics,
        "readout_noise_sensitivity": sensitivity,
        "interpretation": {
            "supported": "Delta-only convergence is falsified on the constructed STALLED regime. A residual-aware controller prevents that failure, while a single global dual criterion burns the full budget on stalls. Typed escalation avoids the stall waste in this fixture.",
            "negative_result": "Typed control is not robust to arbitrarily noisy unresolved-pressure readouts. At noise_sd=0.15 false convergence becomes material, so readout calibration/freshness is a prerequisite.",
            "not_established": "No live FRANK, H1/H2/H3, model-quality, emergence, or target-Ubuntu superiority is established."
        }
    }, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
