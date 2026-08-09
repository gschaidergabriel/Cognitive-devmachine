import numpy as np


def run(seed, steps=5000, unknown_rate=0.35, alpha=0.03, threshold=1.6, trusted_rate=0.12):
    rng = np.random.default_rng(seed)
    init = np.array([[-2.0, 0.0], [2.0, 0.0]])
    prot_naive = init.copy()
    prot_gated = init.copy()
    wrong_unknown_updates = 0
    naive_updates = 0

    for t in range(steps):
        frac = t / (steps - 1)
        centers = np.array([
            [-2.0 + 0.25 * frac, 0.7 * frac],
            [2.0 - 0.20 * frac, -0.6 * frac],
        ])
        is_unknown = rng.random() < unknown_rate
        if is_unknown:
            if frac < 0.5:
                ucenter = np.array([-0.7 - 1.0 * frac, 0.4])
            else:
                ucenter = np.array([0.2 + 1.8 * (frac - 0.5), -0.3])
            x = rng.normal(ucenter, 0.65, size=2)
            true = None
            trusted = False
        else:
            true = int(rng.integers(0, 2))
            x = rng.normal(centers[true], 0.55, size=2)
            trusted = rng.random() < trusted_rate

        d = np.linalg.norm(prot_naive - x, axis=1)
        pred = int(d.argmin())
        if d[pred] < threshold:
            prot_naive[pred] = (1 - alpha) * prot_naive[pred] + alpha * x
            naive_updates += 1
            if true is None:
                wrong_unknown_updates += 1

        if trusted and true is not None:
            prot_gated[true] = (1 - alpha) * prot_gated[true] + alpha * x

    centers = np.array([[-1.75, 0.7], [1.8, -0.6]])
    known_x = np.vstack([
        rng.normal(centers[0], 0.55, size=(1000, 2)),
        rng.normal(centers[1], 0.55, size=(1000, 2)),
    ])
    known_y = np.concatenate([np.zeros(1000, dtype=int), np.ones(1000, dtype=int)])
    unknown_x = np.vstack([
        rng.normal([1.1, -0.3], 0.65, size=(1000, 2)),
        rng.normal([0.0, 1.3], 0.7, size=(1000, 2)),
    ])

    def metrics(proto):
        kd = np.linalg.norm(known_x[:, None, :] - proto[None, :, :], axis=2)
        known_acc = (kd.argmin(axis=1) == known_y).mean()
        ud = np.linalg.norm(unknown_x[:, None, :] - proto[None, :, :], axis=2).min(axis=1)
        unknown_reject = (ud >= threshold).mean()
        return float(known_acc), float(unknown_reject)

    n_acc, n_unk = metrics(prot_naive)
    g_acc, g_unk = metrics(prot_gated)
    return {
        "known_acc_naive": n_acc,
        "known_acc_gated": g_acc,
        "unknown_reject_naive": n_unk,
        "unknown_reject_gated": g_unk,
        "naive_wrong_unknown_update_fraction": wrong_unknown_updates / max(1, naive_updates),
    }


if __name__ == "__main__":
    for unknown_rate in [0.10, 0.25, 0.40, 0.55, 0.70]:
        rows = [run(1000 + i, unknown_rate=unknown_rate) for i in range(30)]
        keys = rows[0].keys()
        means = {k: sum(r[k] for r in rows) / len(rows) for k in keys}
        print(unknown_rate, means)
