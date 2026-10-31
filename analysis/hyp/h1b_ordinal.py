"""H1b robustness (protocol section 5): ordinal logit in place of the multinomial logit. States are ordered 0 (top four)
to 5 (below tier 2); same regressors and the same permutation cells as h1b.py; 999 permutations (seed 20261102).
Usage: python -I h1b_ordinal.py <h1b_sample.csv> <out.json>"""
import sys, json, numpy as np, pandas as pd, warnings
from statsmodels.miscmodels.ordinal_model import OrderedModel
warnings.filterwarnings('ignore')
S, OUT = sys.argv[1:3]; d = pd.read_csv(S)
def X(dd, hist):
    t1 = (dd.s0 <= 2).astype(float)
    x = pd.concat([pd.get_dummies(dd.s0, prefix='s0').reindex(columns=[f's0_{i}' for i in range(1, 5)], fill_value=0),
                   pd.DataFrame({'w': dd.w, 'w2': dd.w ** 2, 'w_t1': dd.w * t1, 'fra': (dd.country == 'FRA').astype(float)})], axis=1)
    if hist: x = pd.concat([x, pd.get_dummies(dd.sm1, prefix='sm1').reindex(columns=[f'sm1_{i}' for i in range(1, 6)], fill_value=0)], axis=1)
    return x.astype(float)
def ll(dd, hist):
    return OrderedModel(dd.s1.values, X(dd, hist), distr='logit').fit(method='bfgs', disp=False, maxiter=2000).llf
def lr(dd): return 2 * (ll(dd, True) - ll(dd, False))
rng = np.random.default_rng(20261102); obs = lr(d)
groups = [g.index.values for _, g in d.groupby(['country', 'season', 's0', 'wt'])]
null = []
for _ in range(999):
    sm = d.sm1.values.copy()
    for ix in groups: sm[ix] = rng.permutation(sm[ix])
    null.append(lr(d.assign(sm1=sm)))
null = np.array(null)
r = dict(n=len(d), LR=round(obs, 3), null_mean=round(float(null.mean()), 3), crit95=round(float(np.percentile(null, 95)), 3), p=round(float((1 + (null >= obs).sum()) / 1000), 4))
json.dump(r, open(OUT, 'w')); print(r)
