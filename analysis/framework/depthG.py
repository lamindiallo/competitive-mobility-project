import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from depth import eng_ladder, trans, fp
from run5 import mfpt
rng=np.random.default_rng(31)
lad=eng_ladder(4)
def statef(depth):
    def f(r):
        if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
        return 2+r.tier-1
    return f
print(f"{'depth':>6s} {'K':>3s} {'obs':>8s} {'null':>7s} {'G':>6s}  {'clubs':>6s}")
for depth in [1,2,3,4]:
    sub=lad[lad.tier<=depth]
    K=3 if depth==1 else 2+depth
    sf=(lambda r: 0 if r.pos<=4 else (1 if r.pos<=10 else 2)) if depth==1 else statef(depth)
    C=trans(sub,sf,K); o=fp(C,2,0)
    tb=sub.copy(); tb['state']=tb.apply(sf,axis=1)
    ss=sorted(tb.Season.unique()); nv=[]
    pairs=[]
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=tb[tb.Season==a].drop_duplicates('k').set_index('k').state
        B=tb[tb.Season==b].drop_duplicates('k').set_index('k').state
        ix=list(A.index.intersection(B.index)); pairs.append((A,B,ix))
    for _ in range(200):
        Cn=np.zeros((K,K))
        for A,B,ix in pairs:
            pm=rng.permutation(B[ix].values)
            for c,s2 in zip(ix,pm): Cn[A[c],s2]+=1
        if (Cn.sum(1)==0).any(): continue
        try: nv.append(mfpt(Cn/Cn.sum(1,keepdims=True),2,0))
        except Exception: pass
    n=float(np.mean(nv))
    print(f"{depth:6d} {K:3d} {o:8.2f} {n:7.2f} {o/n:6.2f}  {len(set(sub.k)):6d}")
