"""Gross mobility G with 95% intervals, from the site's own ladders (D303).
G = expected seasons from the bottom part of the top flight (11th to last) to its top four, divided by the same quantity
in a league where each season's destinations are shuffled at random (trend_eng.G, D172). Ladder: England four divisions,
elsewhere two; seasons 1992/93 (or the league's first season here) to the latest. Interval: seasons resampled in blocks
(season pairs drawn with replacement), as in trend_eras.py. Also reported: G with Spanish reserve teams removed from the
ladder, to show they do not drive the figure.
Also writes <out>_england_vs.csv: the share of resample pairs in which England's G is higher than each other league's.
Usage: python g_intervals.py <data dir> <out.csv>"""
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'trend')); sys.path.insert(0, os.path.join(HERE, '..', '..', 'site'))
import trend_eng
from trend_eng import G, pairs_of
from model import load
DATA, OUT = sys.argv[1:3]; rng = np.random.default_rng(1992); trend_eng.rng = np.random.default_rng(7)
L, _ = load(DATA)
def st(r):
    if r.tier == 1: return 0 if r.pos <= 4 else (1 if r.pos <= 10 else 2)
    return 1 + r.tier
rows = []; draws = {}
for c, d in L.items():
    for variant, dd in (('all', d), ('no_reserves', d[~d.reserve])):
        if variant == 'no_reserves' and not d.reserve.any(): continue
        lad = dd[['k', 'Season', 'tier', 'pos']].copy(); lad['st'] = [st(r) for r in lad.itertuples()]
        K = int(lad.st.max()) + 1; PR = pairs_of(lad); prs = list(PR.values())
        o, n, g = G(prs, K=K, reps=300); bs = []
        for _ in range(300):
            pick = rng.integers(0, len(prs), len(prs)); r = G([prs[i] for i in pick], K=K, reps=60)[2]
            if r == r: bs.append(r)
        if variant == 'all': draws[c] = np.array(bs)
        rows.append(dict(country=c, variant=variant, seasons=f'{min(PR)}-{max(PR) + 1}', season_pairs=len(prs), K=K, observed=round(o, 2), null=round(n, 2),
                         G=round(g, 2), lo=round(np.percentile(bs, 2.5), 2), hi=round(np.percentile(bs, 97.5), 2)))
        print(rows[-1], flush=True)
pd.DataFrame(rows).to_csv(OUT, index=False)
# How often England's resampled G exceeds each other league's (independent resamples; a share near 1 means England is clearly the least mobile)
cmp = [dict(country=c, share_england_higher=round(float((draws['ENG'][:, None] > draws[c][None, :]).mean()), 3)) for c in draws if c != 'ENG']
pd.DataFrame(cmp).to_csv(OUT.replace('.csv', '_england_vs.csv'), index=False); print(cmp)
