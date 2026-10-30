"""Competitive Mobility Project, website v2: data model (D286-D293).
Loads the ladders, assigns every club-season to a position band and measures what happened next.
Realistic ceilings (D288): of all club-seasons in the same band in the same league, the share that reached each goal.
Ten-year goals use starting seasons 2004/05-2015/16; five-year goals 2004/05-2020/21 (outcomes to 2025/26)."""
import os, re
import numpy as np, pandas as pd

LEAGUES = {
    'ENG': dict(country='England', file='ladder_ENG4.csv', start=1992, tiers={1: 'Premier League', 2: 'Championship', 3: 'League One', 4: 'League Two'}),
    'ESP': dict(country='Spain', file='ladder_ESP.csv', start=1993, tiers={1: 'LaLiga', 2: 'Segunda División'}),
    'ITA': dict(country='Italy', file='ladder_ITA.csv', start=1994, tiers={1: 'Serie A', 2: 'Serie B'}),
    'GER': dict(country='Germany', file='ladder_GER.csv', start=1992, tiers={1: 'Bundesliga', 2: '2. Bundesliga'}),
    'FRA': dict(country='France', file='ladder_FRA.csv', start=1993, tiers={1: 'Ligue 1', 2: 'Ligue 2'}),
}
ORDER = ['ENG', 'ESP', 'ITA', 'GER', 'FRA']
# Reserve teams cannot be promoted into their first team's division, so they are left out of every
# realistic-ceiling count (as starting points). They stay on the ladder, where they did take places.
RESERVE = re.compile(r'(?:\bB$|Castilla|Sevilla Atl[eé]tico|Atl[eé]tico Madrid B|Athletic Club B|\bII$)')
START, END10, END5 = 2004, 2015, 2020

GOALS = {  # key: (label, horizon)
    'title10': ('won the league within ten seasons', 10), 'top4next': ('finished in the top four again the next season', 1),
    'top4_10': ('reached the top four within ten seasons', 10), 'top6_10': ('reached the top six within ten seasons', 10),
    'stay5': ('stayed up for all of the next five seasons', 5), 'back5': ('were back in the top flight within five seasons', 5),
    'up5': ('went up within five seasons', 5), 'tf10': ('reached the top flight within ten seasons', 10),
    'backup5': ('were back up within five seasons', 5),
}
BAND_GOALS = {'1': ['title10', 'top4next'], '2-4': ['title10', 'top4next'], '5-7': ['top4_10', 'title10'],
              '8-12': ['top4_10', 'top6_10', 'stay5'], '13+': ['stay5', 'top6_10', 'top4_10'], 'rel': ['back5', 'top4_10'],
              'prom': ['stay5', 'top6_10'], 'top': ['up5', 'tf10'], 'bot': ['up5', 'tf10']}

ARTICLE = {'Premier League', 'Championship', 'Bundesliga', 'Segunda División'}
def the(c, t):
    n = LEAGUES[c]['tiers'][t]; return ('the ' + n) if n in ARTICLE else n

def band_label(c, tier, b):
    T = the(c, tier)
    return {'1': f'won {T}', '2-4': f'finished 2nd to 4th in {T}', '5-7': f'finished 5th to 7th in {T}',
            '8-12': f'finished 8th to 12th in {T}', '13+': f'finished 13th or lower in {T} and stayed up',
            'rel': f'was relegated from {T}', 'prom': f'was promoted from {T}',
            'top': f'finished in the top half of {T} without going up', 'bot': f'finished in the bottom half of {T}'}[b]

def load(IN):
    L, NOCH = {}, {(r.country, r.season) for r in pd.read_csv(os.path.join(IN, 'no_champion.csv')).itertuples()}
    nxt = pd.read_csv(os.path.join(IN, 'tiers_2026_27.csv'))
    for c, m in LEAGUES.items():
        d = pd.read_csv(os.path.join(IN, m['file'])); d = d[d.Season >= m['start']].copy()
        n = d.groupby(['Season', 'tier']).size().unstack(fill_value=0)
        off = {s: {t: int(n.loc[s, [x for x in n.columns if x < t]].sum()) for t in n.columns} for s in n.index}
        d['rank'] = [off[r.Season][r.tier] + r.pos for r in d.itertuples()]
        d['N'] = [int(n.loc[r.Season, r.tier]) for r in d.itertuples()]
        d['champ'] = (d.tier == 1) & (d.pos == 1) & np.array([((c, s) not in NOCH) for s in d.Season])
        last = int(d.Season.max())
        tier_at = {(r.k, r.Season): r.tier for r in d.itertuples()}
        known = {(r.k): r.tier_2026 for r in nxt[nxt.country == c].itertuples()}
        def next_tier(k, s, tier, pos):
            if s < last: return tier_at.get((k, s + 1), 9)
            if k in known: return known[k]
            # 2026/27 not fully known below the top flight: infer what is needed for banding only
            if tier == 1: return 2
            if c == 'ENG' and tier == 2: return 3   # England's top two divisions for 2026/27 are fully listed
            if c == 'ENG' and tier == 3 and pos >= 21: return 4   # League One relegates its bottom four
            return tier   # not promoted (promoted clubs are all listed in tiers_2026_27.csv)
        d['next_tier'] = [next_tier(r.k, r.Season, r.tier, r.pos) for r in d.itertuples()]
        def band(r):
            if r.tier == 1:
                if r.pos == 1: return '1'
                if r.pos <= 4: return '2-4'
                if r.pos <= 7: return '5-7'
                if r.next_tier > 1: return 'rel'
                return '8-12' if r.pos <= 12 else '13+'
            if r.next_tier < r.tier: return 'prom'
            if c == 'ENG' and r.tier in (2, 3) and r.next_tier > r.tier: return 'rel'   # England: the third and fourth divisions are covered
            return 'top' if r.pos <= r.N / 2 else 'bot'
        d['band'] = [band(r) for r in d.itertuples()]
        d['reserve'] = d.club.astype(str).str.contains(RESERVE)
        # outcomes
        S = {(r.k, r.Season): r for r in d.itertuples()}
        def outcome(r, g):
            fut = lambda h: [S.get((r.k, r.Season + i)) for i in range(1, h + 1)]
            if g == 'title10': return any(x is not None and x.champ for x in fut(10))
            if g == 'top4next': x = fut(1)[0]; return x is not None and x.tier == 1 and x.pos <= 4
            if g == 'top4_10': return any(x is not None and x.tier == 1 and x.pos <= 4 for x in fut(10))
            if g == 'top6_10': return any(x is not None and x.tier == 1 and x.pos <= 6 for x in fut(10))
            if g == 'tf10': return any(x is not None and x.tier == 1 for x in fut(10))
            if g == 'back5': return any(x is not None and x.tier == 1 for x in fut(5))
            if g == 'backup5': return any(x is not None and x.tier <= r.tier for x in fut(5))
            if g == 'up5': return any(x is not None and x.tier < r.tier for x in fut(5))
            if g == 'stay5':
                target = 1 if r.tier == 1 else r.tier - 1
                return all(x is not None and x.tier <= target for x in fut(5))
        for g, (_, h) in GOALS.items():
            end = last - h
            d[g] = [outcome(r, g) if START <= r.Season <= end else np.nan for r in d.itertuples()]
        L[c] = d
    return L, NOCH

def club_interval(g, goal, reps=2000, seed=7):
    """95% interval for a share when the same club appears several times: resample clubs, not seasons."""
    v = g[['k', goal]].dropna()
    if v.empty: return (np.nan, np.nan)
    by = v.groupby('k')[goal].agg(['sum', 'count']).values
    rng = np.random.default_rng(seed); idx = rng.integers(0, len(by), size=(reps, len(by)))
    s = by[idx]; share = s[:, :, 0].sum(1) / s[:, :, 1].sum(1)
    return (float(np.percentile(share, 2.5)), float(np.percentile(share, 97.5)))

def ceilings(L):
    rows = []
    for c, d in L.items():
        d = d[~d.reserve]
        for (tier, b), g in d.groupby(['tier', 'band']):
            for goal in (BAND_GOALS[b] if not (b == 'rel' and tier > 1) else ['backup5', 'tf10']):
                if tier >= 3 and goal == 'top6_10': continue
                v = g[goal].dropna(); lo, hi = club_interval(g, goal)
                rows.append(dict(country=c, tier=int(tier), band=b, goal=goal, n=int(len(v)), hits=int(v.sum()), share=float(v.mean()) if len(v) else np.nan,
                                 lo=round(lo, 4) if lo == lo else np.nan, hi=round(hi, 4) if hi == hi else np.nan, clubs=int(g.loc[v.index].k.nunique()),
                                 first=int(g.loc[v.index].Season.min()) if len(v) else None, last=int(g.loc[v.index].Season.max()) if len(v) else None))
    return pd.DataFrame(rows)
