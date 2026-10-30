"""Top-flight positions as officially classified (D284), for published club records.
Results-based tables order tied clubs by goal difference. Spain and Italy separate ties by head-to-head results, and some
seasons carry point deductions. This script re-orders each top-flight season with:
  - head-to-head tie-breaks (Spain all seasons; Italy from 2005/06, when Serie A adopted them): points in matches among the tied clubs, then goal
    difference in those matches, then overall goal difference, then goals scored;
  - documented point deductions (DEDUCT) and administrative classifications (FORCE_LAST);
  - titles revoked and not reassigned (NO_CHAMPION).
Every changed position is written to a log. The registered analyses keep the results-based ladders (D163); this file
feeds the website's club records.
Usage: FR_SRC=... python -I official_positions.py <ladders_in_dir> <out_dir>"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rcm'))
from ladder import eng_ladder
from clubkey import ck

SRC = os.environ['FR_SRC']
# (country, season start, club name as in engsoccerdata): points deducted from the final table
DEDUCT = {('ENG', 1996, 'Middlesbrough'): 3, ('ENG', 2009, 'Portsmouth'): 9, ('ENG', 2023, 'Everton'): 8,
          ('ENG', 2023, 'Nottingham Forest'): 4,
          ('ITA', 2005, 'AC Milan'): 30, ('ITA', 2005, 'ACF Fiorentina'): 30, ('ITA', 2005, 'Lazio Roma'): 30,
          ('ITA', 2006, 'ACF Fiorentina'): 15, ('ITA', 2006, 'AC Milan'): 8, ('ITA', 2006, 'Reggina Calcio'): 11,
          ('ITA', 2006, 'Lazio Roma'): 3, ('ITA', 2006, 'AC Siena'): 1, ('ITA', 2022, 'Juventus'): 10}
FORCE_LAST = {('ITA', 2005, 'Juventus')}          # Calciopoli: classified last and relegated
NO_CHAMPION = {('ITA', 2004)}                     # 2004/05 title revoked, not reassigned
H2H_FROM = {'ESP': 0, 'ITA': 2005}   # Serie A adopted head-to-head tie-breaks in 2005/06
FILES = {'ESP': 'spain', 'ITA': 'italy'}

def table(rows, wp, c, s, h2h):
    t = {}
    for h, a, hg, ag in rows:
        for tm, gf, ga in ((h, hg, ag), (a, ag, hg)):
            d = t.setdefault(tm, dict(Pts=0, GD=0, GF=0)); d['Pts'] += wp if gf > ga else (1 if gf == ga else 0); d['GD'] += gf - ga; d['GF'] += gf
    T = pd.DataFrame([dict(club=k, **v) for k, v in t.items()])
    T['Pts'] -= [DEDUCT.get((c, s, x), 0) for x in T.club]
    T['last'] = [(c, s, x) in FORCE_LAST for x in T.club]
    T['h2h_pts'] = 0; T['h2h_gd'] = 0
    if h2h:
        for p, g in T.groupby('Pts'):
            if len(g) < 2: continue
            grp = set(g.club); mini = {x: [0, 0] for x in grp}
            for hm, aw, hg, ag in rows:
                if hm in grp and aw in grp:
                    mini[hm][0] += wp if hg > ag else (1 if hg == ag else 0); mini[aw][0] += wp if ag > hg else (1 if hg == ag else 0)
                    mini[hm][1] += hg - ag; mini[aw][1] += ag - hg
            for x in grp:
                T.loc[T.club == x, 'h2h_pts'] = mini[x][0]; T.loc[T.club == x, 'h2h_gd'] = mini[x][1]
    T = T.sort_values(['last', 'Pts', 'h2h_pts', 'h2h_gd', 'GD', 'GF'], ascending=[True, False, False, False, False, False]).reset_index(drop=True)
    T['pos_official'] = np.arange(1, len(T) + 1)
    return T

if __name__ == '__main__':
    lin, out = sys.argv[1:3]; os.makedirs(out, exist_ok=True); log = []
    # England: re-sort tier 1 with deductions (no head-to-head rule)
    E = eng_ladder(4, 1992, 2024); E['k'] = E.club.map(ck)
    for (s, tier), g in E[E.tier == 1].groupby(['Season', 'tier']):
        g = g.copy(); g['Pts2'] = g.Pts - [DEDUCT.get(('ENG', s, x), 0) for x in g.club]
        g = g.sort_values(['Pts2', 'GD', 'GF'], ascending=False); newpos = dict(zip(g.index, range(1, len(g) + 1)))
        for i, p in newpos.items():
            if E.at[i, 'pos'] != p: log.append(('ENG', s, E.at[i, 'club'], int(E.at[i, 'pos']), p, 'deduction'))
            E.at[i, 'pos'] = p
    E[['club', 'Season', 'tier', 'pos', 'k']].to_csv(f'{out}/ladder_ENG4.csv', index=False)
    # Spain, Italy: rebuild tier 1 from matches with head-to-head and deductions; map onto the ladder by club name
    for c, f in FILES.items():
        L = pd.read_csv(f'{lin}/ladder_{c}.csv'); M = pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/{f}.csv', low_memory=False); M = M[M.tier == 1]
        for s in sorted(L[L.tier == 1].Season.unique()):
            g = M[M.Season == s]
            rows = list(zip(g.home.str.strip(), g.visitor.str.strip(), g.hgoal.astype(int), g.vgoal.astype(int)))
            if not rows: continue
            T = table(rows, 3 if s >= (1995 if c == 'ESP' else 1994) else 2, c, s, s >= H2H_FROM.get(c, 9999))
            idx = L[(L.Season == s) & (L.tier == 1)]
            names = set(idx.club)
            if set(T.club) != names:
                log.append((c, s, 'NAME MISMATCH', len(names - set(T.club)), len(set(T.club) - names), str(sorted(names ^ set(T.club)))[:120])); continue
            pos = dict(zip(T.club, T.pos_official))
            for i, r in idx.iterrows():
                if r.pos != pos[r.club]: log.append((c, s, r.club, int(r.pos), int(pos[r.club]), 'head-to-head or deduction'))
                L.at[i, 'pos'] = pos[r.club]
        L.to_csv(f'{out}/ladder_{c}.csv', index=False)
    pd.DataFrame(sorted(NO_CHAMPION), columns=['country', 'season']).to_csv(f'{out}/no_champion.csv', index=False)
    G = pd.DataFrame(log, columns=['country', 'season', 'club', 'pos_results', 'pos_official', 'reason'])
    G.to_csv(f'{out}/official_position_changes.csv', index=False)
    print(len(G), 'position changes;', G.groupby('country').size().to_dict())
    print(G[G.club == 'NAME MISMATCH'].to_string() if (G.club == 'NAME MISMATCH').any() else 'no name mismatches')
    top = G[(G.pos_results <= 4) | (G.pos_official <= 4)] if G.pos_results.dtype != object else G
    print(top.to_string(index=False))
