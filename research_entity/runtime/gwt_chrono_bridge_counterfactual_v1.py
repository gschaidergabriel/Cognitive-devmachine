from __future__ import annotations

"""Crazy GWT challenger #2: Counterfactual Chrono-Bridge after a Pulse gap.

The challenger explicitly simulates missed logical Pulse slots in a SIMULATION_ONLY workspace.
It is compared against a direct O(1) elapsed-time state recomputation using the same admitted
dynamics. If the stepped simulation adds no decision gain, it is refuted as unnecessary and,
critically, no simulated slot is ever materialized as a real cognitive Pulse.
"""

from dataclasses import dataclass
import random
import statistics


@dataclass(frozen=True)
class Goal:
    ref: str
    value0: float
    drift_per_slot: float


def score_true(goal: Goal, slots: int, unseen_shock: float) -> float:
    return goal.value0 + goal.drift_per_slot * slots + unseen_shock


def direct_time_recompute(goal: Goal, slots: int) -> float:
    return goal.value0 + goal.drift_per_slot * slots


def chrono_bridge_simulation(goal: Goal, slots: int) -> tuple[float, int]:
    # Explicitly counterfactual. This is not entity_pulses and has no memory/truth authority.
    value = goal.value0
    for _ in range(slots):
        value += goal.drift_per_slot
    return value, slots


def choose(scores: dict[str, float]) -> str:
    return max((score, ref) for ref, score in scores.items())[1]


def episode(seed: int, n_goals: int = 32):
    rnd = random.Random(seed)
    slots = rnd.randint(1, 3600)
    goals = [
        Goal(f'g{i:02d}', rnd.uniform(-1, 1), rnd.uniform(-0.003, 0.003))
        for i in range(n_goals)
    ]
    # Unknown external shocks are deliberately not inferable from time alone.
    shocks = {g.ref: (rnd.gauss(0, 0.15) if rnd.random() < 0.15 else 0.0) for g in goals}
    true = {g.ref: score_true(g, slots, shocks[g.ref]) for g in goals}

    stale = choose({g.ref: g.value0 for g in goals})
    direct = choose({g.ref: direct_time_recompute(g, slots) for g in goals})
    chrono_scores = {}
    work = 0
    for g in goals:
        chrono_scores[g.ref], steps = chrono_bridge_simulation(g, slots)
        work += steps
    chrono = choose(chrono_scores)

    shuffled_slots = rnd.randint(1, 3600)
    shuffled = choose({g.ref: direct_time_recompute(g, shuffled_slots) for g in goals})

    optimum = max(true, key=true.get)
    return {
        'slots': slots,
        'stale_utility': true[stale],
        'direct_utility': true[direct],
        'chrono_utility': true[chrono],
        'shuffled_utility': true[shuffled],
        'optimal_utility': true[optimum],
        'direct_correct': direct == optimum,
        'chrono_correct': chrono == optimum,
        'stale_correct': stale == optimum,
        'shuffled_correct': shuffled == optimum,
        'chrono_equals_direct': chrono == direct,
        'chrono_simulated_steps': work,
        'direct_recompute_ops': n_goals,
        'phantom_pulses_materialized': 0,
    }


def benchmark(episodes: int = 5_000):
    rows = [episode(i) for i in range(episodes)]
    out = {
        'episodes': episodes,
        'mean_gap_slots': statistics.mean(r['slots'] for r in rows),
        'stale_utility': statistics.mean(r['stale_utility'] for r in rows),
        'direct_utility': statistics.mean(r['direct_utility'] for r in rows),
        'chrono_utility': statistics.mean(r['chrono_utility'] for r in rows),
        'shuffled_utility': statistics.mean(r['shuffled_utility'] for r in rows),
        'optimal_utility': statistics.mean(r['optimal_utility'] for r in rows),
        'stale_accuracy': statistics.mean(r['stale_correct'] for r in rows),
        'direct_accuracy': statistics.mean(r['direct_correct'] for r in rows),
        'chrono_accuracy': statistics.mean(r['chrono_correct'] for r in rows),
        'shuffled_accuracy': statistics.mean(r['shuffled_correct'] for r in rows),
        'chrono_equals_direct_rate': statistics.mean(r['chrono_equals_direct'] for r in rows),
        'mean_chrono_simulated_steps': statistics.mean(r['chrono_simulated_steps'] for r in rows),
        'mean_direct_recompute_ops': statistics.mean(r['direct_recompute_ops'] for r in rows),
        'phantom_pulses_materialized': sum(r['phantom_pulses_materialized'] for r in rows),
    }
    out['chrono_gain_vs_direct'] = out['chrono_utility'] - out['direct_utility']
    out['direct_gain_vs_stale'] = out['direct_utility'] - out['stale_utility']
    out['chrono_work_ratio_vs_direct'] = (
        out['mean_chrono_simulated_steps'] / out['mean_direct_recompute_ops']
    )
    out['promotion_decision'] = (
        'REFUTED_AS_DISTINCT_MECHANISM_USE_DIRECT_TIME_RECOMPUTE'
        if out['chrono_equals_direct_rate'] == 1.0 and abs(out['chrono_gain_vs_direct']) < 1e-12
        else 'REQUIRES_MORE_TESTING'
    )
    return out
