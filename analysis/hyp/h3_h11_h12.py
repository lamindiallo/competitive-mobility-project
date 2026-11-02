"""Registered H3, H11 and H12 tests (06 Analysis/H3_H11_H12_Test_Protocol.md, written 2 Nov 2026 07:20 UTC,
before any H3, H11 or H12 statistic was computed).

Implementation notes (not changes to the tests):
  - Revenue quality: England turnover is used only where the wage panel's own pre-existing flag_implausible is False;
    France revenue only where revenue_ok is True. Both flags were set when the panels were built, before this protocol.
  - Relative pay for H3 is pay / the country-season mean of the panel (tiers 1-2), as in H1b.
    Relative pay for H12 is pay / the league-season mean among tier-1 panel clubs.
  - H3 secondary: clubs with no pay at t+2 (below tier 2 by then) cannot be classified and are left out.
  - Logits use a negligible ridge (C = 1e4) so that bootstrap resamples with separation do not diverge.
Usage: python -I h3_h11_h12.py <repo data dir> <wage dir> <out dir> [quick]"""
import os, sys, json
import numpy as np, pandas as pd
from sklearn.linear_model import LogisticRegression

DATA, WAGES, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
QUICK = len(sys.argv) > 4
NB = 199 if QUICK else 1999; NSIM = 100 if QUICK else 500


def state(r):
    if r is None or r.tier > 2: return 5
    if r.tier == 1: return 0 if r.pos <= 4 else (1 if r.pos <= 10 else 2)
    return 3 if r.pos <= 6 else 4


LAD = {}
for c, f in (('ENG', 'ladder_ENG4.csv'), ('FRA', 'ladder_FRA.csv')):
    L = pd.read_csv(os.path.join(DATA, f)); LAD[c] = ({(r.k, int(r.Season)): r for r in L.itertuples()}, int(L.Season.max()))
T = pd.read_csv(os.path.join(DATA, 'tierC_seasons.csv'))
T['rel'] = T.pay / T.groupby(['country', 'season']).pay.transform('mean')
TI = {(r.country, r.k, int(r.season)): r for r in T.itertuples()}


def cluster_boot(d, fn, seed, nb=NB):
    rng = np.random.default_rng(seed); clubs = d.club_id.unique(); g = {c: ix for c, ix in d.groupby('club_id').groups.items()}
    out = []
    for _ in range(nb):
        pick = rng.choice(clubs, len(clubs), replace=True)
        dd = pd.concat([d.loc[g[c]] for c in pick], ignore_index=True)
        try: out.append(fn(dd))
        except Exception: out.append(np.nan)
    return np.array(out, dtype=float)

# ------------------------------------------------------------------ H3
def h3():
    rows = []
    for (c, k, s), r in TI.items():
        S_ = [TI.get((c, k, s - i)) for i in (0, 1, 2)]
        if any(x is None for x in S_): continue
        lad, last = LAD[c]
        if s + 2 > last: continue
        cur = lad.get((k, s)); fut = lad.get((k, s + 2))
        if cur is None or cur.tier > 2: continue
        s0, s2 = state(cur), state(fut)
        r2 = TI.get((c, k, s + 2))
        rows.append(dict(country=c, k=k, season=s, S=float(np.mean([x.places for x in S_])), s0=s0, s2=s2,
                         U=int(s2 < s0), rel=r.rel, rel2=(r2.rel if r2 is not None else np.nan)))
    d = pd.DataFrame(rows)
    d['wt'] = d.groupby(['country', 'season']).rel.transform(lambda x: pd.qcut(x.rank(method='first'), 3, labels=False)).astype(int)
    q = d.groupby('country').S.quantile([.25, .75]).unstack()
    d['lo'] = d.S <= d.country.map(q[0.25]); d['hi'] = d.S >= d.country.map(q[0.75])

    def D(dd, S=None):
        S = dd.S.values if S is None else S
        lo = S <= dd.country.map(q[0.25]).values; hi = S >= dd.country.map(q[0.75]).values
        return dd.U.values[hi].mean() - dd.U.values[lo].mean()

    def perm(dd, seed, U=None):
        rng = np.random.default_rng(seed); dd = dd.reset_index(drop=True)
        if U is not None: dd = dd.assign(U=U)
        groups = [np.asarray(ix) for ix in dd.groupby(['country', 'season', 's0', 'wt']).indices.values()]
        obs = D(dd); null = []
        for _ in range(NB):
            S = dd.S.values.copy()
            for ix in groups: S[ix] = rng.permutation(S[ix])
            null.append(D(dd, S))
        null = np.array(null)
        return obs, null

    obs, null = perm(d, 20261102)
    res = dict(n=len(d), clubs=int(d.k.nunique()), n_hi=int(d.hi.sum()), n_lo=int(d.lo.sum()),
               P_hi=round(d.U[d.hi].mean(), 4), P_lo=round(d.U[d.lo].mean(), 4), D=round(obs, 4),
               null_mean=round(float(null.mean()), 4), crit95=round(float(np.percentile(null, 95)), 4),
               p=round(float((1 + (null >= obs).sum()) / (NB + 1)), 4))
    res['rejected'] = res['p'] >= 0.05
    # by country (reported)
    res['by_country'] = {}
    for c in ('ENG', 'FRA'):
        o, n = perm(d[d.country == c], 20261102)
        res['by_country'][c] = dict(n=int((d.country == c).sum()), D=round(o, 4), p=round(float((1 + (n >= o).sum()) / (NB + 1)), 4))
    # secondary: relative pay did not rise by more than 10%
    ds = d[d.rel2.notna() & (d.rel2 <= 1.10 * d.rel)]
    o, n = perm(ds, 20261102)
    res['secondary_no_pay_rise'] = dict(n=len(ds), P_hi=round(ds.U[ds.hi].mean(), 4), P_lo=round(ds.U[ds.lo].mean(), 4),
                                        D=round(o, 4), p=round(float((1 + (n >= o).sum()) / (NB + 1)), 4))
    # power: baseline P(U) by cell (state x wage tercile x country), top quartile raised by delta
    rng = np.random.default_rng(20261102 + 1)
    base = d.groupby(['country', 's0', 'wt']).U.transform('mean').values
    crit = np.percentile(null, 95); pw = {}
    for delta in (0.05, 0.10):
        hits = 0
        for _ in range(NSIM):
            p = np.clip(base + delta * d.hi.values, 0, 1); U = (rng.random(len(d)) < p).astype(int)
            hits += D(d.assign(U=U)) > crit
        pw[str(delta)] = round(hits / NSIM, 3)
    res['power'] = pw
    d.to_csv(os.path.join(OUT, 'h3_rows.csv'), index=False)
    return res

# ------------------------------------------------------------------ H11
def revenue():
    e = pd.read_csv(os.path.join(WAGES, 'england_wage_panel.csv'))
    e = e[e.turnover_k.notna() & (e.flag_implausible == False)][['k', 'season', 'turnover_k']].rename(columns={'turnover_k': 'rev'})
    e['country'] = 'ENG'
    f = pd.read_csv(os.path.join(WAGES, 'france_wage_panel.csv'))
    f = f[f.revenue_keur.notna() & (f.revenue_ok == True)][['k', 'season', 'revenue_keur']].rename(columns={'revenue_keur': 'rev'})
    f['country'] = 'FRA'
    R = pd.concat([e, f]); R = R[R.rev > 0].drop_duplicates(['country', 'k', 'season'])
    R['r'] = np.log(R.rev / R.groupby(['country', 'season']).rev.transform('mean'))
    return {(x.country, x.k, int(x.season)): x.r for x in R.itertuples()}, R


def h11():
    RV, R = revenue(); rows = []
    for (c, k, s), t in TI.items():
        rr = [RV.get((c, k, s + h)) for h in (-1, 0, 1, 2)]
        if any(x is None for x in rr): continue
        lad, _ = LAD[c]
        para = c == 'ENG' and t.tier == 2 and any((x := lad.get((k, s - i))) is not None and x.tier == 1 for i in (1, 2))
        rows.append(dict(country=c, k=k, club_id=f'{c}:{k}', season=s, tier=int(t.tier), O=t.places,
                         G0=rr[1] - rr[0], G1=rr[2] - rr[0], G2=rr[3] - rr[0], para=para))
    d = pd.DataFrame(rows)

    def betas(dd):
        X = np.column_stack([np.ones(len(dd)), dd.O.values, (dd.country == 'FRA').astype(float), (dd.tier == 2).astype(float)])
        if dd.country.nunique() == 1: X = np.delete(X, 2, axis=1)
        out = []
        for h in ('G0', 'G1', 'G2'):
            b = np.linalg.lstsq(X, dd[h].values, rcond=None)[0]; out.append(b[1])
        return np.array(out)

    def run(dd, seed):
        b = betas(dd); bs = np.array([betas(x) for x in _resamples(dd, seed)])
        D = b[2] - b[1]; Ds = bs[:, 2] - bs[:, 1]
        return dict(n=len(dd), clubs=int(dd.club_id.nunique()),
                    beta={f'h{h}': round(float(b[h]), 4) for h in range(3)},
                    beta_95={f'h{h}': [round(float(np.nanpercentile(bs[:, h], 2.5)), 4), round(float(np.nanpercentile(bs[:, h], 97.5)), 4)] for h in range(3)},
                    p_beta2_gt0=round(float(np.nanmean(bs[:, 2] <= 0)), 4),
                    p_beta1_gt0=round(float(np.nanmean(bs[:, 1] <= 0)), 4),
                    Delta=round(float(D), 4), Delta_95=[round(float(np.nanpercentile(Ds, 2.5)), 4), round(float(np.nanpercentile(Ds, 97.5)), 4)],
                    p_Delta_gt0=round(float(np.nanmean(Ds <= 0)), 4))

    res = run(d, 20261103)
    res['premise_rejected'] = res['p_beta2_gt0'] >= 0.05
    res['rejected'] = res['premise_rejected'] or res['p_Delta_gt0'] >= 0.05
    res['by_country'] = {c: run(d[d.country == c].reset_index(drop=True), 20261103) for c in ('ENG', 'FRA')}
    res['eng_no_parachute'] = run(d[(d.country == 'ENG') & ~d.para].reset_index(drop=True), 20261103)
    res['rev_obs'] = {c: int((R.country == c).sum()) for c in ('ENG', 'FRA')}
    d.to_csv(os.path.join(OUT, 'h11_rows.csv'), index=False)
    return res


def _resamples(d, seed, nb=NB):
    rng = np.random.default_rng(seed); g = d.groupby('club_id').indices; clubs = np.array(list(g))
    for _ in range(nb):
        pick = rng.choice(clubs, len(clubs), replace=True)
        yield d.iloc[np.concatenate([g[c] for c in pick])]

# ------------------------------------------------------------------ H12
def h12():
    t1 = T[T.tier == 1].copy()
    t1['w'] = np.log(t1.pay / t1.groupby(['country', 'season']).pay.transform('mean'))
    fourth = t1.groupby(['country', 'season']).pay.transform(lambda x: x.nlargest(4).iloc[-1] if len(x) >= 4 else np.nan)
    t1['near'] = t1.pay >= 0.75 * fourth
    t1['C'] = t1.groupby(['country', 'season']).near.transform('sum') - t1.near.astype(int)
    rows = []
    for r in t1.itertuples():
        if r.pos <= 4: continue
        lad, last = LAD[r.country]
        if r.season + 1 > last: continue
        nx = lad.get((r.k, int(r.season) + 1))
        y = int(nx is not None and nx.tier == 1 and nx.pos <= 4)
        rows.append(dict(country=r.country, k=r.k, club_id=f'{r.country}:{r.k}', season=int(r.season), y=y, eng=float(r.country == 'ENG'),
                         w=r.w, p=float(r.pos), C=float(r.C)))
    d = pd.DataFrame(rows)

    def coef(dd, var):
        X = dd[[var, 'w', 'p']].values
        m = LogisticRegression(C=1e4, max_iter=5000).fit(X, dd.y.values)
        return float(m.coef_[0][0])

    out = {}
    for var, seed in (('eng', 20261104), ('C', 20261104)):
        b = coef(d, var); bs = np.array([coef(x, var) if x.y.nunique() > 1 else np.nan for x in _resamples(d, seed)])
        out[var] = dict(coef=round(b, 4), ci95=[round(float(np.nanpercentile(bs, 2.5)), 4), round(float(np.nanpercentile(bs, 97.5)), 4)],
                        p_negative=round(float(np.nanmean(bs >= 0)), 4))
    res = dict(n=len(d), clubs=int(d.club_id.nunique()), entries=int(d.y.sum()),
               entries_by_country={c: [int(d[d.country == c].y.sum()), int((d.country == c).sum())] for c in ('ENG', 'FRA')},
               primary_england=out['eng'], secondary_crowding=out['C'],
               C_mean={c: round(float(d[d.country == c].C.mean()), 2) for c in ('ENG', 'FRA')})
    res['rejected'] = res['primary_england']['p_negative'] >= 0.05
    d.to_csv(os.path.join(OUT, 'h12_rows.csv'), index=False)
    return res


if __name__ == '__main__':
    R = dict(H3=h3(), H11=h11(), H12=h12(), nb=NB, nsim=NSIM)
    json.dump(R, open(os.path.join(OUT, 'results.json'), 'w'), indent=1, default=float)
    print(json.dumps(R, indent=1, default=float))
