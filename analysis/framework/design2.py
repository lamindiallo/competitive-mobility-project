import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from run5b import lads
from scot import sco
L=dict(lads); L['SCO']=sco[sco.tier<=2]
rows=[]
for c,lad in L.items():
    lad=lad[lad.tier<=2]
    n=lad.groupby(['Season','tier']).size().unstack(fill_value=0)
    off={s:{1:0,2:int(n.loc[s,1]) if 1 in n.columns else 0} for s in n.index}
    lad=lad.copy(); lad['rank']=[off[r.Season][r.tier]+r.pos for r in lad.itertuples()]
    ss=sorted(set(lad.Season))
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=lad[lad.Season==a].drop_duplicates('k').set_index('k'); B=lad[lad.Season==b].drop_duplicates('k').set_index('k')
        ix=A.index.intersection(B.index)
        if len(ix)<20: continue
        N=len(A)
        d=(B.loc[ix,'rank']-A.loc[ix,'rank']).abs()
        t1=[k for k in ix if A.loc[k,'tier']==1]
        surv=[k for k in t1 if B.loc[k,'tier']==1]
        rho=spearmanr(A.loc[surv,'pos'],B.loc[surv,'pos']).statistic if len(surv)>6 else np.nan
        top6=[k for k in t1 if A.loc[k,'pos']<=6]
        p6=np.mean([1.0 if (B.loc[k,'tier']==1 and B.loc[k,'pos']<=6) else 0.0 for k in top6]) if top6 else np.nan
        rows.append(dict(country=c,Season=a,N=N,jump=d.mean()/N,churn=1-rho,top6persist=p6))
D=pd.DataFrame(rows); D.to_csv('/tmp/fr/03/country_mobility_panel.csv',index=False)
for out in ['jump','churn','top6persist']:
    piv=D.pivot(index='Season',columns='country',values=out)
    print(f"\n=== {out}  (rows 2005-2020)")
    print(piv.loc[2005:2020,['ITA','ESP','ENG','GER','FRA','SCO']].round(3).to_string())
