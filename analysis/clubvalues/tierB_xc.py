"""Tier B, model-free: of club-seasons in a given position, the share whose club reached the top four within 10 seasons.
Observed outcomes only (D231: the chain flatters outsiders). Usage: python -I tierB_xc.py <ladders_dir> <out.csv>"""
import sys, os, pandas as pd
rows = []
for c in ('ENG', 'ESP', 'ITA', 'GER', 'FRA'):
    L = pd.read_csv(os.path.join(sys.argv[1], f'ladder_{c}.csv'))
    top4 = {(r.k, r.Season) for r in L[(L.tier == 1) & (L.pos <= 4)].itertuples()}
    def band(r):
        if r.tier == 1: return 'T1 5-10' if 5 <= r.pos <= 10 else ('T1 11-last' if r.pos > 10 else None)
        return 'Tier 2'
    L['band'] = L.apply(band, axis=1)
    for era, (a, b) in {'1992-2003': (1992, 2003), '2004-2014': (2004, 2014)}.items():
        S = L[(L.Season >= a) & (L.Season <= b) & L.band.notna()]
        for bd, g in S.groupby('band'):
            hit = [any((r.k, s) in top4 for s in range(r.Season + 1, r.Season + 11)) for r in g.itertuples()]
            rows.append(dict(country=c, era=era, band=bd, club_seasons=len(g), share_top4_within10=round(sum(hit) / len(g), 3)))
T = pd.DataFrame(rows); T.to_csv(sys.argv[2], index=False)
print(T.pivot_table(index=['band', 'era'], columns='country', values='share_top4_within10').to_string())
