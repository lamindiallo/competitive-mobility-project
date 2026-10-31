"""Lower divisions as officially classified (D305): England tiers 2-4 and the 2. Bundesliga, 1992/93-2024/25.

The second divisions of Spain, Italy and France already come from published final tables (D157), and 2025/26 comes
from the official tables for every division (D295). England's tiers 2-4 and Germany's tier 2 were still ordered from
match results (points, then goal difference, then goals scored). This script re-orders them with:
  - documented point deductions (DEDUCT, sources in the comments; checked against published tables, see
    06 Analysis/Second_Division_Official_Tables_D305.md);
  - the 2. Bundesliga 1993/94, where Rot-Weiss Essen was classified last (licence refused; opponents keep their results);
  - England 2019/20 League One and League Two, which were curtailed and decided on points per game (after deductions);
  - England's tie-break order: points, goal difference, goals scored. 2. Bundesliga: points, goal difference, goals scored; two points for a win before 1995/96.
Usage: FR_SRC=... python -I official_positions_t2.py <site ladders dir (in and out)> <log csv>"""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'rcm'))
from ladder import parse_of

SRC = os.environ['FR_SRC']
# (country, season start, tier, club name as in the results source): points deducted.
# England: footballsite.co.uk "Points deductions" and thecityground.com "Points deducted!" (agreeing lists), and the
# Wikipedia season articles for 2022/23-2024/25. Germany: de.wikipedia "Ewige Tabelle der 2. Fussball-Bundesliga", footnotes.
DEDUCT = {
    ('ENG', 1996, 4, 'Brighton & Hove Albion'): 2, ('ENG', 1997, 4, 'Leyton Orient'): 3, ('ENG', 2000, 4, 'Chesterfield'): 9,
    ('ENG', 2002, 4, 'Boston United'): 4, ('ENG', 2004, 4, 'Cambridge United'): 10, ('ENG', 2004, 3, 'Wrexham'): 10,
    ('ENG', 2006, 2, 'Leeds United'): 10, ('ENG', 2006, 3, 'Rotherham United'): 10, ('ENG', 2006, 4, 'Boston United'): 10,
    ('ENG', 2007, 3, 'Leeds United'): 15, ('ENG', 2007, 3, 'Luton Town'): 10, ('ENG', 2007, 3, 'AFC Bournemouth'): 10,
    ('ENG', 2007, 4, 'Rotherham United'): 10,
    ('ENG', 2008, 3, 'Stockport County'): 10, ('ENG', 2008, 4, 'Darlington'): 10, ('ENG', 2008, 4, 'AFC Bournemouth'): 17,
    ('ENG', 2008, 4, 'Luton Town'): 30, ('ENG', 2008, 4, 'Rotherham United'): 17,
    ('ENG', 2009, 2, 'Crystal Palace'): 10, ('ENG', 2009, 3, 'Hartlepool United'): 3, ('ENG', 2009, 3, 'Southampton'): 10,
    ('ENG', 2010, 3, 'Plymouth Argyle'): 10, ('ENG', 2010, 4, 'Hereford United'): 3, ('ENG', 2010, 4, 'Torquay United'): 1,
    ('ENG', 2011, 2, 'Portsmouth'): 10, ('ENG', 2011, 4, 'Port Vale'): 10,
    ('ENG', 2012, 3, 'Coventry City'): 10, ('ENG', 2012, 3, 'Portsmouth'): 10,
    ('ENG', 2013, 3, 'Coventry City'): 10, ('ENG', 2013, 4, 'AFC Wimbledon'): 3,
    ('ENG', 2014, 2, 'Rotherham United'): 3,
    ('ENG', 2018, 2, 'Birmingham City'): 9,
    ('ENG', 2019, 2, 'Wigan Athletic'): 12, ('ENG', 2019, 3, 'Bolton Wanderers'): 12, ('ENG', 2019, 4, 'Macclesfield'): 17,
    ('ENG', 2020, 2, 'Sheffield Wednesday'): 6,
    ('ENG', 2021, 2, 'Derby County'): 21, ('ENG', 2021, 2, 'Reading'): 6,
    ('ENG', 2022, 2, 'Reading'): 6, ('ENG', 2022, 2, 'Wigan Athletic'): 3,
    ('ENG', 2023, 3, 'Wigan Athletic'): 8, ('ENG', 2023, 3, 'Reading'): 6, ('ENG', 2023, 4, 'Morecambe'): 3,
    ('ENG', 2024, 2, 'Sheffield United'): 2,
    ('GER', 1995, 2, '1. FC Nurnberg'): 6, ('GER', 1995, 2, 'Hertha BSC'): 3, ('GER', 1996, 2, 'FC Gutersloh'): 3,
    ('GER', 2002, 2, 'SSV Reutlingen'): 6, ('GER', 2007, 2, 'TuS Koblenz'): 6, ('GER', 2008, 2, 'TuS Koblenz'): 3,
    ('GER', 2009, 2, 'Arminia Bielefeld'): 4, ('GER', 2010, 2, 'Arminia Bielefeld'): 3, ('GER', 2010, 2, '1860 Munchen'): 2,
    ('GER', 2014, 2, 'VfR Aalen'): 2, ('GER', 2014, 2, 'SV Sandhausen'): 3, ('GER', 2015, 2, 'SV Sandhausen'): 3,
}
PPG = {('ENG', 2019, 3), ('ENG', 2019, 4)}     # curtailed seasons decided on points per game
# Club classified last after its licence was refused (financial irregularities); its opponents keep their results
# against it, as in the published 1993/94 2. Bundesliga table
ANNUL = {('GER', 1993, 2): 'Rot-Weiss Essen'}
def WP(c, s): return 2 if (c == 'GER' and s < 1995) else 3   # three points for a win: England since 1981, Germany since 1995/96

def nm(x):   # openfootball (England 2022/23) adds FC/AFC suffixes
    for suf in (' AFC', ' FC'):
        if x.endswith(suf): return x[:-len(suf)]
    return x

def table(rows, c, s, t):
    bad = ANNUL.get((c, s, t))
    r = {}
    for h, a, hg, ag in rows:
        for tm, gf, ga in ((h, hg, ag), (a, ag, hg)):
            d = r.setdefault(tm, [0, 0, 0, 0]); d[0] += WP(c, s) if gf > ga else (1 if gf == ga else 0); d[1] += gf - ga; d[2] += gf; d[3] += 1
    T = pd.DataFrame([(k, *v) for k, v in r.items()], columns=['club', 'Pts', 'GD', 'GF', 'P'])
    T['ded'] = [DEDUCT.get((c, s, t, nm(x)), 0) for x in T.club]; T['Pts'] -= T.ded
    T['key'] = T.Pts / T.P if (c, s, t) in PPG else T.Pts
    T = T.sort_values(['key', 'GD', 'GF'], ascending=False).reset_index(drop=True)
    if bad: T = pd.concat([T[T.club != bad], T[T.club == bad]], ignore_index=True)
    return T

if __name__ == '__main__':
    lad, logf = sys.argv[1:3]; log = []; used = set()
    E = pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/england.csv', low_memory=False)
    G = pd.read_csv(f'{SRC}/jalapic_engsoccerdata/data-raw/germany.csv', low_memory=False)
    OF = {2: '2-championship', 3: '3-league1', 4: '4-league2'}
    for c, f, tiers, M in (('ENG', 'ladder_ENG4.csv', (2, 3, 4), E), ('GER', 'ladder_GER.csv', (2,), G)):
        L = pd.read_csv(f'{lad}/{f}')
        for s in range(1992, 2025):
            for t in tiers:
                g = M[(M.Season == s) & (M.tier == t)]
                if len(g): rows = list(zip(g.home.str.strip(), g.visitor.str.strip(), g.hgoal.astype(int), g.vgoal.astype(int)))
                elif c == 'ENG' and s == 2022: rows = parse_of(f'{SRC}/openfootball_england/2022-23/{OF[t]}.txt')
                else: continue
                T = table(rows, c, s, t)
                idx = L[(L.Season == s) & (L.tier == t)]
                if set(T.club) != set(idx.club):
                    log.append((c, s, t, 'NAME MISMATCH', None, None, str(sorted(set(T.club) ^ set(idx.club)))[:150])); continue
                used |= {(c, s, t, nm(x)) for x in T.club if (c, s, t, nm(x)) in DEDUCT}
                pos = dict(zip(T.club, range(1, len(T) + 1)))
                for i, r in idx.iterrows():
                    if r.pos != pos[r.club]:
                        why = 'points per game (curtailed season)' if (c, s, t) in PPG else ('classified last (licence refused)' if (c, s, t) in ANNUL else 'deduction')
                        log.append((c, s, t, r.club, int(r.pos), pos[r.club], why))
                    L.at[i, 'pos'] = pos[r.club]
        L.sort_values(['Season', 'tier', 'pos']).to_csv(f'{lad}/{f}', index=False)
    unused = [k for k in DEDUCT if k not in used]
    G_ = pd.DataFrame(log, columns=['country', 'season', 'tier', 'club', 'pos_results', 'pos_official', 'reason'])
    G_.to_csv(logf, index=False)
    print(len(G_), 'changes', G_.groupby(['country', 'tier']).size().to_dict())
    print('UNUSED deductions (name not found in that season):', unused)
    print(G_[G_.club == 'NAME MISMATCH'].to_string() if (G_.club == 'NAME MISMATCH').any() else 'no name mismatches')
