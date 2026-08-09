import hashlib
import heapq
import json
import random

SEED_MAIN = 0xC1A7C0DE
SEED_RECEIPT = 0x05CC1C1E
CASES = 50_000


def has_cycle(n, edges):
    adj = [[] for _ in range(n)]
    indeg = [0] * n
    for u, v in set(edges):
        adj[u].append(v)
        indeg[v] += 1
    q = [i for i in range(n) if indeg[i] == 0]
    heapq.heapify(q)
    seen = 0
    while q:
        u = heapq.heappop(q)
        seen += 1
        for v in adj[u]:
            indeg[v] -= 1
            if indeg[v] == 0:
                heapq.heappush(q, v)
    return seen != n


def stable_topo(n, deps):
    # (u,v) means eager value u depends on eager value v.
    followers = [[] for _ in range(n)]
    indeg = [0] * n
    for u, v in set(deps):
        followers[v].append(u)
        indeg[u] += 1
    q = [i for i in range(n) if indeg[i] == 0]
    heapq.heapify(q)
    order = []
    while q:
        v = heapq.heappop(q)
        order.append(v)
        for u in sorted(followers[v]):
            indeg[u] -= 1
            if indeg[u] == 0:
                heapq.heappush(q, u)
    return order if len(order) == n else None


def eval_stable(n, deps, base):
    order = stable_topo(n, deps)
    if order is None:
        return None
    depmap = [[] for _ in range(n)]
    for u, v in set(deps):
        depmap[u].append(v)
    values = [None] * n
    for u in order:
        values[u] = base[u] + sum(values[v] for v in depmap[u])
    return tuple(values)


def eval_naive_partial(n, deps, base, roots, edge_order):
    depmap = [[] for _ in range(n)]
    for u, v in edge_order:
        depmap[u].append(v)
    values = [None] * n
    active = set()
    uninitialized_reads = 0

    def init(u):
        nonlocal uninitialized_reads
        if values[u] is not None:
            return values[u]
        if u in active:
            uninitialized_reads += 1
            return 0
        active.add(u)
        value = base[u]
        for v in depmap[u]:
            if v in active and values[v] is None:
                uninitialized_reads += 1
            else:
                value += init(v)
        active.remove(u)
        values[u] = value
        return value

    for u in roots:
        init(u)
    return tuple(values), uninitialized_reads


def tarjan_scc(n, edges):
    adj = [[] for _ in range(n)]
    for u, v in edges:
        adj[u].append(v)
    index = 0
    stack = []
    on_stack = set()
    indices = [None] * n
    low = [None] * n
    comps = []

    def visit(v):
        nonlocal index
        indices[v] = low[v] = index
        index += 1
        stack.append(v)
        on_stack.add(v)
        for w in adj[v]:
            if indices[w] is None:
                visit(w)
                low[v] = min(low[v], low[w])
            elif w in on_stack:
                low[v] = min(low[v], indices[w])
        if low[v] == indices[v]:
            comp = []
            while True:
                w = stack.pop()
                on_stack.remove(w)
                comp.append(w)
                if w == v:
                    break
            comps.append(comp)

    for v in range(n):
        if indices[v] is None:
            visit(v)
    return comps


def canonical_cycle_receipt(n, edges):
    edge_set = set(edges)
    cycles = []
    for comp in tarjan_scc(n, list(edge_set)):
        members = set(comp)
        internal = sorted((u, v) for u, v in edge_set if u in members and v in members)
        if len(comp) > 1 or any(u == v for u, v in internal):
            cycles.append({"members": sorted(comp), "edges": internal})
    cycles.sort(key=lambda x: (x["members"], x["edges"]))
    payload = json.dumps(cycles, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest(), cycles


def run():
    rng = random.Random(SEED_MAIN)
    result = {
        "cases": CASES,
        "import_cycle_cases": 0,
        "eager_value_cycle_cases": 0,
        "import_cycle_but_eager_acyclic_cases": 0,
        "proposed_accepted_eager_acyclic_cases": 0,
        "proposed_order_perturbation_failures": 0,
        "naive_partial_init_order_divergence_cases": 0,
        "naive_partial_init_uninitialized_read_cases": 0,
    }
    for _ in range(CASES):
        n = rng.randint(2, 8)
        eager = []
        imports = []
        for u in range(n):
            for v in range(n):
                if u == v:
                    continue
                if rng.random() < 0.10:
                    eager.append((u, v))
                    imports.append((u, v))
                elif rng.random() < 0.12:
                    imports.append((u, v))
        import_cycle = has_cycle(n, imports)
        eager_cycle = has_cycle(n, eager)
        result["import_cycle_cases"] += int(import_cycle)
        result["eager_value_cycle_cases"] += int(eager_cycle)
        result["import_cycle_but_eager_acyclic_cases"] += int(import_cycle and not eager_cycle)
        base = [rng.randint(1, 9) for _ in range(n)]
        if not eager_cycle:
            result["proposed_accepted_eager_acyclic_cases"] += 1
            baseline = eval_stable(n, eager, base)
            for _ in range(3):
                shuffled = eager[:]
                rng.shuffle(shuffled)
                if eval_stable(n, shuffled, base) != baseline:
                    result["proposed_order_perturbation_failures"] += 1
                    break
        edge_a = eager[:]
        edge_b = eager[:]
        rng.shuffle(edge_a)
        rng.shuffle(edge_b)
        val_a, unread_a = eval_naive_partial(n, eager, base, list(range(n)), edge_a)
        val_b, unread_b = eval_naive_partial(n, eager, base, list(reversed(range(n))), edge_b)
        result["naive_partial_init_order_divergence_cases"] += int(val_a != val_b)
        result["naive_partial_init_uninitialized_read_cases"] += int((unread_a + unread_b) > 0)

    rng2 = random.Random(SEED_RECEIPT)
    receipt = {"cases": CASES, "cyclic_graphs": 0, "canonical_receipt_order_mismatches": 0}
    for _ in range(CASES):
        n = rng2.randint(2, 9)
        edges = [(u, v) for u in range(n) for v in range(n) if rng2.random() < 0.14]
        h1, c1 = canonical_cycle_receipt(n, edges)
        if c1:
            receipt["cyclic_graphs"] += 1
            shuffled = edges[:]
            rng2.shuffle(shuffled)
            h2, c2 = canonical_cycle_receipt(n, shuffled)
            receipt["canonical_receipt_order_mismatches"] += int(h1 != h2 or c1 != c2)

    print(json.dumps({"seed_main": SEED_MAIN, "seed_receipt": SEED_RECEIPT, "module_init": result, "cycle_receipt": receipt}, indent=2, sort_keys=True))


if __name__ == "__main__":
    run()
