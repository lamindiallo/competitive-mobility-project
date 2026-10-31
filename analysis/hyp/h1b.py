"""Registered H1b test (06 Analysis/H1b_Test_Protocol.md, written 31 Oct 2026 12:40 UTC, before any H1b statistic).
Does a club's previous-season state predict its next-season state beyond its current state and its current wage bill?
England (2011/12-2024/25) and France (2008/09-2022/23, no 2012/13-2013/14), tiers 1-2.

Implementation notes (not changes to the test):
  - s_{t-1} uses the same six states as s_{t+1}; state 5 at t-1 means the club was below tier 2 the season before
    (promoted from England's third tier, or arriving from below Ligue 2 / not on the French ladder).
  - Multinomial logits are fitted with a negligible ridge (C = 1e4) in every fit, null and observed alike, so that sparse
    cells cannot make a fit diverge; the LR statistic is computed from the fitted probabilities.
  - Power (protocol section 4) is computed against the critical value of the observed permutation null rather than
    by re-permuting every simulated data set (500 x 3 x 1,999 fits would be needed otherwise).
Usage: python -I h1b.py <data dir> <out dir> [quick]"""
import os, sys, json
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression
HERE = os.path.dirname(os.path.abspath(__file__))
DATA, OUT = sys.argv[1:3]; os.makedirs(OUT, exist_ok=True)
QUICK = len(sys.argv) > 3
NPERM = 199 if QUICK else 1999; NSIM = 100 if QUICK else 500
K = 6

def state(r):
    if r is None or r.tier > 2: return 5
    if r.tier == 1: return 0 if r.pos <= 4 else (1 if r.pos <= 10 else 2)
    return 3 if r.pos <= 6 else 4

def build():
    T = pd.read_csv(os.path.join(DATA, 'tierC_seasons.csv'))
    rows = []
    for c, f in (('ENG', 'ladder_ENG4.csv'), ('FRA', 'ladder_FRA.csv')):
        L = pd.read_csv(os.path.join(DATA, f)); S = {(r.k, r.Season): r for r in L.itertuples()}
        last = int(L.Season.max())
        t = T[T.country == c].copy(); t['w'] = np.log(t.pay / t.groupby('season').pay.transform('mean'))
        for r in t.itertuples():
            s = int(r.season); cur = S.get((r.k, s))
            if cur is None or cur.tier > 2 or s + 1 > last: continue
            prv = S.get((r.k, s - 1)); nxt = S.get((r.k, s + 1))
            if s - 1 < int(L.Season.min()): continue
            # parachute: an English tier-2 club that was in tier 1 one or two seasons earlier (D263)
            para = c == 'ENG' and cur.tier == 2 and any((x := S.get((r.k, s - i))) is not None and x.tier == 1 for i in (1, 2))
            rows.append(dict(country=c, k=r.k, season=s, s0=state(cur), sm1=state(prv), s1=state(nxt), w=r.w, para=para))
    d = pd.DataFrame(rows)
    d['wt'] = d.groupby(['country', 'season']).w.transform(lambda x: pd.qcut(x.rank(method='first'), 3, labels=False)).astype(int)
    return d

def design(d, hist=True, wage=True, wage_terc=False):
    X = [pd.get_dummies(d.s0, prefix='s0').reindex(columns=[f's0_{i}' for i in range(1, 5)], fill_value=0)]
    if wage:
        if wage_terc: X.append(pd.get_dummies(d.wt, prefix='wt').reindex(columns=['wt_1', 'wt_2'], fill_value=0))
        else:
            t1 = (d.s0 <= 2).astype(float)
            X.append(pd.DataFrame({'w': d.w, 'w2': d.w ** 2, 'w_t1': d.w * t1}))
    X.append(pd.DataFrame({'fra': (d.country == 'FRA').astype(float)}))
    if hist: X.append(pd.get_dummies(d.sm1, prefix='sm1').reindex(columns=[f'sm1_{i}' for i in range(1, 6)], fill_value=0))
    return pd.concat(X, axis=1).astype(float).values

def loglik(X, y):
    m = LogisticRegression(C=1e4, max_iter=5000).fit(X, y)
    P = m.predict_proba(X); idx = np.searchsorted(m.classes_, y)
    return float(np.log(np.clip(P[np.arange(len(y)), idx], 1e-12, 1)).sum()), m

def lr_stat(d, sm1, wage=True, wage_terc=False):
    dd = d.assign(sm1=sm1)
    l0, _ = loglik(design(dd, False, wage, wage_terc), dd.s1.values)
    l1, _ = loglik(design(dd, True, wage, wage_terc), dd.s1.values)
    return 2 * (l1 - l0)

def perm_test(d, rng, cells, wage=True, wage_terc=False, nperm=NPERM):
    obs = lr_stat(d, d.sm1.values, wage, wage_terc)
    groups = [g.index.values for _, g in d.groupby(cells)]
    null = []
    for _ in range(nperm):
        sm = d.sm1.values.copy()
        for ix in groups:
            pos = d.index.get_indexer(ix); sm[pos] = rng.permutation(sm[pos])
        null.append(lr_stat(d, sm, wage, wage_terc))
    null = np.array(null)
    return dict(n=len(d), LR=round(obs, 3), null_mean=round(float(null.mean()), 3), crit95=round(float(np.percentile(null, 95)), 3),
                p=round(float((1 + (null >= obs).sum()) / (nperm + 1)), 4)), null

def power(d, crit, rng):
    """Simulate s_{t+1} from M0 plus lambda x the history effect estimated without wages; reject if LR > crit."""
    X0 = design(d, False, True); _, m0 = loglik(X0, d.s1.values)
    Xh = design(d, True, False); _, mh = loglik(Xh, d.s1.values)
    nh = 5; base = m0.decision_function(X0); hist = Xh[:, -nh:] @ mh.coef_[:, -nh:].T
    # align class columns (both models are fitted on the same y, so classes_ coincide)
    out = {}
    for lam in (0.0, 0.5, 1.0):
        eta = base + lam * hist; P = np.exp(eta - eta.max(1, keepdims=True)); P /= P.sum(1, keepdims=True)
        rej = 0
        for _ in range(NSIM):
            y = np.array([rng.choice(m0.classes_, p=p) for p in P])
            dd = d.assign(s1=y)
            try: rej += lr_stat(dd, dd.sm1.values) > crit
            except ValueError: pass
        out[str(lam)] = round(rej / NSIM, 3)
    return out

if __name__ == '__main__':
    d = build(); d.to_csv(os.path.join(OUT, 'h1b_sample.csv'), index=False)
    print('sample', len(d), d.groupby('country').size().to_dict(), flush=True)
    res = {}
    rng = np.random.default_rng(20261101)
    cells = ['country', 'season', 's0', 'wt']
    res['primary'], null = perm_test(d, rng, cells); print('primary', res['primary'], flush=True)
    res['no_wage_same_sample'], _ = perm_test(d, rng, ['country', 'season', 's0'], wage=False); print('no wage', res['no_wage_same_sample'], flush=True)
    for c in ('ENG', 'FRA'):
        dc = d[d.country == c].reset_index(drop=True)
        res[f'country_{c}'], _ = perm_test(dc, rng, cells); print(c, res[f'country_{c}'], flush=True)
    res['power'] = power(d, res['primary']['crit95'], rng); print('power', res['power'], flush=True)
    res['rob_wage_terciles'], _ = perm_test(d, rng, cells, wage_terc=True); print('terciles', res['rob_wage_terciles'], flush=True)
    de = d[(d.country == 'ENG') & (d.s0 <= 2)].reset_index(drop=True)
    res['rob_england_tier1'], _ = perm_test(de, rng, cells); print('eng t1', res['rob_england_tier1'], flush=True)
    dn = d[~d.para].reset_index(drop=True)
    res['rob_no_parachute'], _ = perm_test(dn, rng, cells); print('no parachute', res['rob_no_parachute'], flush=True)
    res['H1b_rejected'] = bool(res['primary']['p'] >= 0.05)
    json.dump(res, open(os.path.join(OUT, 'h1b_results.json'), 'w'), indent=1)
    print(json.dumps(res, indent=1))
