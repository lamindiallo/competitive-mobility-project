"""Registered H8 and H9 tests (`06 Analysis/H8_H9_Test_Protocol.md`).
Usage: FR_SRC=... FR_LADDERS=... python -I h8_h9.py <outdir> [quick]"""
import os, sys, json, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import load, with_states, season_pairs

QUICK = len(sys.argv) > 2
NPERM = 199 if QUICK else 1999
NBOOT = 199 if QUICK else 1999
SERIES2 = ('ESP-2', 'ITA-2', 'GER-2', 'FRA-2')

# ---------------------------------------------------------------- H8
def eq_states(d, K):
    d = d.copy(); d['st'] = (K * (d['rank'] - 1) // d.ntot).astype(int); return d

def h8_pairs(series, config):
    d, u, nt = load(series)
    if config.startswith('EQ'):
        K = int(config[2:].split('+')[0]); d = eq_states(d, K)
    else:
        K, d = with_states(d, 'K5', nt)
    PR = season_pairs(d, u)
    return K, [(a, b) for _, a, b in PR.values()]

def retention(prs, K, exits):
    top = [0, 0]; bot = [0, 0]
    for a, b in prs:
        if not exits:
            m = b >= 0; a, b = a[m], b[m]
        t = a == 0; top[0] += (b[t] == 0).sum(); top[1] += t.sum()
        z = a == K - 1; bot[0] += (b[z] == K - 1).sum(); bot[1] += z.sum()
    return top[0] / top[1], bot[0] / bot[1]

def h8(series, config, rng):
    exits = config.endswith('+exit')
    K, prs = h8_pairs(series, config)
    pt, pb = retention(prs, K, exits); D = pt - pb
    nullD = np.empty(NPERM)
    for r in range(NPERM):
        pp = []
        for a, b in prs:
            if exits: pp.append((a, rng.permutation(b)))
            else:
                m = b >= 0; pp.append((a[m], rng.permutation(b[m])))
        x, y = retention(pp, K, True); nullD[r] = x - y
    p = (1 + (nullD >= D).sum()) / (NPERM + 1)
    bs = []
    for _ in range(NBOOT):
        pick = rng.integers(0, len(prs), len(prs)); x, y = retention([prs[i] for i in pick], K, exits); bs.append(x - y)
    lim1 = pt > pb; lim2 = p < 0.05
    return dict(series=series, config=config, K=K, p_top=pt, p_bottom=pb, D=D, null_mean=nullD.mean(), null_95=np.percentile(nullD, 95),
                p_perm=p, D_lo=np.percentile(bs, 2.5), D_hi=np.percentile(bs, 97.5), limb1=bool(lim1), limb2=bool(lim2),
                H8_rejected=bool(not (lim1 and lim2)))

# ---------------------------------------------------------------- H9
def shorrocks(a, b, K):
    C = np.zeros((K, K)); np.add.at(C, (a, b), 1)
    rows = C.sum(1) > 0
    if rows.sum() < 2: return np.nan
    P = C / np.maximum(C.sum(1, keepdims=True), 1)
    k = rows.sum(); tr = np.diag(P)[rows].sum()          # trace over observed rows only
    return (k - tr) / (k - 1)

def h9_series(series, W, alt=False):
    d, u, nt = load(series)
    K, d = with_states(d, 'K5', nt)
    us = set(u); out = []
    by = {s: g for s, g in d.groupby('Season')}
    for s0 in u:
        ss = list(range(s0, s0 + W))
        if not all(s in us for s in ss): continue
        t1 = [set(by[s][by[s].tier == 1].k) for s in ss]
        E = set.intersection(*t1)
        ea, eb, na, nb = [], [], [], []
        promos = 0
        for s, s2, A1, B1 in zip(ss, ss[1:], t1, t1[1:]):
            A = by[s].set_index('k'); B = by[s2].set_index('k')
            promos += len(B1 - A1)
            for k in A.index.intersection(B.index):
                if k in E:
                    f = lambda p: 0 if p <= 4 else (1 if p <= 7 else 2)
                    ea.append(f(A.pos[k])); eb.append(f(B.pos[k]))
                else:
                    na.append(A.st[k]); nb.append(B.st[k])
        n1 = max(len(x) for x in t1); distinct = len(set.union(*t1))
        R = (distinct - n1) / promos if promos else np.nan
        out.append(dict(series=series, start=s0, E=shorrocks(np.array(ea), np.array(eb), 3),
                        R=R, Rp=shorrocks(np.array(na, int), np.array(nb, int), K), n_elite=len(E)))
    return pd.DataFrame(out)

def corr(df, col):
    x = df.E.values; y = df[col].values; m = np.isfinite(x) & np.isfinite(y)
    return np.corrcoef(x[m], y[m])[0, 1]

def within(df, col):
    g = df.copy()
    for c in ('E', col): g[c] = g[c] - g.groupby('series')[c].transform('mean')
    return corr(g, col)

def block_boot(df, col, W, rng, fn):
    parts = [g.reset_index(drop=True) for _, g in df.groupby('series')]
    vals = []
    for _ in range(NBOOT):
        res = []
        for g in parts:
            n = len(g); idx = []
            while len(idx) < n:
                st = rng.integers(0, max(n - W + 1, 1)); idx += list(range(st, min(st + W, n)))
            res.append(g.iloc[idx[:n]])
        vals.append(fn(pd.concat(res), col))
    return np.array(vals)

def h9(eng, W, col, rng):
    df = pd.concat([h9_series(s, W) for s in (eng,) + SERIES2], ignore_index=True)
    out = {}
    for lab, fn in (('pooled', corr), ('within', within)):
        r = fn(df, col); bs = np.abs(block_boot(df, col, W, rng, fn))
        lo5 = np.percentile(bs, 5)
        out[lab] = dict(r=r, abs_p5=lo5, abs_p95=np.percentile(bs, 95),
                        rejected=bool(abs(r) > 0.5 and lo5 > 0.5), inconclusive=bool(not (abs(r) > 0.5 and lo5 > 0.5) and np.percentile(bs, 95) > 0.5))
    return dict(eng=eng, W=W, component=col, n_windows=len(df), **{f'{k}_{a}': b for k, v in out.items() for a, b in v.items()}), df

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(20261010)
    res8 = []
    for c in ('EQ5', 'K5', 'EQ4', 'EQ6', 'EQ5+exit'):
        for s in ('ENG-4', 'ENG-2') + SERIES2:
            r = h8(s, c, rng); res8.append(r)
            print('H8', json.dumps({a: (round(b, 4) if isinstance(b, float) else b) for a, b in r.items()}), flush=True)
    pd.DataFrame(res8).to_csv(f"{out}/h8_results.csv", index=False)
    res9 = []
    for eng, W, col in [('ENG-4', 10, 'R'), ('ENG-4', 10, 'Rp'), ('ENG-4', 8, 'R'), ('ENG-4', 12, 'R'), ('ENG-2', 10, 'R'), ('ENG-2', 10, 'Rp')]:
        r, df = h9(eng, W, col, rng); res9.append(r)
        if eng == 'ENG-4' and W == 10 and col == 'R': df.to_csv(f"{out}/h9_windows_primary.csv", index=False)
        print('H9', json.dumps({a: (round(b, 4) if isinstance(b, float) else b) for a, b in r.items()}), flush=True)
    pd.DataFrame(res9).to_csv(f"{out}/h9_results.csv", index=False)
