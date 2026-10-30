"""Registered H1 test (Protocol §2): Anderson-Goodman order test + mover-stayer dBIC.
Usage: FR_SRC=... FR_LADDERS=... python -I h1.py <outdir> [quick]"""
import os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import load, with_states

QUICK = len(sys.argv) > 2
NPERM = 199 if QUICK else 1999
NPOW = 100 if QUICK else 500

def triples(d, usable, exit_state=False, K=5):
    """Arrays i,j,k,season for clubs present at t-1,t,(t+1 or exit)."""
    S = {s: g.set_index('k').st for s, g in d.groupby('Season')}
    I, J, Kk, T = [], [], [], []
    us = set(usable)
    for t in usable:
        if t - 1 not in us or t + 1 not in us: continue
        A, B, C = S[t - 1], S[t], S[t + 1]
        ix = A.index.intersection(B.index)
        nxt = C.reindex(ix)
        if exit_state: nxt = nxt.fillna(K)
        else: nxt = nxt.dropna(); ix = nxt.index
        I += list(A[ix].values); J += list(B[ix].values); Kk += list(nxt.values.astype(int)); T += [t] * len(ix)
    return (np.array(I, int), np.array(J, int), np.array(Kk, int), np.array(T, int))

def g2(i, j, k, Kd):
    """Anderson-Goodman LR statistic for order 1 vs order 2. Kd = number of destination categories."""
    K = max(i.max(), j.max()) + 1
    n = np.bincount((i * K + j) * Kd + k, minlength=K * K * Kd).reshape(K, K, Kd).astype(float)
    nij = n.sum(2, keepdims=True); njk = n.sum(0, keepdims=True); nj = n.sum((0, 2), keepdims=True)
    with np.errstate(divide='ignore', invalid='ignore'):
        term = np.where(n > 0, n * np.log(n * nj / (nij * njk)), 0.0)
    return 2 * term.sum(), n

def perm_within(j, k, t, rng):
    g = t * 100 + j
    base = np.argsort(g, kind='stable')
    perm = np.lexsort((rng.random(len(g)), g))
    out = np.empty_like(k); out[base] = k[perm]
    return out

def order_test(i, j, k, t, Kd, rng):
    obs, n = g2(i, j, k, Kd)
    pv = np.array([g2(i, j, perm_within(j, k, t, rng), Kd)[0] for _ in range(NPERM)])
    p_perm = (1 + (pv >= obs).sum()) / (NPERM + 1)
    # secondary: parametric bootstrap from pooled first-order chain
    K = n.shape[0]
    pjk = n.sum(0); pjk = pjk / np.maximum(pjk.sum(1, keepdims=True), 1)
    cum = np.cumsum(pjk, 1)
    def draw(probs_rows):
        u = rng.random(len(probs_rows))
        return (u[:, None] > probs_rows).sum(1)
    bv = []
    for _ in range(NPERM):
        kk = np.minimum(draw(cum[j]), Kd - 1)
        bv.append(g2(i, j, kk, Kd)[0])
    bv = np.array(bv)
    p_boot = (1 + (bv >= obs).sum()) / (NPERM + 1)
    crit = np.percentile(pv, 95)
    # power: p(lambda) = (1-l) p_jk + l p_ijk
    pijk = n / np.maximum(n.sum(2, keepdims=True), 1)
    power = {}
    for lam in (0.0, 0.25, 0.5, 1.0):
        pr = (1 - lam) * pjk[None, :, :] + lam * pijk
        pr = pr / np.maximum(pr.sum(2, keepdims=True), 1e-12)
        cp = np.cumsum(pr, 2)[i, j]
        hits = 0
        for _ in range(NPOW):
            kk = np.minimum(draw(cp), Kd - 1)
            hits += g2(i, j, kk, Kd)[0] > crit
        power[lam] = hits / NPOW
    return dict(G2=obs, p_perm=p_perm, p_boot=p_boot, crit95=crit, null_mean=pv.mean(),
                excess=obs / pv.mean(), n_triples=len(i), power=power)

# ---------------- mover-stayer ----------------
def spells(d, usable):
    us = set(usable); out = []
    for kk, g in d.sort_values('Season').groupby('k'):
        ss = g.Season.values; st = g.st.values
        cur = [st[0]]
        for a, b, sb in zip(ss, ss[1:], st[1:]):
            # consecutive and every season in between usable
            if b == a + 1:
                cur.append(sb)
            else:
                if len(cur) > 1: out.append(np.array(cur))
                cur = [sb]
        if len(cur) > 1: out.append(np.array(cur))
    return out

def fit_markov(sp, K):
    C = np.zeros((K, K))
    for s in sp: np.add.at(C, (s[:-1], s[1:]), 1)
    P = C / np.maximum(C.sum(1, keepdims=True), 1)
    with np.errstate(divide='ignore'):
        ll = np.where(C > 0, C * np.log(np.where(P > 0, P, 1)), 0).sum()
    npar = int(sum(max((C[r] > 0).sum() - 1, 0) for r in range(K)))
    return ll, npar, C, P

def fit_mover_stayer(sp, K, iters=5000, tol=1e-10):
    x0 = np.array([s[0] for s in sp]); T = np.array([len(s) - 1 for s in sp])
    const = np.array([np.all(s == s[0]) for s in sp])
    trans = [(s[:-1], s[1:]) for s in sp]
    _, _, C, M = fit_markov(sp, K)
    sh = np.full(K, 0.1); ll_old = -np.inf
    for it in range(iters):
        # E-step
        logmove = np.array([np.log(np.where(M[a, b] > 0, M[a, b], 1e-300)).sum() for a, b in trans])
        Lmove = (1 - sh[x0]) * np.exp(logmove)
        Lstay = np.where(const, sh[x0], 0.0)
        L = Lmove + Lstay
        ll = np.log(L).sum()
        w = np.where(const, Lstay / L, 0.0)
        # M-step
        sh = np.array([w[x0 == i].mean() if (x0 == i).any() else 0.0 for i in range(K)])
        Cw = np.zeros((K, K))
        for (a, b), wt in zip(trans, 1 - w): np.add.at(Cw, (a, b), wt)
        M = Cw / np.maximum(Cw.sum(1, keepdims=True), 1e-300)
        if abs(ll - ll_old) < tol: break
        ll_old = ll
    return ll, sh, M, it

def ms_test(d, usable, K):
    sp = spells(d, usable)
    llm, pm, C, _ = fit_markov(sp, K)
    llms, sh, M, it = fit_mover_stayer(sp, K)
    n_tr = int(C.sum()); n_sp = len(sp)
    out = dict(n_transitions=n_tr, n_spells=n_sp, ll_markov=llm, ll_ms=llms, p_markov=pm, p_ms=pm + K,
               stayer_share={i: round(float(s), 4) for i, s in enumerate(sh)}, em_iters=it)
    for lab, n in (('trans', n_tr), ('spells', n_sp)):
        bm = -2 * llm + pm * np.log(n); bms = -2 * llms + (pm + K) * np.log(n)
        out[f'dBIC_{lab}'] = bm - bms
    return out

def run(series, config, rng, exit_state=False):
    d, usable, nt = load(series)
    K, d = with_states(d, config, nt)
    i, j, k, t = triples(d, usable, exit_state, K)
    Kd = K + 1 if exit_state else K
    ot = order_test(i, j, k, t, Kd, rng)
    ms = ms_test(d, usable, K) if not exit_state else {}
    rej = (ot['p_perm'] >= 0.05) and (ms.get('dBIC_trans', np.nan) <= 10 if ms else True)
    return dict(series=series, config=config + ('+exit' if exit_state else ''), seasons=f"{usable[0]}-{usable[-1]}",
                n_usable=len(usable), **{f'ot_{a}': b for a, b in ot.items()}, **{f'ms_{a}': b for a, b in ms.items()},
                H1_rejected=bool(rej) if ms else None)

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(20261008)
    res = []
    plan = [('ENG-4', 'K5', False)] + [(s, 'K5', False) for s in ('ENG-2', 'ESP-2', 'ITA-2', 'GER-2', 'FRA-2')]
    plan += [(s, c, False) for s in ('ENG-4', 'ENG-2', 'ESP-2', 'ITA-2', 'GER-2', 'FRA-2') for c in ('K4', 'K6', 'EQ5')]
    plan += [(s, 'K5', True) for s in ('ENG-4', 'ENG-2', 'ESP-2', 'ITA-2', 'GER-2', 'FRA-2')]
    for s, c, ex in plan:
        r = run(s, c, rng, ex); res.append(r)
        print(json.dumps({a: (round(b, 4) if isinstance(b, float) else b) for a, b in r.items()}, default=str), flush=True)
    pd.DataFrame(res).to_csv(f"{out}/h1_results.csv", index=False)
