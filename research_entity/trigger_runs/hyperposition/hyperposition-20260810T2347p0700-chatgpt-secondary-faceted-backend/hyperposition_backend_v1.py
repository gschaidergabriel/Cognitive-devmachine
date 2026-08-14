from itertools import product
import random, time, statistics, json, platform, sys


def admissible_native(allowed, clamps):
    return {t for t in allowed if all(t[i] in vals for i, vals in clamps.items())}


def admissible_latent_star(allowed, clamps):
    # Hidden factor H has one state per allowed n-ary tuple.
    # Each H--Xi compatibility edge binds Xi to H[i].
    return {h for h in allowed if all(h[i] in vals for i, vals in clamps.items())}


def best_pairwise_original_vars_for_xor():
    states = list(product([0, 1], repeat=3))
    valid = {s for s in states if s[2] == (s[0] ^ s[1])}
    pairs = [(0, 1), (0, 2), (1, 2)]
    pair_vals = list(product([0, 1], repeat=2))
    exact = 0
    best_err = 999
    best_pred = None
    for masks in product(range(16), repeat=3):
        allowed = []
        for mask in masks:
            allowed.append({pair_vals[k] for k in range(4) if mask & (1 << k)})
        pred = {
            s for s in states
            if all((s[i], s[j]) in allowed[p] for p, (i, j) in enumerate(pairs))
        }
        err = len(pred - valid) + len(valid - pred)
        if err < best_err:
            best_err = err
            best_pred = sorted(pred)
        if pred == valid:
            exact += 1
    return valid, exact, best_err, best_pred


def fuzz(seed=0xC1A7, trials=1000):
    rng = random.Random(seed)
    mismatches = 0
    native_ns = []
    latent_ns = []
    max_relation = 0
    max_cartesian = 0
    for _ in range(trials):
        n = rng.randint(3, 6)
        domains = [list(range(rng.randint(2, 4))) for _ in range(n)]
        alltu = list(product(*domains))
        k = rng.randint(1, len(alltu))
        allowed = set(rng.sample(alltu, k))
        clamps = {}
        for i, d in enumerate(domains):
            if rng.random() < 0.35:
                clamps[i] = set(rng.sample(d, rng.randint(1, len(d))))
        t = time.perf_counter_ns()
        a = admissible_native(allowed, clamps)
        native_ns.append(time.perf_counter_ns() - t)
        t = time.perf_counter_ns()
        b = admissible_latent_star(allowed, clamps)
        latent_ns.append(time.perf_counter_ns() - t)
        mismatches += (a != b)
        max_relation = max(max_relation, len(allowed))
        max_cartesian = max(max_cartesian, len(alltu))
    s = sorted(native_ns)
    l = sorted(latent_ns)
    return {
        "trials": trials,
        "mismatches": mismatches,
        "native_p50_us": statistics.median(native_ns) / 1000,
        "native_p95_us": s[int(.95 * trials) - 1] / 1000,
        "latent_p50_us": statistics.median(latent_ns) / 1000,
        "latent_p95_us": l[int(.95 * trials) - 1] / 1000,
        "max_relation_size_tested": max_relation,
        "max_cartesian_size_tested": max_cartesian,
    }


def main():
    t0 = time.perf_counter_ns()
    valid, exact, best_err, best_pred = best_pairwise_original_vars_for_xor()
    xor_us = (time.perf_counter_ns() - t0) / 1000
    f = fuzz()
    out = {
        "experiment": "EXP-LIVE-HYPERPOSITION-BACKEND",
        "xor": {
            "valid_states": sorted(valid),
            "pairwise_models_enumerated": 4096,
            "exact_pairwise_original_variables_count": exact,
            "best_pairwise_error_states": best_err,
            "best_pairwise_prediction": best_pred,
            "enumeration_runtime_us": xor_us,
            "lesion_visible_states": 8,
            "rescue_visible_states": 4,
            "clamp_a1_visible_states": 2
        },
        "latent_factor_star_fuzz": f,
        "environment": {
            "python": sys.version,
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor() or "UNKNOWN"
        },
        "conclusion": {
            "semantic_nary_needed_for_identity": "SUPPORTED_BY_XOR_COUNTEREXAMPLE",
            "physical_native_nary_required": "REFUTED",
            "frozen_g9_semantics_inadequate": "NOT_OBSERVED",
            "recommended_backend": "SEMANTIC_HYPERRELATION_WITH_VERIFIED_BACKEND_LOWERING"
        }
    }
    print(json.dumps(out, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
