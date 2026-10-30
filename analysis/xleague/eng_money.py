"""Exploratory: English transfer money relative to, and flowing into, the other Big Five leagues.
Source: eordo/transfermarkt-data (fees in EUR, nominal). Internal analysis only (D207).
Usage: FR_SRC=... python -I eng_money.py"""
import os, pandas as pd, numpy as np
SRC = os.environ['FR_SRC'] + '/eordo_transfermarkt-data'
LG = {'premier_league': 'ENG', 'laliga': 'ESP', 'bundesliga': 'GER', 'serie_a': 'ITA', 'ligue_1': 'FRA'}
CTRY = {'England': 'ENG', 'Spain': 'ESP', 'Germany': 'GER', 'Italy': 'ITA', 'France': 'FRA'}
rows = []
for f, c in LG.items():
    for s in range(2004, 2026):
        p = f'{SRC}/{f}/{s}.csv'
        if os.path.exists(p):
            d = pd.read_csv(p); d['lg'] = c; rows.append(d)
T = pd.concat(rows, ignore_index=True)
T = T[(T.is_loan == 0)]
T['fee'] = pd.to_numeric(T.fee, errors='coerce').fillna(0) / 1e6
buy = T[T.movement == 'in']
spend = buy.groupby(['season', 'lg', 'club']).fee.sum().reset_index()
# all clubs of each league-season, including zero spenders
clubs = T.groupby(['season', 'lg', 'club']).size().reset_index()[['season', 'lg', 'club']]
spend = clubs.merge(spend, how='left').fillna({'fee': 0})
spend = spend.sort_values(['lg', 'club', 'season'])
spend['s3'] = spend.groupby(['lg', 'club']).fee.transform(lambda x: x.rolling(3, min_periods=1).mean())
# promoted = in league this season, not last season (within data)
prev = {(r.season, r.lg): set(g.club) for (r_s, r_l), g in spend.groupby(['season', 'lg']) for r in [g.iloc[0]]}
spend['promoted'] = [ (s - 1, l) in prev and c not in prev[(s - 1, l)] for s, l, c in zip(spend.season, spend.lg, spend.club)]
print('=== A. Gross transfer spend by league (EUR m, nominal, summer+winter, permanent deals) ===')
lgsum = spend.groupby(['season', 'lg']).fee.sum().unstack().round(0)
print(lgsum.loc[[2005, 2010, 2015, 2019, 2022, 2023, 2024, 2025]].to_string())
print('\n=== B. How many of Europe\'s top-20 spenders (single season) are English ===')
for s in [2005, 2010, 2015, 2019, 2022, 2023, 2024, 2025]:
    t = spend[spend.season == s].nlargest(20, 'fee')
    print(s, dict(t.lg.value_counts()))
print('\n=== C. Promoted English clubs: spend in promotion season vs the other leagues ===')
for s in range(2019, 2026):
    pr = spend[(spend.season == s) & (spend.lg == 'ENG') & spend.promoted]
    oth = spend[(spend.season == s) & (spend.lg != 'ENG')]
    for _, r in pr.iterrows():
        rank = (oth.fee > r.fee).sum() + 1
        beats = {l: int((oth[oth.lg == l].fee < r.fee).sum()) for l in ('ESP', 'GER', 'ITA', 'FRA')}
        nl = {l: int((oth.lg == l).sum()) for l in ('ESP', 'GER', 'ITA', 'FRA')}
        print(f"{s} {r.club:28s} {r.fee:6.1f}m  would rank {rank:3d} among {len(oth)} non-English clubs; outspends " +
              ', '.join(f"{beats[l]}/{nl[l]} {l}" for l in beats))
print('\n=== D. English money in other leagues: fees paid BY Premier League clubs TO clubs of each league ===')
eng_in = buy[(buy.lg == 'ENG') & buy.dealing_country.isin(['Spain', 'Germany', 'Italy', 'France'])].copy()
eng_in['to'] = eng_in.dealing_country.map(CTRY)
# each league's total sales income (fees received from anyone), from its own clubs' 'out' rows
sales = T[(T.movement == 'out') & (T.lg != 'ENG')].groupby(['season', 'lg']).fee.sum()
flow = eng_in.groupby(['season', 'to']).fee.sum()
out = pd.DataFrame({'from_ENG': flow, 'all_sales': sales.rename_axis(['season', 'to'])}).fillna(0)
out['share'] = (out.from_ENG / out.all_sales).round(2)
for per, (a, b) in {'2005-09': (2005, 2009), '2010-14': (2010, 2014), '2015-19': (2015, 2019), '2020-25': (2020, 2025)}.items():
    o = out.loc[(slice(a, b), slice(None)), :].groupby(level='to').sum()
    print(per, {l: f"{o.loc[l,'from_ENG']:.0f}m = {o.loc[l,'from_ENG']/o.loc[l,'all_sales']:.0%} of sales" for l in o.index})
print('\n=== E. Who in each league receives English money: the league\'s own big spenders or the rest? (2015-25) ===')
big = {}
for (s, l), g in spend[spend.lg != 'ENG'].groupby(['season', 'lg']):
    big[(s, l)] = set(g.nlargest(4, 's3').club)
e = eng_in[eng_in.season >= 2015].copy()
# map receiving club to its league-season (receiver must be in that league that season)
mem = {(s, l): set(g.club) for (s, l), g in spend.groupby(['season', 'lg'])}
e['in_league'] = [c in mem.get((s, l), set()) for c, s, l in zip(e.dealing_club, e.season, e.to)]
e['big4'] = [c in big.get((s, l), set()) for c, s, l in zip(e.dealing_club, e.season, e.to)]
for l, g in e.groupby('to'):
    tot = g.fee.sum(); il = g[g.in_league].fee.sum(); b4 = g[g.big4].fee.sum()
    print(f"{l}: {tot:.0f}m from English clubs; to top-flight clubs {il/tot:.0%} (of which to the league's 4 biggest spenders {b4/il:.0%}); to clubs outside the top flight {1-il/tot:.0%}")
print('\n=== F. Net transfer balance with England, 2015-25 (EUR m): English purchases from league minus English sales to league ===')
eng_out = T[(T.lg == 'ENG') & (T.movement == 'out') & T.dealing_country.isin(['Spain', 'Germany', 'Italy', 'France'])].copy()
eng_out['to'] = eng_out.dealing_country.map(CTRY)
a = eng_in[eng_in.season >= 2015].groupby('to').fee.sum(); b = eng_out[eng_out.season >= 2015].groupby('to').fee.sum()
print((a - b).round(0).to_dict())
