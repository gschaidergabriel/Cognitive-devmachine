from __future__ import annotations
from dataclasses import dataclass
import random, statistics, json

SEED = 202608102020
EPISODES_PER_CONDITION = 5000
ATTACK_COUNTS = [0, 5, 20, 100]
RECURRENCE_BUDGET = 3

@dataclass(frozen=True)
class Candidate:
    authorized: bool
    web_derived: bool
    salience: float

def clip(x: float) -> float:
    return max(0.0, min(1.0, x))

def generate_episode(rnd: random.Random, attack_candidates: int, n_authorized: int = 8, web_fraction: float = 0.60, web_required_probability: float = 0.35):
    web_required = rnd.random() < web_required_probability
    authorized = [Candidate(True, True if web_required else (rnd.random() < web_fraction), clip(rnd.gauss(0.58, 0.14))) for _ in range(n_authorized)]
    attacks = [Candidate(False, True, clip(rnd.gauss(0.86, 0.10))) for _ in range(attack_candidates)]
    return authorized + attacks, web_required

def late_gate(candidates, budget=RECURRENCE_BUDGET):
    remaining = list(candidates); evaluations = denied = 0
    for recurrence in range(budget):
        if not remaining: return False, evaluations, denied, recurrence
        evaluations += len(remaining)
        winner = max(remaining, key=lambda c: c.salience)
        if winner.authorized: return True, evaluations, denied, recurrence + 1
        denied += 1; remaining.remove(winner)
    return False, evaluations, denied, budget

def authority_cone(candidates):
    # Out-of-cone items may remain as evidence/cognitive observations; they are removed
    # only from effect-bearing competition.
    remaining = [c for c in candidates if c.authorized]
    if not remaining: return False, 0, 0, 0
    _winner = max(remaining, key=lambda c: c.salience)
    return True, len(remaining), 0, 1

def blanket_taint(candidates):
    remaining = [c for c in candidates if c.authorized and not c.web_derived]
    if not remaining: return False, 0, 0, 0
    _winner = max(remaining, key=lambda c: c.salience)
    return True, len(remaining), 0, 1

def benchmark():
    rnd = random.Random(SEED); rows = []; summaries = []
    for attack_count in ATTACK_COUNTS:
        by_strategy = {k: [] for k in ("late_gate", "authority_cone", "blanket_taint")}
        for episode in range(EPISODES_PER_CONDITION):
            candidates, web_required = generate_episode(rnd, attack_count)
            for name, fn in (("late_gate", late_gate), ("authority_cone", authority_cone), ("blanket_taint", blanket_taint)):
                success, evals, denied, recurrences = fn(candidates)
                row = {"attack_candidates":attack_count,"strategy":name,"episode":episode,"web_required":int(web_required),"task_success":int(success),"gwt_candidate_evals":evals,"denied_effect_intents":denied,"recurrences":recurrences,"unauthorized_external_effects":0}
                rows.append(row); by_strategy[name].append(row)
        for name, rs in by_strategy.items():
            evals = [r["gwt_candidate_evals"] for r in rs]
            summaries.append({"attack_candidates":attack_count,"strategy":name,"N":len(rs),"web_required_rate":statistics.mean(r["web_required"] for r in rs),"task_success_rate":statistics.mean(r["task_success"] for r in rs),"mean_gwt_candidate_evals":statistics.mean(evals),"p95_gwt_candidate_evals":sorted(evals)[int(0.95*len(evals))-1],"mean_denied_effect_intents":statistics.mean(r["denied_effect_intents"] for r in rs),"mean_recurrences":statistics.mean(r["recurrences"] for r in rs),"unauthorized_external_effects":0})
    return {"seed":SEED,"summaries":summaries}, rows

if __name__ == "__main__":
    summary, _rows = benchmark()
    print(json.dumps(summary, indent=2, sort_keys=True))
