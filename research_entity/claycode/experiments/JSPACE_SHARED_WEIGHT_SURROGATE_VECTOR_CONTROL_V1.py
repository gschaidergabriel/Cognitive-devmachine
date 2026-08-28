#!/usr/bin/env python3
"""Deterministic J-Space shared-weight hidden-vector control surrogate regression.

RESEARCH SURROGATE ONLY.
This script tests a mechanism: whether a low-dimensional basis learned from hidden-state
control gradients can steer many logical cells sharing the same model weights, compared
with matched random and orthogonal-lesion subspaces. It is not an LLM/API/model-runtime
acceptance test and grants zero EntityOS/HCU/J-Space model-runtime or training credit.
"""
from __future__ import annotations
import json, math, statistics
import torch

torch.set_num_threads(1)


def _orth(a: torch.Tensor) -> torch.Tensor:
    return torch.linalg.qr(a, mode="reduced")[0]


def nonlinear_seed(seed: int, *, cal=1200, trials=240, steps=50, rank=12, max_norm=3.5):
    din, h1d, h2d, nclass = 24, 64, 48, 8
    g = torch.Generator().manual_seed(seed)
    w1 = torch.randn(h1d, din, generator=g) / math.sqrt(din); b1 = torch.randn(h1d, generator=g) * .1
    w2 = torch.randn(h2d, h1d, generator=g) / math.sqrt(h1d); b2 = torch.randn(h2d, generator=g) * .1
    w3 = torch.randn(nclass, h2d, generator=g) / math.sqrt(h2d); b3 = torch.randn(nclass, generator=g) * .1
    hidden = lambda x: torch.tanh(x @ w1.T + b1)
    logits = lambda h: torch.tanh(h @ w2.T + b2) @ w3.T + b3

    x = torch.randn(cal, din, generator=g)
    h = hidden(x).requires_grad_(True)
    l = logits(h); base = l.argmax(1)
    target = (base + torch.randint(1, nclass, (cal,), generator=g)) % nclass
    objective = torch.log_softmax(l, 1).gather(1, target[:, None]).sum()
    grads = torch.autograd.grad(objective, h)[0].detach()
    _, _, vh = torch.linalg.svd(grads, full_matrices=False)
    learned = vh[:rank].T.contiguous()
    random_basis = _orth(torch.randn(h1d, rank, generator=g))
    r = torch.randn(h1d, rank, generator=g)
    lesion = _orth(r - learned @ (learned.T @ r))

    xh = torch.randn(trials, din, generator=g)
    h0 = hidden(xh).detach(); l0 = logits(h0); base0 = l0.argmax(1)
    t = (base0 + torch.randint(1, nclass, (trials,), generator=g)) % nclass
    p0 = torch.softmax(l0, 1).gather(1, t[:, None]).squeeze(1)

    def steer(basis):
        c = torch.zeros(trials, rank, requires_grad=True)
        opt = torch.optim.Adam([c], lr=.3)
        for _ in range(steps):
            opt.zero_grad()
            d = c @ basis.T
            d = d * torch.clamp(max_norm / d.norm(dim=1, keepdim=True).clamp_min(1e-12), max=1.)
            out = logits(h0 + d)
            loss = -torch.log_softmax(out, 1).gather(1, t[:, None]).mean() + .003 * d.pow(2).sum(1).mean()
            loss.backward(); opt.step()
            with torch.no_grad():
                c.mul_(torch.clamp(max_norm / c.norm(dim=1, keepdim=True).clamp_min(1e-12), max=1.))
        with torch.no_grad():
            d = c @ basis.T; out = logits(h0 + d)
            p = torch.softmax(out, 1).gather(1, t[:, None]).squeeze(1)
            success = (out.argmax(1) == t) & (p >= .55)
            return {
                "success_rate": float(success.float().mean()),
                "mean_initial_target_p": float(p0.mean()),
                "mean_final_target_p": float(p.mean()),
                "mean_control_norm": float(d.norm(dim=1).mean()),
            }

    return {"learned": steer(learned), "random": steer(random_basis), "lesion": steer(lesion)}


def linear_broadcast_seed(seed: int, *, batches=25, cells=10, rank=8, max_norm=4.0):
    din, hidden_dim, nclass, cal = 24, 64, 8, 800
    g = torch.Generator().manual_seed(seed)
    w1 = torch.randn(hidden_dim, din, generator=g) / math.sqrt(din); b1 = torch.randn(hidden_dim, generator=g) * .15
    w2 = torch.randn(nclass, hidden_dim, generator=g) / math.sqrt(hidden_dim); b2 = torch.randn(nclass, generator=g) * .1
    hidden = lambda x: torch.tanh(x @ w1.T + b1)
    logits = lambda h: h @ w2.T + b2
    x = torch.randn(cal, din, generator=g); h = hidden(x); l = logits(h); base = l.argmax(1)
    target = (base + torch.randint(1, nclass, (cal,), generator=g)) % nclass
    p = torch.softmax(l, 1)
    grads = w2[target] - p @ w2
    _, _, vh = torch.linalg.svd(grads, full_matrices=False)
    basis = vh[:rank].T.contiguous()

    counts, alphas = [], []
    for _ in range(batches):
        hb = hidden(torch.randn(cells, din, generator=g)); target_class = int(torch.randint(0, nclass, (1,), generator=g))
        pb = torch.softmax(logits(hb), 1)
        grad = (w2[target_class].unsqueeze(0) - pb @ w2).mean(0)
        v = basis @ (basis.T @ grad); v = v / (v.norm() + 1e-12)
        best = (-1.0, 0, 0.0)
        for alpha in torch.linspace(0, max_norm, 41):
            out = logits(hb + alpha * v); pred = out.argmax(1)
            succ = int((pred == target_class).sum()); prob = float(torch.softmax(out, 1)[:, target_class].mean())
            score = succ + .2 * prob
            if score > best[0]: best = (score, succ, float(alpha))
        counts.append(best[1]); alphas.append(best[2])
    return {
        "mean_cells_targeted": statistics.mean(counts),
        "median_cells_targeted": statistics.median(counts),
        "max_cells_targeted": max(counts),
        "cells_per_batch": cells,
        "mean_alpha": statistics.mean(alphas),
    }


def main():
    runs = []
    for seed in range(4):
        runs.append({"seed": seed, "nonlinear": nonlinear_seed(seed), "broadcast": linear_broadcast_seed(seed)})
    agg = {}
    for key in ("learned", "random", "lesion"):
        agg[key] = {m: statistics.mean(r["nonlinear"][key][m] for r in runs)
                    for m in ("success_rate", "mean_initial_target_p", "mean_final_target_p", "mean_control_norm")}
    agg["broadcast"] = {m: statistics.mean(r["broadcast"][m] for r in runs)
                        for m in ("mean_cells_targeted", "median_cells_targeted", "max_cells_targeted", "mean_alpha")}
    agg["broadcast"]["cells_per_batch"] = 10
    print(json.dumps({"schema": "JSPACE_SHARED_WEIGHT_SURROGATE_VECTOR_CONTROL_REGRESSION/v1", "runs": runs, "aggregate": agg}, sort_keys=True))


if __name__ == "__main__":
    main()
