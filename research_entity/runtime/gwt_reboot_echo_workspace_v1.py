from __future__ import annotations

"""Crazy GWT challenger #4: Reboot Echo Workspace.

After a real boot/power gap, the challenger lets one *actually verified pre-shutdown focus* receive
an exponentially decayed bonus when it competes with the current live candidate field. It never
creates missed Pulses or claims cognition during downtime.

Strong reduction: ordinary elapsed-time GoalCheckpoint recomputation combined with current live
evidence, without any special GWT echo. If the echo has no unique information and only adds
hysteresis, it must be refuted.
"""

from dataclasses import dataclass
import math
import random
import statistics


@dataclass(frozen=True)
class Goal:
    ref: str
    checkpoint_value: float
    drift_per_slot: float


def _argmax(values: list[float]) -> int:
    return max(range(len(values)), key=lambda i: (values[i], i))


def run_episode(seed: int, n_goals: int = 32):
    rnd = random.Random(seed)
    gap_slots = rnd.randint(1, 3600)
    goals = [
        Goal(f"g{i:02d}", rnd.uniform(-1, 1), rnd.uniform(-0.002, 0.002))
        for i in range(n_goals)
    ]
    previous_verified_focus = _argmax([g.checkpoint_value for g in goals])

    # External reality may change while the process/host is not executing. Those changes are
    # not inferable from the old focus and become known only through current evidence.
    completed = {i for i in range(n_goals) if rnd.random() < 0.08}
    shocks = [rnd.gauss(0, 0.12) if rnd.random() < 0.20 else 0.0 for _ in goals]
    truth = []
    checkpoint_prediction = []
    for i, g in enumerate(goals):
        current = g.checkpoint_value + g.drift_per_slot * gap_slots + shocks[i]
        if i in completed:
            current = -5.0
        truth.append(current)
        checkpoint_prediction.append(g.checkpoint_value + g.drift_per_slot * gap_slots)

    live_evidence = [value + rnd.gauss(0, 0.10) for value in truth]
    control_scores = [
        0.35 * checkpoint_prediction[i] + 0.65 * live_evidence[i]
        for i in range(n_goals)
    ]
    control_focus = _argmax(control_scores)

    # Challenger: no new evidence, only a decayed persistence boost for the old verified focus.
    echo_scores = list(control_scores)
    echo_amplitude = 0.35 * math.exp(-gap_slots / 900.0)
    echo_scores[previous_verified_focus] += echo_amplitude
    echo_focus = _argmax(echo_scores)

    # Shuffled-focus control receives the same bonus budget but wrong prior identity.
    shuffled_previous = rnd.randrange(n_goals)
    shuffled_scores = list(control_scores)
    shuffled_scores[shuffled_previous] += echo_amplitude
    shuffled_focus = _argmax(shuffled_scores)

    optimum = _argmax(truth)
    return {
        "gap_slots": gap_slots,
        "echo_amplitude": echo_amplitude,
        "previous_verified_focus": previous_verified_focus,
        "previous_focus_externally_completed": previous_verified_focus in completed,
        "control_utility": truth[control_focus],
        "echo_utility": truth[echo_focus],
        "shuffled_utility": truth[shuffled_focus],
        "control_correct": control_focus == optimum,
        "echo_correct": echo_focus == optimum,
        "shuffled_correct": shuffled_focus == optimum,
        "echo_changed_decision": echo_focus != control_focus,
        "echo_lesion_equals_control": control_focus == _argmax(control_scores),
        "phantom_pulses_materialized": 0,
        "downtime_cognition_claimed": False,
    }


def _summary(rows):
    return {
        "n": len(rows),
        "control_utility": statistics.mean(r["control_utility"] for r in rows),
        "echo_utility": statistics.mean(r["echo_utility"] for r in rows),
        "shuffled_utility": statistics.mean(r["shuffled_utility"] for r in rows),
        "control_accuracy": statistics.mean(r["control_correct"] for r in rows),
        "echo_accuracy": statistics.mean(r["echo_correct"] for r in rows),
        "shuffled_accuracy": statistics.mean(r["shuffled_correct"] for r in rows),
        "echo_change_rate": statistics.mean(r["echo_changed_decision"] for r in rows),
        "echo_gain_vs_control": statistics.mean(
            r["echo_utility"] - r["control_utility"] for r in rows
        ),
    }


def benchmark(episodes: int = 20_000):
    rows = [run_episode(i) for i in range(episodes)]
    short = [r for r in rows if r["gap_slots"] < 300]
    long = [r for r in rows if r["gap_slots"] > 2700]
    completed = [r for r in rows if r["previous_focus_externally_completed"]]
    out = {
        "episodes": episodes,
        "all": _summary(rows),
        "short_gap": _summary(short),
        "long_gap": _summary(long),
        "previous_focus_completed": _summary(completed),
        "phantom_pulses_materialized": sum(r["phantom_pulses_materialized"] for r in rows),
        "downtime_cognition_claim_rate": statistics.mean(r["downtime_cognition_claimed"] for r in rows),
        "echo_lesion_control_rate": statistics.mean(r["echo_lesion_equals_control"] for r in rows),
    }
    out["promotion_decision"] = (
        "REFUTED_USE_NORMAL_ELAPSED_CHECKPOINT_PLUS_CURRENT_EVIDENCE"
        if out["all"]["echo_accuracy"] < out["all"]["control_accuracy"]
        and out["all"]["echo_utility"] <= out["all"]["control_utility"]
        else "REQUIRES_MORE_TESTING"
    )
    return out
