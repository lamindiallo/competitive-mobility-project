"""Sensitivity of the D303 ranges on G to dependence between seasons (proposal P18, D321): the same G, with ranges from a
moving-block bootstrap of consecutive season pairs (blocks of 4) instead of independent draws of season pairs.
Usage: python g_block_bootstrap.py <data dir> <out.csv>"""
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'trend')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'site'))
import trend_eng
from trend_eng import G, pairs_of
from model import load
DATA, OUT = sys.argv[1:3]; rng = np.random.default_rng(1993); trend_eng.rng = np.random.default_rng(7)
L, _ = load(DATA)
def st(r):
    if r.tier == 1: return 0 if r.pos <= 4 else (1 if r.pos <= 10 else 2)
    return 1 + r.tier
rows = []; BLOCK = 4; draws = {}
for c, d in L.items():
    lad = d[['k', 'Season', 'tier', 'pos']].copy(); lad['st'] = [st(r) for r in lad.itertuples()]
    K = int(lad.st.max()) + 1; PR = pairs_of(lad); keys = sorted(PR); prs = [PR[k] for k in keys]; n = len(prs)
    g = G(prs, K=K, reps=300)[2]; bs = []
    for _ in range(300):
        idx = []
        while len(idx) < n:
            s0 = rng.integers(0, n - BLOCK + 1); idx.extend(range(s0, s0 + BLOCK))
        r = G([prs[i] for i in idx[:n]], K=K, reps=60)[2]
        if r == r: bs.append(r)
    draws[c] = np.array(bs)
    rows.append(dict(country=c, G=round(g, 2), lo_block=round(np.percentile(bs, 2.5), 2), hi_block=round(np.percentile(bs, 97.5), 2)))
    print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(OUT, index=False)
cmp = [dict(country=c, share_england_higher=round(float((draws['ENG'][:, None] > draws[c][None, :]).mean()), 3)) for c in draws if c != 'ENG']
pd.DataFrame(cmp).to_csv(OUT.replace('.csv', '_england_vs.csv'), index=False); print(cmp)
