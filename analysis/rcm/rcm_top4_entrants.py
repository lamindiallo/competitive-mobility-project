"""D218: classify Premier League top-four entrants by resource trajectory (transfer-spend proxy). Usage: python -I rcm_top4_entrants.py eng_rcm_panel.csv"""
import sys, pandas as pd
P=pd.read_csv(sys.argv[1])
R=P.pivot_table(index='k',columns='Season',values='rank'); Q=P.pivot_table(index='k',columns='Season',values='res_rank')
rows=[]
for s in sorted(P.Season.unique()):
    if s-1 not in R.columns: continue
    for k in R.index[(R[s]<=4)]:
        if not (R.loc[k,s-1]<=4):
            q0=Q.loc[k,s-3] if (s-3) in Q.columns else float('nan')
            rows.append(dict(season=f"{s}/{str(s+1)[2:]}",club=k,finish=int(R.loc[k,s]),res_rank_now=Q.loc[k,s],res_rank_3_before=q0,res_gain=q0-Q.loc[k,s]))
E=pd.DataFrame(rows)
E['type']=E.apply(lambda r:'resource surge (gain>=5)' if r.res_gain>=5 else ('big spender already (res rank<=4)' if r.res_rank_now<=4 else 'beat its money'),axis=1)
BIG6={'arsenal','chelsea','liverpool','manchester city','manchester united','tottenham hotspur'}
E['big6']=E.club.isin(BIG6)
print(E.to_string(index=False))
E['era']=E.season.str[:4].astype(int).map(lambda y:'2006-2013' if y<2014 else '2014-2022')
pd.set_option('display.width',200)
print(); print(pd.crosstab(E.era,E.type)); print(); print(pd.crosstab(E.era,E.big6.map({True:'Big Six re-entry',False:'outsider'})))
