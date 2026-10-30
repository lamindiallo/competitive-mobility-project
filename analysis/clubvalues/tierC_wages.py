"""Tier C prototype on real wages (France): places above the finish a club's relative wage bill normally buys.
Expected performance: quadratic in log relative wage with season fixed effects, capped to the feasible range.
Usage: python -I tierC_wages.py <france_wage_panel.csv> <ladder_FRA.csv> <out.csv>"""
import sys, numpy as np, pandas as pd
rng = np.random.default_rng(42)
P = pd.read_csv(sys.argv[1]); L = pd.read_csv(sys.argv[2]).sort_values(['Season', 'tier', 'pos'])
L['lrank'] = L.groupby('Season').cumcount() + 1; L['N'] = L.Season.map(L.groupby('Season').size())
P = P.merge(L[['Season', 'k', 'lrank', 'N']].rename(columns={'Season': 'season'}), on=['season', 'k'], how='left')
P = P[P.consolidated.fillna(False) == False].copy()          # group perimeters not comparable
P['w'] = np.log(P.payroll_keur / P.groupby('season').payroll_keur.transform('mean'))
P['p'] = 1 - (P.lrank - 1) / (P.N - 1)
X = pd.get_dummies(P.season, prefix='s', dtype=float); X['w'] = P.w; X['w2'] = P.w ** 2
beta, *_ = np.linalg.lstsq(X.values, P.p.values, rcond=None)
P['phat'] = np.clip(X.values @ beta, 0, 1)                  # a club cannot be expected to finish above first
P['places'] = (P.p - P.phat) * (P.N - 1)
out = []
for k, g in P.groupby('k'):
    if len(g) < 8: continue
    v = g.places.values; bs = [rng.choice(v, len(v)).mean() for _ in range(2000)]
    out.append(dict(club=g.ladder_club.iloc[-1], seasons=len(g), places_above_expected=round(v.mean(), 2),
                    lo=round(np.percentile(bs, 2.5), 2), hi=round(np.percentile(bs, 97.5), 2),
                    mean_relative_wage=round(np.exp(g.w.mean()), 2), seasons_tier1=int((g.tier == 1).sum())))
T = pd.DataFrame(out).sort_values('places_above_expected', ascending=False); T.to_csv(sys.argv[3], index=False)
print(len(T), 'clubs; interval excludes zero for', int(((T.lo > 0) | (T.hi < 0)).sum()))
print('corr with wage level %.2f' % np.corrcoef(T.places_above_expected, np.log(T.mean_relative_wage))[0, 1])
print(T.head(8).to_string(index=False)); print('...'); print(T.tail(6).to_string(index=False))
