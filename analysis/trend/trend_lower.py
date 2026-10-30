"""Where in the pyramid did English mobility fall? Era estimates for journeys at different levels of the four-tier ladder.
States K=6 as in trend_eng (t1 top4 / t1 5-10 / t1 11-last / t2 / t3 / t4). Journeys: (2->0) bottom of top flight to top four;
(3->0) Championship to top four; (4->{0,1,2}) third tier to top flight; (5->3) fourth tier to second tier. G vs permutation null.
Usage: FR_SRC=<src> python -I trend_lower.py"""
import os, sys, numpy as np
HERE=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,HERE); sys.path.insert(0,os.path.join(HERE,'..','rcm'))
from trend_eng import pairs_of, state
from ladder import eng_ladder
from clubkey import ck
rng=np.random.default_rng(4)
def mfpt_set(P,i,targets):
    K=len(P); idx=[x for x in range(K) if x not in targets]
    A=np.eye(len(idx))-P[np.ix_(idx,idx)]
    try: return np.linalg.solve(A,np.ones(len(idx)))[idx.index(i)]
    except np.linalg.LinAlgError: return np.nan
def Gset(prs,i,T,reps=150,K=6):
    C=np.zeros((K,K))
    for a,b in prs: np.add.at(C,(a,b),1)
    if (C.sum(1)==0).any(): return np.nan
    o=mfpt_set(C/C.sum(1,keepdims=True),i,T); nv=[]
    for _ in range(reps):
        Cn=np.zeros((K,K))
        for a,b in prs: np.add.at(Cn,(a,rng.permutation(b)),1)
        if (Cn.sum(1)==0).any(): continue
        v=mfpt_set(Cn/Cn.sum(1,keepdims=True),i,T)
        if v==v: nv.append(v)
    return o/np.mean(nv) if nv and o==o else np.nan
lad=eng_ladder(4,1958,2024); lad['k']=lad.club.map(ck); lad['st']=lad.apply(state,axis=1); PR=pairs_of(lad)
J=[('t1 bottom half -> top 4',2,[0]),('Championship -> top 4',3,[0]),('third tier -> top flight',4,[0,1,2]),('fourth tier -> second tier or above',5,[0,1,2,3])]
ERAS=[(1958,1969),(1970,1980),(1981,1991),(1992,2002),(2003,2013),(2014,2023)]
print(f"{'journey':38s} "+" ".join(f"{a}-{b+1:>4d}" for a,b in ERAS))
for name,i,T in J:
    row=[]
    for a,b in ERAS:
        prs=[PR[s] for s in range(a,b+1) if s in PR]; g=Gset(prs,i,T); bs=[]
        for _ in range(100):
            r=Gset([prs[x] for x in rng.integers(0,len(prs),len(prs))],i,T,reps=30)
            if r==r and r>0: bs.append(r)
        row.append(f"{g:4.2f}[{np.percentile(bs,2.5):.2f},{np.percentile(bs,97.5):.2f}]")
    print(f"{name:38s} "+" ".join(f"{x:>17s}" for x in row))

# Raw first-passage times (seasons). For journeys that cross tiers the permutation null ignores the
# one-tier-per-season constraint (structural zeros, D126), so G is dominated by that constraint; raw MFPT is the
# comparable quantity across eras because the constraint is the same in every era.
print("\nRAW MFPT (seasons), same journeys")
print(f"{'journey':38s} "+" ".join(f"{a}-{b+1:>4d}" for a,b in ERAS))
for name,i,T in J:
    row=[]
    for a,b in ERAS:
        prs=[PR[s] for s in range(a,b+1) if s in PR]; C=np.zeros((6,6))
        for x,y in prs: np.add.at(C,(x,y),1)
        row.append(mfpt_set(C/C.sum(1,keepdims=True),i,T))
    print(f"{name:38s} "+" ".join(f"{x:9.1f}" for x in row))
