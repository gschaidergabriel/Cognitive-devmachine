#!/usr/bin/env python3
import json
import numpy as np

SEED = 202608091814
N = 200_000

def clipped_probe_delays(rng, n, probes, mean_ms=0.06, sd_ms=0.015):
    return np.clip(rng.normal(mean_ms, sd_ms, (n, probes)), 0, None).sum(axis=1)

def main():
    deadline_ms = 3.0
    arrival_mean_ms = 2.72
    arrival_sd_ms = 0.34

    rng = np.random.default_rng(SEED)
    arrivals = rng.normal(arrival_mean_ms, arrival_sd_ms, N)
    base_success = float(np.mean(arrivals <= deadline_ms))
    overheads = [0.0, 0.03, 0.08, 0.15, 0.30, 0.45]
    case_a = {}
    for overhead in overheads:
        success = float(np.mean(arrivals + overhead <= deadline_ms))
        case_a[f"{overhead:.2f}"] = {"success": success, "relative_loss": (base_success - success) / base_success}

    modes = {"uninstrumented":0.0,"sampling_proxy":0.03,"armed_no_emit_proxy":0.08,"inline_enabled_proxy":0.30}
    mode_results = {name: float(np.mean(arrivals + overhead <= deadline_ms)) for name, overhead in modes.items()}

    rng = np.random.default_rng(SEED + 1)
    a0 = rng.normal(10.0, 0.20, N)
    b0 = rng.normal(10.0, 0.20, N)
    baseline_a = a0 < b0
    a_asym = a0 + clipped_probe_delays(rng, N, 3)
    b_asym = b0 + clipped_probe_delays(rng, N, 1)
    asymmetric_a = a_asym < b_asym

    rng2 = np.random.default_rng(SEED + 2)
    a_sym = a0 + clipped_probe_delays(rng2, N, 2)
    b_sym = b0 + clipped_probe_delays(rng2, N, 2)
    symmetric_a = a_sym < b_sym

    sensitivity = {}
    for mu in [2.2, 2.4, 2.6, 2.8, 3.0]:
        r = np.random.default_rng(SEED + int(mu * 100))
        x = r.normal(mu, 0.34, 100_000)
        baseline = float(np.mean(x <= 3.0))
        vals = {}
        for overhead in [0.03, 0.08, 0.15, 0.30]:
            success = float(np.mean(x + overhead <= 3.0))
            vals[f"{overhead:.2f}"] = {"success": success, "relative_loss": (baseline - success) / baseline}
        sensitivity[f"{mu:.1f}"] = {"uninstrumented_success": baseline, "overheads": vals}

    result = {
        "experiment_id":"EXP-SPAWN-EM-PROBE-EFFECT-001",
        "seed":SEED,
        "evidence_class":"CHATGPT_HOSTED_SYNTHETIC_PROOF_ONLY",
        "target_host_claim":False,
        "case_a_reentry_deadline":{"N":N,"deadline_ms":deadline_ms,"arrival_mean_ms":arrival_mean_ms,"arrival_sd_ms":arrival_sd_ms,"uninstrumented_success":base_success,"overheads_ms":case_a,"mode_proxies":mode_results},
        "case_b_competition_order":{"N":N,"base_latency_mean_ms":10.0,"base_latency_sd_ms":0.20,"probe_delay_mean_ms":0.06,"probe_delay_sd_ms":0.015,"baseline_a_win_rate":float(np.mean(baseline_a)),"asymmetric_a_win_rate":float(np.mean(asymmetric_a)),"asymmetric_winner_flip_rate":float(np.mean(asymmetric_a != baseline_a)),"symmetric_a_win_rate":float(np.mean(symmetric_a)),"symmetric_winner_flip_rate":float(np.mean(symmetric_a != baseline_a))},
        "case_c_effect_estimate":{"no_reentry_success_proxy":0.18,"unobserved_truthful_reentry_effect":base_success-0.18,"inline_observed_truthful_reentry_effect":mode_results["inline_enabled_proxy"]-0.18,"observed_to_unobserved_effect_ratio":(mode_results["inline_enabled_proxy"]-0.18)/(base_success-0.18)},
        "sensitivity_grid":sensitivity,
        "interpretation_boundary":"Synthetic timing model only. Probe overhead values are illustrative parameters, not measured FRANK, Linux ftrace, eBPF, DTrace, or Ubuntu target-host overheads."
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == "__main__":
    main()
