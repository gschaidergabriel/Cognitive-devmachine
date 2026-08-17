#!/usr/bin/env python3
"""Research-only SWC-001 binary-CSP discriminator.

This is NOT Frank runtime code. It isolates one claim: topology-aware exact
coherence can avoid global solving on certified forest scopes while pairwise
projection consistency is unsafe on cyclic scopes.
"""
from collections import deque
import random
import statistics


def make_instance(rng, n):
    cyclic = rng.random() < 0.35
    edges = []
    for i in range(1, n):
        if rng.random() < 0.82:
            edges.append((rng.randrange(i), i))
    if cyclic:
        possible = [(i, j) for i in range(n) for j in range(i + 1, n)
                    if (i, j) not in edges and (j, i) not in edges]
        rng.shuffle(possible)
        edges += possible[:rng.randint(1, max(1, n // 2))]
    constraints = {}
    for edge in edges:
        kind = rng.choices(["eq", "neq", "any"], weights=[0.42, 0.42, 0.16])[0]
        constraints[edge] = ({(0, 0), (1, 1)} if kind == "eq" else
                             {(0, 1), (1, 0)} if kind == "neq" else
                             {(0, 0), (0, 1), (1, 0), (1, 1)})
    return constraints


def is_forest(n, constraints):
    parent = list(range(n))
    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for i, j in constraints:
        a, b = find(i), find(j)
        if a == b:
            return False
        parent[a] = b
    return True


def pairwise_projection_consistent(constraints):
    items = list(constraints.items())
    if any(not rel for _, rel in items):
        return False
    for a in range(len(items)):
        (i, j), r1 = items[a]
        for b in range(a + 1, len(items)):
            (k, l), r2 = items[b]
            for v in set((i, j)) & set((k, l)):
                p1 = {t[0 if v == i else 1] for t in r1}
                p2 = {t[0 if v == k else 1] for t in r2}
                if not p1.intersection(p2):
                    return False
    return True


def ac3(n, constraints):
    domains = [{0, 1} for _ in range(n)]
    neighbours = [set() for _ in range(n)]
    relations = {}
    for (i, j), rel in constraints.items():
        neighbours[i].add(j); neighbours[j].add(i)
        relations[(i, j)] = rel
        relations[(j, i)] = {(b, a) for a, b in rel}
    queue = deque(relations)
    ops = 0
    while queue:
        i, j = queue.popleft()
        rel = relations[(i, j)]
        removed = set()
        for x in list(domains[i]):
            ops += 1
            if not any((x, y) in rel for y in domains[j]):
                removed.add(x)
        if removed:
            domains[i] -= removed
            if not domains[i]:
                return False, domains, ops
            for k in neighbours[i] - {j}:
                queue.append((k, i))
    return True, domains, ops


def global_solve(n, constraints, domains=None):
    domains = domains or [{0, 1} for _ in range(n)]
    by_var = [[] for _ in range(n)]
    for (i, j), rel in constraints.items():
        by_var[i].append((i, j, rel)); by_var[j].append((i, j, rel))
    order = sorted(range(n), key=lambda v: (len(domains[v]), -len(by_var[v])))
    assignment = {}
    nodes = 0
    def compatible(v, value):
        for i, j, rel in by_var[v]:
            other = j if v == i else i
            if other in assignment:
                pair = (value, assignment[other]) if v == i else (assignment[other], value)
                if pair not in rel:
                    return False
        return True
    def backtrack(index):
        nonlocal nodes
        if index == len(order):
            return True
        v = order[index]
        for value in domains[v]:
            nodes += 1
            if compatible(v, value):
                assignment[v] = value
                if backtrack(index + 1):
                    return True
                del assignment[v]
        return False
    return backtrack(0), nodes


def candidate(n, constraints):
    consistent, domains, ac_ops = ac3(n, constraints)
    if not consistent:
        return False, False, ac_ops
    if is_forest(n, constraints):
        return True, False, ac_ops
    solved, nodes = global_solve(n, constraints, domains)
    return solved, True, ac_ops + nodes


def strong_baseline(n, constraints):
    consistent, domains, ac_ops = ac3(n, constraints)
    if not consistent:
        return False, ac_ops
    solved, nodes = global_solve(n, constraints, domains)
    return solved, ac_ops + nodes


def run(seed, episodes=500):
    rng = random.Random(seed)
    pair_fp = pair_correct = candidate_errors = solver_calls = 0
    candidate_ops = strong_ops = 0
    for _ in range(episodes):
        n = rng.randint(6, 14)
        constraints = make_instance(rng, n)
        truth, _ = global_solve(n, constraints)
        pair = pairwise_projection_consistent(constraints)
        cand, called, c_ops = candidate(n, constraints)
        strong, s_ops = strong_baseline(n, constraints)
        assert strong == truth
        pair_correct += int(pair == truth)
        pair_fp += int(pair and not truth)
        candidate_errors += int(cand != truth)
        solver_calls += int(called)
        candidate_ops += c_ops
        strong_ops += s_ops
    return {
        "seed": seed,
        "episodes": episodes,
        "pair_false_coherent": pair_fp,
        "pair_accuracy": pair_correct / episodes,
        "candidate_errors": candidate_errors,
        "candidate_solver_call_fraction": solver_calls / episodes,
        "candidate_to_strong_counted_op_ratio": candidate_ops / strong_ops,
    }


def main():
    rows = [run(seed, 500) for seed in range(20)]
    print("episodes_total", sum(r["episodes"] for r in rows))
    for key in ["pair_false_coherent", "pair_accuracy", "candidate_solver_call_fraction",
                "candidate_to_strong_counted_op_ratio"]:
        vals = [r[key] for r in rows]
        print(key, "mean", statistics.mean(vals), "sd", statistics.stdev(vals),
              "range", (min(vals), max(vals)))
    print("candidate_errors_total", sum(r["candidate_errors"] for r in rows))
    for row in rows:
        print(row)


if __name__ == "__main__":
    main()
