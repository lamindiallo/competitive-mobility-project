"""Checks run on the wage panels before any registered wage test.
(a) England proxy validation, as D256 for France: Spearman rho between the transfer-spend proxy R3 and payroll, by season.
(b) D221 re-estimated on payroll (England vs France, top flight): at equal relative payroll, do English clubs outside the
    top four reach it less often within five seasons? Exploratory; H12 stays Draft until registered.
Usage: FR_SRC=... python -I wage_checks.py <england_wage_panel.csv> <france_wage_panel.csv> <ladder_FRA.csv> <eng_rcm_panel.csv> <xc_panel.csv>"""
import sys, os
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy.stats import spearmanr
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rcm'))
from ladder import eng_ladder
from clubkey import ck

def coverage(P, L, pay):
    """Share of tier-1 clubs with a payroll value, by season."""
    t1 = L[L.tier == 1].groupby('Season').size()
    have = P[(P.tier == 1) & P[pay].notna()].groupby('season').size()
    return (have / t1).dropna()

def proxy_validation(EP, RCM):
    R = RCM[RCM.tier <= 2][['k', 'Season', 'tier', 'R3']].rename(columns={'Season': 'season'})
    M = EP.merge(R, on=['k', 'season', 'tier'], how='inner').dropna(subset=['payroll_k', 'R3'])
    out = []
    for (s, t), g in M.groupby(['season', 'tier']):
        if len(g) >= 8: out.append(dict(season=s, tier=t, n=len(g), rho=spearmanr(g.R3, g.payroll_k)[0]))
    return pd.DataFrame(out)

def reach_rows(P, L, pay, country, min_cov):
    """Top-flight clubs outside the top four at t, with relative payroll (÷ 4th-largest), and whether they reach the top four in t+1..t+5."""
    L1 = L[L.tier == 1]; last = L1.Season.max(); cov = coverage(P, L, pay)
    top4 = {s: set(g[g.pos <= 4].k) for s, g in L1.groupby('Season')}
    rows = []
    for s, g in P[(P.tier == 1) & P[pay].notna()].groupby('season'):
        if s + 5 > last or cov.get(s, 0) < min_cov: continue
        ref = g[pay].sort_values(ascending=False).iloc[3]
        hit = set().union(*[top4.get(s + j, set()) for j in range(1, 6)])
        for r in g[g.pos > 4].itertuples():
            rows.append(dict(country=country, k=r.k, season=s, lrel=np.log(getattr(r, pay) / ref), hit=r.k in hit))
    return pd.DataFrame(rows)

def logit(O, with_spend):
    X = pd.DataFrame({'FRA': (O.country == 'FRA').astype(float)})
    if with_spend: X['lrel'] = O.lrel.values
    m = sm.Logit(O.hit.astype(float).values, sm.add_constant(X)).fit(disp=0, cov_type='cluster', cov_kwds={'groups': pd.factorize(O.k)[0]})
    return m

if __name__ == '__main__':
    ep, fp, fl, rcm, xc = sys.argv[1:6]
    EP = pd.read_csv(ep); EP = EP[~EP.get('flag_xcheck_conflict', False).astype(bool)] if 'flag_xcheck_conflict' in EP else EP
    FP = pd.read_csv(fp); FL = pd.read_csv(fl); RCM = pd.read_csv(rcm)
    EL = eng_ladder(2, 1990, 2024); EL['k'] = EL.club.map(ck)
    EP = EP.drop(columns=[c for c in ('tier', 'pos') if c in EP]).merge(EL[['Season', 'k', 'tier', 'pos']].rename(columns={'Season': 'season'}), on=['k', 'season'], how='left')
    print('(0) Tier-1 payroll coverage by season')
    print('    England:', coverage(EP, EL, 'payroll_k').round(2).to_dict())
    print('    France: ', coverage(FP, FL, 'payroll_keur').round(2).to_dict())
    V = proxy_validation(EP, RCM)
    print('\n(a) England: Spearman rho, transfer-spend proxy R3 vs payroll')
    if V.empty: print('    too few matched club-seasons'); V = pd.DataFrame(columns=['season', 'tier', 'n', 'rho'])
    for t, g in V.groupby('tier'):
        print(f'    tier {t}: median {g.rho.median():.2f} (range {g.rho.min():.2f}-{g.rho.max():.2f}), {len(g)} seasons, n per season {int(g.n.median())}')
    print(V.round(2).to_string(index=False))
    for min_cov in (0.9, 0.75):
        O = pd.concat([reach_rows(EP, EL, 'payroll_k', 'ENG', min_cov), reach_rows(FP, FL, 'payroll_keur', 'FRA', min_cov)], ignore_index=True)
        if O.country.nunique() < 2 or O.hit.sum() < 5: print(f'\n(b) coverage >= {min_cov}: too little data'); continue
        m0, m1 = logit(O, False), logit(O, True)
        print(f'\n(b) Reach top four within 5 seasons, top-flight clubs not in the top four; seasons with tier-1 payroll coverage >= {min_cov:.0%}')
        print(f'    n = {len(O)} (ENG {int((O.country=="ENG").sum())}, FRA {int((O.country=="FRA").sum())}); hits ENG {int(O[O.country=="ENG"].hit.sum())}, FRA {int(O[O.country=="FRA"].hit.sum())}')
        print(f'    France vs England, no payroll control:   {m0.params["FRA"]:+.2f} (p = {m0.pvalues["FRA"]:.3f})')
        print(f'    France vs England, with log rel. payroll: {m1.params["FRA"]:+.2f} (p = {m1.pvalues["FRA"]:.3f}); payroll coefficient {m1.params["lrel"]:+.2f} (p = {m1.pvalues["lrel"]:.4f})')
    print('\n    Proxy benchmark (D221, all five leagues, transfer spend): France vs England with relative spend +1.27 (p = 0.038)')
