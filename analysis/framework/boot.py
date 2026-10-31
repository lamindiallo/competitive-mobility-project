import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np, pandas as pd
from names import norm
from run5 import mfpt
from run5b import lads
rng=np.random.default_rng(7)

def pairlist(lad,statef,lo=1992,hi=2024):
    tb=lad.copy(); tb['state']=tb.apply(statef,axis=1)
    ss=sorted(x for x in tb.Season.unique() if lo<=x<=hi)
    out=[]
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=tb[tb.Season==a].drop_duplicates('k').set_index('k').state
        B=tb[tb.Season==b].drop_duplicates('k').set_index('k').state
        ix=list(A.index.intersection(B.index))
        out.append((A[ix].values,B[ix].values))
    return out
def cmat(pairs,K,idx=None):
    C=np.zeros((K,K))
    for i in (range(len(pairs)) if idx is None else idx):
        a,b=pairs[i]
        for x,y in zip(a,b): C[x,y]+=1
    return C
def fpt(C,s,t):
    if (C.sum(1)==0).any(): return np.nan
    try: return mfpt(C/C.sum(1,keepdims=True),s,t)
    except Exception: return np.nan
def nullmean(pairs,K,s,t,reps=100,idx=None):
    v=[]
    ii=list(range(len(pairs))) if idx is None else list(idx)
    for _ in range(reps):
        C=np.zeros((K,K))
        for i in ii:
            a,b=pairs[i]; pm=rng.permutation(b)
            for x,y in zip(a,pm): C[x,y]+=1
        r=fpt(C,s,t)
        if not np.isnan(r): v.append(r)
    return np.mean(v) if v else np.nan

t1f=lambda r: 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
pyf=lambda r: (0 if r.pos<=4 else (1 if r.pos<=10 else 2)) if r.tier==1 else 3

print("="*90)
print("H. BLOCK BOOTSTRAP over season pairs, B=600, percentile intervals")
print("="*90)
print(f"{'country':8s} {'raw ratio':>10s} {'95% CI':>16s}   {'G ratio':>8s} {'95% CI':>16s}")
for c in ['ENG','ESP','ITA','GER','FRA']:
    l=lads[c]
    pt=pairlist(l[l.tier==1],t1f); pp=pairlist(l,pyf)
    n=min(len(pt),len(pp))
    raw0=fpt(cmat(pp,4),2,0)/fpt(cmat(pt,3),2,0)
    g0=(fpt(cmat(pp,4),2,0)/nullmean(pp,4,2,0,150))/(fpt(cmat(pt,3),2,0)/nullmean(pt,3,2,0,150))
    R=[];Gr=[]
    for _ in range(600):
        idx=rng.integers(0,n,n)
        a=fpt(cmat(pt,3,idx),2,0); b=fpt(cmat(pp,4,idx),2,0)
        if np.isnan(a) or np.isnan(b): continue
        R.append(b/a)
    for _ in range(120):
        idx=rng.integers(0,n,n)
        a=fpt(cmat(pt,3,idx),2,0); b=fpt(cmat(pp,4,idx),2,0)
        na=nullmean(pt,3,2,0,25,idx); nb=nullmean(pp,4,2,0,25,idx)
        if any(np.isnan(x) for x in [a,b,na,nb]): continue
        Gr.append((b/nb)/(a/na))
    lo,hi=np.percentile(R,[2.5,97.5]); glo,ghi=np.percentile(Gr,[2.5,97.5])
    print(f"{c:8s} {raw0:10.2f} [{lo:6.2f},{hi:6.2f}]   {g0:8.2f} [{glo:6.2f},{ghi:6.2f}]")
