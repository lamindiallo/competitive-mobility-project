"""Long-run Gross Mobility trend, England four tiers, 1958-2024.
Pyramid state space K=6: tier-1 top 4 / tier-1 5-10 / tier-1 11-end / tier 2 / tier 3 / tier 4.
Headline statistic G = MFPT(tier-1 11-end -> tier-1 top 4) / permutation-null MFPT (D172).
Usage: FR_SRC=<src> python -I trend_eng.py <outdir>"""
import os, sys, numpy as np, pandas as pd
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,os.path.join(HERE,'..','rcm'))
from ladder import eng_ladder
from clubkey import ck
rng=np.random.default_rng(1958)
def state(r):
    if r.tier==1: return 0 if r.pos<=4 else (1 if r.pos<=10 else 2)
    return 1+r.tier            # tier2->3, tier3->4, tier4->5
def mfpt(P,i,j):
    K=len(P); idx=[x for x in range(K) if x!=j]
    A=np.eye(len(idx))-P[np.ix_(idx,idx)]
    try: return np.linalg.solve(A,np.ones(len(idx)))[idx.index(i)]
    except np.linalg.LinAlgError: return np.nan   # target unreachable in this (resampled) chain
def pairs_of(lad):
    out={}
    ss=sorted(lad.Season.unique())
    for a,b in zip(ss,ss[1:]):
        if b!=a+1: continue
        A=lad[lad.Season==a].drop_duplicates('k').set_index('k').st
        B=lad[lad.Season==b].drop_duplicates('k').set_index('k').st
        ix=A.index.intersection(B.index); out[a]=(np.array(A[ix].values,dtype=int),np.array(B[ix].values,dtype=int))
    return out
def G(prs,K=6,reps=150):
    C=np.zeros((K,K))
    for a,b in prs:
        np.add.at(C,(a,b),1)
    if (C.sum(1)==0).any(): return np.nan,np.nan,np.nan
    o=mfpt(C/C.sum(1,keepdims=True),2,0); nv=[]
    for _ in range(reps):
        Cn=np.zeros((K,K))
        for a,b in prs: np.add.at(Cn,(a,rng.permutation(b)),1)
        if (Cn.sum(1)==0).any(): continue
        v=mfpt(Cn/Cn.sum(1,keepdims=True),2,0)
        if v==v: nv.append(v)
    if o!=o or not nv: return o,np.nan,np.nan
    n=float(np.mean(nv)); return o,n,o/n
if __name__=='__main__':
    out=sys.argv[1]; os.makedirs(out,exist_ok=True)
    lad=eng_ladder(4,1958,2024); lad['k']=lad.club.map(ck); lad['st']=lad.apply(state,axis=1)
    PR=pairs_of(lad)
    rows=[]
    W=12
    starts=[s for s in sorted(PR) if all((s+j) in PR for j in range(W))]
    for s in starts:
        prs=[PR[s+j] for j in range(W)]
        o,n,g=G(prs)
        # block bootstrap over season pairs
        bs=[]
        for _ in range(80):
            pick=rng.integers(0,W,W); o2,n2,g2=G([prs[i] for i in pick],reps=40)
            if g2==g2: bs.append(g2)
        rows.append(dict(window=f"{s}-{s+W}",start=s,mid=s+W/2,mfpt=o,null=n,G=g,lo=np.percentile(bs,2.5),hi=np.percentile(bs,97.5)))
        print(f"{s}-{s+W}: MFPT {o:7.1f}  null {n:6.1f}  G {g:5.2f}  [{rows[-1]['lo']:.2f},{rows[-1]['hi']:.2f}]",flush=True)
    pd.DataFrame(rows).to_csv(f"{out}/eng_rolling_G.csv",index=False)
