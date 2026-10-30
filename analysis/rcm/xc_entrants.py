"""Top-four entrants across the Big Five, 2007/08-2022/23 (England to 2021/22): established vs outsider (top-four finish in the
previous ten seasons or not), and resource trajectory on the transfer-spend proxy. Usage: FR_SRC=<src> python -I xc_entrants.py xc_panel.csv"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'..','trend'))
from trend_xc import t1
P=pd.read_csv(sys.argv[1]); P['res']=P.groupby(['country','Season']).R3.rank(ascending=False,method='first')
rows=[]
for c in ['ENG','ESP','ITA','GER','FRA']:
    d=t1(c,lo=1990,hi=2024); top=set(zip(d[d.pos<=4].club,d[d.pos<=4].Season))
    Q=P[P.country==c]
    for s in range(2007,int(Q.Season.max())+1):
        cur=Q[(Q.Season==s)&(Q.pos<=4)]
        for r in cur.itertuples():
            if (r.club,s-1) in top: continue                       # not a new entry
            est=any((r.club,s-j) in top for j in range(2,11))
            prev=Q[(Q.Season==s-3)&(Q.ewclub==r.ewclub)]
            gain=(prev.res.iloc[0]-r.res) if len(prev) else np.nan
            kind='resource surge' if gain==gain and gain>=5 else ('top-4 spender' if r.res<=4 else 'beat its money')
            rows.append(dict(country=c,season=s,club=r.club,established=est,res_rank=int(r.res),res_gain_3y=gain,kind=kind))
E=pd.DataFrame(rows); E.to_csv(sys.argv[2],index=False)
pd.set_option('display.width',200)
T=E.groupby('country').agg(entries=('club','size'),outsiders=('established',lambda x:int((~x).sum())))
T['outsider share']=(T.outsiders/T.entries).round(2)
print(T.loc[['ENG','ESP','ITA','GER','FRA']].to_string())
print("\nOutsider entries:"); print(E[~E.established].sort_values(['country','season'])[['country','season','club','res_rank','kind']].to_string(index=False))
print("\nAll entries by resource kind:"); print(pd.crosstab(E.country,E.kind).loc[['ENG','ESP','ITA','GER','FRA']])
