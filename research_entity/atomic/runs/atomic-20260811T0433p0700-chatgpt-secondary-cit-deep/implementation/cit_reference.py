"""CIT-001 synthetic discriminator.
Research-only. No Frank runtime import, external effect, canonical DB write, or training.
"""
from __future__ import annotations
import numpy as np
from sklearn.linear_model import OrthogonalMatchingPursuit


def omp_cv(M, y, seed, kmax=32):
    rng = np.random.default_rng(seed)
    idx = rng.permutation(len(y))
    nv = max(8, len(y)//4)
    va, tr = idx[:nv], idx[nv:]
    best = None
    for k in range(1, min(kmax, len(tr)-2, M.shape[1]) + 1):
        model = OrthogonalMatchingPursuit(n_nonzero_coefs=k, fit_intercept=False)
        model.fit(M[tr], y[tr])
        rmse = float(np.sqrt(np.mean((y[va] - model.predict(M[va]))**2)))
        score = rmse + 0.001*k
        if best is None or score < best[0]:
            best = (score, k, rmse)
    if best is None:
        return 0, np.zeros(M.shape[1]), float('inf')
    k = best[1]
    model = OrthogonalMatchingPursuit(n_nonzero_coefs=k, fit_intercept=False)
    model.fit(M, y)
    return k, model.coef_.copy(), best[2]


def trial(seed: int, N=256, k=8, m=80, interaction=0.0,
          density=0.12, noise=0.01, stale_rate=0.10,
          audit_m=16, val_thresh=0.10, audit_thresh=0.06,
          kmax_accept=12, material_thresh=0.05):
    rng = np.random.default_rng(seed)
    support = rng.choice(N, k, replace=False)
    beta = np.zeros(N)
    beta[support] = rng.uniform(0.2, 1.0, k) * rng.choice([-1, 1], k)
    pairs = []
    for _ in range(max(4, k)):
        i, j = rng.choice(support, 2, replace=False)
        pairs.append((i, j, rng.uniform(-interaction, interaction)))

    def utility(x):
        return float(beta @ x + sum(g*x[i]*x[j] for i, j, g in pairs))

    x0 = np.ones(N)
    u0 = utility(x0)
    exact_loo = np.array([
        u0 - utility(np.where(np.arange(N) == i, 0, 1)) for i in range(N)
    ])
    material = set(np.flatnonzero(np.abs(exact_loo) > material_thresh).tolist())

    masks = (rng.random((m, N)) < density).astype(float)
    y = np.array([
        u0 - utility(np.where(mask.astype(bool), 0, 1)) for mask in masks
    ]) + rng.normal(0, noise, m)

    # Metadata gate: stale probes are rejected rather than fitted.
    stale = rng.random(m) < stale_rate
    good = ~stale
    khat, coef, val_rmse = omp_cv(masks[good], y[good], seed+777,
                                  kmax=min(32, max(2, int(good.sum()/3))))
    candidate = set(np.argsort(np.abs(coef))[-max(1, khat):].tolist())
    preaccept = 0 < khat <= kmax_accept and val_rmse <= val_thresh

    # Complement audit: probe only outside predicted candidates.
    audit = []
    complement = np.array([i for i in range(N) if i not in candidate])
    if preaccept and len(complement):
        for _ in range(audit_m):
            sel = complement[rng.random(len(complement)) < density]
            if len(sel) == 0:
                sel = np.array([rng.choice(complement)])
            x = x0.copy(); x[sel] = 0
            audit.append((u0 - utility(x)) + rng.normal(0, noise))
    audit_max = max(map(abs, audit)) if audit else 0.0
    accept = preaccept and audit_max <= audit_thresh

    # Critical safety: accepted tomography still does not mint credit.
    # Exact individual confirmation is required for selected candidates.
    # Rejected screens fall back to full individual LOO.
    if accept:
        confirmed = {i for i in candidate if abs(exact_loo[i]) > material_thresh}
        interventions = m + audit_m + len(candidate)
    else:
        confirmed = material
        interventions = m + N

    recall = len(confirmed & material) / len(material) if material else 1.0
    precision = len(confirmed & material) / len(confirmed) if confirmed else (1.0 if not material else 0.0)
    return {
        'seed': seed, 'N': N, 'k_nominal': k, 'interaction_strength': interaction,
        'khat': khat, 'val_rmse': val_rmse, 'audit_max': audit_max,
        'accepted_sparse_screen': accept, 'material_causes': len(material),
        'screen_recall': len(candidate & material)/len(material) if material else 1.0,
        'final_confirmed_recall': recall, 'final_confirmed_precision': precision,
        'total_interventions': interventions,
        'intervention_ratio_vs_full_LOO': interventions/N,
    }


if __name__ == '__main__':
    regimes = [('SPARSE_ADDITIVE',4,0.0), ('SPARSE_MODERATE_INTERACTION',8,0.25),
               ('SPARSE_STRONG_INTERACTION',8,1.0), ('DENSE_ADDITIVE',16,0.0)]
    for rix, (name, k, interaction) in enumerate(regimes):
        rows = [trial(202608110000 + 10000*rix + j, k=k, interaction=interaction)
                for j in range(20)]
        print(name,
              'accept_rate=', np.mean([x['accepted_sparse_screen'] for x in rows]),
              'median_ratio=', np.median([x['intervention_ratio_vs_full_LOO'] for x in rows]),
              'min_confirmed_recall=', min(x['final_confirmed_recall'] for x in rows))
