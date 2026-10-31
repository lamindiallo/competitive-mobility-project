import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from scipy.stats import spearmanr
from depth import eng_ladder
lad=eng_ladder(4)
n=lad.groupby(['Season','tier']).size().unstack(fill_value=0)
off={}
for s in n.index:
    c=0; o={}
    for t in [1,2,3,4]: o[t]=c; c+=int(n.loc[s,t])
    off[s]=o
lad['rank']=[off[r.Season][r.tier]+r.pos for r in lad.itertuples()]
ss=sorted(set(lad.Season)); rows=[]
for a,b in zip(ss,ss[1:]):
    if b!=a+1: continue
    A=lad[lad.Season==a].drop_duplicates('k').set_index('k')
    B=lad[lad.Season==b].drop_duplicates('k').set_index('k')
    ix=A.index.intersection(B.index)
    for t in [1,2,3,4]:
        m=(A.loc[ix,'tier']==t)
        ks=[k for k,v in m.items() if v]
        if len(ks)<8: continue
        dl=(B.loc[ks,'rank']-A.loc[ks,'rank']).abs()
        surv=[k for k in ks if B.loc[k,'tier']==t]
        rho=spearmanr(A.loc[surv,'pos'],B.loc[surv,'pos']).statistic if len(surv)>5 else np.nan
        top6=[k for k in ks if A.loc[k,'pos']<=6]
        stay6=np.mean([1.0 if (B.loc[k,'tier']<t or (B.loc[k,'tier']==t and B.loc[k,'pos']<=6)) else 0.0 for k in top6]) if top6 else np.nan
        rows.append(dict(Season=a,tier=t,jump=dl.mean(),exitrate=(A.loc[ks,'tier']!=B.loc[ks,'tier']).mean(),
                         churn=1-rho, top6persist=stay6))
P=pd.DataFrame(rows); P.to_csv('/tmp/fr/03/eng_tier_mobility_panel.csv',index=False)

def did(piv,tr,ct,cut,lo=1992,hi=2023):
    a=piv.loc[lo:cut-1]; b=piv.loc[cut:hi]
    return (b[tr].mean()-a[tr].mean())-(b[ct].mean()-a[ct].mean())
print("="*82)
print("DESIGN 1 — multiple outcomes, League One (tier 3) SCMP; treatment year varied")
print("="*82)
for out in ['jump','exitrate','churn','top6persist']:
    piv=P.pivot(index='Season',columns='tier',values=out).dropna()
    print(f"\n--- outcome: {out}   (tier3 pre {piv.loc[1992:2010,3].mean():.3f} / post {piv.loc[2011:,3].mean():.3f})")
    for cut in [2011,2012]:
        real=did(piv,3,4,cut)
        pl=[did(piv,3,4,y) for y in range(1998,2019)]
        p=np.mean([abs(x)>=abs(real) for x in pl])
        r2=did(piv,3,2,cut); r1=did(piv,3,1,cut)
        print(f"   cut {cut}: vs L2 {real:+.3f} (placebo-year p={p:.2f})   vs Champ {r2:+.3f}   vs PL {r1:+.3f}")
    piv2=piv
    print(f"   placebo UNITS at 2011: 4v1 {did(piv2,4,1,2011):+.3f}  4v2 {did(piv2,4,2,2011):+.3f}  2v1 {did(piv2,2,1,2011):+.3f}")
