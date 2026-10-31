"""Shared data and state definitions for the registered H1/H2 tests.
Implements `06 Analysis/H1_H2_Test_Protocol.md` §1 exactly.
Env: FR_SRC (public GitHub clones, see rcm/README.md), FR_LADDERS (folder holding ladder_XX.csv);
optional FR_ENG4 (a four-tier England ladder CSV with club, Season, tier, pos, k, used instead of rebuilding from FR_SRC)."""
import os, sys, numpy as np, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'rcm'))
from ladder import eng_ladder
from clubkey import ck

LADDERS = os.environ.get('FR_LADDERS')

def load(series):
    """series: 'ENG-4' or 'ENG-2','ESP-2','ITA-2','GER-2','FRA-2'. Returns club-season frame
    with k, Season, tier, pos, n1 (tier-1 size), ntot, rank; plus list of usable seasons."""
    if series == 'ENG-4' and os.environ.get('FR_ENG4'):      # sensitivity runs: a prepared four-tier ladder (e.g. the site's, D303)
        d = pd.read_csv(os.environ['FR_ENG4'])[['club', 'Season', 'tier', 'pos', 'k']].copy(); ntiers = 4
    elif series == 'ENG-4':
        d = eng_ladder(4, 1958, 2024)[['club', 'Season', 'tier', 'pos']].copy()
        d['k'] = d.club.map(ck); ntiers = 4
    else:
        d = pd.read_csv(os.path.join(LADDERS, f"ladder_{series[:3]}.csv"))
        d = d[['club', 'Season', 'tier', 'pos', 'k']].copy(); ntiers = 2
    d = d.drop_duplicates(['Season', 'k'])
    full = d.groupby('Season').tier.nunique()
    usable = sorted(full[full == ntiers].index)
    d = d[d.Season.isin(usable)].copy()
    d['n1'] = d.Season.map(d[d.tier == 1].groupby('Season').size())
    d = d.sort_values(['Season', 'tier', 'pos'])
    d['rank'] = d.groupby('Season').cumcount() + 1
    d['ntot'] = d.Season.map(d.groupby('Season').size())
    return d, usable, ntiers

def state_fn(config, ntiers):
    """Return (K, function row->state) for a configuration of protocol §1.2."""
    def k5(r):
        if r.tier == 1:
            if r.pos <= 4: return 0
            if r.pos <= 7: return 1
            if ntiers == 4: return 2
            return 2 if r.pos <= r.n1 - 3 else 3
        if ntiers == 4: return 3 if r.tier == 2 else 4
        return 3 if r.pos <= 6 else 4
    def k4(r):
        if r.tier == 1: return 0 if r.pos <= 4 else (1 if r.pos <= 10 else 2)
        return 3
    def k6(r):
        if ntiers == 4:
            if r.tier == 1: return 0 if r.pos <= 4 else (1 if r.pos <= 10 else 2)
            return 1 + r.tier
        if r.tier == 1:
            if r.pos <= 4: return 0
            if r.pos <= 7: return 1
            return 2 if r.pos <= r.n1 - 3 else 3
        return 4 if r.pos <= 6 else 5
    def eq5(r):
        return int(5 * (r['rank'] - 1) // r.ntot)
    return {'K5': (5, k5), 'K4': (4, k4), 'K6': (6, k6), 'EQ5': (5, eq5)}[config]

def with_states(d, config, ntiers):
    K, f = state_fn(config, ntiers)
    d = d.copy(); d['st'] = d.apply(f, axis=1).astype(int)
    return K, d

def season_pairs(d, usable):
    """dict a -> (keys_a, states_a, states_b or -1 if absent at b) for consecutive usable seasons."""
    out = {}
    S = {s: g.set_index('k').st for s, g in d.groupby('Season')}
    for a in usable:
        b = a + 1
        if b not in S: continue
        A, B = S[a], S[b]
        out[a] = (A.index.values, A.values.astype(int), B.reindex(A.index).fillna(-1).values.astype(int))
    return out

def reach_mfpt(P, i, j):
    """Mean first-passage time i->j; inf if j is not reached with probability one from i."""
    K = len(P)
    can = {j}; changed = True
    while changed:                           # states that can reach j
        changed = False
        for s in range(K):
            if s not in can and any(P[s, t] > 0 for t in can):
                can.add(s); changed = True
    reach = {i}; stack = [i]                 # states reachable from i without passing j
    while stack:
        s = stack.pop()
        if s == j: continue
        for t in range(K):
            if P[s, t] > 0 and t not in reach:
                reach.add(t); stack.append(t)
    if i == j: return 0.0
    if any(s not in can for s in reach): return np.inf
    idx = sorted(s for s in reach if s != j)
    A = np.eye(len(idx)) - P[np.ix_(idx, idx)]
    try: return float(np.linalg.solve(A, np.ones(len(idx)))[idx.index(i)])
    except np.linalg.LinAlgError: return np.inf
