"""Tier C (D259 as amended by D282): places above the finish a club's relative wage bill normally buys, tiers 1-2.
Expected finish: season effects, then a monotone (isotonic) curve in log relative payroll, per country. The quadratic of
v0.2 under-predicted both tails (England top decile +1.1 places, bottom +2.7; France bottom +2.2); the monotone curve's
mean residual is within 0.2 places at both tails in both countries. 95% interval by resampling the club's seasons;
published only for clubs with >= 8 seasons; signed only where the interval excludes zero. England: parachute seasons kept
and counted (D263); conflicting readings excluded (D277); Aston Villa from group accounts (D264, D274). France: group
(consolidated) perimeters excluded pending the D264 test.
Usage: FR_SRC=... python -I tierC.py ENG <england_wage_panel.csv> <eng_rcm_panel.csv> <out.csv>
       python -I tierC.py FRA <france_wage_panel.csv> <ladder_FRA.csv> <out.csv>"""
import sys, os
import numpy as np, pandas as pd
from sklearn.isotonic import IsotonicRegression

def expected(P):
    S = pd.get_dummies(P.season, dtype=float); X = S.copy(); X['w'] = P.w.values
    b, *_ = np.linalg.lstsq(X.values, P.p.values, rcond=None)
    se = S.values @ b[:-1]; adj = P.p.values - se + se.mean()
    ir = IsotonicRegression(out_of_bounds='clip').fit(P.w.values, adj)
    return np.clip(ir.predict(P.w.values) + se - se.mean(), 0, 1)

def ladder_rank(L):
    L = L[L.tier <= 2].sort_values(['Season', 'tier', 'pos']).copy()
    L['lrank'] = L.groupby('Season').cumcount() + 1; L['N'] = L.Season.map(L.groupby('Season').size()); return L

def table(P, rng, extra):
    P = P.reset_index(drop=True)
    P['w'] = np.log(P.pay / P.groupby('season').pay.transform('mean')); P['p'] = 1 - (P.lrank - 1) / (P.N - 1)
    P['places'] = (P.p - expected(P)) * (P.N - 1)
    out = []
    for k, g in P.groupby('k'):
        if len(g) < 8: continue
        v = g.places.values; bs = [rng.choice(v, len(v)).mean() for _ in range(2000)]
        lo, hi = np.percentile(bs, 2.5), np.percentile(bs, 97.5)
        row = dict(k=k, club=g.club.iloc[-1], seasons=len(g), places_above_expected=round(v.mean(), 2), lo=round(lo, 2), hi=round(hi, 2),
                   published_as=('%+.1f places' % v.mean()) if (lo > 0 or hi < 0) else 'within the normal range',
                   mean_relative_wage=round(np.exp(g.w.mean()), 2), seasons_tier1=int((g.tier == 1).sum()))
        row.update(extra(k, g)); out.append(row)
    return pd.DataFrame(out).sort_values('places_above_expected', ascending=False)

if __name__ == '__main__':
    rng = np.random.default_rng(42); c = sys.argv[1]
    if c == 'ENG':
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rcm'))
        from ladder import eng_ladder
        from clubkey import ck
        P = pd.read_csv(sys.argv[2]); RCM = pd.read_csv(sys.argv[3])
        P = P[~P.flag_xcheck_conflict.astype(bool)].drop(columns=['tier', 'pos'], errors='ignore').rename(columns={'payroll_k': 'pay'})
        L = eng_ladder(2, 2008, 2024); L['k'] = L.club.map(ck); L = ladder_rank(L)
        P = P.merge(L[['Season', 'k', 'club', 'tier', 'lrank', 'N']].rename(columns={'Season': 'season'}), on=['k', 'season'])
        para = RCM[['k', 'Season', 'parachute']].rename(columns={'Season': 'season'}).drop_duplicates(['k', 'season'])
        P = P.merge(para, on=['k', 'season'], how='left'); P['parachute'] = P.parachute.fillna(False).astype(bool)
        T = table(P, rng, lambda k, g: dict(parachute_seasons=int(g.parachute.sum()), group_accounts=k == 'aston villa'))
    else:
        P = pd.read_csv(sys.argv[2]); L = ladder_rank(pd.read_csv(sys.argv[3]))
        P = P[P.consolidated.fillna(False) == False].drop(columns=['tier', 'pos'], errors='ignore').rename(columns={'payroll_keur': 'pay'})
        P = P.merge(L[['Season', 'k', 'club', 'tier', 'lrank', 'N']].rename(columns={'Season': 'season'}), on=['k', 'season'])
        T = table(P, rng, lambda k, g: {})
    T.to_csv(sys.argv[4], index=False)
    print(f'{c}: {len(T)} clubs with >= 8 seasons; interval excludes zero for {int(((T.lo > 0) | (T.hi < 0)).sum())}; '
          f'corr with wage level {np.corrcoef(T.places_above_expected, np.log(T.mean_relative_wage))[0, 1]:+.2f}')
    print(T[(T.lo > 0) | (T.hi < 0)].to_string(index=False))
