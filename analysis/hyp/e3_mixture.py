"""EXPLORATORY (E3, not a registered test). Does persistent club heterogeneity reproduce the
second-order dependence found by the H1 order test?
Fit a C-class mixture of first-order Markov chains to spells (EM); simulate spells of the same
initial state and length from the fitted mixture; recompute the Anderson-Goodman G2 on the
simulated triples. If observed G2 sits inside the simulated distribution, fixed club types are
enough to produce it, and the order test cannot be read as path dependence (D041).
Usage: FR_SRC=... FR_LADDERS=... python -I e3_mixture.py <outdir>"""
import os, sys, json, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import load, with_states
from h1 import spells, g2

def fit_mixture(sp, K, C, rng, iters=2000, tol=1e-8, starts=8):
    x0 = np.array([s[0] for s in sp])
    T = [np.zeros((K, K)) for _ in sp]
    for t, s in zip(T, sp): np.add.at(t, (s[:-1], s[1:]), 1)
    T = np.array(T)
    best = None
    for _ in range(starts):
        R = rng.dirichlet(np.ones(C), len(sp))
        ll_old = -np.inf
        for it in range(iters):
            pi = np.array([[R[x0 == i, c].sum() for c in range(C)] for i in range(K)])
            pi = (pi + 1e-9) / (pi + 1e-9).sum(1, keepdims=True)
            M = np.einsum('sc,sij->cij', R, T)
            M = M / np.maximum(M.sum(2, keepdims=True), 1e-300)
            logM = np.log(np.where(M > 0, M, 1e-300))
            lj = np.einsum('sij,cij->sc', T, logM) + np.log(pi[x0])
            mx = lj.max(1, keepdims=True); L = np.exp(lj - mx)
            ll = (mx[:, 0] + np.log(L.sum(1))).sum()
            R = L / L.sum(1, keepdims=True)
            if abs(ll - ll_old) < tol: break
            ll_old = ll
        if best is None or ll > best[0]: best = (ll, pi, M, R)
    ll, pi, M, R = best
    npar = C * int(sum(max((T.sum(0)[r] > 0).sum() - 1, 0) for r in range(K))) + K * (C - 1)
    return ll, npar, pi, M

def sim_triples(sp, pi, M, rng):
    I, J, Kk = [], [], []
    K = M.shape[1]
    for s in sp:
        c = rng.choice(len(M), p=pi[s[0]])
        x = [s[0]]
        for _ in range(len(s) - 1):
            x.append(rng.choice(K, p=M[c, x[-1]]) if M[c, x[-1]].sum() > 0 else x[-1])
        x = np.array(x)
        if len(x) >= 3: I += list(x[:-2]); J += list(x[1:-1]); Kk += list(x[2:])
    return np.array(I), np.array(J), np.array(Kk)

if __name__ == '__main__':
    out = sys.argv[1]; rng = np.random.default_rng(31415)
    res = []
    for series in ('ENG-4', 'ENG-2', 'ESP-2', 'ITA-2', 'GER-2', 'FRA-2'):
        d, u, nt = load(series); K, d = with_states(d, 'K5', nt)
        sp = spells(d, u)
        tri = [(s[:-2], s[1:-1], s[2:]) for s in sp if len(s) >= 3]
        i = np.concatenate([a for a, _, _ in tri]); j = np.concatenate([b for _, b, _ in tri]); k = np.concatenate([c for _, _, c in tri])
        obs = g2(i, j, k, K)[0]
        ntr = sum(len(s) - 1 for s in sp)
        for C in (1, 2, 3):
            ll, npar, pi, M = fit_mixture(sp, K, C, rng)
            sims = np.array([g2(*sim_triples(sp, pi, M, rng), K)[0] for _ in range(300)])
            r = dict(series=series, C=C, ll=ll, npar=npar, BIC=-2 * ll + npar * np.log(ntr), G2_obs=obs,
                     G2_sim_mean=sims.mean(), G2_sim_95=np.percentile(sims, 95), p=(1 + (sims >= obs).sum()) / 301,
                     class_share_by_x0=np.round(pi, 3).tolist())
            res.append(r)
            print(json.dumps({a: (round(b, 3) if isinstance(b, float) else b) for a, b in r.items()}), flush=True)
    with open(f"{out}/e3_mixture.jsonl", 'w') as fh:
        for r in res: fh.write(json.dumps(r, default=float) + '\n')
