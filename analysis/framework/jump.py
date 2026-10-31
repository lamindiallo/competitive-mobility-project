import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from run5b import lads
print("="*84)
print("D. MAGNITUDE STATISTIC — mean absolute rank change of TIER-1 clubs, 1992-2024")
print("   truncated panel (relegated clubs deleted) vs pyramid ladder (relegation is a move)")
print("="*84)
print(f"{'country':8s} {'truncated':>10s} {'pyramid':>9s} {'ratio':>7s} {'n_trunc':>8s} {'n_pyr':>7s}")
rs=[]
for c in ['ENG','ESP','ITA','GER','FRA']:
    l=lads[c].copy()
    n1=l[l.tier==1].groupby('Season').size().to_dict()
    l['rank']=[r.pos if r.tier==1 else n1.get(r.Season,20)+r.pos for r in l.itertuples()]
    ss=sorted(set(l[l.tier==1].Season)&set(l[l.tier==2].Season))
    T=[];P=[]
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=l[(l.Season==a)&(l.tier==1)].drop_duplicates('k').set_index('k')
        B=l[l.Season==b].drop_duplicates('k').set_index('k')
        B1=B[B.tier==1]
        for k in A.index:
            if k in B1.index: T.append(abs(B1.loc[k,'rank']-A.loc[k,'rank']))
            if k in B.index:  P.append(abs(B.loc[k,'rank']-A.loc[k,'rank']))
    t,p=np.mean(T),np.mean(P); rs.append(p/t)
    print(f"{c:8s} {t:10.2f} {p:9.2f} {p/t:7.2f} {len(T):8d} {len(P):7d}")
print(f"{'MEAN':8s} {'':10s} {'':9s} {np.mean(rs):7.2f}   sd={np.std(rs,ddof=1):.2f}")
print("\n  Truncation UNDERSTATES movement magnitude — the opposite sign to first-passage times.")
