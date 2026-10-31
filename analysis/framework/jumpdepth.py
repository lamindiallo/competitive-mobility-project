import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from depth import eng_ladder
lad=eng_ladder(4)
n=lad.groupby(['Season','tier']).size().unstack(fill_value=0)
print("\nENGLAND — mean absolute ladder-rank change of TIER-1 clubs, by ladder depth")
print(f"{'depth':>6s} {'mean |dRank|':>13s} {'ratio':>7s} {'n':>6s}")
base=None
for depth in [1,2,3,4]:
    sub=lad[lad.tier<=depth].copy()
    off={}
    for s in sorted(set(sub.Season)):
        c=0; o={}
        for t in range(1,depth+1):
            o[t]=c; c+=int(n.loc[s,t]) if t in n.columns else 0
        off[s]=o
    sub['rank']=[off[r.Season][r.tier]+r.pos for r in sub.itertuples()]
    ss=sorted(set(sub.Season)); V=[]
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=sub[(sub.Season==a)&(sub.tier==1)].drop_duplicates('k').set_index('k')
        B=sub[sub.Season==b].drop_duplicates('k').set_index('k')
        for k in A.index:
            if k in B.index: V.append(abs(B.loc[k,'rank']-A.loc[k,'rank']))
    m=np.mean(V)
    if base is None: base=m
    print(f"{depth:6d} {m:13.2f} {m/base:7.2f} {len(V):6d}")
