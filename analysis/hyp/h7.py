"""Registered H7 test (06 Analysis/H7_Test_Protocol.md, written 31 Oct 2026 12:40 UTC, before any revenue figure was
collected). Lower envelope of top-flight concentration (HICB) against log real league revenue, pooled league-seasons.

Implementation notes, recorded with the results:
  - Revenue: Deloitte ARFF euro figures (h7_revenue.py). Deloitte already converts the Premier League to euros at
    contemporary rates, so national deflation would mix exchange-rate effects; the protocol's stated fallback is used:
    every league deflated by euro-area HICP (Eurostat prc_hicp_aind, annual average, calendar year in which the season ends),
    expressed in 2024 euros.
  - Seasons available: 1996/97, 2008/09, 2009/10 (not England), 2010/11 and 2012/13-2024/25. The moving-block bootstrap treats each league's available
    seasons as one ordered sequence.
  - Power (protocol 5) uses the observed bootstrap spread around the estimate as the sampling distribution under each
    simulated slope, instead of a full bootstrap for each of 500 simulations.
Usage: FR_SRC=... python -I h7.py <data dir> <league_revenue.csv> <out dir>"""
import os, sys, json
import numpy as np, pandas as pd
import statsmodels.formula.api as smf
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, '..', 'trend')); sys.path.insert(0, os.path.join(HERE, '..', 'rcm'))
DATA, REV, OUT = sys.argv[1:4]; os.makedirs(OUT, exist_ok=True)
SRC = os.environ['FR_SRC']
from official_positions import DEDUCT
from ladder import parse_of
HICP = {1997: 72.87, 2009: 91.65, 2010: 93.14, 2011: 95.66, 2013: 99.38, 2014: 99.81, 2015: 100.00, 2016: 100.23, 2017: 101.78, 2018: 103.56, 2019: 104.80,
        2020: 105.06, 2021: 107.78, 2022: 116.82, 2023: 123.15, 2024: 126.07, 2025: 128.75}   # Eurostat prc_hicp_aind, EA, 2015=100
FILES = {'England': 'england', 'Spain': 'spain', 'Italy': 'italy', 'Germany': 'germany', 'France': 'france'}
CODE = {'England': 'ENG', 'Spain': 'ESP', 'Italy': 'ITA', 'Germany': 'GER', 'France': 'FRA'}
LAD = {'England': 'ladder_ENG4.csv', 'Spain': 'ladder_ESP.csv', 'Italy': 'ladder_ITA.csv', 'Germany': 'ladder_GER.csv', 'France': 'ladder_FRA.csv'}
B, SEED, TAU = 1999, 20261031, 0.10

def points(league, s):
    if league == 'England' and s == 2022:
        rows = parse_of(f'{SRC}/openfootball_england/2022-23/1-premierleague.txt')
    else:
        M = pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/{FILES[league]}.csv', low_memory=False)
        g = M[(M.Season == s) & (M.tier == 1)]
        rows = list(zip(g.home.str.strip(), g.visitor.str.strip(), g.hgoal.astype(int), g.vgoal.astype(int)))
    P = {}
    for h, a, hg, ag in rows:
        P[h] = P.get(h, 0) + (3 if hg > ag else 1 if hg == ag else 0); P[a] = P.get(a, 0) + (3 if ag > hg else 1 if hg == ag else 0)
    for (c, ss, cl), d in DEDUCT.items():
        if c == CODE[league] and ss == s and cl in P: P[cl] -= d
    return np.array(sorted(P.values(), reverse=True), float)

def build():
    R = pd.read_csv(REV); R['s'] = R.season.str[:4].astype(int)
    out = []
    for r in R.itertuples():
        p = points(r.league, r.s); n = len(p); sh = p / p.sum()
        L = pd.read_csv(os.path.join(DATA, LAD[r.league])); t1 = L[L.tier == 1]
        top = set(t1[(t1.Season == r.s) & (t1.pos <= 4)].k); prev = set(t1[(t1.Season >= r.s - 5) & (t1.Season < r.s) & (t1.pos <= 4)].k)
        real = r.revenue_eur_m * HICP[2024] / HICP[r.s + 1]
        out.append(dict(league=r.league, season=r.season, s=r.s, clubs=n, hicb=100 * n * (sh ** 2).sum(), top4_share=p[:4].sum() / p.sum(),
                        top4_persist=len(top & prev), revenue_eur_m=r.revenue_eur_m, real_rev_2024=real, lrev=np.log(real)))
    return pd.DataFrame(out)

def qslope(d, y='hicb', tau=TAU, fe=False):
    f = f'{y} ~ lrev' + (' + C(league)' if fe else '')
    return float(smf.quantreg(f, d).fit(q=tau, max_iter=5000).params['lrev'])

def boot(d, fn, rng, B=B, block=5):
    out = []
    groups = {k: g.sort_values('s').reset_index(drop=True) for k, g in d.groupby('league')}
    for _ in range(B):
        parts = []
        for k, g in groups.items():
            n = len(g); idx = []
            while len(idx) < n:
                st = rng.integers(0, max(1, n - block + 1)); idx.extend(range(st, min(st + block, n)))
            parts.append(g.iloc[idx[:n]])
        try: out.append(fn(pd.concat(parts, ignore_index=True)))
        except Exception: pass
    return np.array(out)

def test(d, fn, rng, B=B):
    b = fn(d); bs = boot(d, fn, rng, B)
    p = max((bs >= 0).mean(), 1 / (len(bs) + 1))
    return dict(slope=round(b, 4), lo=round(float(np.percentile(bs, 2.5)), 4), hi=round(float(np.percentile(bs, 97.5)), 4),
                p_one_sided=round(float(p), 4), rejected=bool(b < 0 and p < 0.05), n=len(d)), bs

def envelope_md(d, y='hicb'):
    q = pd.qcut(d.lrev, 5, labels=False); m = d.groupby(q).agg(x=('lrev', 'mean'), y=(y, 'min'))
    return float(np.polyfit(m.x, m.y, 1)[0])

if __name__ == '__main__':
    d = build(); d.to_csv(os.path.join(OUT, 'concentration.csv'), index=False)
    rng = np.random.default_rng(SEED); res = {}
    res['primary'], bs = test(d, lambda x: qslope(x), rng); print('primary', res['primary'], flush=True)
    sd = float(d.hicb.std()); rngx = float(d.lrev.max() - d.lrev.min())
    res['magnitude'] = dict(hicb_sd=round(sd, 3), log_revenue_range=round(rngx, 3), implied_change=round(res['primary']['slope'] * rngx, 3),
                            change_in_sd=round(res['primary']['slope'] * rngx / sd, 3))
    # power: slopes equal to a fall of 0.5 and 1 SD across the revenue range; sampling spread taken from the bootstrap
    dev = bs - bs.mean(); q95 = float(np.percentile(dev, 95)); pw = {}
    for k in (0.5, 1.0):
        true = -k * sd / rngx                      # simulated estimate = true + deviation; rejected when its bootstrap upper tail is below zero
        pw[str(k)] = round(float(np.mean(true + dev + q95 < 0)), 3)
    res['power'] = pw; print('power', pw, flush=True)
    for tau in (0.05, 0.20):
        res[f'tau_{tau}'], _ = test(d, lambda x, t=tau: qslope(x, tau=t), rng); print(tau, res[f'tau_{tau}'], flush=True)
    res['min_distance_envelope'], _ = test(d, envelope_md, rng); print('md', res['min_distance_envelope'], flush=True)
    res['league_fixed_effects'], _ = test(d, lambda x: qslope(x, fe=True), rng); print('fe', res['league_fixed_effects'], flush=True)
    dc = d[~d.s.isin([2019, 2020])].reset_index(drop=True)
    res['no_covid'], _ = test(dc, lambda x: qslope(x), rng); print('no covid', res['no_covid'], flush=True)
    res['R1_top4_share'], _ = test(d, lambda x: qslope(x, y='top4_share'), rng); print('R1', res['R1_top4_share'], flush=True)
    res['R2_top4_persistence'], _ = test(d, lambda x: qslope(x, y='top4_persist'), rng); print('R2', res['R2_top4_persistence'], flush=True)
    res['nominal_revenue'], _ = test(d.assign(lrev=np.log(d.revenue_eur_m)), lambda x: qslope(x), rng); print('nominal', res['nominal_revenue'], flush=True)
    res['H7_rejected'] = res['primary']['rejected']
    json.dump(res, open(os.path.join(OUT, 'h7_results.json'), 'w'), indent=1); print(json.dumps(res, indent=1))
