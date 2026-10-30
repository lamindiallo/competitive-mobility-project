"""Registered H2 test (Protocol §3): trend in the block mobility index + Anderson-Goodman stationarity.
Usage: FR_SRC=... FR_LADDERS=... python -I h2.py <outdir> [quick]"""
import os, sys, json, math, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
from common import load, with_states, season_pairs, reach_mfpt

QUICK = len(sys.argv) > 2
NNULL = 99 if QUICK else 499
NBOOT = 999 if QUICK else 9999
NPERM = 199 if QUICK else 1999
NPOW = 100 if QUICK else 300

def pair_list(d, usable):
    PR = season_pairs(d, usable)
    out = []
    for a in sorted(PR):
        keys, sa, sb = PR[a]
        m = sb >= 0
        out.append((a, sa[m], sb[m]))
    return out

def counts(prs, K):
    C = np.zeros((K, K))
    for _, a, b in prs: np.add.at(C, (a, b), 1)
    return C

def block_index(prs, K, src, rng):
    C = counts(prs, K)
    P = C / np.maximum(C.sum(1, keepdims=True), 1)
    obs = reach_mfpt(P, src, 0)
    nv = []
    for _ in range(NNULL):
        Cn = np.zeros((K, K))
        for _, a, b in prs: np.add.at(Cn, (a, rng.permutation(b)), 1)
        Pn = Cn / np.maximum(Cn.sum(1, keepdims=True), 1)
        nv.append(reach_mfpt(Pn, src, 0))
    nv = np.array(nv); fin = nv[np.isfinite(nv)]
    nm = fin.mean()
    M = 0.0 if not np.isfinite(obs) else nm / obs
    Mnull = np.where(np.isfinite(nv), nm / nv, 0.0)
    return dict(start=prs[0][0], end=prs[-1][0] + 1, mfpt=obs, null=nm, G=obs / nm, M=M, Mnull_sd=Mnull.std(ddof=1))

def blocks(prs, W):
    """Non-overlapping blocks of W consecutive pairs, anchored on the most recent; incomplete earliest block dropped."""
    n = len(prs) // W
    tail = prs[len(prs) - n * W:]
    return [tail[b * W:(b + 1) * W] for b in range(n)]

def ols_t(y, x):
    X = np.column_stack([np.ones_like(x), x]); n = len(y)
    XtXi = np.linalg.inv(X.T @ X); beta = XtXi @ X.T @ y; e = y - X @ beta
    V = XtXi @ (X.T * e ** 2) @ X @ XtXi * n / (n - 2)       # HC1
    return beta[1], beta[1] / math.sqrt(V[1, 1])

WEBB = np.array([-math.sqrt(1.5), -1, -math.sqrt(.5), math.sqrt(.5), 1, math.sqrt(1.5)])
def wild_p(y, x, rng):
    b, t = ols_t(y, x)
    e0 = y - y.mean()
    ts = np.empty(NBOOT)
    for r in range(NBOOT):
        ys = y.mean() + e0 * rng.choice(WEBB, len(y))
        ts[r] = ols_t(ys, x)[1]
    return b, t, (1 + (np.abs(ts) >= abs(t)).sum()) / (NBOOT + 1)

def mahonian(n):
    dist = [1]
    for m in range(2, n + 1):
        new = [0] * (len(dist) + m - 1)
        for i, c in enumerate(dist):
            for j in range(m): new[i + j] += c
        dist = new
    return np.array(dist, float)

def mann_kendall(y):
    n = len(y); S = 0; ties = False
    for i in range(n):
        for j in range(i + 1, n):
            s = np.sign(y[j] - y[i]); S += s
            if s == 0: ties = True
    if n <= 10 and not ties:
        dist = mahonian(n); dist /= dist.sum()
        maxinv = n * (n - 1) // 2
        Svals = maxinv - 2 * np.arange(len(dist))        # S = concordant - discordant
        p = dist[np.abs(Svals) >= abs(S)].sum()
        return int(S), float(p), 'exact'
    _, cnt = np.unique(y, return_counts=True)
    var = (n * (n - 1) * (2 * n + 5) - sum(c * (c - 1) * (2 * c + 5) for c in cnt)) / 18
    z = (S - np.sign(S)) / math.sqrt(var) if S != 0 else 0.0
    p = math.erfc(abs(z) / math.sqrt(2))
    return int(S), float(p), 'normal'

def lr_homog(Cs):
    Cp = sum(Cs); Pp = Cp / np.maximum(Cp.sum(1, keepdims=True), 1)
    lr = 0.0
    for C in Cs:
        Pb = C / np.maximum(C.sum(1, keepdims=True), 1)
        with np.errstate(divide='ignore', invalid='ignore'):
            lr += np.where(C > 0, C * np.log(Pb / Pp), 0).sum()
    return 2 * lr

def stationarity(prs, K, groups, rng):
    """groups: list of lists of pair indices (sub-periods). Permute whole pairs across sub-periods."""
    pc = [counts([p], K) for p in prs]
    obs = lr_homog([sum(pc[i] for i in g) for g in groups])
    sizes = [len(g) for g in groups]; allidx = np.concatenate(groups)
    pv = np.empty(NPERM)
    for r in range(NPERM):
        sh = rng.permutation(allidx); gs = np.split(sh, np.cumsum(sizes)[:-1])
        pv[r] = lr_homog([sum(pc[i] for i in g) for g in gs])
    return obs, (1 + (pv >= obs).sum()) / (NPERM + 1)

def stiffen(P, delta):
    Q = P.copy()
    for i in range(len(P)):
        off = [j for j in range(len(P)) if j != i and P[i, j] > 0]
        room = sum(Q[i, j] for j in off)
        if room <= 0: continue
        take = min(delta, room * 0.99); Q[i, i] += take
        for j in off: Q[i, j] -= take * P[i, j] / room
    return Q

def stat_power(prs, K, groups, rng):
    Pp = counts(prs, K); Pp = Pp / np.maximum(Pp.sum(1, keepdims=True), 1)
    half = len(prs) // 2
    def sim(delta):
        P2 = stiffen(Pp, delta); out = []
        for n, (y, a, _) in enumerate(prs):
            P = Pp if n < half else P2
            cum = np.cumsum(P[a], 1); u = rng.random(len(a))
            b = np.minimum((u[:, None] > cum).sum(1), K - 1)
            out.append((y, a, b))
        pc = [counts([p], K) for p in out]
        return lr_homog([sum(pc[i] for i in g) for g in groups])
    null = np.array([sim(0.0) for _ in range(NPOW)]); crit = np.percentile(null, 95)
    return {d: float(np.mean([sim(d) > crit for _ in range(NPOW)])) for d in (0.05, 0.10, 0.20)}

SRC = {('K5', 4): 4, ('K5', 2): 4, ('K4', 4): 3, ('K4', 2): 3, ('K6', 4): 2, ('K6', 2): 2, ('EQ5', 4): 4, ('EQ5', 2): 4}

def run(series, config, W, rng, power=False):
    d, usable, nt = load(series)
    K, d = with_states(d, config, nt)
    prs = pair_list(d, usable)
    bl = blocks(prs, W)
    rows = [block_index(b, K, SRC[(config, nt)], rng) for b in bl]
    df = pd.DataFrame(rows)
    x = np.arange(len(df), dtype=float)
    res = dict(series=series, config=config, W=W, n_blocks=len(df), first=int(df.start.min()), last=int(df.end.max()))
    if len(df) < 4:
        res['note'] = 'not computable: fewer than four blocks'
        return res
    for idx in ('M', 'G'):
        y = df[idx].values.astype(float)
        ok = np.isfinite(y)
        if ok.sum() < 4: continue
        b, t, p = wild_p(y[ok], x[ok], rng)
        S, pmk, how = mann_kendall(y[ok])
        res.update({f'{idx}_slope': b, f'{idx}_t': t, f'{idx}_p_wild': p, f'{idx}_MK_S': S, f'{idx}_MK_p': pmk, f'{idx}_MK': how,
                    f'{idx}_n': int(ok.sum())})
    nullsd = float(np.median(df.Mnull_sd)); change = abs(res['M_slope']) * (len(df) - 1)
    res.update(M_null_sd=nullsd, M_implied_change=change, magnitude_ok=bool(change > nullsd),
               decline_sig=bool(res['M_p_wild'] < 0.05 and res['M_slope'] < 0),
               rise_sig=bool(res['M_p_wild'] < 0.05 and res['M_slope'] > 0))
    # stationarity across the same blocks, then halves and thirds
    used = [p for b in bl for p in b]
    groups = [list(range(i * W, (i + 1) * W)) for i in range(len(bl))]
    res['stat_blocks_LR'], res['stat_blocks_p'] = stationarity(used, K, [np.array(g) for g in groups], rng)
    for lab, parts in (('halves', 2), ('thirds', 3)):
        gs = np.array_split(np.arange(len(prs)), parts)
        res[f'stat_{lab}_LR'], res[f'stat_{lab}_p'] = stationarity(prs, K, gs, rng)
    if power:
        res['stat_power'] = stat_power(used, K, [np.array(g) for g in groups], rng)
    res['blocks'] = df[['start', 'end', 'mfpt', 'null', 'G', 'M', 'Mnull_sd']].round(4).to_dict('records')
    return res

if __name__ == '__main__':
    out = sys.argv[1]; os.makedirs(out, exist_ok=True)
    rng = np.random.default_rng(20261009)
    plan = [(s, 'K5', 4, True) for s in ('ENG-4', 'ESP-2', 'ITA-2', 'GER-2', 'FRA-2', 'ENG-2')]
    plan += [(s, 'K5', w, False) for w in (6, 8) for s in ('ENG-4', 'ESP-2', 'ITA-2', 'GER-2', 'FRA-2', 'ENG-2')]
    plan += [(s, c, 4, False) for c in ('K6', 'K4', 'EQ5') for s in ('ENG-4', 'ESP-2', 'ITA-2', 'GER-2', 'FRA-2', 'ENG-2')]
    allres = []
    with open(f"{out}/h2_results.jsonl", 'w') as fh:
        for s, c, w, pw in plan:
            r = run(s, c, w, rng, pw); allres.append(r)
            fh.write(json.dumps(r, default=float) + '\n'); fh.flush()
            print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items() if k != 'blocks'}, default=float), flush=True)
