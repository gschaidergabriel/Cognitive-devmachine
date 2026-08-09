import numpy as np


def simulate(seed, coupling=0.0, T=4000, lesion=False, lesion_start=2500):
    rng = np.random.default_rng(seed)
    n_c = rng.normal(0, 0.4, size=T)
    n_a = rng.normal(0, 0.35, size=T)
    n_b = rng.normal(0, 0.35, size=T)
    C = np.zeros(T)
    A = np.zeros(T)
    B = np.zeros(T)
    for t in range(2, T):
        C[t] = 0.9 * C[t - 1] + n_c[t]
        if lesion and t >= lesion_start:
            A[t] = 0.0
        else:
            A[t] = 0.6 * A[t - 1] + 0.9 * C[t - 1] + n_a[t]
        B[t] = 0.55 * B[t - 1] + 0.9 * C[t - 2] + coupling * A[t - 1] + n_b[t]
    return C, A, B


def ols_mse(X, y):
    X = np.c_[np.ones(len(X)), X]
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    pred = X @ beta
    return float(((y - pred) ** 2).mean()), beta


def measure(seed, coupling):
    T = 4000
    C, A, B = simulate(seed, coupling=coupling, T=T, lesion=False)
    idx = np.arange(500, T)
    y = B[idx]
    mse_base, _ = ols_mse(B[idx - 1, None], y)
    mse_a, beta_a = ols_mse(np.c_[B[idx - 1], A[idx - 1]], y)
    _, beta_ac = ols_mse(np.c_[B[idx - 1], A[idx - 1], C[idx - 2]], y)

    _, _, b_control = simulate(seed, coupling=coupling, T=T, lesion=False)
    _, _, b_lesion = simulate(seed, coupling=coupling, T=T, lesion=True)
    post = np.arange(2520, T)
    delta = b_control[post] - b_lesion[post]

    return {
        "directed_prediction_gain": 1.0 - mse_a / mse_base,
        "a_coefficient_without_common_driver": float(beta_a[-1]),
        "a_coefficient_with_common_driver": float(beta_ac[-2]),
        "lesion_downstream_mae": float(np.abs(delta).mean()),
        "lesion_downstream_rms": float(np.sqrt((delta ** 2).mean())),
    }


if __name__ == "__main__":
    for coupling in [0.0, 0.35]:
        rows = [measure(2000 + i, coupling) for i in range(50)]
        means = {k: sum(r[k] for r in rows) / len(rows) for k in rows[0]}
        print(coupling, means)
