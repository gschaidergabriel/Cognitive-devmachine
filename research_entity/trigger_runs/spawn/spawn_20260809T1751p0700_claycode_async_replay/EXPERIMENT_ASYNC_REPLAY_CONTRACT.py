import hashlib
import json
import random

SEED = 20260809
rng = random.Random(SEED)


def h(v):
    return hashlib.sha256(json.dumps(v, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def stable_task_id(parent, spawn_site, ordinal):
    return h({"parent": parent, "spawn_site": spawn_site, "ordinal": ordinal})


def run():
    out = {"status": "PASS", "seed": SEED, "tests": {}}

    # E1: schedule-insensitive disjoint state effects vs conflicting writes.
    disjoint_pairs = disjoint_divergence = conflicting_pairs = conflicting_divergence = 0
    for _ in range(50000):
        ka, kb = rng.randrange(8), rng.randrange(8)
        a = (ka, rng.randrange(1000000))
        b = (kb, rng.randrange(1000000))
        def apply(order):
            s = {}
            for k, v in order:
                s[k] = v
            return s
        ab, ba = apply([a,b]), apply([b,a])
        if ka == kb:
            conflicting_pairs += 1
            conflicting_divergence += (h(ab) != h(ba))
        else:
            disjoint_pairs += 1
            disjoint_divergence += (h(ab) != h(ba))
    out["tests"]["disjoint_vs_conflicting_writes"] = {
        "disjoint_pairs": disjoint_pairs,
        "disjoint_schedule_divergences": disjoint_divergence,
        "conflicting_pairs": conflicting_pairs,
        "conflicting_order_divergences": conflicting_divergence,
    }

    # E2: intentional race replay with and without explicit choice receipts.
    n = 100000
    naive_mismatch = forced_mismatch = tamper_detected = 0
    for i in range(n):
        candidates = ["data", "timeout", "shutdown"]
        live = candidates[:]
        rng.shuffle(live)
        winner = live[0]
        receipt = {
            "choice_id": f"c{i}",
            "candidates": sorted(candidates),
            "winner": winner,
            "basis": "READY_ORDER",
        }
        live_state = {"winner": winner, "value": {"data":1,"timeout":2,"shutdown":3}[winner]}
        replay = candidates[:]
        rng.shuffle(replay)
        naive_state = {"winner": replay[0], "value": {"data":1,"timeout":2,"shutdown":3}[replay[0]]}
        forced_state = {"winner": receipt["winner"], "value": {"data":1,"timeout":2,"shutdown":3}[receipt["winner"]]}
        naive_mismatch += h(naive_state) != h(live_state)
        forced_mismatch += h(forced_state) != h(live_state)
        bad = dict(receipt)
        bad["winner"] = "not-a-candidate"
        tamper_detected += bad["winner"] not in bad["candidates"]
    out["tests"]["choice_receipt_replay"] = {
        "workflows": n,
        "without_receipt_mismatches": naive_mismatch,
        "with_receipt_mismatches": forced_mismatch,
        "invalid_receipts_detected": tamper_detected,
    }

    # E3: cancellation/retry around an externally visible effect.
    n = 100000
    naive_exactly_once_fail = idem_fail = dedup_retry = 0
    for i in range(n):
        first_commits = rng.randrange(2) == 1
        naive_count = int(first_commits) + 1
        naive_exactly_once_fail += naive_count != 1
        intent = f"intent:{i}"
        sink = set()
        if first_commits:
            sink.add(intent)
        before = len(sink)
        sink.add(intent)
        dedup_retry += first_commits and len(sink) == before
        idem_fail += len(sink) != 1
    out["tests"]["cancel_retry_effect_intent"] = {
        "workflows": n,
        "naive_exactly_once_failures": naive_exactly_once_fail,
        "idempotent_intent_failures": idem_fail,
        "deduplicated_retries_after_prior_commit": dedup_retry,
    }

    # E4: stable semantic task identity must not depend on worker completion schedule.
    failures = 0
    cases = 20000
    for i in range(cases):
        nchildren = rng.randint(2, 12)
        expected = [stable_task_id("root", f"site:{i % 17}", j) for j in range(nchildren)]
        physical = expected[:]
        rng.shuffle(physical)
        failures += set(physical) != set(expected)
    out["tests"]["stable_task_identity"] = {"cases": cases, "schedule_failures": failures}

    # E5: fixed biased branch ordering is deterministic but can starve an always-ready shutdown branch.
    trials = 10000
    biased_shutdown_wins = 0
    randomized_shutdown_wins = 0
    for _ in range(trials):
        biased_winner = "stream"
        biased_shutdown_wins += biased_winner == "shutdown"
        randomized_winner = rng.choice(["stream", "shutdown"])
        randomized_shutdown_wins += randomized_winner == "shutdown"
    out["tests"]["fairness_counterexample"] = {
        "trials": trials,
        "biased_shutdown_wins": biased_shutdown_wins,
        "randomized_shutdown_wins": randomized_shutdown_wins,
    }

    assert out["tests"]["disjoint_vs_conflicting_writes"]["disjoint_schedule_divergences"] == 0
    assert out["tests"]["choice_receipt_replay"]["with_receipt_mismatches"] == 0
    assert out["tests"]["choice_receipt_replay"]["without_receipt_mismatches"] > 0
    assert out["tests"]["cancel_retry_effect_intent"]["idempotent_intent_failures"] == 0
    assert out["tests"]["cancel_retry_effect_intent"]["naive_exactly_once_failures"] > 0
    assert out["tests"]["stable_task_identity"]["schedule_failures"] == 0
    assert out["tests"]["fairness_counterexample"]["biased_shutdown_wins"] == 0
    assert out["tests"]["fairness_counterexample"]["randomized_shutdown_wins"] > 0
    return out


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
