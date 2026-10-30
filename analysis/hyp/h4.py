"""H4 — conversion of over-performance into payroll. Implements `06 Analysis/H4_Test_Protocol.md` v1.0 exactly.
Joint England-France panel, tiers 1-2. One-sided wild cluster (club) bootstrap, Rademacher, 1,999 draws, null imposed.
Usage:
  FR_SRC=<src dir> python -I h4.py <france_wage_panel.csv> <ladder_FRA.csv> <england_wage_panel.csv> <out_dir>
  python -I h4.py --selftest      (synthetic panel with a known effect; no real data touched)"""
import sys, os, json
import numpy as np, pandas as pd

B = 1999
SEED = 20261028

# ---------------------------------------------------------------- construction (protocol §3)
def tier12_rank(L):
    """L: Season, k, tier, pos (any tiers). Returns tier 1-2 ladder with lrank and N per season."""
    L = L[L.tier <= 2].sort_values(['Season', 'tier', 'pos']).copy()
    L['lrank'] = L.groupby('Season').cumcount() + 1
    L['N'] = L.Season.map(L.groupby('Season').size())
    L['N1'] = L.Season.map(L[L.tier == 1].groupby('Season').size())
    return L

def build_country(P, L, country, pay_col, cons_col=None):
    """P: k, season, payroll. L: tier 1-2 ladder. Returns club-season rows with w, p, residual e."""
    L = tier12_rank(L)
    D = P[['k', 'season', pay_col] + ([cons_col] if cons_col else [])].rename(columns={pay_col: 'pay'})
    D = D.dropna(subset=['pay']); D = D[D.pay > 0]
    D = D.merge(L[['Season', 'k', 'tier', 'pos', 'lrank', 'N', 'N1']].rename(columns={'Season': 'season'}), on=['k', 'season'], how='inner')
    D['consolidated'] = D[cons_col].fillna(False).astype(bool) if cons_col else False
    D['country'] = country
    D['w'] = np.log(D.pay / D.groupby('season').pay.transform('mean'))
    D['p'] = 1 - (D.lrank - 1) / (D.N - 1)
    D['p1'] = np.where(D.tier == 1, 1 - (D.pos - 1) / (D.N1 - 1), np.nan)
    D['e'] = residual(D, 'p')
    t1 = D.tier == 1
    D.loc[t1, 'e1'] = residual(D[t1], 'p1')
    D['in12'] = True
    return D, L

def residual(D, ycol):
    X = pd.get_dummies(D.season, prefix='s', dtype=float); X['w'] = D.w.values; X['w2'] = D.w.values ** 2
    y = D[ycol].values; b, *_ = np.linalg.lstsq(X.values, y, rcond=None)
    return y - X.values @ b

def add_lags(D, L_by_country, h, ecol='e', ncum=3):
    """C_it = sum of e over t..t-(ncum-1) (all required); outcome w_{t+h} - w_t; attrition flag."""
    out = []
    for c, g in D.groupby('country'):
        idx = g.set_index(['k', 'season'])
        Lc = L_by_country[c]; present = set(zip(Lc.k, Lc.Season)); last_season = Lc.Season.max()
        for r in g.itertuples():
            es = [idx[ecol].get((r.k, r.season - j), np.nan) for j in range(ncum)]
            if any(pd.isna(x) for x in es): continue
            wf = idx['w'].get((r.k, r.season + h), np.nan)
            if r.season + h > last_season: continue                     # horizon beyond the data
            attrited = pd.isna(wf) and ((r.k, r.season + h) not in present)
            out.append(dict(country=c, k=r.k, season=r.season, C=float(np.sum(es)), w=r.w, dw=wf - r.w if not pd.isna(wf) else np.nan,
                            attrited=attrited, consolidated=r.consolidated))
    return pd.DataFrame(out)

# ---------------------------------------------------------------- estimation (protocol §4)
def fe_matrix(R, extra=None):
    D = pd.concat([pd.get_dummies(R.k, prefix='c', dtype=float),
                   pd.get_dummies(R.country + '_' + R.season.astype(str), prefix='cs', dtype=float)], axis=1)
    if extra is not None: D = pd.concat([D, extra], axis=1)
    return D.values

def annihilate(F):
    Q, s, _ = np.linalg.svd(F, full_matrices=False); Q = Q[:, s > 1e-9 * s.max()]
    return lambda v: v - Q @ (Q.T @ v)

def beta_t(xt, yt, cl):
    b = (xt @ yt) / (xt @ xt); u = yt - b * xt
    G = len(np.unique(cl)); n = len(yt); k = 1
    s = pd.Series(xt * u).groupby(cl).sum().values
    V = (s @ s) / (xt @ xt) ** 2 * G / (G - 1) * (n - 1) / (n - k)
    return b, b / np.sqrt(V)

def wild_cluster(R, extra=None, seed=SEED):
    """One-sided WCR bootstrap of H0: beta <= 0 vs beta > 0. Returns beta, t, p, n, clusters."""
    R = R.reset_index(drop=True)
    M = annihilate(fe_matrix(R, extra)); y = R.dw.values; x = R.C.values; cl = R.k.values
    xt, yt = M(x), M(y); b, t = beta_t(xt, yt, cl)
    ur = yt                                           # restricted (beta = 0) residuals after FE
    rng = np.random.default_rng(seed); codes, inv = np.unique(cl, return_inverse=True)
    ts = np.empty(B)
    for i in range(B):
        v = rng.choice([-1.0, 1.0], len(codes))[inv]
        ts[i] = beta_t(xt, M(ur * v), cl)[1]
    p = (1 + np.sum(ts >= t)) / (B + 1)
    return dict(beta=float(b), t=float(t), p=float(p), n=int(len(R)), clubs=int(len(codes)))

def jackknife_bc(R, h):
    """Robustness 2: add w_it control; half-panel jackknife (split by season) bias correction."""
    full = wild_cluster(R, extra=pd.DataFrame({'w': R.w.values}))
    mid = np.median(R.season.unique())
    bs = []
    for half in (R[R.season <= mid], R[R.season > mid]):
        half = half.reset_index(drop=True)
        M = annihilate(fe_matrix(half, pd.DataFrame({'w': half.w.values})))
        bs.append(beta_t(M(half.C.values), M(half.dw.values), half.k.values)[0])
    full['beta_bias_corrected'] = float(2 * full['beta'] - np.mean(bs))
    return full

def attrition(R):
    q = pd.qcut(R.C, 5, labels=False, duplicates='drop')
    rate = R.groupby(q).attrited.mean().round(3).to_dict()
    sd = R.dw.std(); Rb = R.copy(); Rb.loc[Rb.attrited, 'dw'] = -sd
    return rate, wild_cluster(Rb.dropna(subset=['dw']))

# ---------------------------------------------------------------- driver
def run(D, Ls, out_dir=None):
    res = {}
    for h in (3, 5):
        R = add_lags(D, Ls, h); Rk = R.dropna(subset=['dw'])
        res[f'primary_h{h}'] = wild_cluster(Rk)
        res[f'r1_no_consolidated_h{h}'] = wild_cluster(Rk[~Rk.consolidated.astype(bool)])
        res[f'r2_w_control_jackknife_h{h}'] = jackknife_bc(Rk, h)
        R2 = add_lags(D, Ls, h, ncum=2).dropna(subset=['dw'])
        res[f'r3_two_season_C_h{h}'] = wild_cluster(R2)
        D1 = D[D.tier == 1].copy(); D1['e'] = D1.e1
        R4 = add_lags(D1, Ls, h).dropna(subset=['dw'])
        res[f'r4_tier1_rank_h{h}'] = wild_cluster(R4) if len(R4) > 30 else None
        rate, bound = attrition(R)
        res[f'r5_attrition_rate_by_C_quintile_h{h}'] = rate
        res[f'r5_attrition_bound_h{h}'] = bound
        res[f'countries_h{h}'] = Rk.country.value_counts().to_dict()
    p3, p5 = res['primary_h3'], res['primary_h5']
    res['verdict'] = 'Not rejected' if (p3['beta'] > 0 and p3['p'] < 0.05 and p5['beta'] > 0 and p5['p'] < 0.05) else 'Rejected'
    rob = [k for k in res if k.startswith('r') and k[1].isdigit() and isinstance(res[k], dict) and 'p' in res[k]]
    res['robustness_survive'] = {k: bool(res[k]['beta'] > 0 and res[k]['p'] < 0.05) for k in rob}
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        json.dump(res, open(f'{out_dir}/h4_results.json', 'w'), indent=1, default=float)
    return res

def selftest():
    """Synthetic two-country panel: payroll responds to past residual performance with a known coefficient."""
    rng = np.random.default_rng(1)
    def country(c, n_clubs=44, T=18, gamma=0.0):
        quality = rng.normal(0, 0.6, n_clubs); w = quality.copy(); rows = []; L = []; e_hist = {i: [] for i in range(n_clubs)}
        for t in range(T):
            perf = 0.8 * w + rng.normal(0, 0.5, n_clubs)
            order = np.argsort(-perf)
            for r, i in enumerate(order):
                L.append(dict(Season=2000 + t, k=f'{c}{i}', tier=1 if r < 20 else 2, pos=r + 1 if r < 20 else r - 19))
            p = 1 - np.argsort(order) / (n_clubs - 1)
            e = p - (0.5 + 0.3 * w); [e_hist[i].append(e[i]) for i in range(n_clubs)]
            for i in range(n_clubs): rows.append(dict(k=f'{c}{i}', season=2000 + t, pay=float(np.exp(w[i]) * 1000)))
            cum = np.array([sum(e_hist[i][-3:]) for i in range(n_clubs)])
            w = 0.9 * w + 0.1 * quality + gamma * cum / 3 + rng.normal(0, 0.1, n_clubs)
        return pd.DataFrame(rows), pd.DataFrame(L)
    for gamma in (0.0, 0.25):
        Ds, Ls = [], {}
        for c in ('ENG', 'FRA'):
            P, L = country(c, gamma=gamma); d, l = build_country(P, L, c, 'pay'); Ds.append(d); Ls[c] = l
        r = run(pd.concat(Ds, ignore_index=True), Ls)
        print(f'gamma={gamma}: h3 beta={r["primary_h3"]["beta"]:+.3f} p={r["primary_h3"]["p"]:.4f} | '
              f'h5 beta={r["primary_h5"]["beta"]:+.3f} p={r["primary_h5"]["p"]:.4f} | verdict {r["verdict"]}')

if __name__ == '__main__':
    if sys.argv[1] == '--selftest': selftest(); sys.exit()
    fr_p, fr_l, en_p, out = sys.argv[1:5]
    sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rcm'))
    from ladder import eng_ladder
    from clubkey import ck
    FP = pd.read_csv(fr_p); FL = pd.read_csv(fr_l)
    EP = pd.read_csv(en_p)   # admissibility = identity check (protocol §2); the turnover-ratio flag is for review only, not a filter
    EL = eng_ladder(2, 1990, 2024); EL['k'] = EL.club.map(ck)
    dF, lF = build_country(FP, FL, 'FRA', 'payroll_keur', 'consolidated')
    dE, lE = build_country(EP, EL, 'ENG', 'payroll_k')
    res = run(pd.concat([dF, dE], ignore_index=True), {'FRA': lF, 'ENG': lE}, out)
    if 'flag_xcheck_conflict' in EP and EP.flag_xcheck_conflict.astype(bool).any():   # NOT pre-listed: reported as a sensitivity only
        dE2, _ = build_country(EP[~EP.flag_xcheck_conflict.astype(bool)], EL, 'ENG', 'payroll_k')
        D2 = pd.concat([dF, dE2], ignore_index=True)
        res['sensitivity_unregistered_drop_xcheck_conflicts'] = {f'h{h}': wild_cluster(add_lags(D2, {'FRA': lF, 'ENG': lE}, h).dropna(subset=['dw'])) for h in (3, 5)}
        json.dump(res, open(f'{out}/h4_results.json', 'w'), indent=1, default=float)
    print(json.dumps({k: res[k] for k in ('primary_h3', 'primary_h5', 'verdict', 'robustness_survive')}, indent=1))
