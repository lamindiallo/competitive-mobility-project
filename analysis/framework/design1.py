import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from depth import eng_ladder
lad=eng_ladder(4)
# ladder rank across all four tiers
n=lad.groupby(['Season','tier']).size().unstack(fill_value=0)
off={}
for s in n.index:
    c=0; o={}
    for t in [1,2,3,4]:
        o[t]=c; c+=int(n.loc[s,t])
    off[s]=o
lad['rank']=[off[r.Season][r.tier]+r.pos for r in lad.itertuples()]
lad['N']=[sum(off[r.Season][4:] if False else [0])+0 for r in lad.itertuples()]
size=lad.groupby('Season').size()
ss=sorted(set(lad.Season))
rows=[]
for a,b in zip(ss,ss[1:]):
    if b!=a+1: continue
    A=lad[lad.Season==a].drop_duplicates('k').set_index('k')
    B=lad[lad.Season==b].drop_duplicates('k').set_index('k')
    ix=A.index.intersection(B.index)
    d=(B.loc[ix,'rank']-A.loc[ix,'rank']).abs()
    for t in [1,2,3,4]:
        m=A.loc[ix,'tier']==t
        if m.sum()<8: continue
        rows.append(dict(Season=a,tier=t,n=int(m.sum()),
                         mob=float(d[m.values].mean()/size[a]),
                         raw=float(d[m.values].mean()),
                         exit_rate=float((A.loc[ix,'tier'][m]!=B.loc[ix,'tier'][m]).mean())))
P=pd.DataFrame(rows)
P.to_csv('/tmp/fr/03/eng_tier_mobility_panel.csv',index=False)
print(P.pivot(index='Season',columns='tier',values='raw').round(2).to_string())
